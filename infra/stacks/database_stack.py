"""Aurora Serverless v2 (PostgreSQL + pgvector) with the RDS Data API enabled.

AWS Migration Plan, Section 5.1 and 10 (steps 2-3): same engine, same
schema as today's Azure PostgreSQL Flexible Server, scale-to-zero via
serverless_v2_min_capacity=0, reached by Lambda over HTTPS via the Data
API (enable_data_api=True) rather than a direct TCP connection.

Run `backend/database/schema_aws.sql` against the cluster after this stack
deploys (Section 10, step 3) - CDK provisions the empty cluster; it does
not load a schema, since schema changes are an application/migration
concern, not infrastructure.
"""

from __future__ import annotations

from aws_cdk import Duration, RemovalPolicy
from aws_cdk import aws_ec2 as ec2
from aws_cdk import aws_rds as rds
from constructs import Construct


class DatabaseStack(Construct):
    def __init__(
        self,
        scope: Construct,
        construct_id: str,
        *,
        project_name: str,
        vpc: ec2.IVpc,
        security_group: ec2.ISecurityGroup,
        min_acu: float = 0,
        max_acu: float = 4,
        database_name: str = "ciroh",
        removal_policy: RemovalPolicy = RemovalPolicy.SNAPSHOT,
    ) -> None:
        super().__init__(scope, construct_id)

        self.cluster = rds.DatabaseCluster(
            self,
            "AuroraCluster",
            cluster_identifier=f"{project_name}-aurora".lower(),
            # PostgreSQL 17, matching today's Azure PostgreSQL Flexible
            # Server 17 (README/Section 2) - same major version, same SQL.
            engine=rds.DatabaseClusterEngine.aurora_postgres(
                version=rds.AuroraPostgresEngineVersion.VER_17_9
            ),
            vpc=vpc,
            vpc_subnets=ec2.SubnetSelection(subnet_type=ec2.SubnetType.PRIVATE_ISOLATED),
            security_groups=[security_group],
            default_database_name=database_name,
            credentials=rds.Credentials.from_generated_secret(
                "ciroh_admin", secret_name=f"{project_name}/aurora/master"
            ),
            enable_data_api=True,
            serverless_v2_min_capacity=min_acu,
            serverless_v2_max_capacity=max_acu,
            serverless_v2_auto_pause_duration=Duration.minutes(5),
            writer=rds.ClusterInstance.serverless_v2("Writer"),
            storage_encrypted=True,
            removal_policy=removal_policy,
        )

        self.database_name = database_name
        self.cluster_arn = self.cluster.cluster_arn
        self.secret_arn = self.cluster.secret.secret_full_arn or self.cluster.secret.secret_arn
