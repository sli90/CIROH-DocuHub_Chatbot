#!/usr/bin/env python3
"""CDK app entry point.

Everything lives in one CloudFormation stack (CirohStack below), assembled
from the Construct-level building blocks in stacks/*.py. For a project this
size, one stack means one atomic `cdk deploy`, no cross-stack exports/
imports to manage, and no deploy-ordering to get right by hand - the
Python-level dependencies between the building blocks (Frontend needs the
Backend's API domain, Backend optionally needs the Guardrail's id) are just
plain attribute references, resolved automatically at synth time.

See docs/AWS_DEPLOYMENT.md for the full deploy walkthrough. Quick start:

    cd infra
    python -m venv .venv && .venv/Scripts/activate  # or source .venv/bin/activate
    pip install -r requirements.txt
    cdk bootstrap
    cdk deploy CirohStack -c budget_alert_email=you@example.com

No Docker needed by default. The Fargate ingestion task (a container image)
is opt-in with `-c enable_ingestion=true`, which does need Docker running.
"""

from __future__ import annotations

import os
from pathlib import Path

import aws_cdk as cdk
from aws_cdk import RemovalPolicy, Tags
from constructs import Construct

from stacks.backend_stack import BackendStack
from stacks.cicd_stack import CicdStack
from stacks.database_stack import DatabaseStack
from stacks.frontend_stack import FrontendStack
from stacks.guardrail_stack import GuardrailStack
from stacks.ingestion_stack import IngestionStack
from stacks.network_stack import NetworkStack
from stacks.observability_stack import ObservabilityStack

REPO_ROOT = Path(__file__).resolve().parent.parent
BACKEND_DIR = str(REPO_ROOT / "backend")
FRONTEND_DIST_DIR = REPO_ROOT / "frontend" / "dist"


