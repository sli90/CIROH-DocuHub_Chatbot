"""Verify Bedrock model access is enabled before deploying.

Anthropic models on Bedrock need a one-time setup per AWS account (the
"use case details" form, plus an AWS Marketplace subscription that is
created automatically the first time *a person* invokes the model). The
deployed Lambda's role cannot do that first-time subscription itself, so
run this script as yourself once, before deploying (docs/AWS_DEPLOYMENT.md,
Part 3). It makes any access problem show up here, with a clear message,
instead of as a cryptic AccessDenied deep in a CloudWatch log.

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
            return False, f"access denied - {e.response.get('Error', {}).get('Message', '')}"
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
        msg = e.response.get("Error", {}).get("Message", "")
        if code == "ResourceNotFoundException" and "use case" in msg.lower():
            return False, "Anthropic use-case form not submitted yet (see below)"
        if code == "AccessDeniedException":
            return False, f"access denied - {msg}"
        return False, f"{code}: {e.response.get('Error', {}).get('Message', '')}"


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--region", default=os.getenv("BEDROCK_REGION") or os.getenv("AWS_REGION", "us-east-1"))
    parser.add_argument(
        "--chat-model", default=os.getenv("BEDROCK_CHAT_MODEL_ID", "us.anthropic.claude-haiku-4-5-20251001-v1:0")
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
        "\nOne or more models are not accessible yet. Fixes, in order of likelihood:\n"
        f"  1. Bedrock console ({args.region}) > Model catalog > Claude Haiku 4.5: if a\n"
        "     'Submit use case details' prompt appears, submit it, wait ~5 minutes, re-run.\n"
        "  2. Open the model in the Bedrock Playground (Chat) and send one message as\n"
        "     yourself - this creates the one-time AWS Marketplace subscription.\n"
        "  3. An AccessDenied that mentions a service control policy, organization, or\n"
        "     Marketplace means your university's AWS admins restrict Bedrock/Marketplace\n"
        "     on this subaccount - send them the error text above."
    )
    return 1


if __name__ == "__main__":
    sys.exit(main())
