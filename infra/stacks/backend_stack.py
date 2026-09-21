"""Lambda (FastAPI + Mangum) behind API Gateway HTTP API, fronted by WAF.

AWS Migration Plan, Section 3.2 and Section 4: "Same application code; runs
only per-request, scales to zero, scales out automatically." No VPC
attachment (Section 3.3) - Lambda reaches Aurora over the RDS Data API and
Bedrock over its public AWS API endpoint, both plain HTTPS.

Known limitation worth flagging explicitly (not silently designed around):
API Gateway integrations - REST or HTTP API - have a hard 29-second
synchronous timeout that AWS does not allow raising. The existing frontend
already accounts for slow answers (frontend/src/config/api.ts sets a
180s client-side timeout because "Hybrid RAG + gpt-5.x often exceeds 30s").
Claude Haiku 4.5 should comfortably answer within 29s (it is the
plan's "fast, cheap" pick, Section 6.3), but this must be validated against
real hybrid-route latency before cutover (see docs/AWS_DEPLOYMENT.md,
"Known limitations"). If it is not fast enough, the documented fallback is
a Lambda Function URL behind CloudFront + WAF instead of API Gateway,
since Function URLs allow the full 15-minute Lambda timeout - a bigger
change than swapping one construct here, so it is not implemented
speculatively.
"""

from __future__ import annotations

from typing import Optional

from aws_cdk import BundlingOptions, Duration, Fn
from aws_cdk import aws_apigatewayv2 as apigwv2
from aws_cdk import aws_apigatewayv2_integrations as apigwv2_integrations
from aws_cdk import aws_iam as iam
from aws_cdk import aws_lambda as _lambda
from aws_cdk import aws_logs as logs
from aws_cdk import aws_wafv2 as wafv2
from constructs import Construct

# backend/ has three sibling packages the Lambda needs together (rag/,
# database/, aws/) but only one of them (rag/) is the API entry point, and
# backend/requirements.txt is the full local-dev dependency set (jupyter,
# pandas, hsclient, ...) that Appendix A explicitly says the Lambda package
# no longer needs. aws_lambda_python_alpha.PythonFunction auto-detects a
# requirements.txt sitting directly in `entry` with no way to point it at a
# different file, which does not fit this layout - so this bundles with a
# plain lambda.Function + an explicit Docker bundling command instead,
# installing from requirements-lambda.txt and copying just the three
# packages this app actually needs at runtime.
_BUNDLE_COMMAND = [
    "bash",
    "-c",
    (
        "pip install --no-cache-dir -r requirements-lambda.txt -t /asset-output "
        "&& cp -r rag database aws /asset-output/"
    ),
]


