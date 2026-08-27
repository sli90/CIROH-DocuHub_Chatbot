"""Migrate active DocuHub URLs from docs.ciroh.org to hub.ciroh.org.

Inactive artifact versions and their chunks are intentionally preserved.
Run without --apply for a read-only audit.
"""
from __future__ import annotations

import argparse
import gzip
import json
import os
import re
from datetime import datetime, timezone
from pathlib import Path

import psycopg2
from dotenv import dotenv_values


SCRIPT_DIR = Path(__file__).resolve().parent
ROOT = SCRIPT_DIR.parent
OLD_HOST = "docs.ciroh.org"
NEW_HOST = "hub.ciroh.org"
DOCUHUB_ARTIFACT_TYPE_ID = 1


def load_config(env_file: Path) -> tuple[dict, str]:
    values = dotenv_values(env_file)

    def setting(name: str) -> str:
        return os.environ.get(name) or values.get(name, "")

    config = {
        "host": setting("POSTGRES_HOST"),
        "database": setting("POSTGRES_DB"),
        "user": setting("POSTGRES_USER"),
        "password": setting("POSTGRES_PASSWORD"),
    }
    missing = [name for name, value in config.items() if not value]
    if missing:
        raise RuntimeError("Missing PostgreSQL settings: " + ", ".join(missing))
    schema = setting("POSTGRES_SCHEMA") or "public"
    if not re.fullmatch(r"[A-Za-z_][A-Za-z0-9_]*", schema):
        raise RuntimeError(f"Unsafe schema name: {schema!r}")
    return config, schema


def scalar(cursor, query: str, params=()):
    cursor.execute(query, params)
    row = cursor.fetchone()
    return row[0] if row else None


def audit(cursor) -> dict:
    active_urls = scalar(
        cursor,
        "SELECT COUNT(*) FROM tblartifacts "
        "WHERE idartifacttype=%s AND isactive=TRUE "
        "AND url ~* '^https?://docs\\.ciroh\\.org(?:/|$)'",
        (DOCUHUB_ARTIFACT_TYPE_ID,),
    )
    inactive_urls = scalar(
        cursor,
        "SELECT COUNT(*) FROM tblartifacts "
        "WHERE idartifacttype=%s AND isactive=FALSE "
        "AND url ~* '^https?://docs\\.ciroh\\.org(?:/|$)'",
        (DOCUHUB_ARTIFACT_TYPE_ID,),
    )
    active_summaries = scalar(
        cursor,
        "SELECT COUNT(*) FROM tblartifacts "
        "WHERE idartifacttype=%s AND isactive=TRUE "
        "AND summary_data::text ILIKE %s",
        (DOCUHUB_ARTIFACT_TYPE_ID, f"%{OLD_HOST}%"),
    )
    active_chunks = scalar(
        cursor,
        "SELECT COUNT(*) FROM tblchunks c "
        "JOIN tblartifacts a ON a.idartifact=c.idartifact "
        "WHERE a.idartifacttype=%s AND a.isactive=TRUE "
        "AND c.chunk_text ILIKE %s",
        (DOCUHUB_ARTIFACT_TYPE_ID, f"%{OLD_HOST}%"),
    )
    collisions = scalar(
        cursor,
        """
        WITH legacy AS (
          SELECT idartifact,
                 regexp_replace(
                   url,
                   '^https?://docs\\.ciroh\\.org',
                   'https://hub.ciroh.org',
                   'i'
                 ) AS new_url
          FROM tblartifacts
          WHERE idartifacttype=%s AND isactive=TRUE
            AND url ~* '^https?://docs\\.ciroh\\.org(?:/|$)'
        )
        SELECT COUNT(*)
        FROM legacy l
        JOIN tblartifacts x
          ON lower(x.url)=lower(l.new_url)
         AND x.idartifact<>l.idartifact
         AND x.isactive=TRUE
        """,
        (DOCUHUB_ARTIFACT_TYPE_ID,),
    )
    return {
        "active_urls": active_urls,
        "active_summaries": active_summaries,
        "active_chunk_texts": active_chunks,
        "inactive_urls_preserved": inactive_urls,
        "active_target_collisions": collisions,
    }


