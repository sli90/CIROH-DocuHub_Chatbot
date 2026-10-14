"""Lets GitHub Actions deploy CirohStack without any stored AWS keys.

GitHub's OIDC identity provider issues each workflow run a short-lived token
naming the repository and branch it runs for. This stack makes AWS trust
those tokens for exactly one repo + branch, and gives that run a role whose
only power is to assume the CDK bootstrap roles (the same ones `cdk deploy`
uses from CloudShell). CloudFormation's own execution role does the actual
resource changes, so the CI role cannot touch anything directly.

Deployed separately from CirohStack, once, by a person:
    cdk deploy CirohCicdStack
The workflow (.github/workflows/deploy.yml) only ever deploys CirohStack,
so a pushed change cannot widen its own permissions.

An AWS account can have only one OIDC provider per URL. If the account
already has GitHub's (token.actions.githubusercontent.com), pass its ARN
with -c github_oidc_provider_arn=arn:aws:iam::<acct>:oidc-provider/token.actions.githubusercontent.com
and this stack reuses it instead of creating one.
"""

from __future__ import annotations

from typing import Optional

from aws_cdk import CfnOutput, Duration, Stack
from aws_cdk import aws_iam as iam
from constructs import Construct

GITHUB_OIDC_URL = "https://token.actions.githubusercontent.com"
GITHUB_OIDC_HOST = "token.actions.githubusercontent.com"
# Default CDK bootstrap qualifier ("cdk bootstrap" without --qualifier).
CDK_QUALIFIER = "hnb659fds"


class CicdStack(Stack):
    def __init__(
        self,
        scope: Construct,
        construct_id: str,
        *,
        project_name: str,
        github_repo: str,
        github_branch: str,
        github_oidc_provider_arn: Optional[str] = None,
        **kwargs,
    ) -> None:
        super().__init__(scope, construct_id, **kwargs)

        if github_oidc_provider_arn:
            provider = iam.OidcProviderNative.from_oidc_provider_arn(
                self, "GitHubOidc", github_oidc_provider_arn
            )
        else:
            provider = iam.OidcProviderNative(
                self,
                "GitHubOidc",
                url=GITHUB_OIDC_URL,
                client_ids=["sts.amazonaws.com"],
            )

        self.deploy_role = iam.Role(
            self,
            "GitHubDeployRole",
            role_name=f"{project_name}-github-deploy",
            description=f"GitHub Actions deploys of {github_repo}@{github_branch}",
            max_session_duration=Duration.hours(1),
            assumed_by=iam.WebIdentityPrincipal(
                provider.oidc_provider_arn,
                conditions={
                    "StringEquals": {
                        f"{GITHUB_OIDC_HOST}:aud": "sts.amazonaws.com",
                        # Only pushes/dispatches on this one branch of this repo.
                        f"{GITHUB_OIDC_HOST}:sub": f"repo:{github_repo}:ref:refs/heads/{github_branch}",
                    }
                },
            ),
        )
        # Exactly what `cdk deploy` needs: the bootstrap deploy, asset
        # publishing and lookup roles in this account and region.
        self.deploy_role.add_to_policy(
            iam.PolicyStatement(
                actions=["sts:AssumeRole", "sts:TagSession"],
                resources=[
                    f"arn:{self.partition}:iam::{self.account}:role/cdk-{CDK_QUALIFIER}-{kind}-role-{self.account}-{self.region}"
                    for kind in ("deploy", "file-publishing", "image-publishing", "lookup")
                ],
            )
        )

        CfnOutput(
            self,
            "GitHubDeployRoleArn",
            value=self.deploy_role.role_arn,
            description="Set as the AWS_DEPLOY_ROLE_ARN variable in the GitHub repo",
        )
