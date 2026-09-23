"""One-time corpus re-embed + load: Azure/OpenAI -> Aurora/Titan.

This is the single largest migration task (AWS Migration Plan, Section 5.2
and Executive Summary): OpenAI's and Amazon Titan's embedding spaces are
not comparable, so there is no way to reuse the existing 1792-dim vectors.
This script reads every artifact type, chunk type, artifact, and chunk from
the source (Azure) database, re-embeds the text that matters for each with
Titan Text Embeddings V2 via Bedrock, and loads everything into a fresh
Aurora Serverless v2 cluster (schema_aws.sql) over the RDS Data API.

Primary keys (idArtifact, idChunk, ...) and parent-hierarchy references
(idArtifactParent, idChunkParent) are copied verbatim from the source, not
remapped, so the existing recursive-CTE breadcrumb queries in
backend/rag/ask.py keep working unchanged against the new database. Rows
are inserted in parent-before-child order (a topological sort on the
self-referencing FK) since the destination is a real foreign key, not a
deferred one.

Usage (in order - see docs/AWS_DEPLOYMENT.md, Part 5):
    python migrate_to_bedrock.py --apply-schema          # create tables in Aurora (safe to re-run)
    python migrate_to_bedrock.py --dry-run               # count source rows, no writes
    python migrate_to_bedrock.py --limit 20              # smoke test: 20 artifacts + their chunks
    python migrate_to_bedrock.py                         # full run (re-runnable; skips rows already loaded)
    python migrate_to_bedrock.py --validate --sample-question "What is NextGen In A Box?"

Every write is INSERT ... ON CONFLICT DO NOTHING and progress is
checkpointed after each batch, so an interrupted run can simply be started
again with the same command.

Required environment (see env-template.txt):
    Source (Azure, read-only):   POSTGRES_HOST/DB/USER/PASSWORD/SCHEMA
    Destination (Aurora):        read automatically from the deployed
                                 CirohStack's outputs, or set
                                 AURORA_CLUSTER_ARN, AURORA_SECRET_ARN explicitly
    Bedrock:                     AWS credentials (aws sso login / aws configure)
"""

from __future__ import annotations

import argparse
import json
import re
import sys
import time
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.append(str(HERE.parent))

from dotenv import load_dotenv  # noqa: E402

load_dotenv(HERE.parent.parent / ".env")

from aws.stack_outputs import load_stack_outputs_into_env  # noqa: E402

load_stack_outputs_into_env()

from aws.bedrock_client import get_embedding  # noqa: E402
from database.rds_data_client import RdsDataApiManager  # noqa: E402

CHECKPOINT_PATH = HERE / "migrate_to_bedrock.checkpoint.json"
SCHEMA_PATH = HERE / "schema_aws.sql"

# Titan Text Embeddings V2 accepts up to 8,192 tokens (~50,000 characters).
MAX_EMBED_CHARS = 30000
BATCH_SIZE = 200


def _source_db():
    # Always psycopg2, regardless of DB_BACKEND: the source is the existing
    # Azure database, which has no Data API of its own. Imported here so
    # --apply-schema / --validate work without psycopg2 or Azure access.
    from database.database import DatabaseManager

    return DatabaseManager()


def _dest_db() -> RdsDataApiManager:
    return RdsDataApiManager()


def _load_checkpoint() -> dict:
    if CHECKPOINT_PATH.exists():
        return json.loads(CHECKPOINT_PATH.read_text())
    return {"artifact_ids_done": [], "chunk_ids_done": []}


def _save_checkpoint(done_artifacts: set, done_chunks: set) -> None:
    CHECKPOINT_PATH.write_text(
        json.dumps({"artifact_ids_done": sorted(done_artifacts), "chunk_ids_done": sorted(done_chunks)})
    )


def _topological_order(rows: list[dict], id_key: str, parent_key: str) -> list[dict]:
    """Order rows so a row's parent always appears before it (self-referencing FK)."""
    by_id = {row[id_key]: row for row in rows}
    ordered: list[dict] = []
    placed: set = set()

    for row in rows:
        # Walk up the parent chain iteratively (a recursive version can hit
        # Python's recursion limit on deep hierarchies), then place the
        # chain top-down.
        chain = []
        seen = set()
        current = row
        while current is not None and current[id_key] not in placed and current[id_key] not in seen:
            seen.add(current[id_key])
            chain.append(current)
            parent_id = current.get(parent_key)
            current = by_id.get(parent_id) if parent_id is not None else None
        for item in reversed(chain):
            placed.add(item[id_key])
            ordered.append(item)
    return ordered


