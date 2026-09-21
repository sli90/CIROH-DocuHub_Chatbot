"""VPC for Aurora + the ingestion Fargate task only - Lambda is NOT VPC-attached.

AWS Migration Plan, Section 3.3: "No VPC-attached Lambda: the RDS Data API
lets Lambda reach Aurora over HTTPS/boto3, avoiding VPC ENI cold-start
penalties." Aurora still needs a VPC to live in, and the ingestion Fargate
task needs outbound internet access (GitHub, HydroShare, CIROH Hub, and the
Bedrock endpoint) - so this stack provisions the minimum VPC needed for
those two things, and nothing for Lambda.

Deliberately no NAT Gateway (~$32-35/month fixed cost that is not budgeted
anywhere in Section 8 and would be idle almost all the time for a batch job
that runs occasionally): the Fargate task runs in a public subnet with a
public IP and its own security group instead, egress-only, no inbound
listener. Aurora sits in the private-isolated subnets, reachable only by
the RDS Data API (control-plane HTTPS, not routed through this VPC at all)
or directly by the Fargate task's security group for one-off script access.
"""

from __future__ import annotations

from aws_cdk import aws_ec2 as ec2
from constructs import Construct


class NetworkStack(Construct):
    def __init__(self, scope: Construct, construct_id: str, *, project_name: str) -> None:
        super().__init__(scope, construct_id)

        self.vpc = ec2.Vpc(
            self,
            "Vpc",
            vpc_name=f"{project_name}-vpc",
            max_azs=2,
            nat_gateways=0,
            subnet_configuration=[
                ec2.SubnetConfiguration(
                    name="public-ingestion",
                    subnet_type=ec2.SubnetType.PUBLIC,
                    cidr_mask=24,
                ),
                ec2.SubnetConfiguration(
                    name="private-aurora",
                    subnet_type=ec2.SubnetType.PRIVATE_ISOLATED,
                    cidr_mask=24,
                ),
            ],
        )

        self.ingestion_security_group = ec2.SecurityGroup(
            self,
            "IngestionSecurityGroup",
            vpc=self.vpc,
            description=f"{project_name} Fargate ingestion task - egress only",
            allow_all_outbound=True,
        )

        self.aurora_security_group = ec2.SecurityGroup(
            self,
            "AuroraSecurityGroup",
            vpc=self.vpc,
            description=f"{project_name} Aurora Serverless v2 cluster",
            allow_all_outbound=False,
        )
        # Direct psql/psycopg2 access from the ingestion task only (e.g. for
        # applying schema_aws.sql or ad hoc admin work). The live /ask path
        # never uses this - Lambda talks to Aurora over the Data API only.
        self.aurora_security_group.add_ingress_rule(
            self.ingestion_security_group,
            ec2.Port.tcp(5432),
            "Fargate ingestion task -> Aurora (direct psql, migration scripts)",
        )
