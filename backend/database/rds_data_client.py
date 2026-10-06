"""Aurora Serverless v2 access via the RDS Data API.

Drop-in replacement for DatabaseManager (backend/database/database.py) that
lets Lambda reach Aurora over HTTPS/boto3 instead of a direct psycopg2/TCP
connection, so Lambda never needs to run inside a VPC or manage a
connection pool across cold-started, horizontally-scaled instances
(AWS Migration Plan, Section 3.3 and 5.1).

Query text in this codebase (backend/rag/ask.py) is written with psycopg2's
"%s" positional placeholders. The Data API instead requires named
parameters ("execute_statement" takes a `parameters` list of
{"name": ..., "value": {...}}). Rather than rewrite every query, this module
translates "%s" -> ":pN" positionally and builds the matching named
parameter list, so query strings do not need to change between backends.

Two Data API limitations shape the translation (Section 5.3):
- pgvector's `vector` type (and jsonb) are not native Data API types, and
  array parameters are not supported at all. Such values are sent as text
  and cast in SQL. "%s::vector" / "%s::jsonb" / "%s::int[]" are rewritten to
  "CAST(:pN AS vector)" etc., since the Data API's parser does not reliably
  accept a "::" cast directly after a named parameter.
- With scale-to-zero, the first call after idle fails fast with
  DatabaseResumingException while the cluster wakes up (~15s). Calls retry
  until it is back, instead of silently returning no rows.
"""

from __future__ import annotations

import json
import os
import re
import time
from functools import lru_cache
from typing import Any, Optional

import boto3
from botocore.config import Config

# "%s" optionally followed by a "::type" cast, e.g. "%s::vector", "%s::int[]".
_PLACEHOLDER = re.compile(r"%s(?:::(\w+(?:\[\])?))?")

# How long to keep retrying while a paused cluster resumes. Kept under the
# Lambda's 28s timeout so a resume still leaves time to answer.
RESUME_WAIT_SECONDS = float(os.getenv("AURORA_RESUME_WAIT_SECONDS", "20"))

# Optional absolute (time.monotonic) cutoff for waiting on a resume, shared
# by every query in one request. Set by rag/ask.py per question so the
# waits of several queries can't add up past API Gateway's 29s limit.
_request_deadline: Optional[float] = None


def set_request_deadline(seconds_from_now: Optional[float]) -> None:
    global _request_deadline
    _request_deadline = None if seconds_from_now is None else time.monotonic() + seconds_from_now


@lru_cache(maxsize=None)
def _client(region: str):
    config = Config(retries={"max_attempts": 5, "mode": "standard"}, read_timeout=45)
    return boto3.client("rds-data", region_name=region, config=config)


class DatabaseUnavailableError(RuntimeError):
    """The cluster is paused/resuming and did not come back in time.

    Raised instead of returning an empty result, so callers can tell the
    user "try again in a moment" rather than "nothing found".
    """


# Error codes / message fragments the Data API returns while a scaled-to-zero
# cluster is waking up (or briefly unreachable during a scaling event).
_RESUME_CODES = {"DatabaseResumingException", "DatabaseUnavailableException", "ServiceUnavailableError"}
_RESUME_TEXT = ("resuming", "communications link failure", "is not available", "unavailable")


def _is_resuming(exc: Exception) -> bool:
    code = getattr(exc, "response", {}).get("Error", {}).get("Code", "")
    text = str(exc).lower()
    return code in _RESUME_CODES or any(t in text for t in _RESUME_TEXT)


