"""Lambda (FastAPI + Mangum) behind API Gateway HTTP API, plus a streaming
twin of it behind a Lambda Function URL for POST /ask/stream.

AWS WAF sits in front of this on the CloudFront distribution
(frontend_stack.py), not here: WAF cannot be attached to API Gateway HTTP
APIs (only REST APIs), and at CloudFront it also sees the real viewer IP
for its per-IP rate limit.

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
"Known limitations"). The chat now uses the streaming path instead: a
Lambda Function URL behind CloudFront + WAF (no 29s cap, and the answer is
shown word by word as it is generated). /ask stays as the non-streaming
fallback the frontend uses if streaming fails.
"""

from __future__ import annotations

import shutil
import subprocess
import sys
from pathlib import Path
from typing import Optional

import jsii
from aws_cdk import BundlingOptions, Duration, Fn, ILocalBundling, RemovalPolicy, Stack
from aws_cdk import aws_apigatewayv2 as apigwv2
from aws_cdk import aws_apigatewayv2_integrations as apigwv2_integrations
from aws_cdk import aws_iam as iam
from aws_cdk import aws_lambda as _lambda
from aws_cdk import aws_logs as logs
from constructs import Construct

# backend/ has three sibling packages the Lambda needs together (rag/,
# database/, aws/), but also ~70 MB of scraped source data, notebooks and
# JSON that the /ask path never reads, and backend/requirements.txt is the
# full local-dev dependency set (jupyter, pandas, hsclient, ...) that
# Appendix A says the Lambda package no longer needs. So the package is
# built explicitly: dependencies from requirements-lambda.txt, plus only
# the .py files of those three packages.
_LAMBDA_PACKAGES = ("rag", "database", "aws")
_LAMBDA_PYTHON_VERSION = "3.12"

# Excluded from the asset's source hash, so editing a notebook or re-scraping
# data does not trigger a Lambda redeploy.
_ASSET_EXCLUDE = [
    "**/__pycache__",
    "**/*.ipynb",
    "**/*.json",
    "**/*.csv",
    "**/.env",
    "database/CIROH-Hub",
    "database/GitHub-CIROH-CodeRepos",
    "database/HydroShare-CIROH-Datasets",
    "database/json",
    "node_modules",
]

# Startup script for the streaming function: the Lambda Web Adapter layer
# runs it, then forwards each invocation to uvicorn on $PORT and streams
# the HTTP response back through the Function URL.
_RUN_SH = """#!/bin/sh
cd "$LAMBDA_TASK_ROOT"
exec python3 -m uvicorn --app-dir rag --host 127.0.0.1 --port "$PORT" main:app
"""

# Docker fallback, only used if the local build below fails.
_BUNDLE_COMMAND = [
    "bash",
    "-c",
    (
        "pip install --no-cache-dir -r requirements-lambda.txt -t /asset-output "
        "&& for p in rag database aws; do mkdir -p /asset-output/$p && cp $p/*.py /asset-output/$p/; done "
        f"&& printf '%s' '{_RUN_SH}' > /asset-output/run.sh && chmod 755 /asset-output/run.sh"
    ),
]


