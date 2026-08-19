"""Draft FastAPI wrapper around ask.answer_question."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Optional

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

from ask import answer_question

TELEMETRY_PATH = Path(__file__).resolve().parent / "telemetry.jsonl"

app = FastAPI(
    title="CIROH AI Bot v2 API",
    description="Draft API wrapping the v2 hybrid RAG pipeline",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "http://localhost:5173",
        "http://127.0.0.1:5173",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class Question(BaseModel):
    text: str
    session_id: Optional[str] = None
    mode: str = "hybrid"


class TelemetryEvent(BaseModel):
    session_id: str
    event: str
    payload: dict[str, Any] = Field(default_factory=dict)


def _append_telemetry(record: dict[str, Any]) -> None:
    record = {"ts": datetime.now(timezone.utc).isoformat(), **record}
    with TELEMETRY_PATH.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(record, ensure_ascii=False) + "\n")


@app.get("/", tags=["Health Check"])
def read_root():
    return {"status": "CIROH AI Bot v2 API is running"}


@app.post("/ask", tags=["AI Assistant"])
def ask_ai(question: Question):
    result = answer_question(question.text, mode=question.mode)
    _append_telemetry(
        {
            "event": "ask",
            "session_id": question.session_id,
            "question": question.text,
            "route": result.get("route"),
            "usage": result.get("usage"),
        }
    )
    return result


@app.post("/telemetry", tags=["Telemetry"])
def record_telemetry(event: TelemetryEvent):
    _append_telemetry(event.model_dump())
    return {"ok": True}
