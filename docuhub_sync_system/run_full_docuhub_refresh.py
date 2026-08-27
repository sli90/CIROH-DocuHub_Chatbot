"""
Full DocuHub refresh pipeline.

This rebuilds the DocuHub JSON artifacts/chunks from a freshly synced
ciroh_hub repository and refreshed external README downloads.

By default this script does not update the database. Pass --update-db only
after reviewing the generated JSON. The DB update path uses full DocuHub JSON
files and validates that every artifact is idArtifactType=1 before it runs,
so Publication rows are outside this process.
"""
import argparse
import importlib.util
import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urlparse

from sync_accounting import (
    build_synchronization_report,
    new_sync_id,
    utc_now_iso,
    write_synchronization_report,
)
from sync_pipeline import (
    callback_step,
    database_step,
    generation_step,
    repository_sync_steps,
    run_sync_steps,
)

ROOT = Path(__file__).resolve().parent
FORMATTED_DIR = ROOT / "dashboard" / "formated_files"
ARTIFACTS_JSON = FORMATTED_DIR / "artifacts.json"
CHUNKS_JSON = FORMATTED_DIR / "content_chunks.json"
REFRESH_ROOT = ROOT / "local_change_dashboard" / "full_docuhub_refresh"

DOCUHUB_ARTIFACT_TYPE_ID = 1
_SYNC_CONTEXT: dict = {}


def load_dotenv_into_environment(path: Path) -> None:
    if not path.exists():
        return
    with open(path, "r", encoding="utf-8") as fh:
        for raw in fh:
            line = raw.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            key, value = line.split("=", 1)
            key = key.strip()
            value = value.strip().strip('"').strip("'")
            if key and key not in os.environ:
                os.environ[key] = value


def load_json(path: Path):
    with open(path, "r", encoding="utf-8") as fh:
        return json.load(fh)


def normalize_chunks(payload):
    if isinstance(payload, dict):
        return payload.get("chunks", [])
    if isinstance(payload, list):
        return payload
    return []


def validate_docuhub_json(artifacts_path: Path, chunks_path: Path) -> dict:
    artifacts = load_json(artifacts_path)
    chunks = normalize_chunks(load_json(chunks_path))

    if not isinstance(artifacts, list):
        raise SystemExit(f"{artifacts_path} must contain a JSON array")

    non_docuhub = [
        {
            "idArtifact": a.get("idArtifact"),
            "idArtifactType": a.get("idArtifactType"),
            "URL": a.get("URL"),
        }
        for a in artifacts
        if a.get("idArtifactType") != DOCUHUB_ARTIFACT_TYPE_ID
    ]
    if non_docuhub:
        sample = non_docuhub[:5]
        raise SystemExit(
            "Refusing to update DB: artifacts.json contains non-DocuHub "
            f"artifact types. Sample: {sample}"
        )

    urls = [a.get("URL") for a in artifacts]
    missing_urls = [a.get("idArtifact") for a in artifacts if not a.get("URL")]
    if missing_urls:
        raise SystemExit(
            f"Refusing to continue: artifacts without URL: {missing_urls[:10]}"
        )
    seen_urls = set()
    duplicate_urls = set()
    for url in urls:
        if url in seen_urls:
            duplicate_urls.add(url)
        seen_urls.add(url)
    duplicate_urls = sorted(duplicate_urls)
    if duplicate_urls:
        raise SystemExit(
            f"Refusing to continue: duplicate artifact URLs: {duplicate_urls[:5]}"
        )

    publication_urls = []
    for url in urls:
        path = urlparse(url).path.rstrip("/").lower()
        if path == "/publications" or path.startswith("/publications/"):
            publication_urls.append(url)
        elif path == "/docs/publications" or path.startswith("/docs/publications/"):
            publication_urls.append(url)
    if publication_urls:
        raise SystemExit(
            "Refusing to continue: publication URLs are outside the DocuHub "
            f"refresh scope. Sample: {publication_urls[:5]}"
        )

    artifact_source_ids = {a.get("idArtifact") for a in artifacts}
    chunk_source_ids = {c.get("idArtifact") for c in chunks}
    missing_artifacts = sorted(
        chunk_source_ids - artifact_source_ids,
        key=lambda value: "" if value is None else str(value),
    )
    if missing_artifacts:
        raise SystemExit(
            "Refusing to continue: chunks reference missing source artifact "
            f"IDs: {missing_artifacts[:10]}"
        )

    return {
        "artifacts": len(artifacts),
        "chunks": len(chunks),
        "artifact_type": DOCUHUB_ARTIFACT_TYPE_ID,
        "unique_urls": len(set(urls)),
        "artifacts_with_summary": sum(
            1 for artifact in artifacts if artifact.get("summary_data") is not None
        ),
    }


