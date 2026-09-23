"""Fill in Aurora/Guardrail settings from the deployed CloudFormation stack.

Local scripts (migrate_to_bedrock.py, scripts/*.py) need the Aurora cluster
and secret ARNs that `cdk deploy` prints as outputs. Rather than making you
copy them into .env by hand, this reads them straight from the stack when
they are not already set.
"""

from __future__ import annotations

import os

STACK_NAME = os.getenv("CIROH_STACK_NAME", "CirohStack")

_OUTPUT_TO_ENV = {
    "AuroraClusterArn": "AURORA_CLUSTER_ARN",
    "AuroraSecretArn": "AURORA_SECRET_ARN",
    "GuardrailId": "BEDROCK_GUARDRAIL_ID",
    "FrontendUrl": "CIROH_FRONTEND_URL",
}


def get_stack_outputs(region: str | None = None) -> dict[str, str]:
    import boto3

    region = region or os.getenv("AURORA_REGION") or os.getenv("AWS_REGION") or "us-east-1"
    cfn = boto3.client("cloudformation", region_name=region)
    stack = cfn.describe_stacks(StackName=STACK_NAME)["Stacks"][0]
    return {o["OutputKey"]: o["OutputValue"] for o in stack.get("Outputs", [])}


def load_stack_outputs_into_env(region: str | None = None) -> None:
    """Set any missing AURORA_* env vars from the stack's outputs."""
    region = region or os.getenv("AURORA_REGION") or os.getenv("AWS_REGION") or "us-east-1"
    # Not setdefault: a blank line in .env ("AURORA_DATABASE=") counts as unset.
    os.environ["AURORA_REGION"] = region
    if not os.getenv("AURORA_DATABASE"):
        os.environ["AURORA_DATABASE"] = "ciroh"
    if os.getenv("AURORA_CLUSTER_ARN") and os.getenv("AURORA_SECRET_ARN"):
        return
    outputs = get_stack_outputs(region)
    for output_key, env_key in _OUTPUT_TO_ENV.items():
        if output_key in outputs and not os.getenv(env_key):
            os.environ[env_key] = outputs[output_key]
