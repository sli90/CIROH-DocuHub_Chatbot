"""S3 + CloudFront frontend hosting, with /ask and /telemetry proxied to the API.

AWS Migration Plan, Section 3.2 ("Static hosting for a built SPA; pay per
GB served, scales infinitely, no servers") and Section 4, step 2: "the SPA
POSTs { text } to /api/ask, which CloudFront routes (via a separate cache
behavior) to the API origin instead of S3." This deployment keeps the
existing frontend's actual route names (`/ask`, `/telemetry` -
frontend/src/config/api.ts and backend/rag/main.py) rather than renaming
them to `/api/ask`, so no frontend or backend route code has to change for
the cutover - only two CloudFront cache behaviors.

Routing both through one CloudFront distribution also means the browser's
requests to /ask are same-origin in production, so ALLOWED_ORIGINS-based
CORS (backend_stack.py) only matters for local dev and any direct,
cross-origin calls to the API Gateway domain - not for normal production
traffic.

AWS WAF (rate limit per viewer IP + AWS managed common rules) is attached
here, to the distribution, because WAF cannot protect API Gateway HTTP APIs
directly. CloudFront-scoped web ACLs must be created in us-east-1, so WAF
is only added when the stack is deployed there (the default region).

Deploy this after backend_stack.py (it takes the API's domain name as an
input) and build the frontend with VITE_API_BASE_URL="" so requests go to
same-origin relative paths (see docs/AWS_DEPLOYMENT.md).
"""

from __future__ import annotations

from aws_cdk import Aws, Duration, RemovalPolicy
from aws_cdk import aws_cloudfront as cloudfront
from aws_cdk import aws_cloudfront_origins as origins
from aws_cdk import aws_lambda as _lambda
from aws_cdk import aws_s3 as s3
from aws_cdk import aws_s3_deployment as s3_deployment
from aws_cdk import aws_wafv2 as wafv2
from constructs import Construct


