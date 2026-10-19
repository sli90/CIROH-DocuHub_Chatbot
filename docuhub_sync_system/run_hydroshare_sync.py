"""Command-line entry point for HydroShare artifact/chunk generation."""
from __future__ import annotations

import argparse
import json
from pathlib import Path

from dotenv import load_dotenv

from hydroshare_sync import synchronize_hydroshare_resources


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Build incremental HydroShare artifacts and chunks without updating a DB."
    )
    parser.add_argument(
        "--root",
        type=Path,
        default=Path(__file__).resolve().parent,
        help="Synchronization system root (defaults to this script's directory).",
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="Rebuild all discovered resources even when fingerprints are unchanged.",
    )
    parser.add_argument(
        "--allow-large-removals",
        action="store_true",
        help=(
            "Allow a severely reduced but non-empty discovery result to replace "
            "the previous snapshot. Empty discovery is always refused. Use only "
            "after verifying the removals are intentional."
        ),
    )
    args = parser.parse_args()
    load_dotenv(args.root / ".env")
    report = synchronize_hydroshare_resources(
        args.root,
        force=args.force,
        allow_large_removals=args.allow_large_removals,
    )
    print(json.dumps(report, indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