def preservation_signature(cursor, *, active: bool) -> dict:
    return {
        "artifacts": scalar(
            cursor,
            """
            SELECT md5(COALESCE(string_agg(
              idartifact::text || '|' || url || '|' ||
              COALESCE(summary_data::text, '') || '|' ||
              COALESCE(metadata::text, ''), E'\n' ORDER BY idartifact
            ), ''))
            FROM tblartifacts
            WHERE idartifacttype=%s AND isactive=%s
            """,
            (DOCUHUB_ARTIFACT_TYPE_ID, active),
        ),
        "chunks": scalar(
            cursor,
            """
            SELECT md5(COALESCE(string_agg(
              c.idchunk::text || '|' || COALESCE(c.chunk_text, '') || '|' ||
              COALESCE(c.metadata::text, ''), E'\n' ORDER BY c.idchunk
            ), ''))
            FROM tblchunks c
            JOIN tblartifacts a ON a.idartifact=c.idartifact
            WHERE a.idartifacttype=%s AND a.isactive=%s
            """,
            (DOCUHUB_ARTIFACT_TYPE_ID, active),
        ),
    }


def embedding_signature(cursor) -> dict:
    return {
        "artifacts": scalar(
            cursor,
            """
            SELECT md5(COALESCE(string_agg(
              idartifact::text || '|' || COALESCE(embedding::text, ''),
              E'\n' ORDER BY idartifact
            ), ''))
            FROM tblartifacts
            WHERE idartifacttype=%s AND isactive=TRUE
            """,
            (DOCUHUB_ARTIFACT_TYPE_ID,),
        ),
        "chunks": scalar(
            cursor,
            """
            SELECT md5(COALESCE(string_agg(
              c.idchunk::text || '|' || COALESCE(c.embedding::text, ''),
              E'\n' ORDER BY c.idchunk
            ), ''))
            FROM tblchunks c
            JOIN tblartifacts a ON a.idartifact=c.idartifact
            WHERE a.idartifacttype=%s AND a.isactive=TRUE
            """,
            (DOCUHUB_ARTIFACT_TYPE_ID,),
        ),
    }


def write_backup(cursor, backup_path: Path, audit_before: dict) -> None:
    cursor.execute(
        """
        SELECT idartifact, url, summary_data, metadata
        FROM tblartifacts
        WHERE idartifacttype=%s AND isactive=TRUE
          AND (url ILIKE %s OR summary_data::text ILIKE %s)
        ORDER BY idartifact
        """,
        (DOCUHUB_ARTIFACT_TYPE_ID, f"%{OLD_HOST}%", f"%{OLD_HOST}%"),
    )
    artifacts = [
        {
            "idartifact": row[0],
            "url": row[1],
            "summary_data": row[2],
            "metadata": row[3],
        }
        for row in cursor.fetchall()
    ]
    cursor.execute(
        """
        SELECT c.idchunk, c.chunk_text, c.metadata
        FROM tblchunks c
        JOIN tblartifacts a ON a.idartifact=c.idartifact
        WHERE a.idartifacttype=%s AND a.isactive=TRUE
          AND c.chunk_text ILIKE %s
        ORDER BY c.idchunk
        """,
        (DOCUHUB_ARTIFACT_TYPE_ID, f"%{OLD_HOST}%"),
    )
    chunks = [
        {"idchunk": row[0], "chunk_text": row[1], "metadata": row[2]}
        for row in cursor.fetchall()
    ]
    payload = {
        "created_at": datetime.now(timezone.utc).isoformat(),
        "scope": "active DocuHub URL migration backup",
        "old_host": OLD_HOST,
        "new_host": NEW_HOST,
        "audit_before": audit_before,
        "artifacts": artifacts,
        "chunks": chunks,
    }
    backup_path.parent.mkdir(parents=True, exist_ok=True)
    with gzip.open(backup_path, "wt", encoding="utf-8") as handle:
        json.dump(payload, handle, ensure_ascii=False, separators=(",", ":"))


