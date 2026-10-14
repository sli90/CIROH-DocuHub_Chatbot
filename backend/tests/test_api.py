"""API behaviour: email requirement, daily limit, streaming events,
follow-up suggestions and structured sources (Bedrock and Aurora faked)."""

from __future__ import annotations

import json

import ask
from quota import normalize_email

QUESTION = "How do I install NGIAB?"


def stream(client, text=QUESTION, email="test@ua.edu"):
    r = client.post("/ask/stream", json={"text": text, "email": email})
    assert r.status_code == 200
    assert r.headers["content-type"].startswith("application/x-ndjson")
    return [json.loads(line) for line in r.text.splitlines()]


def done_event(events):
    return next(e for e in events if e["type"] == "done")


def test_email_is_required(client):
    assert client.post("/ask", json={"text": QUESTION}).status_code == 422
    assert client.post("/ask/stream", json={"text": QUESTION}).status_code == 422
    assert client.post("/ask", json={"text": QUESTION, "email": "nope"}).status_code == 400
    assert client.post("/ask/stream", json={"text": QUESTION, "email": "a@b"}).status_code == 400


def test_normalize_email():
    assert normalize_email("  Jane.Doe@UA.edu ") == "jane.doe@ua.edu"
    for bad in ["", "nope", "a@b", "a b@ua.edu", "@ua.edu", "x@ua.e"]:
        assert normalize_email(bad) is None


def test_stream_sends_status_text_then_done(client):
    events = stream(client)
    types = [e["type"] for e in events]
    assert types[0] == "status"
    assert types[-1] == "done"
    assert "".join(e["text"] for e in events if e["type"] == "delta") == "Hello **world**"


def test_done_carries_sources_follow_ups_and_quota(client):
    done = done_event(stream(client))
    assert done["route"] == "bottom_up"
    assert done["follow_ups"] == ["What does NGIAB need?", "How do I run NGIAB?", "Where is NGIAB data?"]
    assert done["source_details"][0] == {
        "title": "Install guide",
        "path": "CIROH Hub > Products > NGIAB",
        "url": "/docs/products/ngiab/install",
        "type": "Hub Page",
    }
    assert done["quota"] == {"allowed": True, "used": 1, "limit": 2, "remaining": 1}


def test_daily_limit_blocks_after_limit(client, usage_db):
    stream(client, email="Test@UA.edu")
    stream(client, email="test@ua.edu")
    events = stream(client, email="test@ua.edu")
    done = done_event(events)
    assert done["route"] == "limit"
    assert done["quota"]["allowed"] is False
    answer = "".join(e["text"] for e in events if e["type"] == "delta")
    assert "limit of 2 questions" in answer
    assert usage_db.used == {"test@ua.edu": 2}  # emails are normalized


def test_greetings_are_free(client, usage_db):
    for _ in range(3):
        assert done_event(stream(client, text="hi"))["route"] == "help"
    assert usage_db.used == {}


def test_guardrail_retraction_replaces_answer_and_drops_follow_ups(client, fake_models):
    fake_models["blocked"] = True
    events = stream(client)
    assert [e["text"] for e in events if e["type"] == "replace"] == [ask.OFF_TOPIC_MESSAGE]
    assert done_event(events)["follow_ups"] == []


def test_non_streaming_ask(client):
    r = client.post("/ask", json={"text": QUESTION, "email": "other@ua.edu"})
    assert r.status_code == 200
    body = r.json()
    assert body["answer"] == "plain answer"
    assert body["quota"]["remaining"] == 1
    assert len(body["follow_ups"]) == 3
    assert len(body["source_details"]) == 2
