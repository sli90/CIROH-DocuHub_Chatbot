"""Amazon Bedrock client wrapper: embeddings, chat, structured output, guardrails.

Replaces the direct OpenAI dependency in backend/rag/ask.py once
LLM_PROVIDER=bedrock (see AWS Migration Plan, Section 6). Every call here is
billed on the AWS account's Bedrock line item, authenticated with the
Lambda/task execution role's IAM credentials (no separate API key).

Model IDs are read from environment variables so they can be repointed
without a code change; confirm the exact IDs available in your target
region in the Bedrock console before first deploy (Section 11, Risks).
"""

from __future__ import annotations

import json
import os
from functools import lru_cache
from typing import Any, Optional

import boto3
from botocore.config import Config

BEDROCK_REGION = os.getenv("BEDROCK_REGION") or os.getenv("AWS_REGION", "us-east-1")

# Claude Haiku 4.5 is only invocable on-demand through a cross-region
# inference profile (the "us." prefix), not by its bare foundation-model ID.
CHAT_MODEL_ID = os.getenv("BEDROCK_CHAT_MODEL_ID", "us.anthropic.claude-haiku-4-5-20251001-v1:0")
EMBED_MODEL_ID = os.getenv("BEDROCK_EMBED_MODEL_ID", "amazon.titan-embed-text-v2:0")
EMBED_DIMENSIONS = int(os.getenv("BEDROCK_EMBED_DIMENSIONS", "1024"))

GUARDRAIL_ID = os.getenv("BEDROCK_GUARDRAIL_ID") or None
GUARDRAIL_VERSION = os.getenv("BEDROCK_GUARDRAIL_VERSION", "DRAFT")

GUARDRAIL_INTERVENED_STOP_REASON = "guardrail_intervened"


@lru_cache(maxsize=1)
def _runtime_client():
    """A single boto3 bedrock-runtime client, reused across invocations.

    Cached at module scope so a warm Lambda execution environment (or a
    long-running local process) does not re-create a client per request.
    """
    # Adaptive retries absorb ThrottlingException bursts (the bulk corpus
    # re-embed runs many embedding calls in parallel).
    config = Config(retries={"max_attempts": 8, "mode": "adaptive"}, read_timeout=60)
    return boto3.client("bedrock-runtime", region_name=BEDROCK_REGION, config=config)


def get_embedding(
    text: str,
    dimensions: Optional[int] = None,
    model_id: Optional[str] = None,
    normalize: bool = True,
) -> tuple[list[float], dict[str, int]]:
    """Embed `text` with Amazon Titan Text Embeddings V2.

    Returns (vector, usage) where usage uses the same key names the
    existing UsageMeter already understands (input_tokens), so no change
    is needed to backend/rag/ask.py's cost accounting.
    """
    body = json.dumps(
        {
            "inputText": text,
            "dimensions": dimensions or EMBED_DIMENSIONS,
            "normalize": normalize,
        }
    )
    resp = _runtime_client().invoke_model(modelId=model_id or EMBED_MODEL_ID, body=body)
    payload = json.loads(resp["body"].read())
    usage = {"input_tokens": payload.get("inputTextTokenCount", 0)}
    return payload["embedding"], usage


def _extract_text(message: dict[str, Any]) -> str:
    return "".join(block.get("text", "") for block in message.get("content", []) if "text" in block)


def _usage_from_response(resp: dict[str, Any]) -> dict[str, int]:
    usage = resp.get("usage", {}) or {}
    return {
        "input_tokens": usage.get("inputTokens", 0),
        "output_tokens": usage.get("outputTokens", 0),
    }


def _guardrail_config() -> Optional[dict[str, str]]:
    if not GUARDRAIL_ID:
        return None
    return {
        "guardrailIdentifier": GUARDRAIL_ID,
        "guardrailVersion": GUARDRAIL_VERSION,
        "trace": "enabled",
    }


