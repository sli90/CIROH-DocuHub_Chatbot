"""Offline ingestion as an on-demand/scheduled ECS Fargate task.

AWS Migration Plan, Section 3.2: "Same scripts, containerized, runs only
when triggered; no always-on server for a job that runs occasionally."
This never shares a code path or failure domain with the live /ask Lambda
(Section 3.3, "Ingestion is decoupled from serving") - it has its own image,
its own IAM role, and runs in the public-ingestion subnet with a public IP
so it can reach GitHub/HydroShare/CIROH Hub and Bedrock without a NAT
Gateway (network_stack.py).

The EventBridge schedule is created disabled by default: this repo's
day-to-day scraper/populate pipeline is still notebook-driven (README,
"In Progress / Planned" - "Automatic artifact synchronization" is not yet
integrated), so there is no fixed cadence to encode yet. Enable the rule,
or just run `aws ecs run-task` on demand, once that automation exists.
"""

from __future__ import annotations

from aws_cdk import aws_ec2 as ec2
from aws_cdk import aws_ecs as ecs
from aws_cdk import aws_events as events
from aws_cdk import aws_events_targets as targets
from aws_cdk import aws_iam as iam
from aws_cdk import aws_logs as logs
from constructs import Construct


class IngestionStack(Construct):
    def __init__(
        self,
        scope: Construct,
        construct_id: str,
        *,
        project_name: str,
        vpc: ec2.IVpc,
        security_group: ec2.ISecurityGroup,
        repo_root: str,
        aurora_cluster_arn: str,
        aurora_secret_arn: str,
        aurora_database: str,
        default_command: list[str] | None = None,
        schedule_enabled: bool = False,
        schedule_expression: str = "cron(0 6 * * ? *)",  # daily 06:00 UTC, once enabled
    ) -> None:
        super().__init__(scope, construct_id)

        self.cluster = ecs.Cluster(self, "Cluster", cluster_name=f"{project_name}-ingestion", vpc=vpc)

        task_definition = ecs.FargateTaskDefinition(
            self,
            "TaskDefinition",
            family=f"{project_name}-ingestion",
            cpu=1024,
            memory_limit_mib=2048,
        )

        log_group = logs.LogGroup(
            self,
            "LogGroup",
            log_group_name=f"/ecs/{project_name}-ingestion",
            retention=logs.RetentionDays.ONE_MONTH,
        )

        self.container = task_definition.add_container(
            "IngestionContainer",
            # `exclude` matters here beyond tidiness: repo_root is the whole
            # checkout, and without it CDK hashes/sends the local Python
            # .venv, frontend node_modules, and .git as Docker build
            # context on every synth - slow, and on some setups multiple
            # GB. The image itself only ever needs backend/.
            image=ecs.ContainerImage.from_asset(
                repo_root,
                file="backend/ingestion.Dockerfile",
                exclude=[
                    ".venv",
                    ".git",
                    "frontend/node_modules",
                    "frontend/dist",
                    "backend/database/HydroShare-CIROH-Datasets",
                    "backend/database/GitHub-CIROH-CodeRepos",
                    "backend/database/CIROH-Hub",
                    "**/__pycache__",
                ],
            ),
            logging=ecs.LogDrivers.aws_logs(stream_prefix="ingestion", log_group=log_group),
            environment={
                "DB_BACKEND": "rds_data_api",
                "AURORA_CLUSTER_ARN": aurora_cluster_arn,
                "AURORA_SECRET_ARN": aurora_secret_arn,
                "AURORA_DATABASE": aurora_database,
                "LLM_PROVIDER": "bedrock",
            },
            command=default_command or ["database/migrate_to_bedrock.py", "--validate"],
        )

        task_definition.add_to_task_role_policy(
            iam.PolicyStatement(
                actions=["bedrock:InvokeModel", "bedrock:Converse"],
                resources=["*"],
            )
        )
        task_definition.add_to_task_role_policy(
            iam.PolicyStatement(
                actions=["rds-data:ExecuteStatement", "rds-data:BatchExecuteStatement"],
                resources=[aurora_cluster_arn],
            )
        )
        task_definition.add_to_task_role_policy(
            iam.PolicyStatement(
                actions=["secretsmanager:GetSecretValue"],
                resources=[aurora_secret_arn],
            )
        )

        self.task_definition = task_definition

        rule = events.Rule(
            self,
            "ScheduleRule",
            rule_name=f"{project_name}-ingestion-schedule",
            schedule=events.Schedule.expression(schedule_expression),
            enabled=schedule_enabled,
        )
        rule.add_target(
            targets.EcsTask(
                cluster=self.cluster,
                task_definition=task_definition,
                launch_type=ecs.LaunchType.FARGATE,
                subnet_selection=ec2.SubnetSelection(subnet_type=ec2.SubnetType.PUBLIC),
                security_groups=[security_group],
                assign_public_ip=True,
            )
        )
