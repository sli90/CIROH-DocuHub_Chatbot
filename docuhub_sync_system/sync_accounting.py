"""OpenAI usage accounting and per-synchronization report helpers.

Token counts come from API response ``usage`` objects. Dollar amounts are
estimates based on configurable prices per one million tokens; the defaults
match OpenAI's standard pricing published on 2026-08-20.
"""
from __future__ import annotations

import json
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable


PRICING_SOURCE_URL = "https://developers.openai.com/api/docs/pricing"
PRICING_EFFECTIVE_DATE = "2026-08-20"

# USD per 1M tokens. Keep these scoped to models used by this repository.
DEFAULT_PRICING = {
    "gpt-5.2": {
        "input": 1.75,
        "cached_input": 0.175,
        "cache_write_input": None,
        "output": 14.00,
    },
    "text-embedding-3-large": {
        "input": 0.13,
        "cached_input": None,
        "cache_write_input": None,
        "output": None,
    },
}

TOKEN_FIELDS = (
    "input_tokens",
    "cached_input_tokens",
    "cache_write_input_tokens",
    "uncached_input_tokens",
    "output_tokens",
    "reasoning_tokens",
    "total_tokens",
)


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def new_sync_id() -> str:
    return datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S_%fZ")


def _get(value: Any, key: str, default: Any = None) -> Any:
    if isinstance(value, dict):
        return value.get(key, default)
    return getattr(value, key, default)


def _as_int(value: Any) -> int:
    try:
        return max(0, int(value or 0))
    except (TypeError, ValueError):
        return 0


def extract_response_usage(response: Any) -> dict[str, int] | None:
    """Normalize Responses and Embeddings API usage shapes."""
    usage = _get(response, "usage")
    if usage is None:
        return None

    input_tokens = _as_int(
        _get(usage, "input_tokens", _get(usage, "prompt_tokens", 0))
    )
    output_tokens = _as_int(_get(usage, "output_tokens", 0))
    total_tokens = _as_int(_get(usage, "total_tokens", 0))
    if not output_tokens and total_tokens > input_tokens:
        # Embeddings have no output tokens. This fallback is for older text
        # response shapes that only expose prompt/total token counts.
        output_tokens = total_tokens - input_tokens

    input_details = _get(usage, "input_tokens_details", {}) or {}
    output_details = _get(usage, "output_tokens_details", {}) or {}
    cached = _as_int(_get(input_details, "cached_tokens", 0))
    cache_write = _as_int(_get(input_details, "cache_write_tokens", 0))
    reasoning = _as_int(_get(output_details, "reasoning_tokens", 0))
    uncached = max(0, input_tokens - cached - cache_write)

    if not total_tokens:
        total_tokens = input_tokens + output_tokens

    return {
        "input_tokens": input_tokens,
        "cached_input_tokens": cached,
        "cache_write_input_tokens": cache_write,
        "uncached_input_tokens": uncached,
        "output_tokens": output_tokens,
        "reasoning_tokens": reasoning,
        "total_tokens": total_tokens,
    }


def _matching_default_prices(model: str) -> dict[str, float | None]:
    if model in DEFAULT_PRICING:
        return dict(DEFAULT_PRICING[model])
    for known_model in sorted(DEFAULT_PRICING, key=len, reverse=True):
        if model.startswith(f"{known_model}-"):
            return dict(DEFAULT_PRICING[known_model])
    return {
        "input": None,
        "cached_input": None,
        "cache_write_input": None,
        "output": None,
    }


def pricing_for(model: str, operation: str) -> tuple[dict, list[str]]:
    """Return rates, applying operation-specific environment overrides."""
    prices = _matching_default_prices(model)
    env_prefix = (
        "OPENAI_EMBEDDING" if operation.startswith("embedding") else "OPENAI_SUMMARY"
    )
    env_keys = {
        "input": f"{env_prefix}_INPUT_USD_PER_1M",
        "cached_input": f"{env_prefix}_CACHED_INPUT_USD_PER_1M",
        "cache_write_input": f"{env_prefix}_CACHE_WRITE_INPUT_USD_PER_1M",
        "output": f"{env_prefix}_OUTPUT_USD_PER_1M",
    }
    overrides: list[str] = []
    for rate_name, env_key in env_keys.items():
        raw = os.environ.get(env_key)
        if raw is None or not raw.strip():
            continue
        try:
            prices[rate_name] = float(raw)
        except ValueError as exc:
            raise ValueError(f"{env_key} must be a number, got {raw!r}") from exc
        overrides.append(env_key)
    return prices, overrides