def converse_text(
    user_message: str,
    system_prompt: Optional[str] = None,
    max_tokens: int = 500,
    temperature: float = 0.2,
    model_id: Optional[str] = None,
    guarded_text: Optional[str] = None,
) -> dict[str, Any]:
    """Plain-text answer generation via Bedrock Converse.

    `guarded_text`, if given, is appended after `user_message`. When a
    Guardrail is configured it is sent as a guardContent block, so the
    Guardrail's input policies evaluate only that text (the user's question)
    rather than the whole message (retrieved context included).

    Returns {"text", "usage", "blocked", "stop_reason"}. `blocked` is True
    when a configured Guardrail intervened, in which case `text` is a
    placeholder and the caller should show a generic refusal, not the
    (potentially partial) model output.
    """
    guardrail = _guardrail_config()
    if guarded_text is None:
        content: list[dict[str, Any]] = [{"text": user_message}]
    elif guardrail:
        content = [{"text": user_message}, {"guardContent": {"text": {"text": guarded_text}}}]
    else:
        content = [{"text": f"{user_message}\n{guarded_text}"}]

    kwargs: dict[str, Any] = {
        "modelId": model_id or CHAT_MODEL_ID,
        "messages": [{"role": "user", "content": content}],
        "inferenceConfig": {"maxTokens": max_tokens, "temperature": temperature},
    }
    if system_prompt:
        kwargs["system"] = [{"text": system_prompt}]
    if guardrail:
        kwargs["guardrailConfig"] = guardrail

    resp = _runtime_client().converse(**kwargs)
    stop_reason = resp.get("stopReason")
    blocked = stop_reason == GUARDRAIL_INTERVENED_STOP_REASON
    text = "" if blocked else _extract_text(resp["output"]["message"])
    return {
        "text": text,
        "usage": _usage_from_response(resp),
        "blocked": blocked,
        "stop_reason": stop_reason,
    }


def converse_json(
    user_message: str,
    tool_name: str,
    json_schema: dict[str, Any],
    tool_description: str = "Return the requested structured result.",
    system_prompt: Optional[str] = None,
    max_tokens: int = 200,
    temperature: float = 0.0,
    model_id: Optional[str] = None,
) -> dict[str, Any]:
    """Structured (JSON) output via Bedrock Converse tool-use forcing.

    Bedrock's Converse API has no OpenAI-style `response_format=json_object`
    mode. The reliable equivalent for Claude models is to define a single
    tool whose input schema is the JSON shape we want, then force the model
    to call it (toolChoice). This is used for the scope/hybrid-route
    classifiers that ask.py's OpenAI path drives via `text.format=json_object`.

    Returns {"data": dict, "usage": dict}. `data` is `{}` if the model did
    not return a tool_use block (should not happen with toolChoice set, but
    handled defensively since this feeds routing logic, not just display text).
    """
    kwargs: dict[str, Any] = {
        "modelId": model_id or CHAT_MODEL_ID,
        "messages": [{"role": "user", "content": [{"text": user_message}]}],
        "inferenceConfig": {"maxTokens": max_tokens, "temperature": temperature},
        "toolConfig": {
            "tools": [
                {
                    "toolSpec": {
                        "name": tool_name,
                        "description": tool_description,
                        "inputSchema": {"json": json_schema},
                    }
                }
            ],
            "toolChoice": {"tool": {"name": tool_name}},
        },
    }
    if system_prompt:
        kwargs["system"] = [{"text": system_prompt}]

    resp = _runtime_client().converse(**kwargs)
    data: dict[str, Any] = {}
    for block in resp["output"]["message"].get("content", []):
        tool_use = block.get("toolUse")
        if tool_use and tool_use.get("name") == tool_name:
            data = tool_use.get("input", {})
            break
    return {"data": data, "usage": _usage_from_response(resp)}


def apply_guardrail_text(
    text: str,
    guardrail_id: Optional[str] = None,
    guardrail_version: Optional[str] = None,
    source: str = "INPUT",
) -> dict[str, Any]:
    """Pre-screen raw user input with ApplyGuardrail, ahead of embedding/retrieval.

    Section 9.1: an obviously out-of-scope request (denied-topics match) can
    be rejected before either the embedding call or any DB round-trip, which
    is the cheapest possible rejection point. No-ops (returns not-blocked)
    if no guardrail is configured, so this is safe to call unconditionally.
    """
    gid = guardrail_id or GUARDRAIL_ID
    if not gid:
        return {"blocked": False, "action": "NONE", "assessments": []}
    resp = _runtime_client().apply_guardrail(
        guardrailIdentifier=gid,
        guardrailVersion=guardrail_version or GUARDRAIL_VERSION,
        source=source,
        content=[{"text": {"text": text}}],
    )
    action = resp.get("action", "NONE")
    return {
        "blocked": action == "GUARDRAIL_INTERVENED",
        "action": action,
        "assessments": resp.get("assessments", []),
    }