class FrontendStack(Construct):
    def __init__(
        self,
        scope: Construct,
        construct_id: str,
        *,
        project_name: str,
        api_domain_name: str,
        stream_function_url: _lambda.IFunctionUrl | None = None,
        frontend_dist_dir: str | None = None,
        removal_policy: RemovalPolicy = RemovalPolicy.RETAIN,
        enable_waf: bool = True,
        waf_rate_limit_per_5min: int = 500,
    ) -> None:
        super().__init__(scope, construct_id)

        self.web_acl = (
            self._web_acl(project_name, waf_rate_limit_per_5min) if enable_waf else None
        )

        self.bucket = s3.Bucket(
            self,
            "FrontendBucket",
            bucket_name=None,  # let CFN generate a unique name
            removal_policy=removal_policy,
            auto_delete_objects=removal_policy == RemovalPolicy.DESTROY,
            block_public_access=s3.BlockPublicAccess.BLOCK_ALL,
            encryption=s3.BucketEncryption.S3_MANAGED,
        )

        s3_origin = origins.S3BucketOrigin.with_origin_access_control(self.bucket)
        api_origin = origins.HttpOrigin(
            api_domain_name,
            protocol_policy=cloudfront.OriginProtocolPolicy.HTTPS_ONLY,
        )

        # Caching disabled + all-viewer forwarding for the API behavior:
        # /ask is a POST with a JSON body and must not be cached, and needs
        # its headers/method forwarded through untouched.
        api_behavior = cloudfront.BehaviorOptions(
            origin=api_origin,
            viewer_protocol_policy=cloudfront.ViewerProtocolPolicy.HTTPS_ONLY,
            allowed_methods=cloudfront.AllowedMethods.ALLOW_ALL,
            cache_policy=cloudfront.CachePolicy.CACHING_DISABLED,
            origin_request_policy=cloudfront.OriginRequestPolicy.ALL_VIEWER_EXCEPT_HOST_HEADER,
        )

        additional_behaviors = {
            "/ask": api_behavior,
            "/telemetry": api_behavior,
        }
        if stream_function_url is not None:
            # Streaming answers go straight to the streaming Lambda's
            # Function URL, signed by Origin Access Control (the URL is
            # IAM-authenticated, so it is unreachable except through here).
            # 60s is the most CloudFront allows between bytes without a
            # quota increase; the backend sends a keep-alive every 10s.
            additional_behaviors["/ask/stream"] = cloudfront.BehaviorOptions(
                origin=origins.FunctionUrlOrigin.with_origin_access_control(
                    stream_function_url,
                    read_timeout=Duration.seconds(60),
                ),
                viewer_protocol_policy=cloudfront.ViewerProtocolPolicy.HTTPS_ONLY,
                allowed_methods=cloudfront.AllowedMethods.ALLOW_ALL,
                cache_policy=cloudfront.CachePolicy.CACHING_DISABLED,
                origin_request_policy=cloudfront.OriginRequestPolicy.ALL_VIEWER_EXCEPT_HOST_HEADER,
            )

        self.distribution = cloudfront.Distribution(
            self,
            "Distribution",
            comment=f"{project_name} frontend + API edge",
            default_root_object="index.html",
            default_behavior=cloudfront.BehaviorOptions(
                origin=s3_origin,
                viewer_protocol_policy=cloudfront.ViewerProtocolPolicy.REDIRECT_TO_HTTPS,
                cache_policy=cloudfront.CachePolicy.CACHING_OPTIMIZED,
            ),
            additional_behaviors=additional_behaviors,
            # No SPA error_responses (403/404 -> index.html): the frontend has
            # no client-side routes, and those rewrites are distribution-wide,
            # so they would also turn API/WAF errors on /ask into an HTML page.
            web_acl_id=self.web_acl.attr_arn if self.web_acl else None,
        )

        if stream_function_url is not None:
            # Function URLs created since Oct 2025 also need lambda:InvokeFunction
            # (scoped to URL invocations); CDK's OAC origin only grants
            # lambda:InvokeFunctionUrl.
            _lambda.CfnPermission(
                self,
                "StreamInvokeFromCloudFront",
                action="lambda:InvokeFunction",
                function_name=stream_function_url.function_arn,
                principal="cloudfront.amazonaws.com",
                source_arn=(
                    f"arn:{Aws.PARTITION}:cloudfront::{Aws.ACCOUNT_ID}:"
                    f"distribution/{self.distribution.distribution_id}"
                ),
                invoked_via_function_url=True,
            )

        if frontend_dist_dir:
            # Two uploads with different browser caching. Vite puts a content
            # hash in every assets/ filename, so those can be cached for a
            # year. index.html keeps its name and points at the current
            # hashes, so it must be revalidated on every load, or browsers keep
            # running the previous release after a deploy.
            # prune=False on both: each would otherwise delete the other's
            # files (old hashed assets are left behind; they are tiny).
            assets = s3_deployment.BucketDeployment(
                self,
                "DeployFrontend",
                sources=[s3_deployment.Source.asset(frontend_dist_dir, exclude=["index.html"])],
                destination_bucket=self.bucket,
                prune=False,
                cache_control=[
                    s3_deployment.CacheControl.from_string("public, max-age=31536000, immutable")
                ],
            )
            index = s3_deployment.BucketDeployment(
                self,
                "DeployIndexHtml",
                sources=[s3_deployment.Source.asset(frontend_dist_dir, exclude=["*", "!index.html"])],
                destination_bucket=self.bucket,
                prune=False,
                cache_control=[s3_deployment.CacheControl.no_cache()],
                distribution=self.distribution,
                distribution_paths=["/*"],
            )
            # New index.html only after the assets it references exist.
            index.node.add_dependency(assets)

        self.domain_name = self.distribution.distribution_domain_name

    def _web_acl(self, project_name: str, rate_limit_per_5min: int) -> wafv2.CfnWebACL:
        """Section 4 step 3 / 8.4: per-IP rate limit + AWS managed common rules."""

        def visibility(metric: str) -> wafv2.CfnWebACL.VisibilityConfigProperty:
            return wafv2.CfnWebACL.VisibilityConfigProperty(
                sampled_requests_enabled=True,
                cloud_watch_metrics_enabled=True,
                metric_name=metric,
            )

        return wafv2.CfnWebACL(
            self,
            "WebAcl",
            name=f"{project_name}-waf",
            scope="CLOUDFRONT",
            default_action=wafv2.CfnWebACL.DefaultActionProperty(allow={}),
            visibility_config=visibility(f"{project_name}-waf"),
            rules=[
                # Only /ask and /telemetry reach Lambda/Bedrock, so only they
                # are rate limited; static page loads are cheap CDN hits.
                wafv2.CfnWebACL.RuleProperty(
                    name="RateLimitApiPerIp",
                    priority=0,
                    action=wafv2.CfnWebACL.RuleActionProperty(block={}),
                    statement=wafv2.CfnWebACL.StatementProperty(
                        rate_based_statement=wafv2.CfnWebACL.RateBasedStatementProperty(
                            limit=rate_limit_per_5min,
                            aggregate_key_type="IP",
                            scope_down_statement=wafv2.CfnWebACL.StatementProperty(
                                byte_match_statement=wafv2.CfnWebACL.ByteMatchStatementProperty(
                                    field_to_match=wafv2.CfnWebACL.FieldToMatchProperty(uri_path={}),
                                    positional_constraint="STARTS_WITH",
                                    search_string="/ask",
                                    text_transformations=[
                                        wafv2.CfnWebACL.TextTransformationProperty(
                                            priority=0, type="LOWERCASE"
                                        )
                                    ],
                                )
                            ),
                        )
                    ),
                    visibility_config=visibility(f"{project_name}-rate-limit"),
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
                    visibility_config=visibility(f"{project_name}-common-rules"),
                ),
            ],
        )
