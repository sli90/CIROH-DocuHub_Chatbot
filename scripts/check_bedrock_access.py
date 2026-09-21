"""Verify Bedrock model access is enabled before deploying.

Model access is a manual, per-model, per-region console opt-in that's easy
to forget until the first Lambda invocation fails (AWS Migration Plan,
Section 11 / docs/AWS_DEPLOYMENT.md, step 0). This makes that failure
happen here, with a clear message, instead of as a cryptic AccessDenied
deep in a CloudWatch log after a full deploy.

Usage:
    python scripts/check_bedrock_access.py
    python scripts/check_bedrock_access.py --region us-west-2
"""

from __future__ import annotations

import argparse
import json
import os
import sys

import boto3
from botocore.exceptions import ClientError


def _check_invoke_model(runtime, model_id: str) -> tuple[bool, str]:
    try:
        runtime.invoke_model(
            modelId=model_id,
            body=json.dumps({"inputText": "ping", "dimensions": 256, "normalize": True}),
        )
        return True, "ok"
    except ClientError as e:
        code = e.response.get("Error", {}).get("Code", "")
        if code == "AccessDeniedException":
            return False, "access not granted - enable it in Bedrock console > Model access"
        if code == "ValidationException":
            # Reached the model but sent it embeddings-shaped input; access is fine.
            return True, "ok (reachable)"
        return False, f"{code}: {e.response.get('Error', {}).get('Message', '')}"


def _check_converse(runtime, model_id: str) -> tuple[bool, str]:
    try:
        runtime.converse(
            modelId=model_id,
            messages=[{"role": "user", "content": [{"text": "ping"}]}],
            inferenceConfig={"maxTokens": 8},
        )
        return True, "ok"
    except ClientError as e:
        code = e.response.get("Error", {}).get("Code", "")
        if code == "AccessDeniedException":
            return False, "access not granted - enable it in Bedrock console > Model access"
        return False, f"{code}: {e.response.get('Error', {}).get('Message', '')}"


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--region", default=os.getenv("BEDROCK_REGION") or os.getenv("AWS_REGION", "us-east-1"))
    parser.add_argument(
        "--chat-model", default=os.getenv("BEDROCK_CHAT_MODEL_ID", "anthropic.claude-haiku-4-5-v1:0")
    )
    parser.add_argument(
        "--embed-model", default=os.getenv("BEDROCK_EMBED_MODEL_ID", "amazon.titan-embed-text-v2:0")
    )
    args = parser.parse_args()

    runtime = boto3.client("bedrock-runtime", region_name=args.region)

    print(f"Region: {args.region}\n")

    ok_chat, msg_chat = _check_converse(runtime, args.chat_model)
    print(f"[{'OK' if ok_chat else 'FAIL'}] Converse  {args.chat_model}: {msg_chat}")

    ok_embed, msg_embed = _check_invoke_model(runtime, args.embed_model)
    print(f"[{'OK' if ok_embed else 'FAIL'}] Embed     {args.embed_model}: {msg_embed}")

    if ok_chat and ok_embed:
        print("\nBoth models reachable. Safe to proceed with deploy.")
        return 0

    print(
        "\nOne or more models are not accessible yet. In the Bedrock console for "
        f"{args.region}: Model access > Manage model access > request the models above. "
        "Approval can take a few minutes to a few hours the first time an account requests "
        "Anthropic models."
    )
    return 1


if __name__ == "__main__":
    sys.exit(main())
