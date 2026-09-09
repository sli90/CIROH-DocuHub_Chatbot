"""Create and validate immutable, retryable synchronization bundles."""
from __future__ import annotations

import hashlib
import json
import shutil
from pathlib import Path
from typing import Any

from sync_accounting import utc_now_iso


BUNDLE_SCHEMA_VERSION = 1
PREPARED_DIRECTORY = Path("local_change_dashboard") / "prepared_syncs"
MANIFEST_FILENAME = "manifest.json"


class PreparedSyncError(RuntimeError):
    """Raised when a prepared synchronization bundle is incomplete or altered."""


def _load_json(path: Path) -> Any:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise PreparedSyncError(f"Could not read valid JSON from {path}: {exc}") from exc


def _write_json_atomic(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(f".{path.name}.tmp")
    temporary.write_text(
        json.dumps(payload, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    temporary.replace(path)


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def _normalize_chunks(payload: Any) -> list[dict]:
    if isinstance(payload, dict):
        payload = payload.get("chunks")
    if not isinstance(payload, list) or not all(
        isinstance(item, dict) for item in payload
    ):
        raise PreparedSyncError("Chunk payload must be a JSON list of objects")
    return payload


def _validate_snapshot(
    artifacts_payload: Any,
    chunks_payload: Any,
    *,
    expected_type: int,
    require_summaries: bool,
) -> dict[str, int]:
    if not isinstance(artifacts_payload, list) or not all(
        isinstance(item, dict) for item in artifacts_payload
    ):
        raise PreparedSyncError("Artifact payload must be a JSON list of objects")
    chunks = _normalize_chunks(chunks_payload)
    artifact_ids: set[int] = set()
    urls: set[str] = set()
    missing_summaries = 0
    for artifact in artifacts_payload:
        if artifact.get("idArtifactType") != expected_type:
            raise PreparedSyncError(
                f"Prepared type-{expected_type} snapshot contains artifact type "
                f"{artifact.get('idArtifactType')!r}"
            )
        try:
            source_id = int(artifact["idArtifact"])
        except (KeyError, TypeError, ValueError) as exc:
            raise PreparedSyncError("Artifact has no valid idArtifact") from exc
        url = str(artifact.get("URL") or "").strip()
        if not url:
            raise PreparedSyncError(f"Artifact {source_id} has no URL")
        if source_id in artifact_ids:
            raise PreparedSyncError(f"Duplicate artifact source ID: {source_id}")
        if url in urls:
            raise PreparedSyncError(f"Duplicate artifact URL: {url}")
        artifact_ids.add(source_id)
        urls.add(url)
        if artifact.get("summary_data") is None:
            missing_summaries += 1

    unknown_chunk_artifacts = sorted(
        {
            int(chunk.get("idArtifact"))
            for chunk in chunks
            if chunk.get("idArtifact") is not None
        }
        - artifact_ids
    )
    if unknown_chunk_artifacts:
        raise PreparedSyncError(
            "Chunks reference missing artifact source IDs: "
            f"{unknown_chunk_artifacts[:10]}"
        )
    if require_summaries and missing_summaries:
        raise PreparedSyncError(
            f"Prepared type-{expected_type} snapshot has "
            f"{missing_summaries} artifacts without summaries"
        )
    return {
        "artifacts": len(artifacts_payload),
        "chunks": len(chunks),
        "missing_summaries": missing_summaries,
    }


def create_prepared_bundle(
    root: Path | str,
    *,
    sync_id: str,
    include_github_repositories: bool,
    allow_pending_summaries: bool = False,
) -> Path:
    """Freeze generated JSON files before any database update begins."""
    root = Path(root).resolve()
    formatted = root / "dashboard" / "formated_files"
    bundle_dir = root / PREPARED_DIRECTORY / sync_id
    if bundle_dir.exists():
        raise PreparedSyncError(f"Prepared bundle already exists: {bundle_dir}")

    source_files: dict[str, Path] = {
        "docuhub_artifacts": formatted / "artifacts.json",
        "docuhub_chunks": formatted / "content_chunks.json",
        "docuhub_generation_report": formatted / "generation_report.json",
    }
    target_names = {
        "docuhub_artifacts": "docuhub_artifacts.json",
        "docuhub_chunks": "docuhub_chunks.json",
        "docuhub_generation_report": "docuhub_generation_report.json",
    }
    if include_github_repositories:
        source_files.update(
            {
                "github_artifacts": formatted / "coderepo_artifacts.json",
                "github_chunks": formatted / "coderepo_chunks.json",
                "github_generation_report": (
                    formatted / "github_repository_generation_report.json"
                ),
            }
        )
        target_names.update(
            {
                "github_artifacts": "github_artifacts.json",
                "github_chunks": "github_chunks.json",
                "github_generation_report": "github_generation_report.json",
            }
        )

    missing = [str(path) for path in source_files.values() if not path.is_file()]
    if missing:
        raise PreparedSyncError(f"Generated files are missing: {missing}")

    docuhub_validation = _validate_snapshot(
        _load_json(source_files["docuhub_artifacts"]),
        _load_json(source_files["docuhub_chunks"]),
        expected_type=1,
        require_summaries=not allow_pending_summaries,
    )
    github_validation = None
    if include_github_repositories:
        github_report = _load_json(source_files["github_generation_report"])
        if not isinstance(github_report, dict) or github_report.get("status") != "completed":
            raise PreparedSyncError("GitHub repository generation did not complete")
        github_validation = _validate_snapshot(
            _load_json(source_files["github_artifacts"]),
            _load_json(source_files["github_chunks"]),
            expected_type=4,
            require_summaries=not allow_pending_summaries,
        )

    bundle_dir.mkdir(parents=True)
    file_manifest: dict[str, dict[str, Any]] = {}
    for role, source in source_files.items():
        target = bundle_dir / target_names[role]
        shutil.copy2(source, target)
        file_manifest[role] = {
            "filename": target.name,
            "bytes": target.stat().st_size,
            "sha256": _sha256(target),
        }

    manifest = {
        "schema_version": BUNDLE_SCHEMA_VERSION,
        "status": "prepared",
        "sync_id": sync_id,
        "created_at": utc_now_iso(),
        "include_github_repositories": include_github_repositories,
        "allow_pending_summaries": allow_pending_summaries,
        "validation": {
            "docuhub": docuhub_validation,
            "github_repositories": github_validation,
        },
        "files": file_manifest,
    }
    _write_json_atomic(bundle_dir / MANIFEST_FILENAME, manifest)
    _write_json_atomic(
        root / PREPARED_DIRECTORY / "latest.json",
        {
            "sync_id": sync_id,
            "bundle": str(bundle_dir),
            "manifest_sha256": _sha256(bundle_dir / MANIFEST_FILENAME),
            "updated_at": utc_now_iso(),
        },
    )
    return bundle_dir


def resolve_prepared_bundle(root: Path | str, bundle: Path | str | None) -> Path:
    root = Path(root).resolve()
    if bundle is None:
        latest = _load_json(root / PREPARED_DIRECTORY / "latest.json")
        bundle = latest.get("bundle") if isinstance(latest, dict) else None
        if not bundle:
            raise PreparedSyncError("No latest prepared synchronization is recorded")
    candidate = Path(bundle)
    if not candidate.is_absolute():
        direct = (root / candidate).resolve()
        by_id = (root / PREPARED_DIRECTORY / candidate).resolve()
        candidate = direct if direct.is_dir() else by_id
    candidate = candidate.resolve()
    if not candidate.is_dir():
        raise PreparedSyncError(f"Prepared bundle directory does not exist: {candidate}")
    return candidate


def validate_prepared_bundle(bundle_dir: Path | str) -> dict[str, Any]:
    """Verify hashes and snapshot invariants without changing any files."""
    bundle_dir = Path(bundle_dir).resolve()
    manifest = _load_json(bundle_dir / MANIFEST_FILENAME)
    if not isinstance(manifest, dict):
        raise PreparedSyncError("Prepared manifest must be a JSON object")
    if manifest.get("schema_version") != BUNDLE_SCHEMA_VERSION:
        raise PreparedSyncError("Unsupported prepared synchronization schema")
    if manifest.get("status") != "prepared":
        raise PreparedSyncError("Synchronization bundle is not in prepared state")
    files = manifest.get("files")
    if not isinstance(files, dict):
        raise PreparedSyncError("Prepared manifest has no file inventory")

    resolved_files: dict[str, Path] = {}
    for role, details in files.items():
        if not isinstance(details, dict):
            raise PreparedSyncError(f"Invalid file entry for {role}")
        path = (bundle_dir / str(details.get("filename") or "")).resolve()
        if path.parent != bundle_dir:
            raise PreparedSyncError(f"Unsafe prepared filename for {role}")
        if not path.is_file():
            raise PreparedSyncError(f"Prepared file is missing: {path}")
        if path.stat().st_size != int(details.get("bytes") or -1):
            raise PreparedSyncError(f"Prepared file size changed: {path.name}")
        if _sha256(path) != details.get("sha256"):
            raise PreparedSyncError(f"Prepared file hash changed: {path.name}")
        resolved_files[role] = path

    required = {
        "docuhub_artifacts",
        "docuhub_chunks",
        "docuhub_generation_report",
    }
    if manifest.get("include_github_repositories"):
        required.update(
            {"github_artifacts", "github_chunks", "github_generation_report"}
        )
    missing_roles = sorted(required - set(resolved_files))
    if missing_roles:
        raise PreparedSyncError(f"Prepared file roles are missing: {missing_roles}")

    require_summaries = not bool(manifest.get("allow_pending_summaries"))
    validations = {
        "docuhub": _validate_snapshot(
            _load_json(resolved_files["docuhub_artifacts"]),
            _load_json(resolved_files["docuhub_chunks"]),
            expected_type=1,
            require_summaries=require_summaries,
        )
    }
    if manifest.get("include_github_repositories"):
        validations["github_repositories"] = _validate_snapshot(
            _load_json(resolved_files["github_artifacts"]),
            _load_json(resolved_files["github_chunks"]),
            expected_type=4,
            require_summaries=require_summaries,
        )
    return {
        "bundle_dir": bundle_dir,
        "manifest": manifest,
        "files": resolved_files,
        "validation": validations,
    }