class BackendStack(Construct):
    def __init__(
        self,
        scope: Construct,
        construct_id: str,
        *,
        project_name: str,
        backend_source_dir: str,
        aurora_cluster_arn: str,
        aurora_secret_arn: str,
        aurora_database: str,
        allowed_origins: str,
        guardrail_id: Optional[str] = None,
        guardrail_version: Optional[str] = None,
        bedrock_chat_model_id: str = "anthropic.claude-haiku-4-5-v1:0",
        bedrock_embed_model_id: str = "amazon.titan-embed-text-v2:0",
        bedrock_embed_dimensions: int = 1024,
        retrieval_similarity_threshold: float = 0.7,
        waf_rate_limit_per_5min: int = 1000,
    ) -> None:
        super().__init__(scope, construct_id)

        environment = {
            "LLM_PROVIDER": "bedrock",
            "DB_BACKEND": "rds_data_api",
            "AURORA_CLUSTER_ARN": aurora_cluster_arn,
            "AURORA_SECRET_ARN": aurora_secret_arn,
            "AURORA_DATABASE": aurora_database,
            "POSTGRES_SCHEMA": "public",
            "ALLOWED_ORIGINS": allowed_origins,
            "BEDROCK_CHAT_MODEL_ID": bedrock_chat_model_id,
            "BEDROCK_EMBED_MODEL_ID": bedrock_embed_model_id,
            "BEDROCK_EMBED_DIMENSIONS": str(bedrock_embed_dimensions),
            "RETRIEVAL_SIMILARITY_THRESHOLD": str(retrieval_similarity_threshold),
        }
        if guardrail_id:
            environment["BEDROCK_GUARDRAIL_ID"] = guardrail_id
            environment["BEDROCK_GUARDRAIL_VERSION"] = guardrail_version or "DRAFT"

        runtime = _lambda.Runtime.PYTHON_3_12
        function_name = f"{project_name}-ask".lower()
        self.function = _lambda.Function(
            self,
            "AskFunction",
            function_name=function_name,
            runtime=runtime,
            handler="rag.lambda_handler.handler",
            code=_lambda.Code.from_asset(
                backend_source_dir,
                bundling=BundlingOptions(
                    image=runtime.bundling_image,
                    command=_BUNDLE_COMMAND,
                ),
            ),
            timeout=Duration.seconds(28),  # stay under API Gateway's fixed 29s cap
            memory_size=1024,
            environment=environment,
            log_group=logs.LogGroup(
                self,
                "AskFunctionLogs",
                log_group_name=f"/aws/lambda/{function_name}",
                retention=logs.RetentionDays.ONE_MONTH,
            ),
        )

        # Least-privilege IAM (Section 9.3: "no wildcard resource
        # permissions"). Bedrock model invocation is scoped to the account's
        # models generally (Bedrock foundation-model ARNs are not
        # account-owned resources, so this cannot be scoped further); Data
        # API and Secrets Manager access is scoped to this cluster/secret only.
        self.function.add_to_role_policy(
            iam.PolicyStatement(
                actions=["bedrock:InvokeModel", "bedrock:Converse", "bedrock:ApplyGuardrail"],
                resources=["*"],
            )
        )
        self.function.add_to_role_policy(
            iam.PolicyStatement(
                actions=[
                    "rds-data:ExecuteStatement",
                    "rds-data:BatchExecuteStatement",
                ],
                resources=[aurora_cluster_arn],
            )
        )
        self.function.add_to_role_policy(
            iam.PolicyStatement(
                actions=["secretsmanager:GetSecretValue"],
                resources=[aurora_secret_arn],
            )
        )

        self.http_api = apigwv2.HttpApi(
            self,
            "HttpApi",
            api_name=f"{project_name}-api",
            create_default_stage=False,
            default_integration=apigwv2_integrations.HttpLambdaIntegration(
                "AskIntegration", handler=self.function
            ),
            cors_preflight=apigwv2.CorsPreflightOptions(
                allow_origins=allowed_origins.split(","),
                allow_methods=[apigwv2.CorsHttpMethod.GET, apigwv2.CorsHttpMethod.POST],
                allow_headers=["Content-Type"],
            ),
        )
        # create_default_stage=False + an explicit HttpStage here because
        # ThrottleSettings (API Gateway throttling, Section 4 step 4 and
        # 8.4's cost-control list) can only be set at HttpStage construction
        # time, not on the auto-created default stage after the fact.
        self.stage = apigwv2.HttpStage(
            self,
            "DefaultStage",
            http_api=self.http_api,
            stage_name="$default",
            auto_deploy=True,
            throttle=apigwv2.ThrottleSettings(
                rate_limit=50,  # steady-state requests/sec; starting guess, Section 11
                burst_limit=100,
            ),
        )

        self.web_acl = wafv2.CfnWebACL(
            self,
            "WebAcl",
            name=f"{project_name}-api-waf",
            scope="REGIONAL",
            default_action=wafv2.CfnWebACL.DefaultActionProperty(allow={}),
            visibility_config=wafv2.CfnWebACL.VisibilityConfigProperty(
                sampled_requests_enabled=True,
                cloud_watch_metrics_enabled=True,
                metric_name=f"{project_name}-api-waf",
            ),
            rules=[
                wafv2.CfnWebACL.RuleProperty(
                    name="RateLimitPerIp",
                    priority=0,
                    action=wafv2.CfnWebACL.RuleActionProperty(block={}),
                    statement=wafv2.CfnWebACL.StatementProperty(
                        rate_based_statement=wafv2.CfnWebACL.RateBasedStatementProperty(
                            limit=waf_rate_limit_per_5min,
                            aggregate_key_type="IP",
                        )
                    ),
                    visibility_config=wafv2.CfnWebACL.VisibilityConfigProperty(
                        sampled_requests_enabled=True,
                        cloud_watch_metrics_enabled=True,
                        metric_name=f"{project_name}-rate-limit",
                    ),
                ),
                wafv2.CfnWebACL.RuleProperty(
                    name="AWSManagedCommonRuleSet",
                    priority=1,
                    override_action=wafv2.CfnWebACL.OverrideActionProperty(none={}),
                    statement=wafv2.CfnWebACL.StatementProperty(
                        managed_rule_group_statement=wafv2.CfnWebACL.ManagedRuleGroupStatementProperty(
                            vendor_name="AWS",
                            name="AWSManagedRulesCommonRuleSet",
                        )
                    ),
                    visibility_config=wafv2.CfnWebACL.VisibilityConfigProperty(
                        sampled_requests_enabled=True,
                        cloud_watch_metrics_enabled=True,
                        metric_name=f"{project_name}-common-rules",
                    ),
                ),
                # Optional, extra cost (~$10/month): AWS Managed Bot Control.
                # Uncomment if scraper/bot abuse becomes a real problem
                # (Section 9.1 is about *scope*, not just cost, but bot
                # traffic is a volume concern this rule targets directly).
                # wafv2.CfnWebACL.RuleProperty(
                #     name="AWSManagedBotControl",
                #     priority=2,
                #     override_action=wafv2.CfnWebACL.OverrideActionProperty(none={}),
                #     statement=wafv2.CfnWebACL.StatementProperty(
                #         managed_rule_group_statement=wafv2.CfnWebACL.ManagedRuleGroupStatementProperty(
                #             vendor_name="AWS", name="AWSManagedRulesBotControlRuleSet"
                #         )
                #     ),
                #     visibility_config=wafv2.CfnWebACL.VisibilityConfigProperty(
                #         sampled_requests_enabled=True, cloud_watch_metrics_enabled=True,
                #         metric_name=f"{project_name}-bot-control",
                #     ),
                # ),
            ],
        )

        self.web_acl_association = wafv2.CfnWebACLAssociation(
            self,
            "WebAclAssociation",
            resource_arn=self._stage_arn(),
            web_acl_arn=self.web_acl.attr_arn,
        )

        # Host-only form of api_endpoint (a CloudFormation-resolved Token,
        # not a plain Python string - Fn.select/Fn.split is the safe way to
        # pick the host out of it) for FrontendStack's CloudFront origin
        # (Section 4, step 2: CloudFront routes /ask to the API origin).
        self.api_domain_name = Fn.select(2, Fn.split("/", self.http_api.api_endpoint))

    def _stage_arn(self) -> str:
        # HTTP API stage ARN format WAFv2 expects:
        # arn:aws:apigateway:{region}::/apis/{api-id}/stages/{stage-name}
        from aws_cdk import Stack

        stack = Stack.of(self)
        return (
            f"arn:aws:apigateway:{stack.region}::/apis/"
            f"{self.http_api.http_api_id}/stages/{self.stage.stage_name}"
        )
