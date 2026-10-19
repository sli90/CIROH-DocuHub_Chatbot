"""
Delta processor for CIROH AI Bot artifacts and chunks.

Reads artifacts and chunks from JSON files, deactivates existing artifacts
by URL without deleting their chunks, re-inserts as active with summary_data,
then generates and stores embeddings. Previous artifact versions and chunks
are kept with isActive=FALSE for historical record.

Usage:
    python process_delta.py                          # uses artifacts_delta.json
    python process_delta.py --test                   # uses *_update.json files
    python process_delta.py --artifacts <path> --chunks <path>
"""

import argparse
import hashlib
import json
import os
import sys
import time
from datetime import datetime
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(SCRIPT_DIR))
ROOT = SCRIPT_DIR.parent
sys.path.insert(0, str(ROOT))

from database import DatabaseManager  # noqa: E402
from dotenv import load_dotenv  # noqa: E402
from psycopg2.extras import Json  # noqa: E402
from sync_accounting import UsageAccumulator  # noqa: E402

load_dotenv(SCRIPT_DIR / ".env")

EMBEDDING_MODEL = os.getenv("EMBEDDING_MODEL", "text-embedding-3-large")
DIMENSIONS = 1792
FLUSH_EVERY = 50
PAGE_SIZE = 200

DELTA_DIR = SCRIPT_DIR.parent / "dashboard" / "formated_files"
result_output_path = DELTA_DIR / "db_update_result.json"

FILE_CHUNKTYPE_TO_NAME = {1: "Section", 2: "Subsection", 3: "Subsubsection"}
REPOSITORY_CHUNK_TYPES = (
    "Project Overview",
    "Installation Setup",
    "Usage Examples",
    "Repository Structure",
    "Contributing Guidelines",
    "License Citation",
    "Documentation Section",
    "Notebook Section",
    "Configuration / Deployment",
    "Change Log / Release Notes",
)
HYDROSHARE_ARTIFACT_TYPE_ID = 3
HYDROSHARE_ARTIFACT_ROLE = "hydroshare_resource"
HYDROSHARE_PORTAL_TYPES = (
    "Apps",
    "Datasets",
    "Courses",
    "Presentations",
    "Events",
    "Notebooks",
)
HYDROSHARE_CHUNK_TYPES = (
    "Abstract",
    "Spatial Coverage",
    "Temporal Coverage",
    "Variable Metadata",
    "Data Services Info",
    "File Description",
    "Collection Contents",
    "Subject Keywords",
    "Related Resources Context",
    "Citation",
    "Creator",
    "Contributor",
    "Funding Agency",
    "Additional Metadata",
    "Readme File",
)
HYDROSHARE_PORTAL_TYPE_FIELDS = (
    "hs_research_portal_types",
    "research_portal_types",
    "portal_types",
)

db_manager = DatabaseManager()
client = None
embedding_usage = UsageAccumulator("embeddings", EMBEDDING_MODEL)


# ─── Data Loading ─────────────────────────────────────────────────

def load_delta_artifacts(delta_path: Path):
    """Load from delta format {new:[], updated:[], deleted:[]}.

    The `deleted` list from generate_formatted_files.py is a flat
    list of URL strings (not dicts), so we normalise both forms.
    """
    with open(delta_path, "r", encoding="utf-8") as f:
        delta = json.load(f)
    to_upsert = delta.get("new", []) + delta.get("updated", [])

    raw_deleted = delta.get("deleted", [])
    to_delete = []
    for item in raw_deleted:
        if isinstance(item, str):
            to_delete.append({"URL": item})
        elif isinstance(item, dict):
            to_delete.append(item)
    return to_upsert, to_delete


def load_update_artifacts(artifacts_path: Path):
    """Load from flat array format (all treated as upserts)."""
    with open(artifacts_path, "r", encoding="utf-8") as f:
        return json.load(f), []


def load_chunks(chunks_path: Path):
    """Handle both flat array and delta wrapper {chunks: [...]}.

    Returns empty list if file does not exist.
    """
    if not chunks_path.exists():
        print(f"  Chunks file not found: {chunks_path}")
        print("  Proceeding with no chunks.")
        return []
    with open(chunks_path, "r", encoding="utf-8") as f:
        data = json.load(f)
    if isinstance(data, dict) and "chunks" in data:
        return data["chunks"]
    return data


def _is_hydroshare_artifact(artifact: dict) -> bool:
    """Return whether an input record explicitly identifies HydroShare."""
    if artifact.get("artifact_role") == HYDROSHARE_ARTIFACT_ROLE:
        return True
    metadata = artifact.get("metadata")
    if not isinstance(metadata, dict):
        return False
    hydroshare = metadata.get("hydroshare")
    return (
        isinstance(hydroshare, dict)
        and hydroshare.get("artifact_role") == HYDROSHARE_ARTIFACT_ROLE
    )


def get_hydroshare_portal_types(artifact: dict) -> list[str]:
    """Return a stable, de-duplicated portal-type list from accepted fields."""
    raw_types = None
    for field in HYDROSHARE_PORTAL_TYPE_FIELDS:
        if field in artifact:
            raw_types = artifact.get(field)
            break

    if raw_types is None:
        metadata = artifact.get("metadata")
        hydroshare = (
            metadata.get("hydroshare")
            if isinstance(metadata, dict)
            else None
        )
        if isinstance(hydroshare, dict):
            for field in HYDROSHARE_PORTAL_TYPE_FIELDS:
                if field in hydroshare:
                    raw_types = hydroshare.get(field)
                    break

    if raw_types is None:
        return []
    if isinstance(raw_types, str):
        raw_types = [raw_types]
    if not isinstance(raw_types, (list, tuple, set)):
        raise RuntimeError(
            "HydroShare research portal types must be a list of names"
        )

    canonical_by_case = {
        name.casefold(): name for name in HYDROSHARE_PORTAL_TYPES
    }
    normalized = set()
    for value in raw_types:
        name = str(value).strip()
        if name:
            normalized.add(canonical_by_case.get(name.casefold(), name))
    return sorted(normalized)


def _fingerprint_artifact_payload(artifact: dict) -> dict:
    """Normalize volatile/aliased fields before content fingerprinting."""
    payload = {
        key: value
        for key, value in artifact.items()
        if key not in {"idArtifact", "_sync_content_fingerprint"}
    }
    if _is_hydroshare_artifact(artifact):
        for field in HYDROSHARE_PORTAL_TYPE_FIELDS:
            payload.pop(field, None)
        payload["hs_research_portal_types"] = get_hydroshare_portal_types(
            artifact
        )
    return payload