def apply_schema(dest: RdsDataApiManager) -> None:
    """Run schema_aws.sql one statement at a time (the Data API does not
    accept multiple statements in one call). Every statement is
    IF NOT EXISTS, so this is safe to re-run."""
    sql = SCHEMA_PATH.read_text(encoding="utf-8")
    sql = "\n".join(line for line in sql.splitlines() if not line.strip().startswith("--"))
    statements = [s.strip() for s in sql.split(";") if s.strip()]
    print(
        f"Applying {len(statements)} statements from {SCHEMA_PATH.name} "
        "(the first one may wait ~15s while Aurora wakes up)..."
    )
    for statement in statements:
        preview = re.sub(r"\s+", " ", statement)[:70]
        print(f"  {preview}")
        dest.execute_ddl(statement)
    print("Schema ready.")


def fetch_artifact_types(source) -> list[dict]:
    with source as db:
        return db.execute_query(
            "SELECT idArtifactType, TypeName FROM TBLArtifactTypes ORDER BY idArtifactType",
            fetch=True,
        ) or []


def fetch_chunk_types(source) -> list[dict]:
    with source as db:
        return db.execute_query(
            "SELECT idChunkType, idArtifactType, TypeName FROM TBLChunkTypes ORDER BY idChunkType",
            fetch=True,
        ) or []


def fetch_artifacts(source, limit: int | None) -> list[dict]:
    # Note: Postgres folds unquoted identifiers to lowercase, so
    # RealDictCursor rows come back with lowercase keys (idartifact, title,
    # ...) regardless of how the columns are capitalized in schema.sql or
    # in this SELECT - every dict access below uses the lowercase form.
    query = (
        "SELECT idArtifact, idArtifactType, Title, URL, idArtifactParent, "
        "summary_data, metadata, last_updated, isActive FROM TBLArtifacts "
        "ORDER BY idArtifact"
    )
    with source as db:
        rows = db.execute_query(query, fetch=True) or []
    if not limit:
        return rows
    # A smoke test still needs every parent of the artifacts it loads, or
    # the idArtifactParent foreign key rejects the insert.
    by_id = {r["idartifact"]: r for r in rows}
    keep: dict = {}
    for row in rows[:limit]:
        current = row
        while current is not None and current["idartifact"] not in keep:
            keep[current["idartifact"]] = current
            current = by_id.get(current.get("idartifactparent"))
    return list(keep.values())


def fetch_chunks(source, artifact_ids: list[int] | None) -> list[dict]:
    """All chunks, or (for a --limit smoke test) only those of the given artifacts."""
    query = (
        'SELECT idChunk, idArtifact, idChunkType, idChunkParent, "order", '
        "chunk_text, metadata FROM TBLChunks"
    )
    params = None
    if artifact_ids is not None:
        query += " WHERE idArtifact = ANY(%s)"
        params = (list(artifact_ids),)
    query += " ORDER BY idChunk"
    with source as db:
        return db.execute_query(query, params=params, fetch=True) or []


def _artifact_embedding_text(row: dict) -> str:
    summary = (row.get("summary_data") or {}).get("summary_text") or ""
    keywords = (row.get("summary_data") or {}).get("keywords") or []
    metadata_text = (row.get("metadata") or {}).get("retrieval_metadata_text") or ""
    parts = [row.get("title") or ""]
    if summary:
        parts.append(summary)
    if keywords:
        parts.append("Keywords: " + ", ".join(str(k) for k in keywords))
    if metadata_text:
        parts.append(metadata_text)
    return "\n".join(p for p in parts if p)


def _embed_one(text: str):
    text = (text or "").strip()[:MAX_EMBED_CHARS]
    if not text:
        return None  # Titan rejects empty input; store a NULL embedding instead.
    vector, _usage = get_embedding(text)
    return vector


def _embed_many(texts: list[str], concurrency: int) -> list:
    with ThreadPoolExecutor(max_workers=concurrency) as pool:
        return list(pool.map(_embed_one, texts))


def _json_or_none(value):
    return json.dumps(value) if value is not None else None


