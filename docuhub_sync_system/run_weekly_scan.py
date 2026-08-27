"""
Weekly scan pipeline for the CIROH dashboard.
Run once a week (e.g. via Windows Task Scheduler or cron) so the dashboard stays up to date.

Steps:
  1. Pull latest ciroh_hub from GitHub (download_repo.py)
  2. Update local repo change tracking (check_changes.py)
  3. Update external README tracking and downloads (external_repo_checker.py)
  4. POST to backend to regenerate the mixed docs folder
  5. Generate formatted JSON files for RAG/chatbot (generate_formatted_files.py)

Set DASHBOARD_API_BASE (default http://127.0.0.1:8001) if the backend runs elsewhere.
"""
import os
import json
import sys
import urllib.request
from pathlib import Path

from sync_accounting import (
    build_synchronization_report,
    new_sync_id,
    utc_now_iso,
    write_synchronization_report,
)
from sync_pipeline import (
    SyncStepError,
    callback_step,
    generation_step,
    repository_sync_steps,
    run_sync_steps,
)

ROOT = os.path.abspath(os.path.dirname(__file__))
API_BASE = os.environ.get("DASHBOARD_API_BASE", "http://127.0.0.1:8001")
FORMATTED_DIR = Path(ROOT) / "dashboard" / "formated_files"


def post_export_markdown_folder():
    url = f"{API_BASE.rstrip('/')}/api/export-markdown-folder"
    print(f"[run] POST {url}")
    try:
        req = urllib.request.Request(url, method="POST")
        with urllib.request.urlopen(req, timeout=600) as resp:
            body = resp.read().decode("utf-8")
            print(f"[run] {resp.status} {body[:200]}")
            return {"status": resp.status, "response": body[:200]}
    except Exception as e:
        raise RuntimeError(f"POST {url} failed: {e}") from e


def main():
    sync_id = new_sync_id()
    started_at = utc_now_iso()
    print("Weekly scan started.")
    completed_steps: set[str] = set()
    failure: SyncStepError | None = None
    steps = [
        *repository_sync_steps(root=ROOT),
        callback_step(
            4,
            "merge_documents",
            "Merging documents...",
            post_export_markdown_folder,
        ),
        generation_step(5, root=ROOT, summarize=True),
    ]
    try:
        run_sync_steps(
            steps,
            on_step_start=lambda step: print(f"[step {step.number}] {step.label}"),
            on_step_complete=lambda result: completed_steps.add(result.key),
        )
    except SyncStepError as exc:
        failure = exc
        print(str(exc), file=sys.stderr)

    generation_report = {}
    generation_report_path = FORMATTED_DIR / "generation_report.json"
    if "generate_artifacts" in completed_steps and generation_report_path.exists():
        try:
            with open(generation_report_path, "r", encoding="utf-8") as fh:
                generation_report = json.load(fh)
        except (OSError, json.JSONDecodeError):
            pass
    status = "failed" if failure else "completed"
    sync_report = build_synchronization_report(
        sync_id=sync_id,
        mode="weekly_scan",
        started_at=started_at,
        completed_at=utc_now_iso(),
        status=status,
        generation_report=generation_report,
        error=str(failure) if failure else None,
        metadata={
            "completed_steps": sorted(completed_steps),
            "failed_step": failure.step.key if failure else None,
            "database_update_requested": False,
        },
    )
    report_path = write_synchronization_report(FORMATTED_DIR, sync_report)
    usage = sync_report["openai_usage"]
    print(
        f"OpenAI usage: {usage['total_tokens']} tokens; "
        f"estimated cost USD {usage['estimated_cost_usd']}"
    )
    print(f"Synchronization report: {report_path}")

    print("Weekly scan finished." if not failure else "Weekly scan failed.")
    return 0 if not failure else 1


if __name__ == "__main__":
    sys.exit(main())