class RdsDataApiManager:
    """Same calling convention as DatabaseManager: `with RdsDataApiManager() as db:`."""

    def __init__(self):
        self.cluster_arn = os.environ["AURORA_CLUSTER_ARN"]
        self.secret_arn = os.environ["AURORA_SECRET_ARN"]
        self.database = os.environ["AURORA_DATABASE"]
        region = os.getenv("AURORA_REGION") or os.getenv("AWS_REGION", "us-east-1")
        self._client = _client(region)

    def __enter__(self):
        # The Data API is a stateless HTTP call per statement; there is no
        # persistent connection to open. The `with` block only exists to
        # match DatabaseManager's context-manager shape.
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        return None

    def _call(self, fn, wait_seconds: float = RESUME_WAIT_SECONDS, **kwargs):
        deadline = time.monotonic() + wait_seconds
        if _request_deadline is not None:
            deadline = min(deadline, _request_deadline)
        while True:
            try:
                return fn(
                    resourceArn=self.cluster_arn,
                    secretArn=self.secret_arn,
                    database=self.database,
                    **kwargs,
                )
            except Exception as e:  # noqa: BLE001 - re-raised unless it is a resume
                if not _is_resuming(e) or time.monotonic() >= deadline:
                    raise
                time.sleep(2)

    def ping(self, wait_seconds: float = 0) -> bool:
        """Cheap `SELECT 1`. With wait_seconds=0 this just kicks off a resume
        of a paused cluster without waiting for it (used by /telemetry when
        the chat panel opens, so the database is warm by the first question)."""
        try:
            self._call(self._client.execute_statement, wait_seconds=wait_seconds, sql="SELECT 1")
            return True
        except Exception:  # noqa: BLE001
            return False

    def execute_query(self, query, params=None, fetch=False):
        """Same signature as DatabaseManager.execute_query.

        On error, mirrors DatabaseManager's behavior of logging and
        returning None rather than raising, since ask.py's retrieval
        helpers assume a query that fails returns an empty/None result
        instead of crashing the whole /ask request.
        """
        named_sql, parameters = _to_named_parameters(query, params)
        try:
            resp = self._call(
                self._client.execute_statement,
                sql=named_sql,
                parameters=parameters,
                formatRecordsAs="JSON",
            )
        except Exception as e:  # noqa: BLE001 - intentionally broad, see docstring
            print(f"RDS Data API error: {e}")
            if _is_resuming(e):
                # Not "no rows": the database is still waking up. Surfacing
                # this lets /ask say so instead of claiming nothing matched.
                raise DatabaseUnavailableError(str(e)) from e
            return None
        if not fetch:
            return None
        formatted = resp.get("formattedRecords")
        if not formatted:
            return []
        return json.loads(formatted)

    def execute_ddl(self, sql: str) -> None:
        """Run one statement and raise on failure (schema setup, migrations)."""
        self._call(self._client.execute_statement, wait_seconds=120, sql=sql)

    def execute_batch(self, query, param_rows, page_size=25):
        """Bulk insert/update via BatchExecuteStatement. Raises on failure.

        NOTE - different calling convention than DatabaseManager.execute_batch:
        DatabaseManager mirrors psycopg2's execute_values (one "%s" standing
        in for a whole VALUES row). The Data API's batch_execute_statement
        instead wants one placeholder per column, repeated per parameter
        set. So `query` here must look like:

            INSERT INTO tblartifacts (title, url, embedding)
            VALUES (%s, %s, %s::vector)

        and `param_rows` is a list of tuples, one per row, each matching
        the "%s" count in `query`. This is the convention the corpus
        migration script (backend/database/migrate_to_bedrock.py) uses.
        page_size is small because each row can carry a 1024-float vector
        plus chunk text, and Data API requests are size-limited.
        """
        if not param_rows:
            return
        named_sql, _ = _to_named_parameters(query, param_rows[0])
        for start in range(0, len(param_rows), page_size):
            batch = param_rows[start : start + page_size]
            parameter_sets = [_to_named_parameters(query, row)[1] for row in batch]
            self._call(
                self._client.batch_execute_statement,
                wait_seconds=120,
                sql=named_sql,
                parameterSets=parameter_sets,
            )


def _to_named_parameters(sql: str, params: Optional[Any]):
    """Rewrite positional "%s" placeholders to ":p0", ":p1", ... and build
    the matching Data API `parameters` list from `params` (a tuple/list in
    the same order as the placeholders, matching psycopg2 convention)."""
    if params is None:
        params = ()
    counter = {"i": 0}

    def _replace(match):
        idx = counter["i"]
        counter["i"] += 1
        cast = match.group(1)
        return f"CAST(:p{idx} AS {cast})" if cast else f":p{idx}"

    named_sql = _PLACEHOLDER.sub(_replace, sql)
    parameters = [_to_data_api_value(f"p{i}", value) for i, value in enumerate(params)]
    return named_sql, parameters


def _to_data_api_value(name: str, value: Any) -> dict[str, Any]:
    if value is None:
        return {"name": name, "value": {"isNull": True}}
    if isinstance(value, bool):
        return {"name": name, "value": {"booleanValue": value}}
    if isinstance(value, int):
        return {"name": name, "value": {"longValue": value}}
    if isinstance(value, float):
        return {"name": name, "value": {"doubleValue": value}}
    if isinstance(value, (list, tuple)):
        return {"name": name, "value": {"stringValue": _array_literal(value)}}
    return {"name": name, "value": {"stringValue": str(value)}}


def _array_literal(value) -> str:
    """Text form of a list, for a SQL-side CAST (the Data API has no array params).

    A list of ints becomes a Postgres array literal "{1,2,3}" (for
    `%s::int[]`); anything else is treated as an embedding vector and
    becomes pgvector's "[0.1,0.2,...]" (for `%s::vector`).
    """
    if value and all(isinstance(v, int) and not isinstance(v, bool) for v in value):
        return "{" + ",".join(str(v) for v in value) + "}"
    if not value:
        return "{}"
    # 8 significant digits is float32 precision, which is what pgvector stores.
    return "[" + ",".join(f"{float(v):.8g}" for v in value) + "]"
