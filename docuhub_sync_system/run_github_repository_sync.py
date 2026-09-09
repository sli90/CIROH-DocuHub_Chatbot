"""Guarded CLI for CIROH GitHub repository artifact generation."""
from __future__ import annotations

import argparse
import os
from pathlib import Path

from dotenv import load_dotenv

from github_repository_sync import (
    DEFAULT_OWNER,
    GitHubClient,
    RepositorySyncConfig,
    synchronize_repository_artifacts,
)


ROOT = Path(__file__).resolve().parent


def main() -> int:
    parser = argparse.ArgumentParser(
        description=(
            "Download selected CIROH GitHub repository content and generate "
            "repository artifacts, LLM descriptions, and RAG chunks. This never "
            "updates the DB."
        )
    )
    parser.add_argument(
        "--execute",
        action="store_true",
        help="Required safety flag. Without it, no GitHub or OpenAI calls are made.",
    )
    parser.add_argument("--owner", default=DEFAULT_OWNER)
    parser.add_argument(
        "--force",
        action="store_true",
        help="Re-download and re-summarize repositories even when their SHA is unchanged.",
    )
    parser.add_argument(
        "--skip-summaries",
        action="store_true",
        help=(
            "Build repository snapshots/artifacts/chunks without calling OpenAI; "
            "ambiguous chunks use Documentation Section."
        ),
    )
    args = parser.parse_args()

    if not args.execute:
        parser.error(
            "No work performed. Pass --execute only when you are ready to call "
            "GitHub and, unless --skip-summaries is set, OpenAI."
        )

    load_dotenv(ROOT / ".env")
    summarize = not args.skip_summaries
    llm_client = None
    if summarize:
        from openai import OpenAI

        llm_client = OpenAI()

    report = synchronize_repository_artifacts(
        RepositorySyncConfig(root=ROOT, owner=args.owner),
        GitHubClient(token=os.getenv("GITHUB_TOKEN") or None),
        llm_client=llm_client,
        summarize=summarize,
        force=args.force,
    )
    usage = report["openai_usage"]
    print(
        "GitHub repository artifact generation complete: "
        f"artifacts={report['total_artifacts']}, "
        f"chunks={report['total_chunks']}, "
        f"summarized={report['summarized_count']}, "
        f"tokens={usage['total_tokens']}, "
        f"estimated_cost_usd={usage['estimated_cost_usd']}"
    )
    print("Database update: skipped by design.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