def load_artifact_types(dest: RdsDataApiManager, rows: list[dict]) -> None:
    if not rows:
        return
    query = (
        "INSERT INTO TBLArtifactTypes (idArtifactType, TypeName) VALUES (%s, %s) "
        "ON CONFLICT DO NOTHING"
    )
    dest.execute_batch(query, [(r["idartifacttype"], r["typename"]) for r in rows])


def load_chunk_types(dest: RdsDataApiManager, rows: list[dict]) -> None:
    if not rows:
        return
    query = (
        "INSERT INTO TBLChunkTypes (idChunkType, idArtifactType, TypeName) VALUES (%s, %s, %s) "
        "ON CONFLICT DO NOTHING"
    )
    dest.execute_batch(query, [(r["idchunktype"], r["idartifacttype"], r["typename"]) for r in rows])


def load_artifacts(dest: RdsDataApiManager, rows: list[dict], embeddings: list) -> None:
    # jsonb and vector are sent as text and cast in SQL (Section 5.3).
    query = (
        "INSERT INTO TBLArtifacts "
        "(idArtifact, idArtifactType, Title, URL, idArtifactParent, summary_data, "
        "metadata, embedding, isActive) "
        "VALUES (%s, %s, %s, %s, %s, %s::jsonb, %s::jsonb, %s::vector, %s) "
        "ON CONFLICT DO NOTHING"
    )
    params = [
        (
            r["idartifact"],
            r["idartifacttype"],
            r["title"],
            r["url"],
            r["idartifactparent"],
            _json_or_none(r.get("summary_data")),
            _json_or_none(r.get("metadata")),
            e,
            bool(r["isactive"]),
        )
        for r, e in zip(rows, embeddings)
    ]
    dest.execute_batch(query, params)


def load_chunks(dest: RdsDataApiManager, rows: list[dict], embeddings: list) -> None:
    query = (
        "INSERT INTO TBLChunks "
        '(idChunk, idArtifact, idChunkType, idChunkParent, "order", chunk_text, embedding, metadata) '
        "VALUES (%s, %s, %s, %s, %s, %s, %s::vector, %s::jsonb) "
        "ON CONFLICT DO NOTHING"
    )
    params = [
        (
            r["idchunk"],
            r["idartifact"],
            r["idchunktype"],
            r["idchunkparent"],
            r.get("order"),
            r.get("chunk_text"),
            e,
            _json_or_none(r.get("metadata")),
        )
        for r, e in zip(rows, embeddings)
    ]
    dest.execute_batch(query, params)


def _migrate_in_batches(label, rows, id_key, text_fn, load_fn, dest, done, save, concurrency):
    """Embed + load `rows` BATCH_SIZE at a time, checkpointing after each batch."""
    pending = [r for r in rows if r[id_key] not in done]
    print(f"{label}: {len(rows) - len(pending)} already loaded, {len(pending)} to go.")
    started = time.time()
    for start in range(0, len(pending), BATCH_SIZE):
        batch = pending[start : start + BATCH_SIZE]
        embeddings = _embed_many([text_fn(r) for r in batch], concurrency)
        load_fn(dest, batch, embeddings)
        done.update(r[id_key] for r in batch)
        save()
        print(
            f"  {min(start + BATCH_SIZE, len(pending))}/{len(pending)} "
            f"({time.time() - started:.0f}s elapsed)"
        )


def reset_sequences(dest: RdsDataApiManager) -> None:
    """Explicit-PK inserts don't advance the SERIAL sequences; fix them up
    so future ingestion runs (PopulateDB.ipynb) don't collide with migrated ids."""
    for table, column in (
        ("tblartifacttypes", "idartifacttype"),
        ("tblchunktypes", "idchunktype"),
        ("tblartifacts", "idartifact"),
        ("tblchunks", "idchunk"),
    ):
        dest.execute_query(
            f"SELECT setval(pg_get_serial_sequence('{table}', '{column}'), "
            f"COALESCE((SELECT MAX({column}) FROM {table}), 1))"
        )


