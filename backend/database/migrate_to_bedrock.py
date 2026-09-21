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

Usage:
    python migrate_to_bedrock.py --dry-run
    python migrate_to_bedrock.py --limit 50              # smoke test
    python migrate_to_bedrock.py --concurrency 8
    python migrate_to_bedrock.py --resume                # skip already-loaded rows
    python migrate_to_bedrock.py --validate               # spot-check retrieval only

Required environment (see env-template.txt):
    Source (Azure, read-only):   POSTGRES_HOST/DB/USER/PASSWORD/SCHEMA
    Destination (Aurora):        AURORA_CLUSTER_ARN, AURORA_SECRET_ARN,
                                  AURORA_DATABASE, AURORA_REGION
    Bedrock:                     AWS credentials with bedrock:InvokeModel
                                  (BEDROCK_EMBED_MODEL_ID, BEDROCK_EMBED_DIMENSIONS
                                  optional, default amazon.titan-embed-text-v2:0 / 1024)

Run `schema_aws.sql` against the destination cluster first (Section 10, step 3).
"""

from __future__ import annotations

import argparse
import json
import sys
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.append(str(HERE.parent))

from dotenv import load_dotenv  # noqa: E402

load_dotenv(HERE.parent.parent / ".env")

from aws.bedrock_client import get_embedding  # noqa: E402
from database.database import DatabaseManager  # noqa: E402
from database.rds_data_client import RdsDataApiManager  # noqa: E402

CHECKPOINT_PATH = HERE / "migrate_to_bedrock.checkpoint.json"


def _source_db() -> DatabaseManager:
    # Always psycopg2, regardless of DB_BACKEND: the source is the existing
    # Azure database, which has no Data API of its own.
    return DatabaseManager()


def _dest_db() -> RdsDataApiManager:
    return RdsDataApiManager()


def _load_checkpoint() -> dict:
    if CHECKPOINT_PATH.exists():
        return json.loads(CHECKPOINT_PATH.read_text())
    return {"artifact_ids_done": [], "chunk_ids_done": []}


def _save_checkpoint(state: dict) -> None:
    CHECKPOINT_PATH.write_text(json.dumps(state))


def _topological_order(rows: list[dict], id_key: str, parent_key: str) -> list[dict]:
    """Order rows so a row's parent always appears before it (self-referencing FK)."""
    by_id = {row[id_key]: row for row in rows}
    ordered: list[dict] = []
    placed: set = set()

    def place(row):
        rid = row[id_key]
        if rid in placed:
            return
        parent_id = row.get(parent_key)
        if parent_id is not None and parent_id in by_id and parent_id not in placed:
            place(by_id[parent_id])
        placed.add(rid)
        ordered.append(row)

    for row in rows:
        place(row)
    return ordered


def fetch_artifact_types(source: DatabaseManager) -> list[dict]:
    with source as db:
        return db.execute_query(
            "SELECT idArtifactType, TypeName FROM TBLArtifactTypes ORDER BY idArtifactType",
            fetch=True,
        ) or []


def fetch_chunk_types(source: DatabaseManager) -> list[dict]:
    with source as db:
        return db.execute_query(
            "SELECT idChunkType, idArtifactType, TypeName FROM TBLChunkTypes ORDER BY idChunkType",
            fetch=True,
        ) or []


def fetch_artifacts(source: DatabaseManager, limit: int | None) -> list[dict]:
    # Note: Postgres folds unquoted identifiers to lowercase, so
    # RealDictCursor rows come back with lowercase keys (idartifact, title,
    # ...) regardless of how the columns are capitalized in schema.sql or
    # in this SELECT - every dict access below uses the lowercase form.
    query = (
        "SELECT idArtifact, idArtifactType, Title, URL, idArtifactParent, "
        "summary_data, metadata, last_updated, isActive FROM TBLArtifacts "
        "ORDER BY idArtifact"
    )
    if limit:
        query += f" LIMIT {int(limit)}"
    with source as db:
        return db.execute_query(query, fetch=True) or []


def fetch_chunks(source: DatabaseManager, limit: int | None) -> list[dict]:
    query = (
        'SELECT idChunk, idArtifact, idChunkType, idChunkParent, "order", '
        "chunk_text, metadata FROM TBLChunks ORDER BY idChunk"
    )
    if limit:
        query += f" LIMIT {int(limit)}"
    with source as db:
        return db.execute_query(query, fetch=True) or []


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