class UsageAccumulator:
    """Accumulate actual API response usage for one model/operation."""

    def __init__(self, operation: str, model: str):
        self.operation = operation
        self.model = model
        self.requests = 0
        self.responses_with_usage = 0
        self.errors = 0
        self.tokens = {field: 0 for field in TOKEN_FIELDS}

    def record_request(self) -> None:
        self.requests += 1

    def add_response(self, response: Any) -> None:
        usage = extract_response_usage(response)
        if usage is None:
            return
        self.responses_with_usage += 1
        for field in TOKEN_FIELDS:
            self.tokens[field] += usage[field]

    def record_error(self) -> None:
        self.errors += 1

    def add_report(self, report: dict | None) -> None:
        """Restore previously checkpointed usage into this accumulator."""
        if not isinstance(report, dict):
            return
        operation = report.get("operation")
        model = report.get("model")
        if operation and operation != self.operation:
            raise ValueError(
                f"Cannot restore {operation!r} usage into {self.operation!r}"
            )
        if model and model != self.model:
            raise ValueError(f"Cannot restore {model!r} usage into {self.model!r}")
        self.requests += _as_int(report.get("requests"))
        self.responses_with_usage += _as_int(report.get("responses_with_usage"))
        self.errors += _as_int(report.get("errors"))
        for field in TOKEN_FIELDS:
            self.tokens[field] += _as_int(report.get(field))

    def report(self) -> dict:
        rates, overrides = pricing_for(self.model, self.operation)
        priced_quantities = {
            "input": self.tokens["uncached_input_tokens"],
            "cached_input": self.tokens["cached_input_tokens"],
            "cache_write_input": self.tokens["cache_write_input_tokens"],
            "output": self.tokens["output_tokens"],
        }

        cost = 0.0
        cost_available = True
        for rate_name, quantity in priced_quantities.items():
            if not quantity:
                continue
            rate = rates.get(rate_name)
            if rate is None:
                cost_available = False
                continue
            cost += quantity * rate / 1_000_000

        return {
            "operation": self.operation,
            "model": self.model,
            "requests": self.requests,
            "responses_with_usage": self.responses_with_usage,
            "errors": self.errors,
            **self.tokens,
            "rates_usd_per_1m_tokens": rates,
            "estimated_cost_usd": round(cost, 10) if cost_available else None,
            "pricing_source": PRICING_SOURCE_URL,
            "pricing_effective_date": PRICING_EFFECTIVE_DATE,
            "price_override_environment_variables": overrides,
        }


def aggregate_usage(operation_reports: Iterable[dict | None]) -> dict:
    operations: list[dict] = []
    for report in operation_reports:
        if not isinstance(report, dict):
            continue
        nested = report.get("operations")
        if not report.get("operation") and isinstance(nested, list):
            operations.extend(item for item in nested if isinstance(item, dict))
        else:
            operations.append(report)
    totals = {field: 0 for field in TOKEN_FIELDS}
    total_requests = 0
    total_errors = 0
    total_cost = 0.0
    cost_available = True

    for report in operations:
        total_requests += _as_int(report.get("requests"))
        total_errors += _as_int(report.get("errors"))
        for field in TOKEN_FIELDS:
            totals[field] += _as_int(report.get(field))
        operation_cost = report.get("estimated_cost_usd")
        if operation_cost is None:
            if _as_int(report.get("total_tokens")):
                cost_available = False
        else:
            total_cost += float(operation_cost)

    return {
        "operations": operations,
        "requests": total_requests,
        "errors": total_errors,
        **totals,
        "estimated_cost_usd": round(total_cost, 10) if cost_available else None,
        "currency": "USD",
        "cost_is_estimate": True,
    }


def build_synchronization_report(
    *,
    sync_id: str,
    mode: str,
    started_at: str,
    completed_at: str,
    status: str,
    generation_report: dict | None = None,
    db_report: dict | None = None,
    additional_usage_reports: Iterable[dict | None] | None = None,
    error: str | None = None,
    metadata: dict | None = None,
) -> dict:
    generation_report = generation_report or {}
    db_report = db_report or {}
    operations = [generation_report.get("openai_usage")]
    if db_report:
        operations.append(db_report.get("openai_usage"))
    operations.extend(additional_usage_reports or [])

    duration_seconds = None
    try:
        started = datetime.fromisoformat(started_at.replace("Z", "+00:00"))
        completed = datetime.fromisoformat(completed_at.replace("Z", "+00:00"))
        duration_seconds = max(0.0, round((completed - started).total_seconds(), 3))
    except (AttributeError, TypeError, ValueError):
        pass

    report = {
        "schema_version": 1,
        "sync_id": sync_id,
        "mode": mode,
        "status": status,
        "started_at": started_at,
        "completed_at": completed_at,
        "duration_seconds": duration_seconds,
        "content": {
            "total_artifacts": generation_report.get("total_artifacts", 0),
            "total_chunks": generation_report.get("total_chunks", 0),
            "new_count": generation_report.get("new_count", 0),
            "updated_count": generation_report.get("updated_count", 0),
            "deleted_count": generation_report.get("deleted_count", 0),
            "summarized_count": generation_report.get("summarized_count", 0),
            "summary_error_count": len(
                generation_report.get("summary_errors") or []
            ),
            "pending_summary_count": len(
                generation_report.get("pending_summaries") or []
            ),
        },
        "openai_usage": aggregate_usage(operations),
    }
    if db_report:
        report["database"] = {
            "upserted_artifacts": db_report.get("upserted_artifacts", 0),
            "deactivated_artifacts": db_report.get("deactivated_artifacts", 0),
            "chunks_inserted": db_report.get("chunks_inserted", 0),
            "elapsed_seconds": db_report.get("elapsed_seconds", 0),
        }
    if error:
        report["error"] = error
    if metadata:
        report["metadata"] = metadata
    return report


def write_synchronization_report(output_dir: Path | str, report: dict) -> Path:
    """Write both the latest report and an immutable report for this sync."""
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    history_dir = output_dir / "synchronization_reports"
    history_dir.mkdir(parents=True, exist_ok=True)

    sync_id = str(report.get("sync_id") or new_sync_id())
    history_path = history_dir / f"sync_{sync_id}.json"
    latest_path = output_dir / "synchronization_report.json"

    payload = json.dumps(report, indent=2, ensure_ascii=False) + "\n"
    history_path.write_text(payload, encoding="utf-8")
    latest_path.write_text(payload, encoding="utf-8")
    return history_path