def load_backend_app():
    app_path = ROOT / "dashboard" / "backend" / "app.py"
    spec = importlib.util.spec_from_file_location("ciroh_dashboard_backend_app", app_path)
    if spec is None or spec.loader is None:
        raise SystemExit(f"Could not load backend app module from {app_path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def write_fresh_mixed_docs() -> tuple[Path, dict]:
    backend = load_backend_app()
    stamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    output_root = REFRESH_ROOT / f"mixed_docs_{stamp}"
    manifest_path = REFRESH_ROOT / f"mixed_docs_manifest_{stamp}.json"
    output_root.mkdir(parents=True, exist_ok=True)
    REFRESH_ROOT.mkdir(parents=True, exist_ok=True)

    external = backend._load_external()
    external_map = backend._external_download_map(external)
    external_meta = backend._external_meta_map(external)
    download_root = external.get("download_root") or str(
        ROOT / "local_change_dashboard" / "external_repo_files"
    )

    original_manifest = backend.MIXED_MANIFEST_PATH
    try:
        backend.MIXED_MANIFEST_PATH = str(manifest_path)
        counts = backend._write_mixed_markdown(
            str(output_root),
            external_map,
            external_meta,
            download_root,
            external.get("last_checked"),
            force=True,
        )
    finally:
        backend.MIXED_MANIFEST_PATH = original_manifest

    return output_root, counts


def write_completed_sync_report(
    *,
    sync_id: str,
    started_at: str,
    include_db: bool,
    metadata: dict,
) -> Path:
    generation_report = load_json(FORMATTED_DIR / "generation_report.json")
    db_report = None
    if include_db:
        db_report = load_json(FORMATTED_DIR / "db_update_result.json")
    report = build_synchronization_report(
        sync_id=sync_id,
        mode="full_docuhub_refresh",
        started_at=started_at,
        completed_at=utc_now_iso(),
        status="completed",
        generation_report=generation_report,
        db_report=db_report,
        metadata=metadata,
    )
    history_path = write_synchronization_report(FORMATTED_DIR, report)
    usage = report["openai_usage"]
    print(
        "[usage] "
        f"tokens={usage['total_tokens']}, "
        f"estimated_cost_usd={usage['estimated_cost_usd']}"
    )
    print(f"[report] {history_path}")
    return history_path


def _mtime_ns(path: Path) -> int | None:
    try:
        return path.stat().st_mtime_ns
    except OSError:
        return None


def write_failed_sync_report(error: BaseException) -> Path | None:
    """Write partial usage only from reports changed by the current run."""
    if not _SYNC_CONTEXT:
        return None

    generation_report = None
    db_report = None
    generation_path = FORMATTED_DIR / "generation_report.json"
    db_path = FORMATTED_DIR / "db_update_result.json"
    if _mtime_ns(generation_path) != _SYNC_CONTEXT.get("generation_mtime_ns"):
        try:
            generation_report = load_json(generation_path)
        except (OSError, json.JSONDecodeError):
            pass
    if (
        _SYNC_CONTEXT.get("include_db")
        and _mtime_ns(db_path) != _SYNC_CONTEXT.get("db_mtime_ns")
    ):
        try:
            db_report = load_json(db_path)
        except (OSError, json.JSONDecodeError):
            pass

    report = build_synchronization_report(
        sync_id=_SYNC_CONTEXT["sync_id"],
        mode="full_docuhub_refresh",
        started_at=_SYNC_CONTEXT["started_at"],
        completed_at=utc_now_iso(),
        status="failed",
        generation_report=generation_report,
        db_report=db_report,
        error=str(error),
        metadata={"database_update_requested": _SYNC_CONTEXT.get("include_db", False)},
    )
    history_path = write_synchronization_report(FORMATTED_DIR, report)
    print(f"[report] failed synchronization: {history_path}", file=sys.stderr)
    return history_path


def main() -> int:
    global _SYNC_CONTEXT
    parser = argparse.ArgumentParser(
        description="Refresh DocuHub repo, external README content, and JSON artifacts."
    )
    parser.add_argument(
        "--update-db",
        action="store_true",
        help="After JSON generation, update DocuHub rows in the DB using full files.",
    )
    parser.add_argument(
        "--skip-summarize",
        action="store_true",
        help="Generate JSON without calling the LLM summarizer.",
    )
    parser.add_argument(
        "--use-github-token",
        action="store_true",
        help="Use GITHUB_TOKEN from the environment/.env for GitHub API calls.",
    )
    parser.add_argument(
        "--skip-embeddings",
        action="store_true",
        help="When --update-db is used, skip embedding generation.",
    )
    parser.add_argument(
        "--allow-pending-summaries",
        action="store_true",
        help="Allow --update-db even when generation_report has pending summaries.",
    )
    args = parser.parse_args()
    sync_id = new_sync_id()
    started_at = utc_now_iso()
    _SYNC_CONTEXT = {
        "sync_id": sync_id,
        "started_at": started_at,
        "include_db": args.update_db,
        "generation_mtime_ns": _mtime_ns(FORMATTED_DIR / "generation_report.json"),
        "db_mtime_ns": _mtime_ns(FORMATTED_DIR / "db_update_result.json"),
    }

    if not args.use_github_token:
        # The repo is public in this workflow. Masking the token prevents a
        # stale local GITHUB_TOKEN from causing GitHub API 401 responses.
        os.environ["CIROH_IGNORE_GITHUB_TOKEN"] = "1"
        os.environ["GITHUB_TOKEN"] = ""
    else:
        load_dotenv_into_environment(ROOT / ".env")

    # Let child git commands operate on the local synced checkout without
    # requiring a global safe.directory change for this sandbox user.
    os.environ.setdefault("GIT_CONFIG_COUNT", "1")
    os.environ.setdefault("GIT_CONFIG_KEY_0", "safe.directory")
    os.environ.setdefault("GIT_CONFIG_VALUE_0", str(ROOT / "ciroh_hub"))

    state: dict = {}

    def merge_documents() -> dict:
        mixed_docs, mixed_counts = write_fresh_mixed_docs()
        state["mixed_docs"] = mixed_docs
        state["mixed_counts"] = mixed_counts
        print(f"[mixed_docs] {mixed_docs}")
        print(f"[mixed_docs] {mixed_counts}")
        return {"path": str(mixed_docs), "counts": mixed_counts}

    def validate_generated_json() -> dict:
        summary = validate_docuhub_json(ARTIFACTS_JSON, CHUNKS_JSON)
        state["validation"] = summary
        print(f"[validate] DocuHub-only JSON: {summary}")

        report = load_json(FORMATTED_DIR / "generation_report.json")
        pending_summaries = len(report.get("pending_summaries") or [])
        summary_errors = len(report.get("summary_errors") or [])
        state["pending_summaries"] = pending_summaries
        state["summary_errors"] = summary_errors
        if pending_summaries or summary_errors:
            print(
                "[validate] summaries incomplete: "
                f"pending={pending_summaries}, errors={summary_errors}"
            )
        if (
            args.update_db
            and pending_summaries
            and not args.allow_pending_summaries
        ):
            raise RuntimeError(
                "Refusing DB update: generated artifacts have pending summaries. "
                "Fix the summarization quota/key and rerun, or pass "
                "--allow-pending-summaries if null summary_data is intentional."
            )
        return {
            "validation": summary,
            "pending_summaries": pending_summaries,
            "summary_errors": summary_errors,
        }

    steps = [
        *repository_sync_steps(root=ROOT),
        callback_step(
            4, "merge_documents", "Merging documents...", merge_documents
        ),
        generation_step(
            5,
            mixed_docs=lambda: state["mixed_docs"],
            output_dir=FORMATTED_DIR,
            summarize=not args.skip_summarize,
            root=ROOT,
        ),
        callback_step(
            6,
            "validate_generated_json",
            "Validating generated DocuHub JSON...",
            validate_generated_json,
        ),
    ]
    if args.update_db:
        steps.append(
            database_step(
                7,
                artifacts=ARTIFACTS_JSON,
                chunks=CHUNKS_JSON,
                deactivate_active_artifact_type=DOCUHUB_ARTIFACT_TYPE_ID,
                skip_embeddings=args.skip_embeddings,
                root=ROOT,
            )
        )

    run_sync_steps(
        steps,
        on_step_start=lambda step: print(f"[step {step.number}] {step.label}"),
    )

    if not args.update_db:
        print("[db] skipped. Pass --update-db to refresh DocuHub DB rows.")

    write_completed_sync_report(
        sync_id=sync_id,
        started_at=started_at,
        include_db=args.update_db,
        metadata={
            "database_update_requested": args.update_db,
            "summarization_requested": not args.skip_summarize,
            "embeddings_requested": args.update_db and not args.skip_embeddings,
            "mixed_docs": str(state["mixed_docs"]),
            "mixed_doc_counts": state["mixed_counts"],
            "validation": state["validation"],
        },
    )
    return 0


if __name__ == "__main__":
    try:
        exit_code = main()
    except BaseException as exc:
        try:
            write_failed_sync_report(exc)
        except Exception as report_exc:
            print(f"[report] could not write failure report: {report_exc}", file=sys.stderr)
        raise
    raise SystemExit(exit_code)