def migrate(cursor) -> dict:
    cursor.execute(
        """
        UPDATE tblartifacts
        SET url=regexp_replace(
          url,
          '^https?://docs\\.ciroh\\.org',
          'https://hub.ciroh.org',
          'i'
        )
        WHERE idartifacttype=%s AND isactive=TRUE
          AND url ~* '^https?://docs\\.ciroh\\.org(?:/|$)'
        """,
        (DOCUHUB_ARTIFACT_TYPE_ID,),
    )
    urls_updated = cursor.rowcount
    cursor.execute(
        """
        UPDATE tblartifacts
        SET summary_data=regexp_replace(
          summary_data::text,
          'docs\\.ciroh\\.org',
          'hub.ciroh.org',
          'gi'
        )::jsonb
        WHERE idartifacttype=%s AND isactive=TRUE
          AND summary_data::text ILIKE %s
        """,
        (DOCUHUB_ARTIFACT_TYPE_ID, f"%{OLD_HOST}%"),
    )
    summaries_updated = cursor.rowcount
    cursor.execute(
        """
        UPDATE tblchunks c
        SET chunk_text=regexp_replace(
          c.chunk_text,
          'docs\\.ciroh\\.org',
          'hub.ciroh.org',
          'gi'
        )
        FROM tblartifacts a
        WHERE a.idartifact=c.idartifact
          AND a.idartifacttype=%s AND a.isactive=TRUE
          AND c.chunk_text ILIKE %s
        """,
        (DOCUHUB_ARTIFACT_TYPE_ID, f"%{OLD_HOST}%"),
    )
    chunks_updated = cursor.rowcount
    return {
        "urls_updated": urls_updated,
        "summaries_updated": summaries_updated,
        "chunk_texts_updated": chunks_updated,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--apply", action="store_true")
    parser.add_argument("--env-file", type=Path, default=SCRIPT_DIR / ".env")
    parser.add_argument(
        "--backup-dir",
        type=Path,
        default=ROOT / "dashboard" / "formated_files" / "database_backups",
    )
    args = parser.parse_args()

    config, schema = load_config(args.env_file)
    connection = psycopg2.connect(**config)
    try:
        with connection.cursor() as cursor:
            cursor.execute(f'SET search_path TO "{schema}", public')
            audit_before = audit(cursor)
            print(json.dumps({"mode": "apply" if args.apply else "audit", **audit_before}, indent=2))
            if not args.apply:
                connection.rollback()
                return 0
            if audit_before["active_target_collisions"]:
                raise RuntimeError("Active target URL collisions detected; refusing migration")

            stamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
            backup_path = args.backup_dir / f"docuhub_active_urls_{stamp}.json.gz"
            write_backup(cursor, backup_path, audit_before)
            inactive_before = preservation_signature(cursor, active=False)
            embeddings_before = embedding_signature(cursor)
            updates = migrate(cursor)
            audit_after = audit(cursor)
            inactive_after = preservation_signature(cursor, active=False)
            embeddings_after = embedding_signature(cursor)

            if inactive_after != inactive_before:
                raise RuntimeError("Inactive history changed; rolling back")
            if embeddings_after != embeddings_before:
                raise RuntimeError("Embeddings changed; rolling back")
            if audit_after["active_urls"] or audit_after["active_summaries"] or audit_after["active_chunk_texts"]:
                raise RuntimeError("Legacy active references remain; rolling back")
            connection.commit()

            report = {
                "status": "completed",
                "completed_at": datetime.now(timezone.utc).isoformat(),
                "old_host": OLD_HOST,
                "new_host": NEW_HOST,
                "inactive_history_preserved": True,
                "embeddings_preserved": True,
                "backup_path": str(backup_path),
                "updates": updates,
                "audit_before": audit_before,
                "audit_after": audit_after,
            }
            report_path = args.backup_dir / f"docuhub_active_urls_{stamp}_report.json"
            report_path.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
            print(json.dumps(report, indent=2))
    except Exception:
        connection.rollback()
        raise
    finally:
        connection.close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
