"""Test setup: import the API with Bedrock and Aurora replaced by fakes.

Nothing here touches AWS, so these tests run in CI before every deploy
(.github/workflows/deploy.yml) and locally with `pytest backend/tests`.
"""

from __future__ import annotations

import os
import sys
from pathlib import Path

import pytest

BACKEND = Path(__file__).resolve().parent.parent
sys.path[:0] = [str(BACKEND), str(BACKEND / "rag")]
os.environ.update(LLM_PROVIDER="bedrock", DB_BACKEND="", AWS_REGION="us-east-1")

import ask  # noqa: E402
import main  # noqa: E402
import quota  # noqa: E402
import aws.bedrock_client as bedrock  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402

SOURCES = [
    {"title": "CIROH Hub > Products > NGIAB > Install guide", "url": "/docs/products/ngiab/install", "type": "Hub Page"},
    {"title": "NGIAB paper", "url": "https://doi.org/x", "type": "Publication"},
]
FOLLOW_UPS = ["What does NGIAB need?", "How do I run NGIAB?", "Where is NGIAB data?", "a fourth one"]


class FakeUsageDb:
    """Stands in for Aurora: implements the one quota statement."""

    def __init__(self):
        self.used: dict[str, int] = {}

    def __enter__(self):
        return self

    def __exit__(self, *exc):
        return False

    def execute_query(self, sql, params=None, fetch=False):
        if "CREATE TABLE" in sql:
            return None
        email, _tz, limit, _email = params
        if self.used.get(email, 0) >= limit:
            return []
        self.used[email] = self.used.get(email, 0) + 1
        return [{"questions": self.used[email]}]


@pytest.fixture
def usage_db(monkeypatch):
    db = FakeUsageDb()
    monkeypatch.setattr(ask, "_db", lambda: db)
    monkeypatch.setattr(quota, "DAILY_QUESTION_LIMIT", 2)
    return db


@pytest.fixture
def fake_models(monkeypatch):
    """Retrieval and Bedrock replaced. `state` controls and records them:
    state["blocked"] makes the Guardrail retract the streamed answer;
    state["searched"] / state["answer_calls"] / state["condense_calls"]
    record what retrieval, answer generation and question rewriting got."""
    state = {"blocked": False, "searched": [], "answer_calls": [], "condense_calls": []}

    monkeypatch.setattr(bedrock, "apply_guardrail_text", lambda q: {"blocked": False})

    def fake_prepare(q, mode, model, meter):
        state["searched"].append(q)
        return None, {"blocks": ["ctx"], "sources": SOURCES, "route": "bottom_up", "route_info": {"reason": "test"}}

    monkeypatch.setattr(ask, "_prepare_answer", fake_prepare)

    def fake_stream(*args, **kwargs):
        state["answer_calls"].append({"prompt": args[0] if args else None, **kwargs})
        yield "delta", "Hello "
        yield "delta", "**world**"
        yield "done", {"usage": {"input_tokens": 10, "output_tokens": 5}, "blocked": state["blocked"], "stop_reason": "end_turn"}

    def fake_text(*args, **kwargs):
        state["answer_calls"].append({"prompt": args[0] if args else None, **kwargs})
        return {"text": "plain answer", "usage": {}, "blocked": False, "stop_reason": "end_turn"}

    def fake_json(prompt, tool_name, *args, **kwargs):
        usage = {"input_tokens": 50, "output_tokens": 20}
        if tool_name == "standalone_question":
            state["condense_calls"].append(prompt)
            return {"data": {"standalone_question": "How do I install NGIAB?"}, "usage": usage}
        return {"data": {"questions": FOLLOW_UPS}, "usage": usage}

    monkeypatch.setattr(bedrock, "converse_text_stream", fake_stream)
    monkeypatch.setattr(bedrock, "converse_text", fake_text)
    monkeypatch.setattr(bedrock, "converse_json", fake_json)
    return state


@pytest.fixture
def client(usage_db, fake_models):
    return TestClient(main.app)