class CirohStack(cdk.Stack):
    def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        project_name = self.node.try_get_context("project_name") or "CIROH-DocuHub"
        env_name = self.node.try_get_context("env_name") or "dev"
        is_prod = env_name == "prod"
        min_acu = float(self.node.try_get_context("aurora_min_acu") or 0)
        max_acu = float(self.node.try_get_context("aurora_max_acu") or 4)
        budget_usd = float(self.node.try_get_context("budget_monthly_usd") or 60)
        alert_email = self.node.try_get_context("budget_alert_email") or None
        # Some university/organization accounts block AWS Budgets via a
        # service control policy; -c enable_budgets=false skips them.
        enable_budgets = str(self.node.try_get_context("enable_budgets")).lower() != "false"
        # Retrieval-gate cosine-distance cutoff (docs/GUARDRAILS_AND_COST.md).
        similarity_threshold = float(self.node.try_get_context("retrieval_similarity_threshold") or 0.7)
        # Bedrock model that writes the answers. Anthropic models need a one-time
        # AWS Marketplace subscription; Amazon Nova models (e.g.
        # "us.amazon.nova-pro-v1:0") do not.
        chat_model_id = (
            self.node.try_get_context("bedrock_chat_model_id")
            or "us.anthropic.claude-haiku-4-5-20251001-v1:0"
        )
        # Set once the frontend's real domain is known (either a manually
        # supplied custom domain, or the CloudFront domain from a first
        # deploy's output) - see docs/AWS_DEPLOYMENT.md, "Two-phase deploy".
        allowed_origins = self.node.try_get_context("allowed_origins") or "http://localhost:5173"
        # The Fargate ingestion task is built from a Docker image, so it is
        # opt-in: the one-time corpus migration runs fine from a laptop
        # (docs/AWS_DEPLOYMENT.md), and the recurring ingestion it exists for
        # is still notebook-driven (README, "In Progress / Planned").
        enable_ingestion = str(self.node.try_get_context("enable_ingestion")).lower() == "true"
        # CloudFront-scoped WAF web ACLs can only be created in us-east-1.
        enable_waf = self.region == "us-east-1"
        if not enable_waf:
            cdk.Annotations.of(self).add_warning(
                f"Region is {self.region}, not us-east-1: CloudFront WAF skipped. "
                "API Gateway throttling and Budgets still apply."
            )

        network = NetworkStack(self, "Network", project_name=project_name)

        database = DatabaseStack(
            self,
            "Database",
            project_name=project_name,
            vpc=network.vpc,
            security_group=network.aurora_security_group,
            min_acu=min_acu,
            max_acu=max_acu,
            removal_policy=RemovalPolicy.SNAPSHOT if is_prod else RemovalPolicy.DESTROY,
        )

        guardrail = GuardrailStack(self, "Guardrail", project_name=project_name)

        backend = BackendStack(
            self,
            "Backend",
            project_name=project_name,
            backend_source_dir=BACKEND_DIR,
            aurora_cluster_arn=database.cluster_arn,
            aurora_secret_arn=database.secret_arn,
            aurora_database=database.database_name,
            allowed_origins=allowed_origins,
            guardrail_id=guardrail.guardrail_id,
            guardrail_version=guardrail.guardrail_version,
            retrieval_similarity_threshold=similarity_threshold,
            bedrock_chat_model_id=chat_model_id,
        )

        frontend = FrontendStack(
            self,
            "Frontend",
            project_name=project_name,
            api_domain_name=backend.api_domain_name,
            stream_function_url=backend.stream_function_url,
            frontend_dist_dir=str(FRONTEND_DIST_DIR) if FRONTEND_DIST_DIR.exists() else None,
            removal_policy=RemovalPolicy.RETAIN if is_prod else RemovalPolicy.DESTROY,
            enable_waf=enable_waf,
        )

        if enable_ingestion:
            ingestion = IngestionStack(
                self,
                "Ingestion",
                project_name=project_name,
                vpc=network.vpc,
                security_group=network.ingestion_security_group,
                repo_root=str(REPO_ROOT),
                aurora_cluster_arn=database.cluster_arn,
                aurora_secret_arn=database.secret_arn,
                aurora_database=database.database_name,
            )
            cdk.CfnOutput(self, "IngestionClusterName", value=ingestion.cluster.cluster_name)

        ObservabilityStack(
            self,
            "Observability",
            project_name=project_name,
            function=backend.function,
            http_api_id=backend.http_api.http_api_id,
            monthly_budget_usd=budget_usd,
            alert_email=alert_email,
            enable_budgets=enable_budgets,
        )

        cdk.CfnOutput(self, "FrontendUrl", value=f"https://{frontend.domain_name}")
        cdk.CfnOutput(self, "ApiDomainName", value=backend.api_domain_name)
        cdk.CfnOutput(self, "FrontendDomainName", value=frontend.domain_name)
        cdk.CfnOutput(self, "AuroraClusterArn", value=database.cluster_arn)
        cdk.CfnOutput(self, "AuroraSecretArn", value=database.secret_arn)
        cdk.CfnOutput(self, "GuardrailId", value=guardrail.guardrail_id)

        # Cost allocation tags (Section 6.2 and 8.2): every resource in this
        # stack rolls up under one Cost Explorer / Budgets tag, independent
        # of any other workload in the same AWS account.
        Tags.of(self).add("Project", project_name)
        Tags.of(self).add("Environment", env_name)


app = cdk.App()
# Pinned to us-east-1 rather than following the CLI profile's region: the
# CloudFront WAF requires it, and the local scripts default to it too.
# Override with `-c region=...` only if you know you need another region.
env = cdk.Environment(
    account=os.getenv("CDK_DEFAULT_ACCOUNT"),
    region=app.node.try_get_context("region") or "us-east-1",
)
CirohStack(app, "CirohStack", env=env)

# GitHub Actions deploy access (.github/workflows/deploy.yml). A separate
# stack, deployed once by hand with `cdk deploy CirohCicdStack`; CI itself
# only deploys CirohStack.
CicdStack(
    app,
    "CirohCicdStack",
    env=env,
    project_name=app.node.try_get_context("project_name") or "CIROH-DocuHub",
    github_repo=app.node.try_get_context("github_repo") or "sli90/CIROH-DocuHub_Chatbot",
    github_branch=app.node.try_get_context("github_branch") or "aws-bedrock-migration",
    github_oidc_provider_arn=app.node.try_get_context("github_oidc_provider_arn") or None,
)
app.synth()