def validate(dest: RdsDataApiManager, sample_questions: list[str] | None = None) -> None:
    """Spot-check retrieval quality post-migration (Section 11: "spot-check
    answers against known-good questions before cutover"). This checks
    counts and that vector search returns rows at all; it intentionally
    does not call the LLM (fast, nearly free, run it as often as you like)."""
    dest.ping(wait_seconds=60)

    def count(sql):
        rows = dest.execute_query(sql, fetch=True)
        return rows[0]["n"] if rows else "?"

    orphans = count(
        "SELECT COUNT(*) AS n FROM TBLChunks c "
        "LEFT JOIN TBLArtifacts a ON a.idArtifact = c.idArtifact WHERE a.idArtifact IS NULL"
    )
    print(f"Artifacts: {count('SELECT COUNT(*) AS n FROM TBLArtifacts')}")
    print(f"Chunks:    {count('SELECT COUNT(*) AS n FROM TBLChunks')}")
    print(f"Orphan chunks (no matching artifact): {orphans}")
    print(
        "Artifacts with NULL embedding: "
        f"{count('SELECT COUNT(*) AS n FROM TBLArtifacts WHERE embedding IS NULL')}"
    )
    if orphans not in (0, "?"):
        print("WARNING: orphan chunks found - check topological load order / source FK integrity.")

    for question in sample_questions or []:
        vector, _usage = get_embedding(question)
        rows = dest.execute_query(
            "SELECT idArtifact, Title, (embedding <=> %s::vector) AS distance "
            "FROM TBLArtifacts WHERE embedding IS NOT NULL "
            "ORDER BY embedding <=> %s::vector LIMIT 3",
            params=(vector, vector),
            fetch=True,
        )
        print(f"\nQ: {question}")
        for row in rows or []:
            print(f"  distance={row['distance']:.4f}  {row['title']}")


def main() -> None:
    parser = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    parser.add_argument("--apply-schema", action="store_true", help="Create the tables in Aurora, then exit.")
    parser.add_argument("--dry-run", action="store_true", help="Count source rows only, no embedding/writes.")
    parser.add_argument("--limit", type=int, default=None, help="Only migrate N artifacts (+ their chunks).")
    parser.add_argument("--concurrency", type=int, default=8, help="Parallel Bedrock embedding calls.")
    parser.add_argument("--restart", action="store_true", help="Ignore the checkpoint file and start over.")
    parser.add_argument("--validate", action="store_true", help="Run post-load validation only.")
    parser.add_argument(
        "--sample-question",
        action="append",
        default=[],
        help="Question(s) to spot-check retrieval against (repeatable). Used with --validate.",
    )
    # Kept for backwards compatibility: resuming is now the default behavior.
    parser.add_argument("--resume", action="store_true", help=argparse.SUPPRESS)
    args = parser.parse_args()

    dest = _dest_db()

    if args.apply_schema:
        apply_schema(dest)
        return

    if args.validate:
        validate(dest, sample_questions=args.sample_question)
        return

    source = _source_db()
    print("Fetching source rows from Azure...")
    artifact_types = fetch_artifact_types(source)
    chunk_types = fetch_chunk_types(source)
    artifacts = fetch_artifacts(source, args.limit)
    chunks = fetch_chunks(source, [a["idartifact"] for a in artifacts] if args.limit else None)
    print(
        f"  {len(artifact_types)} artifact types, {len(chunk_types)} chunk types, "
        f"{len(artifacts)} artifacts, {len(chunks)} chunks"
    )
    if not artifacts:
        sys.exit("No artifacts read from the source database - check the POSTGRES_* values in .env.")

    if args.dry_run:
        print("Dry run: no embeddings computed, no writes made.")
        return

    checkpoint = {"artifact_ids_done": [], "chunk_ids_done": []} if args.restart else _load_checkpoint()
    done_artifacts = set(checkpoint["artifact_ids_done"])
    done_chunks = set(checkpoint["chunk_ids_done"])

    def save():
        _save_checkpoint(done_artifacts, done_chunks)

    print("Waking Aurora (up to ~15s if it was paused)...")
    dest.ping(wait_seconds=60)

    print("Loading reference tables...")
    load_artifact_types(dest, artifact_types)
    load_chunk_types(dest, chunk_types)

    _migrate_in_batches(
        "Artifacts",
        _topological_order(artifacts, "idartifact", "idartifactparent"),
        "idartifact",
        _artifact_embedding_text,
        load_artifacts,
        dest,
        done_artifacts,
        save,
        args.concurrency,
    )
    _migrate_in_batches(
        "Chunks",
        _topological_order(chunks, "idchunk", "idchunkparent"),
        "idchunk",
        lambda c: c.get("chunk_text") or "",
        load_chunks,
        dest,
        done_chunks,
        save,
        args.concurrency,
    )

    print("Resetting sequences...")
    reset_sequences(dest)

    print("Done. Run with --validate to spot-check retrieval before cutover.")


if __name__ == "__main__":
    main()
