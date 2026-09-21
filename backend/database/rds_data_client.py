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

Embeddings are the one case that needs special handling: pgvector's
`vector` type is not a native Data API type. Per Section 5.3, an embedding
list[float] is passed as a stringified array and cast in SQL
(e.g. "%s::vector" -> ":p0::vector"), not as a Data API arrayValue.
"""

from __future__ import annotations

import os
import re
from typing import Any, Optional

import boto3

_PLACEHOLDER = re.compile(r"%s")


class RdsDataApiManager:
    """Same calling convention as DatabaseManager: `with RdsDataApiManager() as db:`."""

    def __init__(self):
        self.cluster_arn = os.environ["AURORA_CLUSTER_ARN"]
        self.secret_arn = os.environ["AURORA_SECRET_ARN"]
        self.database = os.environ["AURORA_DATABASE"]
        self.schema = os.getenv("POSTGRES_SCHEMA", "public")
        region = os.getenv("AURORA_REGION") or os.getenv("AWS_REGION", "us-east-1")
        self._client = boto3.client("rds-data", region_name=region)
        self._in_session = False

    def __enter__(self):
        # The Data API is a stateless HTTP call per statement; there is no
        # persistent connection to open. `_in_session` only exists so the
        # `with` block matches DatabaseManager's context-manager shape.
        self._in_session = True
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self._in_session = False

    def _execute(self, sql: str, params: Optional[Any] = None, include_metadata: bool = False):
        named_sql, parameters = _to_named_parameters(sql, params)
        kwargs = dict(
            resourceArn=self.cluster_arn,
            secretArn=self.secret_arn,
            database=self.database,
            sql=named_sql,
            parameters=parameters,
            formatRecordsAs="JSON",
            includeResultMetadata=include_metadata,
        )
        if self.schema:
            kwargs["schema"] = self.schema
        return self._client.execute_statement(**kwargs)

    def execute_query(self, query, params=None, fetch=False):
        """Same signature as DatabaseManager.execute_query.

        On error, mirrors DatabaseManager's behavior of logging and
        returning None rather than raising, since ask.py's retrieval
        helpers assume a query that fails returns an empty/None result
        instead of crashing the whole /ask request.
        """
        try:
            resp = self._execute(query, params)
        except Exception as e:  # noqa: BLE001 - intentionally broad, see docstring
            print(f"RDS Data API error: {e}")
            return None
        if not fetch:
            return None
        formatted = resp.get("formattedRecords")
        if not formatted:
            return []
        import json

        return json.loads(formatted)

    def execute_batch(self, query, param_rows, page_size=100):
        """Bulk insert/update via BatchExecuteStatement.

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
        """
        if not param_rows:
            return
        named_sql, _ = _to_named_parameters(query, param_rows[0])
        for start in range(0, len(param_rows), page_size):
            batch = param_rows[start : start + page_size]
            parameter_sets = [_to_named_parameters(query, row)[1] for row in batch]
            self._client.batch_execute_statement(
                resourceArn=self.cluster_arn,
                secretArn=self.secret_arn,
                database=self.database,
                schema=self.schema,
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

    def _replace(_match):
        idx = counter["i"]
        counter["i"] += 1
        return f":p{idx}"

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
        return _to_data_api_array_value(name, value)
    return {"name": name, "value": {"stringValue": str(value)}}


def _to_data_api_array_value(name: str, value) -> dict[str, Any]:
    if not value:
        return {"name": name, "value": {"arrayValue": {"longValues": []}}}
    if all(isinstance(v, bool) for v in value):
        return {"name": name, "value": {"arrayValue": {"booleanValues": list(value)}}}
    if all(isinstance(v, int) for v in value):
        # Native int array (e.g. `unnest(:pN::int[])` for artifact-id lookups).
        return {"name": name, "value": {"arrayValue": {"longValues": list(value)}}}
    # A list of floats is treated as an embedding vector: pgvector has no
    # native Data API type, so it is passed as a stringified array and cast
    # in SQL via "::vector" (Section 5.3), not as a Data API arrayValue.
    stringified = "[" + ",".join(repr(float(v)) for v in value) + "]"
    return {"name": name, "value": {"stringValue": stringified}}