@jsii.implements(ILocalBundling)
class _LocalPipBundler:
    """Builds the Lambda package with the local pip instead of Docker.

    pip downloads Linux (manylinux) wheels for Lambda's Python version, so
    this works from Windows/macOS without Docker Desktop. Returning False
    makes CDK fall back to the Docker build above.
    """

    def __init__(self, source_dir: str) -> None:
        self.source_dir = Path(source_dir)

    def try_bundle(self, output_dir: str, options: BundlingOptions) -> bool:  # noqa: ARG002
        out = Path(output_dir)
        cmd = [
            sys.executable, "-m", "pip", "install",
            "-r", str(self.source_dir / "requirements-lambda.txt"),
            "-t", str(out),
            "--platform", "manylinux2014_x86_64",
            "--implementation", "cp",
            "--python-version", _LAMBDA_PYTHON_VERSION,
            "--only-binary=:all:",
            "--upgrade",
            "--quiet",
            "--disable-pip-version-check",
        ]
        print("Bundling Lambda package with local pip (no Docker needed)...")
        if subprocess.run(cmd, check=False).returncode != 0:
            print("Local pip bundling failed; falling back to Docker bundling.")
            return False
        for package in _LAMBDA_PACKAGES:
            dest = out / package
            dest.mkdir(parents=True, exist_ok=True)
            for py_file in (self.source_dir / package).glob("*.py"):
                shutil.copy2(py_file, dest / py_file.name)
        run_sh = out / "run.sh"
        run_sh.write_bytes(_RUN_SH.encode())
        run_sh.chmod(0o755)
        return True


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
        bedrock_chat_model_id: str = "us.anthropic.claude-haiku-4-5-20251001-v1:0",
        bedrock_embed_model_id: str = "amazon.titan-embed-text-v2:0",
        bedrock_embed_dimensions: int = 1024,
        retrieval_similarity_threshold: float = 0.7,
        web_adapter_layer_version: int = 25,
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
        code = _lambda.Code.from_asset(
            backend_source_dir,
            exclude=_ASSET_EXCLUDE,
            bundling=BundlingOptions(
                image=runtime.bundling_image,
                command=_BUNDLE_COMMAND,
                local=_LocalPipBundler(backend_source_dir),
            ),
        )

        function_name = f"{project_name}-ask".lower()
        self.function = _lambda.Function(
            self,
            "AskFunction",
            function_name=function_name,
            runtime=runtime,
            handler="rag.lambda_handler.handler",
            code=code,
            timeout=Duration.seconds(28),  # stay under API Gateway's fixed 29s cap
            memory_size=1024,
            environment=environment,
            log_group=logs.LogGroup(
                self,
                "AskFunctionLogs",
                log_group_name=f"/ciroh-docuhub/{function_name}", removal_policy=RemovalPolicy.DESTROY,
                retention=logs.RetentionDays.ONE_MONTH,
            ),
        )

        # Streaming answers (POST /ask/stream). API Gateway buffers whole
        # responses, so this second function sits behind a Function URL in
        # RESPONSE_STREAM mode (reached only through CloudFront + WAF, see
        # frontend_stack.py). Python has no native Lambda response
        # streaming, so the AWS Lambda Web Adapter layer runs the same
        # FastAPI app under uvicorn (run.sh) and streams its output. No 29s
        # cap here, so a cold database is waited out instead of refused.
        stream_function_name = f"{project_name}-ask-stream".lower()
        self.stream_function = _lambda.Function(
            self,
            "AskStreamFunction",
            function_name=stream_function_name,
            runtime=runtime,
            handler="run.sh",
            code=code,
            timeout=Duration.seconds(120),
            memory_size=1024,
            environment={
                **environment,
                "AWS_LAMBDA_EXEC_WRAPPER": "/opt/bootstrap",
                "AWS_LWA_INVOKE_MODE": "response_stream",
                "AWS_LWA_READINESS_CHECK_PATH": "/",
                "PORT": "8080",
                "STREAM_DB_WAIT_BUDGET_SECONDS": "45",
            },
            layers=[
                _lambda.LayerVersion.from_layer_version_arn(
                    self,
                    "WebAdapterLayer",
                    f"arn:aws:lambda:{Stack.of(self).region}:753240598075:layer:"
                    f"LambdaAdapterLayerX86:{web_adapter_layer_version}",
                )
            ],
            log_group=logs.LogGroup(
                self,
                "AskStreamFunctionLogs",
                log_group_name=f"/ciroh-docuhub/{stream_function_name}",
                removal_policy=RemovalPolicy.DESTROY,
                retention=logs.RetentionDays.ONE_MONTH,
            ),
        )
        # IAM-authenticated: only CloudFront (via Origin Access Control) can
        # call it, so WAF's rate limit cannot be bypassed.
        self.stream_function_url = self.stream_function.add_function_url(
            auth_type=_lambda.FunctionUrlAuthType.AWS_IAM,
            invoke_mode=_lambda.InvokeMode.RESPONSE_STREAM,
        )

        # Least-privilege IAM (Section 9.3). Bedrock is scoped by action, not
        # resource: Claude Haiku 4.5 runs through a cross-region inference
        # profile, which needs InvokeModel on the profile *and* on the
        # foundation model in every region it may route to. Converse is
        # authorized by bedrock:InvokeModel (there is no separate action;
        # ConverseStream needs InvokeModelWithResponseStream).
        # Data API and Secrets Manager access is scoped to this cluster/secret.
        for fn in (self.function, self.stream_function):
            fn.add_to_role_policy(
                iam.PolicyStatement(
                    actions=[
                        "bedrock:InvokeModel",
                        "bedrock:InvokeModelWithResponseStream",
                        "bedrock:ApplyGuardrail",
                    ],
                    resources=["*"],
                )
            )
            fn.add_to_role_policy(
                iam.PolicyStatement(
                    actions=[
                        "rds-data:ExecuteStatement",
                        "rds-data:BatchExecuteStatement",
                    ],
                    resources=[aurora_cluster_arn],
                )
            )
            fn.add_to_role_policy(
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

        # Host-only form of api_endpoint (a CloudFormation-resolved Token,
        # not a plain Python string - Fn.select/Fn.split is the safe way to
        # pick the host out of it) for FrontendStack's CloudFront origin
        # (Section 4, step 2: CloudFront routes /ask to the API origin).
        self.api_domain_name = Fn.select(2, Fn.split("/", self.http_api.api_endpoint))