def _repository_snapshot_fingerprint(
    artifact: dict, repository_chunks: list[dict]
) -> str:
    """Return a stable fingerprint for one artifact and its chunks."""
    artifact_payload = _fingerprint_artifact_payload(artifact)
    chunk_payload = []
    for chunk in sorted(
        repository_chunks,
        key=lambda item: (
            int(item.get("order") or 0),
            int(item.get("idChunk") or 0),
        ),
    ):
        chunk_payload.append(
            {
                key: value
                for key, value in chunk.items()
                if key not in {"idArtifact", "idChunk"}
            }
        )
    encoded = json.dumps(
        {"artifact": artifact_payload, "chunks": chunk_payload},
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def _snapshot_fingerprints_with_parent_versions(
    artifacts_by_source_id: dict[int, dict],
    chunks_by_artifact: dict[int, list[dict]],
) -> dict[int, str]:
    """Fingerprint content plus the current parent version for safe retries."""
    base = {
        source_id: _repository_snapshot_fingerprint(
            artifact, chunks_by_artifact.get(source_id, [])
        )
        for source_id, artifact in artifacts_by_source_id.items()
    }
    resolved: dict[int, str] = {}

    def resolve(source_id: int, stack: set[int]) -> str:
        if source_id in resolved:
            return resolved[source_id]
        if source_id in stack:
            raise RuntimeError(f"Artifact parent cycle detected at {source_id}")
        artifact = artifacts_by_source_id[source_id]
        parent_source_id = artifact.get("idArtifactParent")
        if parent_source_id is None:
            resolved[source_id] = base[source_id]
            return resolved[source_id]
        try:
            parent_source_id = int(parent_source_id)
        except (TypeError, ValueError) as exc:
            raise RuntimeError(
                f"Invalid parent source ID {parent_source_id!r} for {source_id}"
            ) from exc
        if parent_source_id not in artifacts_by_source_id:
            raise RuntimeError(
                f"Artifact {source_id} references missing parent {parent_source_id}"
            )
        parent_fingerprint = resolve(parent_source_id, stack | {source_id})
        encoded = json.dumps(
            {
                "content_fingerprint": base[source_id],
                "parent_fingerprint": parent_fingerprint,
            },
            sort_keys=True,
            separators=(",", ":"),
        ).encode("utf-8")
        resolved[source_id] = hashlib.sha256(encoded).hexdigest()
        return resolved[source_id]

    for source_id in artifacts_by_source_id:
        resolve(source_id, set())
    return resolved


def reconcile_artifact_snapshot(
    db,
    artifacts: list[dict],
    chunks: list[dict],
    artifact_type_id: int,
    *,
    hydroshare_only: bool = False,
    allow_large_hydroshare_removals: bool = False,
):
    """Compare a full snapshot with active DB rows and return a true delta.

    Missing or changed artifacts are versioned. Active rows absent from the
    snapshot are soft-deactivated. Matching rows remain untouched, so an
    unchanged repository does not receive duplicate artifacts or embeddings.
    """
    if hydroshare_only and artifact_type_id != HYDROSHARE_ARTIFACT_TYPE_ID:
        raise RuntimeError(
            "HydroShare snapshot reconciliation requires artifact type 3"
        )
    if allow_large_hydroshare_removals and not hydroshare_only:
        raise RuntimeError(
            "Large HydroShare removal override requires HydroShare snapshot "
            "reconciliation"
        )
    if hydroshare_only and not artifacts:
        raise RuntimeError(
            "HydroShare snapshot is empty; refusing to deactivate every "
            "active HydroShare resource"
        )

    source_ids: set[int] = set()
    urls: set[str] = set()
    chunks_by_artifact: dict[int, list[dict]] = {}
    for chunk in chunks:
        source_id = chunk.get("idArtifact")
        if source_id is not None:
            chunks_by_artifact.setdefault(int(source_id), []).append(chunk)

    artifacts_by_source_id: dict[int, dict] = {}
    for artifact in artifacts:
        source_id = artifact.get("idArtifact")
        url = artifact.get("URL")
        actual_type = artifact.get("idArtifactType")
        if source_id is None or not url:
            raise RuntimeError("Snapshot artifacts must have idArtifact and URL")
        if actual_type != artifact_type_id:
            raise RuntimeError(
                "Snapshot contains artifact type "
                f"{actual_type}; expected {artifact_type_id}"
            )
        if hydroshare_only and not _is_hydroshare_artifact(artifact):
            raise RuntimeError(
                "HydroShare snapshot contains an artifact not marked "
                f"artifact_role={HYDROSHARE_ARTIFACT_ROLE!r}: {url}"
            )
        if hydroshare_only and not get_hydroshare_portal_types(artifact):
            raise RuntimeError(
                "HydroShare snapshot artifact has no research-portal type: "
                f"{url}"
            )
        source_id = int(source_id)
        if source_id in source_ids:
            raise RuntimeError(f"Duplicate snapshot idArtifact: {source_id}")
        if url in urls:
            raise RuntimeError(f"Duplicate snapshot URL: {url}")
        source_ids.add(source_id)
        urls.add(url)
        artifacts_by_source_id[source_id] = artifact

    unknown_chunk_artifacts = sorted(set(chunks_by_artifact) - source_ids)
    if unknown_chunk_artifacts:
        raise RuntimeError(
            "Snapshot chunks reference missing artifact IDs: "
            f"{unknown_chunk_artifacts[:10]}"
        )

    fingerprints_by_source_id = _snapshot_fingerprints_with_parent_versions(
        artifacts_by_source_id, chunks_by_artifact
    )
    prepared: list[dict] = []
    current_fingerprints: dict[str, str] = {}
    for source_id, artifact in artifacts_by_source_id.items():
        url = artifact["URL"]
        fingerprint = fingerprints_by_source_id[source_id]
        record = dict(artifact)
        record["_sync_content_fingerprint"] = fingerprint
        prepared.append(record)
        current_fingerprints[url] = fingerprint

    active_scope = ""
    if hydroshare_only:
        active_scope = (
            " AND ("
            "metadata->'hydroshare'->>'artifact_role' = "
            "'hydroshare_resource' "
            "OR metadata->'hydroshare'->>'resource_id' IS NOT NULL "
            # psycopg2 uses percent-style parameter binding, so literal SQL
            # wildcards must be doubled whenever the query also has params.
            "OR url ILIKE '%%hydroshare.org/resource/%%'"
            ")"
        )
    active_rows = db.execute_query(
        "SELECT url, metadata FROM tblartifacts "
        "WHERE idartifacttype = %s AND isactive = TRUE"
        f"{active_scope};",
        (artifact_type_id,),
        fetch=True,
    ) or []
    active_fingerprints = {
        row["url"]: (
            ((row.get("metadata") or {}).get("sync") or {}).get(
                "content_fingerprint"
            )
        )
        for row in active_rows
    }

    upserts = [
        artifact
        for artifact in prepared
        if active_fingerprints.get(artifact["URL"])
        != artifact["_sync_content_fingerprint"]
    ]
    deletes = [
        {"URL": url}
        for url in sorted(set(active_fingerprints) - set(current_fingerprints))
    ]
    active_count = len(active_fingerprints)
    removed_count = len(deletes)
    if (
        hydroshare_only
        and not allow_large_hydroshare_removals
        and removed_count >= 5
        and removed_count * 4 >= active_count
    ):
        removal_percentage = (removed_count / active_count) * 100
        raise RuntimeError(
            "HydroShare snapshot would deactivate "
            f"{removed_count} of {active_count} active HydroShare resources "
            f"({removal_percentage:.1f}%); refusing a large removal without "
            "--allow-large-hydroshare-removals"
        )
    stats = {
        "snapshot_artifacts": len(prepared),
        "unchanged_artifacts": len(prepared) - len(upserts),
        "missing_or_changed_artifacts": len(upserts),
        "removed_artifacts": len(deletes),
    }
    if hydroshare_only:
        stats["scope"] = "hydroshare"
        stats["large_removals_allowed"] = bool(
            allow_large_hydroshare_removals
        )
    return upserts, deletes, stats


def validate_version_history_schema(db):
    """Require URL uniqueness that permits inactive historical versions."""
    rows = db.execute_query(
        "SELECT idx.relname AS indexname, "
        "pg_get_indexdef(ind.indexrelid) AS indexdef, "
        "ind.indpred IS NOT NULL AS is_partial "
        "FROM pg_index ind "
        "JOIN pg_class idx ON idx.oid = ind.indexrelid "
        "JOIN pg_attribute attr ON attr.attrelid = ind.indrelid "
        "  AND attr.attnum = ANY(ind.indkey) "
        "WHERE ind.indrelid = 'tblartifacts'::regclass "
        "AND ind.indisunique = TRUE "
        "AND ind.indnkeyatts = 1 "
        "AND attr.attname = 'url';",
        fetch=True,
    ) or []
    global_indexes = [row for row in rows if not row.get("is_partial")]
    active_only_indexes = [
        row
        for row in rows
        if row.get("is_partial")
        and "isactive" in str(row.get("indexdef") or "").lower()
    ]
    if global_indexes:
        names = [row.get("indexname") for row in global_indexes]
        raise RuntimeError(
            "tblartifacts has global URL uniqueness, which prevents keeping "
            f"inactive versions: {names}. Use a unique active-URL partial index."
        )
    if not active_only_indexes:
        raise RuntimeError(
            "tblartifacts must have a unique URL index restricted to active rows"
        )


# ─── Phase 1: Deactivate existing artifacts by URL ───────────────

def deactivate_artifacts_by_urls(
    db, urls: list[str], artifact_type_id: int | None = None
):
    """
    Soft-delete: set isActive=FALSE on currently active artifacts whose
    URLs match.
    Artifact rows and existing chunks are preserved for historical record.
    The event time is recorded in metadata.sync.deactivated_at because the
    Azure-aligned table does not have a dedicated deactivated_at column.
    """
    if not urls:
        return 0
    urls = sorted(set(urls))
    type_clause = "" if artifact_type_id is None else " AND idartifacttype = %s"
    params = (urls,) if artifact_type_id is None else (urls, artifact_type_id)
    rows = db.execute_query(
        "UPDATE tblartifacts SET "
        "isactive = FALSE, "
        "metadata = COALESCE(metadata, '{}'::jsonb) || "
        "jsonb_build_object('sync', "
        "COALESCE(metadata->'sync', '{}'::jsonb) || "
        "jsonb_build_object('deactivated_at', to_jsonb(CURRENT_TIMESTAMP))) "
        "WHERE url = ANY(%s) AND isactive = TRUE"
        f"{type_clause} RETURNING idartifact;",
        params,
        fetch=True,
    ) or []
    return len(rows)


def deactivate_artifacts_by_type(db, artifact_type_id: int):
    """
    Soft-delete all currently active artifacts for one artifact type.
    Existing artifact rows and chunks are preserved.
    """
    rows = db.execute_query(
        "UPDATE tblartifacts SET "
        "isactive = FALSE, "
        "metadata = COALESCE(metadata, '{}'::jsonb) || "
        "jsonb_build_object('sync', "
        "COALESCE(metadata->'sync', '{}'::jsonb) || "
        "jsonb_build_object('deactivated_at', to_jsonb(CURRENT_TIMESTAMP))) "
        "WHERE idartifacttype = %s AND isactive = TRUE "
        "RETURNING idartifact;",
        (artifact_type_id,),
        fetch=True,
    ) or []
    return len(rows)


# ─── Phase 2: Insert artifacts ────────────────────────────────────

def resolve_artifact_type_id(db, type_name: str) -> int:
    rows = db.execute_query(
        "SELECT idartifacttype FROM tblartifacttypes "
        "WHERE typename = %s;",
        (type_name,), fetch=True
    )
    if not rows:
        raise RuntimeError(
            f"Artifact type '{type_name}' not in tblartifacttypes"
        )
    return rows[0]["idartifacttype"]


def resolve_artifact_type_map(db) -> dict[int, str]:
    rows = db.execute_query(
        "SELECT idartifacttype, typename FROM tblartifacttypes;",
        fetch=True
    ) or []
    return {r["idartifacttype"]: r["typename"] for r in rows}


def parse_date(s):
    if not s:
        return None
    value = str(s).strip()
    try:
        return datetime.strptime(value, "%m/%d/%Y")
    except ValueError:
        try:
            return datetime.fromisoformat(value.replace("Z", "+00:00"))
        except ValueError:
            return None


def build_metadata(rec: dict) -> dict:
    existing = rec.get("metadata")
    metadata = dict(existing) if isinstance(existing, dict) else {}
    if _is_hydroshare_artifact(rec):
        hydroshare_fields = (
            "artifact_role",
            "resource_id",
            "resource_type",
            "abstract",
            "keywords",
            "document_type",
            "identifier",
            "language",
            "doi",
            "date_created",
            "date_last_updated",
            "published",
            "immutable",
            "public",
            "discoverable",
            "shareable",
            "authors",
            "creators",
            "coverages",
        )
        hydroshare_metadata = dict(metadata.get("hydroshare") or {})
        hydroshare_metadata.update({
            key: rec.get(key)
            for key in hydroshare_fields
            if rec.get(key) is not None
        })
        hydroshare_metadata["artifact_role"] = HYDROSHARE_ARTIFACT_ROLE
        hydroshare_metadata["hs_research_portal_types"] = (
            get_hydroshare_portal_types(rec)
        )
        metadata["hydroshare"] = hydroshare_metadata

        source_version = rec.get("date_last_updated")
        if source_version:
            sync_metadata = dict(metadata.get("sync") or {})
            sync_metadata["source_version"] = source_version
            metadata["sync"] = sync_metadata
    elif (
        rec.get("idArtifactType") == 4
        or rec.get("artifact_role") == "repository"
    ):
        repository_fields = (
            "description",
            "topics",
            "default_branch",
            "frozen_commit_sha",
            "language",
            "created_at",
            "updated_at",
            "pushed_at",
            "contributors_summary",
            "full_name",
            "artifact_role",
            "selected_files_summary",
        )
        metadata["github_repository"] = {
            key: rec.get(key)
            for key in repository_fields
            if rec.get(key) is not None
        }
        sync_metadata = dict(metadata.get("sync") or {})
        fingerprint = rec.get("_sync_content_fingerprint")
        if fingerprint:
            sync_metadata["content_fingerprint"] = fingerprint
        if rec.get("frozen_commit_sha"):
            sync_metadata["source_version"] = rec["frozen_commit_sha"]
        if sync_metadata:
            metadata["sync"] = sync_metadata
    else:
        metadata["docuhub"] = {
            "source_id": rec.get("idArtifact"),
            "parent_source_id": rec.get("idArtifactParent"),
            "description": rec.get("description", "") or "",
            "tags": rec.get("tags", []) or [],
            "source_last_updated": (
                rec.get("Last updated date", "") or ""
            ),
        }

    sync_metadata = dict(metadata.get("sync") or {})
    fingerprint = rec.get("_sync_content_fingerprint")
    if fingerprint:
        sync_metadata["content_fingerprint"] = fingerprint
    if sync_metadata:
        metadata["sync"] = sync_metadata
    return metadata


def insert_artifacts(db, artifacts: list[dict]):
    """
    Insert artifacts in two passes:
    1) All with idArtifactParent=NULL
    2) UPDATE parent relationships using source IDs -> DB IDs
    """
    type_map = resolve_artifact_type_map(db)

    type_name_to_id = {}
    for tid, tname in type_map.items():
        type_name_to_id[tname] = tid

    INSERT_Q = """
    INSERT INTO tblartifacts
      (idartifacttype, title, url, idartifactparent,
       summary_data, metadata, last_updated)
    VALUES %s;
    """

    rows = []
    for rec in artifacts:
        url = rec.get("URL")
        if not url:
            print(f"  SKIP: artifact with no URL (source id={rec.get('idArtifact')})")
            continue

        art_type_id = rec.get("idArtifactType")
        if art_type_id not in type_map:
            raise RuntimeError(
                f"Unknown idArtifactType={art_type_id} for {url}"
            )

        title = rec.get("Title", "")
        summary = rec.get("summary_data")
        md = build_metadata(rec)
        dt = parse_date(
            rec.get("date_last_updated")
            or rec.get("Last updated date")
            or rec.get("pushed_at")
            or rec.get("updated_at")
        )

        rows.append((
            art_type_id, title, url, None,
            Json(summary) if summary is not None else None,
            Json(md), dt
        ))

    if rows:
        db.execute_batch(INSERT_Q, rows, page_size=500)
    print(f"  Inserted {len(rows)} artifacts.")

    # Build URL -> DB idArtifact mapping (only active artifacts)
    urls = [r.get("URL") for r in artifacts if r.get("URL")]
    db_rows = db.execute_query(
        "SELECT idartifact, url FROM tblartifacts "
        "WHERE url = ANY(%s) AND isactive = TRUE;",
        (urls,), fetch=True
    ) or []
    url_to_db_id = {r["url"]: r["idartifact"] for r in db_rows}

    # Build source_id -> URL mapping
    source_to_url = {}
    for rec in artifacts:
        sid = rec.get("idArtifact")
        url = rec.get("URL")
        if sid is not None and url:
            source_to_url[sid] = url

    # Update parent relationships
    UPDATE_PARENT_Q = """
    UPDATE tblartifacts AS t
    SET idartifactparent = v.parent_id::int
    FROM (VALUES %s) AS v(parent_id, url)
    WHERE t.url = v.url
      AND t.isactive = TRUE;
    """
    parent_updates = []
    for rec in artifacts:
        url = rec.get("URL")
        parent_src = rec.get("idArtifactParent")
        if not url:
            continue
        if parent_src is None:
            parent_db = None
        else:
            parent_url = source_to_url.get(parent_src)
            parent_db = url_to_db_id.get(parent_url) if parent_url else None
            if parent_db is None:
                # Parent might already exist in DB from a previous load
                if parent_url:
                    existing = db.execute_query(
                        "SELECT idartifact FROM tblartifacts "
                        "WHERE url = %s AND isactive = TRUE;",
                        (parent_url,), fetch=True
                    )
                    if existing:
                        parent_db = existing[0]["idartifact"]
        parent_updates.append((parent_db, url))

    if parent_updates:
        db.execute_batch(UPDATE_PARENT_Q, parent_updates, page_size=500)
    print(f"  Updated {len(parent_updates)} parent relationships.")

    return url_to_db_id, source_to_url


def insert_hydroshare_portal_mappings(
    db,
    artifacts: list[dict],
    url_to_db_id: dict[str, int],
) -> int:
    """Attach active HydroShare artifact versions to portal lookup values.

    Inserts are idempotent. Mappings on inactive historical artifact versions
    remain untouched.
    """
    hydroshare_artifacts = [
        artifact
        for artifact in artifacts
        if _is_hydroshare_artifact(artifact)
    ]
    if not hydroshare_artifacts:
        return 0

    wrong_types = [
        artifact.get("URL") or artifact.get("idArtifact")
        for artifact in hydroshare_artifacts
        if artifact.get("idArtifactType") != HYDROSHARE_ARTIFACT_TYPE_ID
    ]
    if wrong_types:
        raise RuntimeError(
            "HydroShare resources must use idArtifactType=3. Sample: "
            f"{wrong_types[:5]}"
        )

    lookup_rows = db.execute_query(
        "SELECT idhsresearchportaltype, hsresearchportaltype "
        "FROM tblhsresearchportaltypes;",
        fetch=True,
    ) or []
    type_ids = {
        row["hsresearchportaltype"]: row["idhsresearchportaltype"]
        for row in lookup_rows
    }

    rows = []
    errors = []
    for artifact in hydroshare_artifacts:
        url = artifact.get("URL")
        db_artifact_id = url_to_db_id.get(url)
        if db_artifact_id is None:
            errors.append(f"no active database artifact for {url!r}")
            continue
        portal_types = get_hydroshare_portal_types(artifact)
        if not portal_types:
            errors.append(f"no HydroShare portal types for {url!r}")
            continue
        for portal_type in portal_types:
            portal_type_id = type_ids.get(portal_type)
            if portal_type_id is None:
                errors.append(
                    f"unknown HydroShare portal type {portal_type!r} "
                    f"for {url!r}"
                )
                continue
            rows.append((db_artifact_id, portal_type_id))

    if errors:
        raise RuntimeError(
            "Cannot insert HydroShare research-portal mappings. Sample: "
            f"{errors[:5]}"
        )

    if rows:
        db.execute_batch(
            "INSERT INTO trlartifactshsresearchportaltypes "
            "(idartifact, idhsresearchportaltype) VALUES %s "
            "ON CONFLICT (idartifact, idhsresearchportaltype) DO NOTHING;",
            sorted(set(rows)),
            page_size=500,
        )
    print(f"  Ensured {len(set(rows))} HydroShare portal mappings.")
    return len(set(rows))


def ensure_hydroshare_snapshot_portal_mappings(
    db,
    snapshot_artifacts: list[dict],
) -> int:
    """Ensure mappings for every active HydroShare artifact in a snapshot.

    Snapshot reconciliation may decide that every artifact is unchanged. The
    bridge table still needs to be backfilled when it is new or empty, so IDs
    are resolved from the active database rows instead of only from records
    inserted during this apply.
    """
    hydroshare_artifacts = [
        artifact
        for artifact in snapshot_artifacts
        if _is_hydroshare_artifact(artifact)
    ]
    if not hydroshare_artifacts:
        return 0

    urls = sorted({
        artifact.get("URL")
        for artifact in hydroshare_artifacts
        if artifact.get("URL")
    })
    active_rows = db.execute_query(
        "SELECT idartifact, url FROM tblartifacts "
        "WHERE url = ANY(%s) AND idartifacttype = %s "
        "AND isactive = TRUE;",
        (urls, HYDROSHARE_ARTIFACT_TYPE_ID),
        fetch=True,
    ) or []
    url_to_db_id = {
        row["url"]: row["idartifact"]
        for row in active_rows
    }
    return insert_hydroshare_portal_mappings(
        db,
        hydroshare_artifacts,
        url_to_db_id,
    )


# ─── Phase 3: Insert chunks ──────────────────────────────────────

def resolve_chunk_type_map(db, artifact_type_id: int) -> dict:
    rows = db.execute_query(
        "SELECT idchunktype, typename FROM tblchunktypes "
        "WHERE idartifacttype = %s;",
        (artifact_type_id,), fetch=True
    ) or []
    return {r["typename"]: r["idchunktype"] for r in rows}


def ensure_repository_chunk_types(db, artifact_type_id: int):
    """Idempotently register the symbolic chunk types used by type-4 data."""
    if artifact_type_id != 4:
        raise RuntimeError(
            "Repository chunk types may only be registered for artifact type 4"
        )
    db.execute_batch(
        "INSERT INTO tblchunktypes (idartifacttype, typename) VALUES %s "
        "ON CONFLICT (idartifacttype, typename) DO NOTHING;",
        [(artifact_type_id, name) for name in REPOSITORY_CHUNK_TYPES],
        page_size=len(REPOSITORY_CHUNK_TYPES),
    )


def ensure_hydroshare_chunk_types(db):
    """Idempotently register symbolic chunk types used by HydroShare data."""
    db.execute_batch(
        "INSERT INTO tblchunktypes (idartifacttype, typename) VALUES %s "
        "ON CONFLICT (idartifacttype, typename) DO NOTHING;",
        [
            (HYDROSHARE_ARTIFACT_TYPE_ID, name)
            for name in HYDROSHARE_CHUNK_TYPES
        ],
        page_size=len(HYDROSHARE_CHUNK_TYPES),
    )


def sanitize_text(x) -> str:
    if x is None:
        return ""
    return str(x).replace("\x00", "")


def insert_chunks(
    db, chunks: list[dict],
    source_to_url: dict, url_to_db_id: dict,
    artifact_type_id: int
):
    """
    Insert chunks with proper FK resolution.
    Handles parent-child chunk relationships in a second pass.
    """
    # Map file chunk type IDs to DB chunk type IDs
    chunk_type_map = resolve_chunk_type_map(db, artifact_type_id)
    filetype_to_dbtype = {}
    for file_id, name in FILE_CHUNKTYPE_TO_NAME.items():
        db_id = chunk_type_map.get(name)
        filetype_to_dbtype[file_id] = db_id

    INSERT_Q = """
    INSERT INTO tblchunks
      (idartifact, idchunktype, idchunkparent, "order",
       chunk_text, embedding, metadata)
    VALUES %s;
    """

    rows_to_insert = []
    parent_edges = []
    errors = []

    # Build per-artifact mapping: source idChunk -> order
    src_chunk_to_order = {}
    for ch in chunks:
        sid = ch.get("idArtifact")
        cid = ch.get("idChunk")
        order = ch.get("order")
        if sid is not None and cid is not None and order is not None:
            src_chunk_to_order[(sid, cid)] = order

    for ch in chunks:
        src_art_id = ch.get("idArtifact")
        if src_art_id is None:
            errors.append({"chunk": ch.get("idChunk"), "error": "no idArtifact"})
            continue

        art_url = source_to_url.get(src_art_id)
        db_art_id = url_to_db_id.get(art_url) if art_url else None

        if db_art_id is None:
            # Try looking it up in DB directly (active only)
            if art_url:
                existing = db.execute_query(
                    "SELECT idartifact FROM tblartifacts "
                    "WHERE url = %s AND isactive = TRUE;",
                    (art_url,), fetch=True
                )
                if existing:
                    db_art_id = existing[0]["idartifact"]
                    url_to_db_id[art_url] = db_art_id

        if db_art_id is None:
            errors.append({
                "idArtifact": src_art_id,
                "idChunk": ch.get("idChunk"),
                "error": "no matching artifact in DB"
            })
            continue

        chunk_type_name = ch.get("chunk_type_name")
        file_chunk_type = ch.get("idChunkType")
        db_chunk_type = (
            chunk_type_map.get(chunk_type_name)
            if chunk_type_name
            else filetype_to_dbtype.get(file_chunk_type)
        )
        if db_chunk_type is None:
            errors.append({
                "idChunk": ch.get("idChunk"),
                "error": (
                    f"unmapped chunk type name={chunk_type_name!r}, "
                    f"idChunkType={file_chunk_type!r}"
                )
            })
            continue

        order_val = ch.get("order")
        chunk_text = sanitize_text(ch.get("chunk_text", ""))
        title = sanitize_text(ch.get("title", ""))

        md = {
            "section_hint": sanitize_text(ch.get("section_hint") or title),
            "supporting_quote": ch.get("supporting_quote") or [],
            "type_specific": ch.get("type_specific") or {},
            "chunk_type_name": chunk_type_name,
            "source_artifact_id": ch.get("source_artifact_id", src_art_id),
            "source_chunk_id": ch.get("idChunk"),
        }

        rows_to_insert.append((
            db_art_id, db_chunk_type, None, order_val,
            chunk_text, None, Json(md)
        ))

        parent_src = ch.get("idChunkParent")
        if parent_src is not None:
            child_order = order_val
            parent_order = src_chunk_to_order.get(
                (src_art_id, parent_src)
            )
            if parent_order is not None:
                parent_edges.append(
                    (db_art_id, child_order, parent_order)
                )

    if errors:
        raise RuntimeError(
            f"Cannot insert {len(errors)} chunks because references or chunk "
            f"types could not be resolved. Sample: {errors[:5]}"
        )

    if rows_to_insert:
        db.execute_batch(INSERT_Q, rows_to_insert, page_size=5000)
    print(f"  Inserted {len(rows_to_insert)} chunks.")

    # Resolve chunk parent relationships
    if parent_edges:
        affected_artifacts = sorted({a for a, _, _ in parent_edges})
        rows = db.execute_query(
            'SELECT idchunk, idartifact, "order" '
            "FROM tblchunks WHERE idartifact = ANY(%s::int[]);",
            (affected_artifacts,), fetch=True
        ) or []
        key_to_id = {
            (r["idartifact"], r["order"]): r["idchunk"]
            for r in rows
        }

        UPDATE_PARENT_Q = """
        UPDATE tblchunks AS t
        SET idchunkparent = v.idchunkparent
        FROM (VALUES %s) AS v(idchunk, idchunkparent)
        WHERE t.idchunk = v.idchunk;
        """
        updates = []
        for db_art_id, child_order, parent_order in parent_edges:
            child_id = key_to_id.get((db_art_id, child_order))
            parent_id = key_to_id.get((db_art_id, parent_order))
            if child_id and parent_id:
                updates.append((child_id, parent_id))

        if updates:
            db.execute_batch(UPDATE_PARENT_Q, updates, page_size=5000)
        print(f"  Resolved {len(updates)} chunk parent relationships.")

    return len(rows_to_insert)


# ─── Phase 4: Embeddings ─────────────────────────────────────────

def get_embedding(text: str):
    global client
    if not text or not text.strip():
        return None
    if client is None:
        from openai import OpenAI
        client = OpenAI()
    embedding_usage.record_request()
    try:
        resp = client.embeddings.create(
            model=EMBEDDING_MODEL,
            input=text.strip(),
            encoding_format="float",
            dimensions=DIMENSIONS,
        )
        embedding_usage.add_response(resp)
        return resp.data[0].embedding
    except Exception as e:
        embedding_usage.record_error()
        print(f"  Embedding error: {e}")
        return None


def embed_artifacts(db, urls: list[str]):
    """Generate embeddings for artifacts that have summary_data but no embedding."""
    if not urls:
        return

    SELECT_Q = """
    SELECT
      idartifact,
      title || E':\\n\\n'
      || COALESCE(summary_data->>'summary_text', '')
      || E'\\n\\nKeywords: '
      || COALESCE((
          SELECT string_agg(k, ', ')
          FROM jsonb_array_elements_text(summary_data->'keywords') AS k
      ), '') AS text_for_embedding
    FROM tblartifacts
    WHERE url = ANY(%s)
      AND isactive = TRUE
      AND summary_data IS NOT NULL
      AND embedding IS NULL
    ORDER BY idartifact;
    """
    rows = db.execute_query(SELECT_Q, (urls,), fetch=True) or []

    if not rows:
        print("  No artifacts need embedding.")
        return

    print(f"  Embedding {len(rows)} artifacts...")
    UPDATE_Q = """
    UPDATE tblartifacts AS t
    SET embedding = v.embedding::vector
    FROM (VALUES %s) AS v(embedding, idartifact)
    WHERE t.idartifact = v.idartifact;
    """

    updates = []
    failed = 0
    t0 = time.perf_counter()

    for i, r in enumerate(rows, 1):
        emb = get_embedding(r["text_for_embedding"])
        if emb is None:
            failed += 1
            continue
        updates.append((json.dumps(emb), r["idartifact"]))

        if len(updates) >= FLUSH_EVERY:
            db.execute_batch(UPDATE_Q, updates, page_size=PAGE_SIZE)
            updates.clear()

        if i % 25 == 0:
            elapsed = time.perf_counter() - t0
            print(f"    {i}/{len(rows)} ({elapsed:.1f}s)")

    if updates:
        db.execute_batch(UPDATE_Q, updates, page_size=PAGE_SIZE)

    elapsed = time.perf_counter() - t0
    print(f"  Artifact embeddings done: {len(rows) - failed} OK, "
          f"{failed} failed ({elapsed:.1f}s)")
    if failed:
        raise RuntimeError(
            f"Artifact embedding generation failed for {failed} rows"
        )


def embed_chunks(db, db_artifact_ids: list[int]):
    """Generate embeddings for chunks belonging to the given artifacts."""
    if not db_artifact_ids:
        return

    SELECT_Q = """
    SELECT
      c.idchunk,
      c.chunk_text AS text_for_embedding,
      ct.typename AS chunk_type,
      COALESCE(c.metadata->>'section_hint', '') AS section_hint
    FROM tblchunks c
    JOIN tblchunktypes ct ON ct.idchunktype = c.idchunktype
    WHERE c.idartifact = ANY(%s::int[])
      AND c.chunk_text IS NOT NULL
      AND btrim(c.chunk_text) <> ''
      AND c.embedding IS NULL
    ORDER BY c.idchunk;
    """
    rows = db.execute_query(
        SELECT_Q, (db_artifact_ids,), fetch=True
    ) or []

    if not rows:
        print("  No chunks need embedding.")
        return

    print(f"  Embedding {len(rows)} chunks...")
    UPDATE_Q = """
    UPDATE tblchunks AS t
    SET embedding = v.embedding::vector
    FROM (VALUES %s) AS v(embedding, idchunk)
    WHERE t.idchunk = v.idchunk;
    """

    updates = []
    failed = 0
    t0 = time.perf_counter()

    for i, r in enumerate(rows, 1):
        text = r["text_for_embedding"]
        prefix_parts = []
        if r.get("chunk_type"):
            prefix_parts.append(f"Chunk type: {r['chunk_type']}")
        if r.get("section_hint"):
            prefix_parts.append(f"Section: {r['section_hint']}")
        if prefix_parts:
            text = "\n".join(prefix_parts) + "\n\n" + text

        emb = get_embedding(text)
        if emb is None:
            failed += 1
            continue
        updates.append((json.dumps(emb), r["idchunk"]))

        if len(updates) >= FLUSH_EVERY:
            db.execute_batch(UPDATE_Q, updates, page_size=PAGE_SIZE)
            updates.clear()

        if i % 50 == 0:
            elapsed = time.perf_counter() - t0
            print(f"    {i}/{len(rows)} ({elapsed:.1f}s)")

    if updates:
        db.execute_batch(UPDATE_Q, updates, page_size=PAGE_SIZE)

    elapsed = time.perf_counter() - t0
    print(f"  Chunk embeddings done: {len(rows) - failed} OK, "
          f"{failed} failed ({elapsed:.1f}s)")
    if failed:
        raise RuntimeError(
            f"Chunk embedding generation failed for {failed} rows"
        )


# ─── Main ─────────────────────────────────────────────────────────

def main():
    global embedding_usage, result_output_path
    embedding_usage = UsageAccumulator("embeddings", EMBEDDING_MODEL)

    parser = argparse.ArgumentParser(
        description="Process artifact/chunk deltas into the local DB."
    )
    parser.add_argument(
        "--test", action="store_true",
        help="Use *_update.json files instead of *_delta.json"
    )
    parser.add_argument("--artifacts", type=str, help="Path to artifacts JSON")
    parser.add_argument("--chunks", type=str, help="Path to chunks JSON")
    parser.add_argument(
        "--skip-embeddings", action="store_true",
        help="Skip embedding generation"
    )
    parser.add_argument(
        "--deactivate-active-artifact-type",
        type=int,
        help=(
            "Before URL-specific deactivation, set all active artifacts for "
            "this idArtifactType to inactive. Use 1 for a full DocuHub refresh."
        ),
    )
    parser.add_argument(
        "--expected-artifact-type",
        type=int,
        help="Refuse input upserts containing any other idArtifactType.",
    )
    parser.add_argument(
        "--reconcile-snapshot-artifact-type",
        type=int,
        help=(
            "Treat the explicit files as a full snapshot for this artifact "
            "type and update only missing, changed, or removed rows."
        ),
    )
    parser.add_argument(
        "--reconcile-hydroshare-snapshot",
        action="store_true",
        help=(
            "Treat the explicit files as the complete HydroShare snapshot. "
            "Only active type-3 HydroShare resources are reconciled; other "
            "type-3 datasets remain untouched."
        ),
    )
    parser.add_argument(
        "--allow-large-hydroshare-removals",
        action="store_true",
        help=(
            "Allow a HydroShare snapshot to remove at least five and at "
            "least 25%% of active scoped resources. Valid only with "
            "--reconcile-hydroshare-snapshot."
        ),
    )
    parser.add_argument(
        "--ensure-repository-chunk-types",
        action="store_true",
        help="Idempotently register the type-4 symbolic chunk type names.",
    )
    parser.add_argument(
        "--require-summaries",
        action="store_true",
        help="Refuse the update if any input artifact has null summary_data.",
    )
    parser.add_argument(
        "--result-file",
        default="db_update_result.json",
        help="Result JSON filename, or an absolute output path.",
    )
    args = parser.parse_args()

    result_output_path = Path(args.result_file)
    if not result_output_path.is_absolute():
        result_output_path = DELTA_DIR / result_output_path
    result_output_path.parent.mkdir(parents=True, exist_ok=True)

    # Resolve file paths
    if args.artifacts and args.chunks:
        artifacts_path = Path(args.artifacts)
        chunks_path = Path(args.chunks)
        is_delta = False
    elif args.test:
        artifacts_path = DELTA_DIR / "artifacts_update.json"
        chunks_path = DELTA_DIR / "content_chunks_update.json"
        is_delta = False
    else:
        artifacts_path = DELTA_DIR / "artifacts_delta.json"
        chunks_path = DELTA_DIR / "content_chunks_delta.json"
        is_delta = True

    if args.reconcile_snapshot_artifact_type is not None and is_delta:
        raise RuntimeError("Snapshot reconciliation requires explicit full files")
    if (
        args.allow_large_hydroshare_removals
        and not args.reconcile_hydroshare_snapshot
    ):
        raise RuntimeError(
            "--allow-large-hydroshare-removals is valid only with "
            "--reconcile-hydroshare-snapshot"
        )
    if args.reconcile_hydroshare_snapshot:
        if not (args.artifacts and args.chunks):
            raise RuntimeError(
                "HydroShare snapshot reconciliation requires explicit "
                "--artifacts and --chunks files"
            )
        if args.reconcile_snapshot_artifact_type is not None:
            raise RuntimeError(
                "Use either --reconcile-hydroshare-snapshot or "
                "--reconcile-snapshot-artifact-type, not both"
            )
        if args.deactivate_active_artifact_type is not None:
            raise RuntimeError(
                "--deactivate-active-artifact-type is unsafe with a "
                "HydroShare-scoped snapshot"
            )
        if (
            args.expected_artifact_type is not None
            and args.expected_artifact_type != HYDROSHARE_ARTIFACT_TYPE_ID
        ):
            raise RuntimeError(
                "HydroShare snapshot reconciliation requires artifact type 3"
            )
    if (
        args.expected_artifact_type is not None
        and args.reconcile_snapshot_artifact_type is not None
        and args.expected_artifact_type != args.reconcile_snapshot_artifact_type
    ):
        raise RuntimeError(
            "Expected and reconciled artifact type IDs must be the same"
        )

    print("=" * 60)
    print("CIROH Delta Processor")
    print("=" * 60)
    print(f"Artifacts file: {artifacts_path}")
    print(f"Chunks file:    {chunks_path}")
    print(f"Mode:           {'delta' if is_delta else 'full update'}")
    print()

    # Load data
    if is_delta:
        artifacts_to_upsert, artifacts_to_delete = load_delta_artifacts(
            artifacts_path
        )
    else:
        artifacts_to_upsert, artifacts_to_delete = load_update_artifacts(
            artifacts_path
        )

    chunks = load_chunks(chunks_path)
    hydroshare_snapshot_artifacts = (
        list(artifacts_to_upsert)
        if args.reconcile_hydroshare_snapshot
        else []
    )

    expected_type = (
        HYDROSHARE_ARTIFACT_TYPE_ID
        if args.reconcile_hydroshare_snapshot
        else args.expected_artifact_type
    )
    if expected_type is not None:
        wrong_types = sorted({
            artifact.get("idArtifactType")
            for artifact in artifacts_to_upsert
            if artifact.get("idArtifactType") != expected_type
        }, key=lambda value: str(value))
        if wrong_types:
            raise RuntimeError(
                f"Input contains artifact types {wrong_types}; expected only "
                f"{expected_type}"
            )
    if args.require_summaries:
        missing_summaries = [
            artifact.get("URL") or artifact.get("idArtifact")
            for artifact in artifacts_to_upsert
            if artifact.get("summary_data") is None
        ]
        if missing_summaries:
            raise RuntimeError(
                "Refusing database update: artifacts have pending summaries. "
                f"Sample: {missing_summaries[:5]}"
            )

    t_total = time.perf_counter()
    reconciliation = None
    chunks_inserted = 0
    portal_mappings_inserted = 0

    with db_manager as db:
        validate_version_history_schema(db)
        if args.reconcile_snapshot_artifact_type is not None:
            (
                artifacts_to_upsert,
                artifacts_to_delete,
                reconciliation,
            ) = reconcile_artifact_snapshot(
                db,
                artifacts_to_upsert,
                chunks,
                args.reconcile_snapshot_artifact_type,
            )
        elif args.reconcile_hydroshare_snapshot:
            (
                artifacts_to_upsert,
                artifacts_to_delete,
                reconciliation,
            ) = reconcile_artifact_snapshot(
                db,
                artifacts_to_upsert,
                chunks,
                HYDROSHARE_ARTIFACT_TYPE_ID,
                hydroshare_only=True,
                allow_large_hydroshare_removals=(
                    args.allow_large_hydroshare_removals
                ),
            )

        upsert_source_ids = {
            r.get("idArtifact") for r in artifacts_to_upsert
            if r.get("idArtifact") is not None
        }
        relevant_chunks = [
            ch for ch in chunks
            if ch.get("idArtifact") in upsert_source_ids
        ]

        print(f"Artifacts to upsert:  {len(artifacts_to_upsert)}")
        print(f"Artifacts to delete:  {len(artifacts_to_delete)}")
        print(f"Relevant chunks:      {len(relevant_chunks)}")
        if reconciliation:
            print(f"Snapshot reconciliation: {reconciliation}")
        print()

        if args.ensure_repository_chunk_types:
            ensure_repository_chunk_types(
                db, args.reconcile_snapshot_artifact_type or expected_type or 4
            )
        if args.reconcile_hydroshare_snapshot or any(
            _is_hydroshare_artifact(artifact)
            for artifact in artifacts_to_upsert
        ):
            ensure_hydroshare_chunk_types(db)

        # PHASE 1: Deactivate
        print("=" * 60)
        print("PHASE 1: Deactivate existing artifacts")
        print("=" * 60)

        deactivated = 0
        if args.deactivate_active_artifact_type is not None:
            deactivated += deactivate_artifacts_by_type(
                db, args.deactivate_active_artifact_type
            )

        # Collect URLs to deactivate (from explicit deletes + upserts)
        urls_to_deactivate = []
        for rec in artifacts_to_delete:
            url = rec.get("URL") or rec.get("url")
            if url:
                urls_to_deactivate.append(url)
        for rec in artifacts_to_upsert:
            url = rec.get("URL")
            if url:
                urls_to_deactivate.append(url)

        deactivation_scope = (
            args.reconcile_snapshot_artifact_type or expected_type
        )
        deactivated += deactivate_artifacts_by_urls(
            db, urls_to_deactivate, deactivation_scope
        )
        print(f"  Deactivated {deactivated} artifacts (chunks preserved).")
        print()

        if not artifacts_to_upsert:
            print("No artifacts to insert; unchanged rows were left untouched.")
            if args.reconcile_hydroshare_snapshot:
                portal_mappings_inserted = (
                    ensure_hydroshare_snapshot_portal_mappings(
                        db,
                        hydroshare_snapshot_artifacts,
                    )
                )
            print()
        else:
            # PHASE 2: Insert artifacts
            print("=" * 60)
            print("PHASE 2: Insert artifacts")
            print("=" * 60)

            url_to_db_id, source_to_url = insert_artifacts(
                db, artifacts_to_upsert
            )
            if args.reconcile_hydroshare_snapshot:
                portal_mappings_inserted = (
                    ensure_hydroshare_snapshot_portal_mappings(
                        db,
                        hydroshare_snapshot_artifacts,
                    )
                )
            else:
                portal_mappings_inserted = insert_hydroshare_portal_mappings(
                    db, artifacts_to_upsert, url_to_db_id
                )
            print()

            # PHASE 3: Insert chunks
            print("=" * 60)
            print("PHASE 3: Insert chunks")
            print("=" * 60)

            art_type_ids = {
                r.get("idArtifactType") for r in artifacts_to_upsert
                if r.get("idArtifactType") is not None
            }
            for at_id in sorted(art_type_ids):
                type_source_ids = {
                    r.get("idArtifact") for r in artifacts_to_upsert
                    if r.get("idArtifactType") == at_id
                }
                type_chunks = [
                    ch for ch in relevant_chunks
                    if ch.get("idArtifact") in type_source_ids
                ]
                if type_chunks:
                    print(f"  Processing chunks for artifact type {at_id}...")
                    chunks_inserted += insert_chunks(
                        db, type_chunks,
                        source_to_url, url_to_db_id, at_id
                    )
            print()

            # PHASE 4: Embeddings
            if args.skip_embeddings:
                print("Skipping embeddings (--skip-embeddings).")
            else:
                print("=" * 60)
                print("PHASE 4: Generate embeddings")
                print("=" * 60)

                upsert_urls = [
                    r.get("URL") for r in artifacts_to_upsert
                    if r.get("URL")
                ]
                embed_artifacts(db, upsert_urls)

                db_art_ids = [
                    url_to_db_id[u] for u in upsert_urls
                    if u in url_to_db_id
                ]
                embed_chunks(db, db_art_ids)

        elapsed = time.perf_counter() - t_total
        print()
        print("=" * 60)
        print(f"DONE. Total elapsed: {elapsed:.1f}s")
        print("=" * 60)

        # Write before commit so a report-write failure also rolls back the DB.
        result = {
            "status": "completed",
            "upserted_artifacts": len(artifacts_to_upsert),
            "deactivated_artifacts": deactivated,
            "chunks_inserted": chunks_inserted,
            "hydroshare_portal_mappings_inserted": (
                portal_mappings_inserted
            ),
            "elapsed_seconds": round(elapsed, 1),
            "openai_usage": embedding_usage.report(),
        }
        if reconciliation is not None:
            result["reconciliation"] = reconciliation
        with open(result_output_path, "w", encoding="utf-8") as f:
            json.dump(result, f, indent=2)


if __name__ == "__main__":
    try:
        main()
    except Exception as exc:
        # Preserve any usage already returned by the API even if a later DB or
        # parsing operation fails. The synchronization runner can then include
        # partial spend in its failed-run report.
        failure_result = {
            "status": "failed",
            "error": str(exc),
            "upserted_artifacts": 0,
            "deactivated_artifacts": 0,
            "chunks_inserted": 0,
            "hydroshare_portal_mappings_inserted": 0,
            "elapsed_seconds": 0,
            "openai_usage": embedding_usage.report(),
        }
        result_output_path.parent.mkdir(parents=True, exist_ok=True)
        with open(result_output_path, "w", encoding="utf-8") as f:
            json.dump(failure_result, f, indent=2)
        raise
