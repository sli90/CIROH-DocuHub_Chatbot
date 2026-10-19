"""Reuse embeddings from an already-synchronized PostgreSQL database.

This utility is intended for the second phase of a prepared synchronization:

1. Apply a validated bundle to the target with ``--skip-embeddings``.
2. Run this utility to copy the matching vectors from a trusted local DB.

The command is a dry-run unless ``--execute`` is supplied.  It never matches
rows by database-generated IDs: artifacts are matched by artifact type + URL,
and chunks by artifact URL + ``metadata.source_chunk_id``.  Chunk order, type,
and text must also agree before a vector can be copied.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Iterable, Mapping

import psycopg2
from dotenv import dotenv_values
from psycopg2 import sql
from psycopg2.extras import RealDictCursor, execute_values

from prepared_sync import resolve_prepared_bundle, validate_prepared_bundle
from sync_accounting import new_sync_id, utc_now_iso


ROOT = Path(__file__).resolve().parent
VECTOR_DIMENSIONS = 1792
ADVISORY_LOCK_NAME = "ciroh_prepared_sync_embedding_reuse_v1"
HUB_CHUNK_TYPES = {1: "Section", 2: "Subsection", 3: "Subsubsection"}


class EmbeddingReuseError(RuntimeError):
    """Raised when a source/target row cannot be proven to match the bundle."""


@dataclass(frozen=True)
class DatabaseConfig:
    host: str
    database: str
    user: str
    password: str = field(repr=False)
    schema: str = "CIROH_AIBot"
    port: int = 5432
    sslmode: str | None = None
    connect_timeout: int = 15

    @property
    def identity(self) -> tuple[str, int, str, str]:
        return (
            self.host.casefold(),
            self.port,
            self.database.casefold(),
            self.schema,
        )

    def connection_kwargs(self, application_name: str) -> dict[str, Any]:
        kwargs: dict[str, Any] = {
            "host": self.host,
            "port": self.port,
            "database": self.database,
            "user": self.user,
            "password": self.password,
            "connect_timeout": self.connect_timeout,
            "application_name": application_name,
        }
        if self.sslmode:
            kwargs["sslmode"] = self.sslmode
        return kwargs


ArtifactKey = tuple[int, str]
ChunkKey = tuple[int, str, int]


@dataclass(frozen=True)
class SnapshotArtifact:
    artifact_type: int
    source_id: int
    url: str
    source_name: str
    title: Any = None
    summary_data: Any = None

    @property
    def key(self) -> ArtifactKey:
        return (self.artifact_type, self.url)


@dataclass(frozen=True)
class SnapshotChunk:
    artifact_key: ArtifactKey
    source_chunk_id: int
    order: int
    chunk_type: str
    section_hint: str
    text: str
    source_name: str

    @property
    def key(self) -> ChunkKey:
        artifact_type, url = self.artifact_key
        return (artifact_type, url, self.source_chunk_id)

    @property
    def has_embedding_input(self) -> bool:
        return bool(self.text.strip())


@dataclass(frozen=True)
class SnapshotInventory:
    artifacts: dict[ArtifactKey, SnapshotArtifact]
    chunks: dict[ChunkKey, SnapshotChunk]
    source_counts: dict[str, dict[str, int]]

    @property
    def artifact_count(self) -> int:
        return len(self.artifacts)

    @property
    def chunk_count(self) -> int:
        return len(self.chunks)

    @property
    def nonempty_chunk_count(self) -> int:
        return sum(chunk.has_embedding_input for chunk in self.chunks.values())

    @property
    def empty_chunk_count(self) -> int:
        return self.chunk_count - self.nonempty_chunk_count


@dataclass(frozen=True)
class DatabaseArtifact:
    database_id: int
    embedding_text: str | None
    embedding_dimensions: int | None


@dataclass(frozen=True)
class DatabaseChunk:
    database_id: int
    embedding_text: str | None
    embedding_dimensions: int | None


@dataclass(frozen=True)
class DatabaseInventory:
    artifacts: dict[ArtifactKey, DatabaseArtifact]
    chunks: dict[ChunkKey, DatabaseChunk]


SOURCE_SPECS = (
    ("docuhub", 1, "docuhub_artifacts", "docuhub_chunks", None),
    (
        "github_repositories",
        4,
        "github_artifacts",
        "github_chunks",
        "include_github_repositories",
    ),
    (
        "hydroshare_resources",
        3,
        "hydroshare_artifacts",
        "hydroshare_chunks",
        "include_hydroshare_resources",
    ),
)


def _write_json_atomic(path: Path, payload: Mapping[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(f".{path.name}.tmp")
    temporary.write_text(
        json.dumps(payload, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    temporary.replace(path)


def _load_json(path: Path) -> Any:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise EmbeddingReuseError(f"Could not read valid JSON from {path}") from exc


def _as_object_list(payload: Any, *, role: str) -> list[dict[str, Any]]:
    if isinstance(payload, dict) and role.endswith("chunks"):
        payload = payload.get("chunks")
    if not isinstance(payload, list) or not all(
        isinstance(item, dict) for item in payload
    ):
        raise EmbeddingReuseError(f"Prepared {role} must be a JSON object list")
    return payload


def _required_int(value: Any, *, field_name: str, context: str) -> int:
    if isinstance(value, bool) or value is None:
        raise EmbeddingReuseError(f"{context} has no valid {field_name}")
    try:
        return int(value)
    except (TypeError, ValueError) as exc:
        raise EmbeddingReuseError(
            f"{context} has no valid {field_name}: {value!r}"
        ) from exc


def _sanitize_text(value: Any) -> str:
    if value is None:
        return ""
    return str(value).replace("\x00", "")


def _snapshot_chunk_type(chunk: Mapping[str, Any], artifact_type: int) -> str:
    named = str(chunk.get("chunk_type_name") or "").strip()
    if named:
        return named
    if artifact_type == 1:
        file_type = _required_int(
            chunk.get("idChunkType"),
            field_name="idChunkType",
            context="DocuHub chunk",
        )
        resolved = HUB_CHUNK_TYPES.get(file_type)
        if resolved:
            return resolved
    raise EmbeddingReuseError(
        "Prepared chunk has no supported chunk type name: "
        f"artifact_type={artifact_type}, idChunk={chunk.get('idChunk')!r}"
    )


def build_snapshot_inventory(
    validated_bundle: Mapping[str, Any],
    *,
    expected_artifacts: int | None = None,
    expected_chunks: int | None = None,
) -> SnapshotInventory:
    """Build strict URL/source-chunk keys from a validated prepared bundle."""
    manifest = validated_bundle["manifest"]
    files = validated_bundle["files"]
    artifacts: dict[ArtifactKey, SnapshotArtifact] = {}
    chunks: dict[ChunkKey, SnapshotChunk] = {}
    source_counts: dict[str, dict[str, int]] = {}

    for source_name, artifact_type, artifact_role, chunk_role, include_flag in SOURCE_SPECS:
        if include_flag and not manifest.get(include_flag):
            continue
        artifact_payload = _as_object_list(
            _load_json(Path(files[artifact_role])), role=artifact_role
        )
        chunk_payload = _as_object_list(
            _load_json(Path(files[chunk_role])), role=chunk_role
        )

        source_id_to_key: dict[int, ArtifactKey] = {}
        for item in artifact_payload:
            actual_type = _required_int(
                item.get("idArtifactType"),
                field_name="idArtifactType",
                context=f"{source_name} artifact",
            )
            if actual_type != artifact_type:
                raise EmbeddingReuseError(
                    f"{source_name} artifact type {actual_type} != {artifact_type}"
                )
            source_id = _required_int(
                item.get("idArtifact"),
                field_name="idArtifact",
                context=f"{source_name} artifact",
            )
            url = str(item.get("URL") or "").strip()
            if not url:
                raise EmbeddingReuseError(
                    f"{source_name} artifact {source_id} has no URL"
                )
            artifact = SnapshotArtifact(
                artifact_type=artifact_type,
                source_id=source_id,
                url=url,
                source_name=source_name,
                title=item.get("Title", ""),
                summary_data=item.get("summary_data"),
            )
            if artifact.key in artifacts:
                raise EmbeddingReuseError(
                    f"Duplicate prepared artifact key: {artifact.key!r}"
                )
            if source_id in source_id_to_key:
                raise EmbeddingReuseError(
                    f"Duplicate {source_name} source artifact ID: {source_id}"
                )
            artifacts[artifact.key] = artifact
            source_id_to_key[source_id] = artifact.key

        source_chunk_count = 0
        for item in chunk_payload:
            source_artifact_id = _required_int(
                item.get("idArtifact"),
                field_name="idArtifact",
                context=f"{source_name} chunk",
            )
            artifact_key = source_id_to_key.get(source_artifact_id)
            if artifact_key is None:
                raise EmbeddingReuseError(
                    f"{source_name} chunk references unknown artifact "
                    f"{source_artifact_id}"
                )
            source_chunk_id = _required_int(
                item.get("idChunk"),
                field_name="idChunk",
                context=f"{source_name} chunk",
            )
            order = _required_int(
                item.get("order"),
                field_name="order",
                context=f"{source_name} chunk {source_chunk_id}",
            )
            chunk = SnapshotChunk(
                artifact_key=artifact_key,
                source_chunk_id=source_chunk_id,
                order=order,
                chunk_type=_snapshot_chunk_type(item, artifact_type),
                section_hint=_sanitize_text(
                    item.get("section_hint") or item.get("title") or ""
                ),
                text=_sanitize_text(item.get("chunk_text")),
                source_name=source_name,
            )
            if chunk.key in chunks:
                raise EmbeddingReuseError(
                    f"Duplicate prepared chunk key: {chunk.key!r}"
                )
            chunks[chunk.key] = chunk
            source_chunk_count += 1

        source_counts[source_name] = {
            "artifacts": len(artifact_payload),
            "chunks": source_chunk_count,
        }

    inventory = SnapshotInventory(
        artifacts=artifacts,
        chunks=chunks,
        source_counts=source_counts,
    )
    if expected_artifacts is not None and inventory.artifact_count != expected_artifacts:
        raise EmbeddingReuseError(
            f"Prepared artifact count {inventory.artifact_count} != explicitly "
            f"expected {expected_artifacts}"
        )
    if expected_chunks is not None and inventory.chunk_count != expected_chunks:
        raise EmbeddingReuseError(
            f"Prepared chunk count {inventory.chunk_count} != explicitly "
            f"expected {expected_chunks}"
        )
    return inventory


def load_database_config(path: Path | str) -> DatabaseConfig:
    path = Path(path).expanduser().resolve()
    if not path.is_file():
        raise EmbeddingReuseError(f"Database environment file does not exist: {path}")
    values = dotenv_values(path)
    required = (
        "POSTGRES_HOST",
        "POSTGRES_DB",
        "POSTGRES_SCHEMA",
        "POSTGRES_USER",
        "POSTGRES_PASSWORD",
    )
    missing = [key for key in required if not str(values.get(key) or "").strip()]
    if missing:
        raise EmbeddingReuseError(
            f"Database environment file is missing required variables: {missing}"
        )
    try:
        port = int(values.get("POSTGRES_PORT") or 5432)
        timeout = int(values.get("POSTGRES_CONNECT_TIMEOUT") or 15)
    except (TypeError, ValueError) as exc:
        raise EmbeddingReuseError("POSTGRES_PORT/connect timeout must be integers") from exc
    schema = str(values.get("POSTGRES_SCHEMA") or "CIROH_AIBot").strip()
    if not schema:
        raise EmbeddingReuseError("POSTGRES_SCHEMA cannot be empty")
    return DatabaseConfig(
        host=str(values["POSTGRES_HOST"]).strip(),
        database=str(values["POSTGRES_DB"]).strip(),
        user=str(values["POSTGRES_USER"]).strip(),
        password=str(values["POSTGRES_PASSWORD"]),
        schema=schema,
        port=port,
        sslmode=(str(values.get("POSTGRES_SSLMODE")).strip() or None)
        if values.get("POSTGRES_SSLMODE") is not None
        else None,
        connect_timeout=timeout,
    )


def _prepare_connection(connection: Any, schema: str, *, read_only: bool) -> None:
    connection.set_session(
        readonly=read_only,
        autocommit=False,
        isolation_level="REPEATABLE READ",
    )
    with connection.cursor() as cursor:
        cursor.execute(
            sql.SQL("SET LOCAL search_path TO {}, public").format(
                sql.Identifier(schema)
            )
        )
        cursor.execute("SELECT current_schema()")
        current_schema = cursor.fetchone()[0]
        if current_schema != schema:
            raise EmbeddingReuseError(
                f"Configured PostgreSQL schema is unavailable: {schema!r}"
            )


def _acquire_target_lock(connection: Any) -> None:
    with connection.cursor() as cursor:
        cursor.execute(
            "SELECT pg_advisory_xact_lock(hashtext(%s));",
            (ADVISORY_LOCK_NAME,),
        )


def _lock_target_tables(connection: Any) -> None:
    with connection.cursor() as cursor:
        cursor.execute(
            "LOCK TABLE tblartifacts, tblchunks IN SHARE ROW EXCLUSIVE MODE;"
        )


def _artifact_scope_count(
    cursor: Any,
    artifact_type: int,
) -> int:
    hydroshare_scope = ""
    if artifact_type == 3:
        hydroshare_scope = (
            " AND ("
            "metadata->'hydroshare'->>'artifact_role' = 'hydroshare_resource' "
            "OR metadata->'hydroshare'->>'resource_id' IS NOT NULL "
            "OR url ILIKE '%%hydroshare.org/resource/%%'"
            ")"
        )
    cursor.execute(
        "SELECT count(*) AS row_count FROM tblartifacts "
        "WHERE isactive = TRUE AND idartifacttype = %s" + hydroshare_scope,
        (artifact_type,),
    )
    return int(cursor.fetchone()["row_count"])


def _fetch_database_rows(
    connection: Any,
    snapshot: SnapshotInventory,
    *,
    reject_extra_active: bool,
) -> tuple[list[Mapping[str, Any]], list[Mapping[str, Any]]]:
    artifact_rows: list[Mapping[str, Any]] = []
    urls_by_type: dict[int, list[str]] = {}
    for artifact_type, url in snapshot.artifacts:
        urls_by_type.setdefault(artifact_type, []).append(url)

    with connection.cursor(cursor_factory=RealDictCursor) as cursor:
        for artifact_type, urls in sorted(urls_by_type.items()):
            cursor.execute(
                "SELECT idartifact, idartifacttype, url, title, summary_data, "
                "embedding::text AS embedding_text, "
                "CASE WHEN embedding IS NULL THEN NULL "
                "ELSE vector_dims(embedding) END AS embedding_dimensions "
                "FROM tblartifacts "
                "WHERE isactive = TRUE AND idartifacttype = %s "
                "AND url = ANY(%s::text[]) "
                "ORDER BY url, idartifact",
                (artifact_type, sorted(urls)),
            )
            artifact_rows.extend(cursor.fetchall())
            if reject_extra_active:
                expected = len(urls)
                actual = _artifact_scope_count(cursor, artifact_type)
                if actual != expected:
                    raise EmbeddingReuseError(
                        f"Target active artifact scope for type {artifact_type} "
                        f"contains {actual} rows; prepared snapshot requires {expected}"
                    )

        artifact_ids = [int(row["idartifact"]) for row in artifact_rows]
        if not artifact_ids:
            chunk_rows: list[Mapping[str, Any]] = []
        else:
            cursor.execute(
                "SELECT c.idchunk, c.idartifact, c.\"order\" AS chunk_order, "
                "c.chunk_text, ct.typename AS chunk_type, "
                "COALESCE(c.metadata->>'section_hint', '') AS section_hint, "
                "c.metadata->>'source_chunk_id' AS source_chunk_id, "
                "c.embedding::text AS embedding_text, "
                "CASE WHEN c.embedding IS NULL THEN NULL "
                "ELSE vector_dims(c.embedding) END AS embedding_dimensions "
                "FROM tblchunks c "
                "JOIN tblchunktypes ct ON ct.idchunktype = c.idchunktype "
                "WHERE c.idartifact = ANY(%s::int[]) "
                "ORDER BY c.idartifact, c.idchunk",
                (artifact_ids,),
            )
            chunk_rows = list(cursor.fetchall())
    return artifact_rows, chunk_rows


def validate_database_rows(
    snapshot: SnapshotInventory,
    artifact_rows: Iterable[Mapping[str, Any]],
    chunk_rows: Iterable[Mapping[str, Any]],
    *,
    label: str,
    require_vectors: bool,
) -> DatabaseInventory:
    """Validate DB rows against every structural field in the frozen bundle."""
    artifacts: dict[ArtifactKey, DatabaseArtifact] = {}
    database_id_to_key: dict[int, ArtifactKey] = {}
    for row in artifact_rows:
        key = (
            _required_int(
                row.get("idartifacttype"),
                field_name="idartifacttype",
                context=f"{label} artifact row",
            ),
            str(row.get("url") or ""),
        )
        if key not in snapshot.artifacts:
            raise EmbeddingReuseError(f"{label} has an unexpected artifact: {key!r}")
        if key in artifacts:
            raise EmbeddingReuseError(f"{label} has duplicate active artifact: {key!r}")
        database_id = _required_int(
            row.get("idartifact"),
            field_name="idartifact",
            context=f"{label} artifact {key!r}",
        )
        if database_id in database_id_to_key:
            raise EmbeddingReuseError(
                f"{label} repeats artifact database ID {database_id}"
            )
        expected_artifact = snapshot.artifacts[key]
        artifact_mismatches: list[str] = []
        if row.get("title") != expected_artifact.title:
            artifact_mismatches.append("title")
        if row.get("summary_data") != expected_artifact.summary_data:
            artifact_mismatches.append("summary_data")
        if artifact_mismatches:
            raise EmbeddingReuseError(
                f"{label} artifact {key!r} differs in "
                f"{', '.join(artifact_mismatches)}"
            )
        embedding_text = row.get("embedding_text")
        dimensions = row.get("embedding_dimensions")
        if embedding_text is not None and int(dimensions or 0) != VECTOR_DIMENSIONS:
            raise EmbeddingReuseError(
                f"{label} artifact {key!r} embedding is not "
                f"{VECTOR_DIMENSIONS}-dimensional"
            )
        if require_vectors and embedding_text is None:
            raise EmbeddingReuseError(f"{label} artifact {key!r} has no embedding")
        artifacts[key] = DatabaseArtifact(
            database_id=database_id,
            embedding_text=str(embedding_text) if embedding_text is not None else None,
            embedding_dimensions=int(dimensions) if dimensions is not None else None,
        )
        database_id_to_key[database_id] = key

    missing_artifacts = sorted(set(snapshot.artifacts) - set(artifacts))
    if missing_artifacts:
        raise EmbeddingReuseError(
            f"{label} is missing {len(missing_artifacts)} prepared artifacts; "
            f"sample={missing_artifacts[:3]!r}"
        )

    chunks: dict[ChunkKey, DatabaseChunk] = {}
    for row in chunk_rows:
        artifact_database_id = _required_int(
            row.get("idartifact"),
            field_name="idartifact",
            context=f"{label} chunk row",
        )
        artifact_key = database_id_to_key.get(artifact_database_id)
        if artifact_key is None:
            raise EmbeddingReuseError(
                f"{label} chunk references unmatched artifact {artifact_database_id}"
            )
        source_chunk_id = _required_int(
            row.get("source_chunk_id"),
            field_name="metadata.source_chunk_id",
            context=f"{label} chunk row",
        )
        key = (artifact_key[0], artifact_key[1], source_chunk_id)
        expected = snapshot.chunks.get(key)
        if expected is None:
            raise EmbeddingReuseError(f"{label} has an unexpected chunk: {key!r}")
        if key in chunks:
            raise EmbeddingReuseError(f"{label} has duplicate chunk key: {key!r}")

        actual_order = _required_int(
            row.get("chunk_order"),
            field_name="order",
            context=f"{label} chunk {key!r}",
        )
        actual_type = str(row.get("chunk_type") or "")
        actual_section_hint = _sanitize_text(row.get("section_hint"))
        actual_text = _sanitize_text(row.get("chunk_text"))
        mismatches: list[str] = []
        if actual_order != expected.order:
            mismatches.append("order")
        if actual_type != expected.chunk_type:
            mismatches.append("chunk type")
        if actual_section_hint != expected.section_hint:
            mismatches.append("section hint")
        if actual_text != expected.text:
            mismatches.append("chunk text")
        if mismatches:
            raise EmbeddingReuseError(
                f"{label} chunk {key!r} differs in {', '.join(mismatches)}"
            )

        embedding_text = row.get("embedding_text")
        dimensions = row.get("embedding_dimensions")
        if embedding_text is not None and int(dimensions or 0) != VECTOR_DIMENSIONS:
            raise EmbeddingReuseError(
                f"{label} chunk {key!r} embedding is not "
                f"{VECTOR_DIMENSIONS}-dimensional"
            )
        if require_vectors and expected.has_embedding_input and embedding_text is None:
            raise EmbeddingReuseError(
                f"{label} nonempty chunk {key!r} has no embedding"
            )
        if require_vectors and not expected.has_embedding_input and embedding_text is not None:
            raise EmbeddingReuseError(
                f"{label} empty chunk {key!r} unexpectedly has an embedding"
            )
        database_id = _required_int(
            row.get("idchunk"),
            field_name="idchunk",
            context=f"{label} chunk {key!r}",
        )
        chunks[key] = DatabaseChunk(
            database_id=database_id,
            embedding_text=str(embedding_text) if embedding_text is not None else None,
            embedding_dimensions=int(dimensions) if dimensions is not None else None,
        )

    missing_chunks = sorted(set(snapshot.chunks) - set(chunks))
    if missing_chunks:
        raise EmbeddingReuseError(
            f"{label} is missing {len(missing_chunks)} prepared chunks; "
            f"sample={missing_chunks[:3]!r}"
        )
    if len(chunks) != snapshot.chunk_count:
        raise EmbeddingReuseError(
            f"{label} chunk count {len(chunks)} != {snapshot.chunk_count}"
        )
    return DatabaseInventory(artifacts=artifacts, chunks=chunks)


def load_database_inventory(
    connection: Any,
    snapshot: SnapshotInventory,
    *,
    label: str,
    require_vectors: bool,
    reject_extra_active: bool,
) -> DatabaseInventory:
    artifact_rows, chunk_rows = _fetch_database_rows(
        connection,
        snapshot,
        reject_extra_active=reject_extra_active,
    )
    return validate_database_rows(
        snapshot,
        artifact_rows,
        chunk_rows,
        label=label,
        require_vectors=require_vectors,
    )


def _vector_digest(value: str | None) -> str | None:
    if value is None:
        return None
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def compare_vector_digests(
    source: DatabaseInventory,
    target: DatabaseInventory,
) -> None:
    if set(source.artifacts) != set(target.artifacts):
        raise EmbeddingReuseError("Artifact keys changed during embedding copy")
    if set(source.chunks) != set(target.chunks):
        raise EmbeddingReuseError("Chunk keys changed during embedding copy")
    for key, source_row in source.artifacts.items():
        if _vector_digest(source_row.embedding_text) != _vector_digest(
            target.artifacts[key].embedding_text
        ):
            raise EmbeddingReuseError(
                f"Target artifact embedding digest differs after copy: {key!r}"
            )
    for key, source_row in source.chunks.items():
        if _vector_digest(source_row.embedding_text) != _vector_digest(
            target.chunks[key].embedding_text
        ):
            raise EmbeddingReuseError(
                f"Target chunk embedding digest differs after copy: {key!r}"
            )


def validate_target_vector_conflicts(
    source: DatabaseInventory,
    target: DatabaseInventory,
) -> None:
    """Fail closed if a target already has a different non-null vector."""
    for key, target_row in target.artifacts.items():
        if (
            target_row.embedding_text is not None
            and _vector_digest(target_row.embedding_text)
            != _vector_digest(source.artifacts[key].embedding_text)
        ):
            raise EmbeddingReuseError(
                f"Target artifact already has a conflicting embedding: {key!r}"
            )
    for key, target_row in target.chunks.items():
        if (
            target_row.embedding_text is not None
            and _vector_digest(target_row.embedding_text)
            != _vector_digest(source.chunks[key].embedding_text)
        ):
            raise EmbeddingReuseError(
                f"Target chunk already has a conflicting embedding: {key!r}"
            )


def _execute_vector_updates(
    cursor: Any,
    query: str,
    rows: list[tuple[int, str | None]],
    *,
    label: str,
) -> int:
    if not rows:
        return 0
    returned = execute_values(
        cursor,
        query,
        rows,
        page_size=100,
        fetch=True,
    )
    updated_ids = {int(row[0]) for row in returned}
    expected_ids = {row[0] for row in rows}
    if updated_ids != expected_ids or len(returned) != len(rows):
        raise EmbeddingReuseError(
            f"Target {label} embedding update affected {len(returned)} rows; "
            f"expected {len(rows)}"
        )
    return len(returned)


def apply_embeddings(
    connection: Any,
    source: DatabaseInventory,
    target: DatabaseInventory,
) -> dict[str, int]:
    artifact_rows = [
        (target.artifacts[key].database_id, source_row.embedding_text)
        for key, source_row in source.artifacts.items()
    ]
    chunk_rows = [
        (target.chunks[key].database_id, source_row.embedding_text)
        for key, source_row in source.chunks.items()
    ]
    with connection.cursor() as cursor:
        artifact_updates = _execute_vector_updates(
            cursor,
            "UPDATE tblartifacts AS target SET embedding = v.embedding::vector "
            "FROM (VALUES %s) AS v(idartifact, embedding) "
            "WHERE target.idartifact = v.idartifact::int "
            "RETURNING target.idartifact",
            artifact_rows,
            label="artifact",
        )
        chunk_updates = _execute_vector_updates(
            cursor,
            "UPDATE tblchunks AS target SET embedding = v.embedding::vector "
            "FROM (VALUES %s) AS v(idchunk, embedding) "
            "WHERE target.idchunk = v.idchunk::int "
            "RETURNING target.idchunk",
            chunk_rows,
            label="chunk",
        )
    return {
        "artifact_rows_updated": artifact_updates,
        "chunk_rows_updated": chunk_updates,
        "artifact_vectors_copied": sum(
            row.embedding_text is not None for row in source.artifacts.values()
        ),
        "chunk_vectors_copied": sum(
            row.embedding_text is not None for row in source.chunks.values()
        ),
        "null_empty_chunks_copied": sum(
            row.embedding_text is None for row in source.chunks.values()
        ),
    }


def transfer_embeddings(
    source_connection: Any,
    target_connection: Any,
    snapshot: SnapshotInventory,
    *,
    source_schema: str,
    target_schema: str,
    execute: bool,
    overwrite_conflicting_target_vectors: bool = False,
) -> dict[str, Any]:
    """Validate both DBs and optionally copy all vectors atomically."""
    try:
        _prepare_connection(source_connection, source_schema, read_only=True)
        source = load_database_inventory(
            source_connection,
            snapshot,
            label="Source",
            require_vectors=True,
            reject_extra_active=False,
        )

        _prepare_connection(target_connection, target_schema, read_only=not execute)
        if execute:
            _acquire_target_lock(target_connection)
            _lock_target_tables(target_connection)
        target_before = load_database_inventory(
            target_connection,
            snapshot,
            label="Target",
            require_vectors=False,
            reject_extra_active=True,
        )
        if not overwrite_conflicting_target_vectors:
            validate_target_vector_conflicts(source, target_before)

        updates = {
            "artifact_rows_updated": 0,
            "chunk_rows_updated": 0,
            "artifact_vectors_copied": 0,
            "chunk_vectors_copied": 0,
            "null_empty_chunks_copied": 0,
        }
        if execute:
            updates = apply_embeddings(target_connection, source, target_before)
            target_after = load_database_inventory(
                target_connection,
                snapshot,
                label="Target after copy",
                require_vectors=True,
                reject_extra_active=True,
            )
            compare_vector_digests(source, target_after)
            source_connection.rollback()
            target_connection.commit()
        else:
            target_connection.rollback()
            source_connection.rollback()
        return {
            "mode": "execute" if execute else "dry_run",
            "mapping_validated": True,
            "vector_digests_verified": bool(execute),
            "conflicting_target_vectors_overwritten": bool(
                execute and overwrite_conflicting_target_vectors
            ),
            **updates,
        }
    except BaseException:
        try:
            target_connection.rollback()
        finally:
            source_connection.rollback()
        raise


def _inventory_report(snapshot: SnapshotInventory) -> dict[str, Any]:
    return {
        "artifacts": snapshot.artifact_count,
        "chunks": snapshot.chunk_count,
        "artifact_vectors_required": snapshot.artifact_count,
        "nonempty_chunk_vectors_required": snapshot.nonempty_chunk_count,
        "empty_chunks_expected_without_vectors": snapshot.empty_chunk_count,
        "vector_dimensions": VECTOR_DIMENSIONS,
        "sources": snapshot.source_counts,
    }


def _resolve_report_path(
    bundle_dir: Path,
    result_file: str | None,
    run_id: str,
) -> Path:
    if result_file:
        candidate = Path(result_file)
        return candidate if candidate.is_absolute() else (ROOT / candidate).resolve()
    return bundle_dir / "applications" / f"embedding_reuse_{run_id}.json"


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description=(
            "Validate and reuse local embeddings for an already-applied "
            "prepared synchronization bundle. Dry-run by default."
        )
    )
    parser.add_argument("--bundle", help="Prepared bundle path or sync ID")
    parser.add_argument(
        "--source-env",
        default=str(ROOT / ".env"),
        help="Environment file for the trusted, synchronized source DB",
    )
    parser.add_argument(
        "--target-env",
        required=True,
        help="Environment file for the target DB",
    )
    parser.add_argument(
        "--expected-artifacts",
        type=int,
        help="Optional exact prepared artifact-count guard",
    )
    parser.add_argument(
        "--expected-chunks",
        type=int,
        help="Optional exact prepared chunk-count guard",
    )
    parser.add_argument(
        "--result-file",
        help="Optional result JSON path (defaults inside bundle/applications)",
    )
    parser.add_argument(
        "--execute",
        action="store_true",
        help="Required to update target embeddings; otherwise validation only",
    )
    parser.add_argument(
        "--overwrite-conflicting-target-vectors",
        action="store_true",
        help=(
            "Permit --execute to replace a target vector that is already "
            "non-null but differs from the trusted source. Without this "
            "explicit flag the command fails closed."
        ),
    )
    args = parser.parse_args(argv)

    run_id = new_sync_id()
    started_at = utc_now_iso()
    bundle_dir = resolve_prepared_bundle(ROOT, args.bundle)
    report_path = _resolve_report_path(bundle_dir, args.result_file, run_id)
    report: dict[str, Any] = {
        "schema_version": 1,
        "run_id": run_id,
        "status": "running",
        "mode": "execute" if args.execute else "dry_run",
        "started_at": started_at,
        "bundle": str(bundle_dir),
        "database_update_performed": False,
    }

    source_connection = None
    target_connection = None
    try:
        validated = validate_prepared_bundle(bundle_dir)
        snapshot = build_snapshot_inventory(
            validated,
            expected_artifacts=args.expected_artifacts,
            expected_chunks=args.expected_chunks,
        )
        report["source_sync_id"] = validated["manifest"].get("sync_id")
        report["inventory"] = _inventory_report(snapshot)

        source_config = load_database_config(args.source_env)
        target_config = load_database_config(args.target_env)
        if source_config.identity == target_config.identity:
            raise EmbeddingReuseError(
                "Source and target resolve to the same database/schema; refusing "
                "an embedding transfer"
            )

        source_connection = psycopg2.connect(
            **source_config.connection_kwargs("ciroh-embedding-reuse-source")
        )
        target_connection = psycopg2.connect(
            **target_config.connection_kwargs("ciroh-embedding-reuse-target")
        )
        transfer_result = transfer_embeddings(
            source_connection,
            target_connection,
            snapshot,
            source_schema=source_config.schema,
            target_schema=target_config.schema,
            execute=args.execute,
            overwrite_conflicting_target_vectors=(
                args.overwrite_conflicting_target_vectors
            ),
        )
        report["transfer"] = transfer_result
        report["database_update_performed"] = bool(args.execute)
        report["status"] = "completed" if args.execute else "validated"
        report["completed_at"] = utc_now_iso()
        _write_json_atomic(report_path, report)
        print(f"Prepared bundle: {bundle_dir}")
        print(
            "Validated inventory: "
            f"{snapshot.artifact_count} artifacts, {snapshot.chunk_count} chunks"
        )
        if args.execute:
            print(
                "Copied embeddings atomically: "
                f"{transfer_result['artifact_vectors_copied']} artifacts, "
                f"{transfer_result['chunk_vectors_copied']} nonempty chunks"
            )
        else:
            print("Dry-run only; no target rows were changed. Pass --execute to copy.")
        print(f"Result report: {report_path}")
        return 0
    except BaseException as exc:
        report["status"] = "failed"
        report["completed_at"] = utc_now_iso()
        report["error"] = str(exc)
        try:
            _write_json_atomic(report_path, report)
        except OSError:
            pass
        raise
    finally:
        if source_connection is not None:
            source_connection.close()
        if target_connection is not None:
            target_connection.close()


if __name__ == "__main__":
    raise SystemExit(main())