def _embed_many(texts: list[str], concurrency: int) -> list[list[float]]:
    results: list[list[float] | None] = [None] * len(texts)
    with ThreadPoolExecutor(max_workers=concurrency) as pool:
        futures = {pool.submit(get_embedding, text): i for i, text in enumerate(texts)}
        for future in as_completed(futures):
            idx = futures[future]
            vector, _usage = future.result()
            results[idx] = vector
    return results  # type: ignore[return-value]


def load_artifact_types(dest: RdsDataApiManager, rows: list[dict]) -> None:
    if not rows:
        return
    query = "INSERT INTO TBLArtifactTypes (idArtifactType, TypeName) VALUES (%s, %s)"
    with dest as db:
        db.execute_batch(query, [(r["idartifacttype"], r["typename"]) for r in rows])


def load_chunk_types(dest: RdsDataApiManager, rows: list[dict]) -> None:
    if not rows:
        return
    query = "INSERT INTO TBLChunkTypes (idChunkType, idArtifactType, TypeName) VALUES (%s, %s, %s)"
    with dest as db:
        db.execute_batch(
            query, [(r["idchunktype"], r["idartifacttype"], r["typename"]) for r in rows]
        )


def load_artifacts(dest: RdsDataApiManager, rows: list[dict], embeddings: list[list[float]]) -> None:
    if not rows:
        return
    query = (
        "INSERT INTO TBLArtifacts "
        "(idArtifact, idArtifactType, Title, URL, idArtifactParent, summary_data, "
        "metadata, embedding, isActive) "
        "VALUES (%s, %s, %s, %s, %s, %s, %s, %s::vector, %s)"
    )
    rows_ordered = _topological_order(rows, "idartifact", "idartifactparent")
    embed_by_id = {r["idartifact"]: e for r, e in zip(rows, embeddings)}
    params = [
        (
            r["idartifact"],
            r["idartifacttype"],
            r["title"],
            r["url"],
            r["idartifactparent"],
            json.dumps(r["summary_data"]) if r.get("summary_data") is not None else None,
            json.dumps(r["metadata"]) if r.get("metadata") is not None else None,
            embed_by_id[r["idartifact"]],
            bool(r["isactive"]),
        )
        for r in rows_ordered
    ]
    with dest as db:
        db.execute_batch(query, params)


def load_chunks(dest: RdsDataApiManager, rows: list[dict], embeddings: list[list[float]]) -> None:
    if not rows:
        return
    query = (
        "INSERT INTO TBLChunks "
        '(idChunk, idArtifact, idChunkType, idChunkParent, "order", chunk_text, embedding, metadata) '
        "VALUES (%s, %s, %s, %s, %s, %s, %s::vector, %s)"
    )
    rows_ordered = _topological_order(rows, "idchunk", "idchunkparent")
    embed_by_id = {r["idchunk"]: e for r, e in zip(rows, embeddings)}
    params = [
        (
            r["idchunk"],
            r["idartifact"],
            r["idchunktype"],
            r["idchunkparent"],
            r.get("order"),
            r.get("chunk_text"),
            embed_by_id[r["idchunk"]],
            json.dumps(r["metadata"]) if r.get("metadata") is not None else None,
        )
        for r in rows_ordered
    ]
    with dest as db:
        db.execute_batch(query, params)


def reset_sequences(dest: RdsDataApiManager) -> None:
    """Explicit-PK inserts don't advance the SERIAL sequences; fix them up
    so future ingestion runs (PopulateDB.ipynb) don't collide with migrated ids."""
    with dest as db:
        db.execute_query(
            "SELECT setval('tblartifacttypes_idartifacttype_seq', "
            "COALESCE((SELECT MAX(idArtifactType) FROM TBLArtifactTypes), 1))"
        )
        db.execute_query(
            "SELECT setval('tblchunktypes_idchunktype_seq', "
            "COALESCE((SELECT MAX(idChunkType) FROM TBLChunkTypes), 1))"
        )
        db.execute_query(
            "SELECT setval('tblartifacts_idartifact_seq', "
            "COALESCE((SELECT MAX(idArtifact) FROM TBLArtifacts), 1))"
        )
        db.execute_query(
            "SELECT setval('tblchunks_idchunk_seq', COALESCE((SELECT MAX(idChunk) FROM TBLChunks), 1))"
        )


