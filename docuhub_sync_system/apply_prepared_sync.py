"""Apply an already-generated synchronization bundle to PostgreSQL."""
from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path
from typing import Any

from prepared_sync import (
    PreparedSyncError,
    resolve_prepared_bundle,
    validate_prepared_bundle,
)
from sync_accounting import new_sync_id, utc_now_iso


ROOT = Path(__file__).resolve().parent


def _write_json_atomic(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(f".{path.name}.tmp")
    temporary.write_text(
        json.dumps(payload, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    temporary.replace(path)


def _load_result(path: Path) -> dict | None:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None
    return payload if isinstance(payload, dict) else None


def _resolve_hydroshare_removal_policy(
    manifest: dict[str, Any],
    *,
    apply_override: bool,
    override_reason: str | None,
) -> dict[str, Any]:
    """Resolve a target-specific large-removal override with provenance."""
    allowed_by_bundle = bool(
        manifest.get("allow_large_hydroshare_removals")
    )
    reason = (override_reason or "").strip()

    if apply_override and not manifest.get("include_hydroshare_resources"):
        raise PreparedSyncError(
            "A HydroShare removal override requires a bundle that includes "
            "HydroShare resources"
        )
    if apply_override and not allowed_by_bundle and not reason:
        raise PreparedSyncError(
            "--large-hydroshare-removal-reason is required when overriding "
            "the prepared bundle's HydroShare removal guard"
        )

    if allowed_by_bundle:
        source = "prepared_generation"
    elif apply_override:
        source = "apply_override"
    else:
        source = "blocked"
    return {
        "allowed": allowed_by_bundle or apply_override,
        "source": source,
        "reason": reason or None,
    }


def _database_command(
    *,
    artifacts: Path,
    chunks: Path,
    artifact_type: int,
    result_file: Path,
    require_summaries: bool,
    skip_embeddings: bool,
    reconcile_hydroshare_snapshot: bool = False,
    allow_large_hydroshare_removals: bool = False,
) -> list[str]:
    command = [
        sys.executable,
        "Andres_implementation/process_delta.py",
        "--artifacts",
        str(artifacts),
        "--chunks",
        str(chunks),
        "--expected-artifact-type",
        str(artifact_type),
        "--result-file",
        str(result_file),
    ]
    if reconcile_hydroshare_snapshot:
        command.append("--reconcile-hydroshare-snapshot")
    else:
        command.extend(
            ["--reconcile-snapshot-artifact-type", str(artifact_type)]
        )
    if allow_large_hydroshare_removals:
        command.append("--allow-large-hydroshare-removals")
    if artifact_type == 4:
        command.append("--ensure-repository-chunk-types")
    if require_summaries:
        command.append("--require-summaries")
    if skip_embeddings:
        command.append("--skip-embeddings")
    return command


def main() -> int:
    parser = argparse.ArgumentParser(
        description=(
            "Validate and apply a frozen synchronization bundle without "
            "re-running source downloads or OpenAI summarization."
        )
    )
    parser.add_argument(
        "--bundle",
        help="Prepared bundle directory or sync ID. Defaults to latest.",
    )
    parser.add_argument(
        "--execute",
        action="store_true",
        help="Required safety flag. Without it, only validate and preview.",
    )
    parser.add_argument(
        "--skip-embeddings",
        action="store_true",
        help="Apply rows/chunks without calling the embeddings API.",
    )
    parser.add_argument(
        "--allow-pending-summaries",
        action="store_true",
        help="Allow a bundle that was prepared with missing summaries.",
    )
    parser.add_argument(
        "--allow-large-hydroshare-removals",
        action="store_true",
        help=(
            "Override the bundle guard for a reviewed target-specific "
            "HydroShare removal. Requires a recorded reason when the "
            "prepared generation did not already allow large removals."
        ),
    )
    parser.add_argument(
        "--large-hydroshare-removal-reason",
        help="Reason recorded when using the target-specific removal override.",
    )
    args = parser.parse_args()

    bundle_dir = resolve_prepared_bundle(ROOT, args.bundle)
    validated = validate_prepared_bundle(bundle_dir)
    manifest = validated["manifest"]
    files = validated["files"]
    if manifest.get("allow_pending_summaries") and not args.allow_pending_summaries:
        raise PreparedSyncError(
            "Bundle permits pending summaries; explicitly pass "
            "--allow-pending-summaries to apply it"
        )
    hydroshare_removal_policy = _resolve_hydroshare_removal_policy(
        manifest,
        apply_override=args.allow_large_hydroshare_removals,
        override_reason=args.large_hydroshare_removal_reason,
    )

    print(f"Prepared bundle: {bundle_dir}")
    print(f"Source sync ID:  {manifest.get('sync_id')}")
    print(f"Validation:      {validated['validation']}")
    print(
        "GitHub repositories: "
        f"{'included' if manifest.get('include_github_repositories') else 'not included'}"
    )
    print(
        "HydroShare resources: "
        f"{'included' if manifest.get('include_hydroshare_resources') else 'not included'}"
    )
    if manifest.get("include_hydroshare_resources"):
        print(
            "Large HydroShare removals: "
            + (
                f"allowed ({hydroshare_removal_policy['source']})"
                if hydroshare_removal_policy["allowed"]
                else "blocked"
            )
        )
        if hydroshare_removal_policy["reason"]:
            print(
                "HydroShare removal reason: "
                f"{hydroshare_removal_policy['reason']}"
            )
    if not args.execute:
        print("Database update: preview only; pass --execute to apply this bundle.")
        return 0

    apply_id = new_sync_id()
    application_dir = bundle_dir / "applications" / f"apply_{apply_id}"
    report_path = application_dir / "application_report.json"
    report: dict[str, Any] = {
        "schema_version": 1,
        "apply_id": apply_id,
        "source_sync_id": manifest.get("sync_id"),
        "bundle": str(bundle_dir),
        "status": "running",
        "started_at": utc_now_iso(),
        "skip_embeddings": args.skip_embeddings,
        "hydroshare_removal_policy": hydroshare_removal_policy,
        "allow_large_hydroshare_removals": hydroshare_removal_policy[
            "allowed"
        ],
        "steps": [],
    }
    _write_json_atomic(report_path, report)

    steps = [
        (
            "docuhub",
            _database_command(
                artifacts=files["docuhub_artifacts"],
                chunks=files["docuhub_chunks"],
                artifact_type=1,
                result_file=application_dir / "docuhub_db_result.json",
                require_summaries=not args.allow_pending_summaries,
                skip_embeddings=args.skip_embeddings,
            ),
            application_dir / "docuhub_db_result.json",
        )
    ]
    if manifest.get("include_github_repositories"):
        steps.append(
            (
                "github_repositories",
                _database_command(
                    artifacts=files["github_artifacts"],
                    chunks=files["github_chunks"],
                    artifact_type=4,
                    result_file=application_dir / "github_db_result.json",
                    require_summaries=not args.allow_pending_summaries,
                    skip_embeddings=args.skip_embeddings,
                ),
                application_dir / "github_db_result.json",
            )
        )
    if manifest.get("include_hydroshare_resources"):
        steps.append(
            (
                "hydroshare_resources",
                _database_command(
                    artifacts=files["hydroshare_artifacts"],
                    chunks=files["hydroshare_chunks"],
                    artifact_type=3,
                    result_file=application_dir / "hydroshare_db_result.json",
                    require_summaries=False,
                    skip_embeddings=args.skip_embeddings,
                    reconcile_hydroshare_snapshot=True,
                    allow_large_hydroshare_removals=(
                        hydroshare_removal_policy["allowed"]
                    ),
                ),
                application_dir / "hydroshare_db_result.json",
            )
        )

    try:
        for name, command, result_path in steps:
            print(f"[database] Applying prepared {name} snapshot...")
            completed = subprocess.run(command, cwd=ROOT, check=False)
            step_report = {
                "name": name,
                "returncode": completed.returncode,
                "result_file": str(result_path),
                "result": _load_result(result_path),
            }
            report["steps"].append(step_report)
            _write_json_atomic(report_path, report)
            if completed.returncode != 0:
                raise RuntimeError(
                    f"Prepared {name} database step failed with exit code "
                    f"{completed.returncode}"
                )
    except BaseException as exc:
        report["status"] = "failed"
        report["completed_at"] = utc_now_iso()
        report["error"] = str(exc)
        _write_json_atomic(report_path, report)
        print(f"Application failed. The prepared bundle is unchanged: {bundle_dir}")
        print(f"Retry report: {report_path}")
        raise

    report["status"] = "completed"
    report["completed_at"] = utc_now_iso()
    _write_json_atomic(report_path, report)
    print(f"Prepared synchronization applied successfully: {report_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