def validate(dest: RdsDataApiManager, sample_questions: list[str] | None = None) -> None:
    """Spot-check retrieval quality post-migration (Section 11: "spot-check
    answers against known-good questions before cutover"). This checks
    counts and that vector search returns rows at all; it intentionally
    does not call the LLM (fast, free, run it as often as you like)."""
    with dest as db:
        artifact_count = db.execute_query("SELECT COUNT(*) AS n FROM TBLArtifacts", fetch=True)
        chunk_count = db.execute_query("SELECT COUNT(*) AS n FROM TBLChunks", fetch=True)
        orphan_chunks = db.execute_query(
            "SELECT COUNT(*) AS n FROM TBLChunks c "
            "LEFT JOIN TBLArtifacts a ON a.idArtifact = c.idArtifact WHERE a.idArtifact IS NULL",
            fetch=True,
        )
        null_embeddings = db.execute_query(
            "SELECT COUNT(*) AS n FROM TBLArtifacts WHERE embedding IS NULL", fetch=True
        )
    print(f"Artifacts: {artifact_count[0]['n'] if artifact_count else '?'}")
    print(f"Chunks:    {chunk_count[0]['n'] if chunk_count else '?'}")
    print(f"Orphan chunks (no matching artifact): {orphan_chunks[0]['n'] if orphan_chunks else '?'}")
    print(f"Artifacts with NULL embedding: {null_embeddings[0]['n'] if null_embeddings else '?'}")
    if orphan_chunks and orphan_chunks[0]["n"]:
        print("WARNING: orphan chunks found - check topological load order / source FK integrity.")

    for question in sample_questions or []:
        vector, _usage = get_embedding(question)
        with dest as db:
            rows = db.execute_query(
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
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dry-run", action="store_true", help="Count rows only, no embedding/writes.")
    parser.add_argument("--limit", type=int, default=None, help="Cap rows fetched, for a smoke test.")
    parser.add_argument("--concurrency", type=int, default=8, help="Parallel Bedrock embedding calls.")
    parser.add_argument("--resume", action="store_true", help="Skip rows already in the checkpoint file.")
    parser.add_argument("--validate", action="store_true", help="Run post-load validation only.")
    parser.add_argument(
        "--sample-question",
        action="append",
        default=[],
        help="Question(s) to spot-check retrieval against (repeatable). Used with --validate.",
    )
    args = parser.parse_args()

    if args.validate:
        validate(_dest_db(), sample_questions=args.sample_question)
        return

    source = _source_db()
    dest = _dest_db()

    print("Fetching source rows from Azure...")
    artifact_types = fetch_artifact_types(source)
    chunk_types = fetch_chunk_types(source)
    artifacts = fetch_artifacts(source, args.limit)
    chunks = fetch_chunks(source, args.limit)
    print(
        f"  {len(artifact_types)} artifact types, {len(chunk_types)} chunk types, "
        f"{len(artifacts)} artifacts, {len(chunks)} chunks"
    )

    if args.dry_run:
        print("Dry run: no embeddings computed, no writes made.")
        return

    checkpoint = _load_checkpoint() if args.resume else {"artifact_ids_done": [], "chunk_ids_done": []}
    done_artifacts = set(checkpoint["artifact_ids_done"])
    done_chunks = set(checkpoint["chunk_ids_done"])

    pending_artifacts = [a for a in artifacts if a["idartifact"] not in done_artifacts]
    pending_chunks = [c for c in chunks if c["idchunk"] not in done_chunks]

    print("Loading reference tables...")
    load_artifact_types(dest, artifact_types)
    load_chunk_types(dest, chunk_types)

    print(f"Embedding {len(pending_artifacts)} artifacts with Titan Text Embeddings V2...")
    started = time.time()
    artifact_texts = [_artifact_embedding_text(a) for a in pending_artifacts]
    artifact_embeddings = _embed_many(artifact_texts, args.concurrency)
    print(f"  done in {time.time() - started:.1f}s")

    print("Loading artifacts into Aurora...")
    load_artifacts(dest, pending_artifacts, artifact_embeddings)
    done_artifacts.update(a["idartifact"] for a in pending_artifacts)
    _save_checkpoint({"artifact_ids_done": sorted(done_artifacts), "chunk_ids_done": sorted(done_chunks)})

    print(f"Embedding {len(pending_chunks)} chunks with Titan Text Embeddings V2...")
    started = time.time()
    chunk_texts = [c.get("chunk_text") or "" for c in pending_chunks]
    chunk_embeddings = _embed_many(chunk_texts, args.concurrency)
    print(f"  done in {time.time() - started:.1f}s")

    print("Loading chunks into Aurora...")
    load_chunks(dest, pending_chunks, chunk_embeddings)
    done_chunks.update(c["idchunk"] for c in pending_chunks)
    _save_checkpoint({"artifact_ids_done": sorted(done_artifacts), "chunk_ids_done": sorted(done_chunks)})

    print("Resetting sequences...")
    reset_sequences(dest)

    print("Done. Run with --validate to spot-check retrieval before cutover.")


if __name__ == "__main__":
    main()
