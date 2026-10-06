"""Package this repo into one zip to upload to AWS CloudShell.

For deploying without AWS credentials on your laptop (no access portal /
access keys): everything AWS-side runs in CloudShell, the terminal built
into the AWS console, and this script prepares what it needs. Runs on your
laptop, needs NO AWS access:

  1. builds the website (frontend/dist) for production,
  2. exports the knowledge-base corpus from the Azure database (CloudShell
     cannot reach Azure through its firewall, your laptop can),
  3. zips the code CloudShell needs + those two outputs into
     ciroh-cloudshell.zip (secrets such as .env are never included).

Usage (repo root, backend venv active):
    python scripts/make_cloudshell_bundle.py
    python scripts/make_cloudshell_bundle.py --skip-corpus    # code-only update, keep the data you already loaded
    python scripts/make_cloudshell_bundle.py --skip-frontend

See docs/AWS_DEPLOYMENT_CLOUDSHELL.md.
"""

from __future__ import annotations

import argparse
import os
import subprocess
import sys
import zipfile
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
FRONTEND_DIR = REPO_ROOT / "frontend"
CORPUS_FILE = REPO_ROOT / "backend" / "database" / "corpus_export.json.gz"
OUTPUT_ZIP = REPO_ROOT / "ciroh-cloudshell.zip"

# Only what CloudShell needs to deploy and load data. Everything else
# (scraped source data, notebooks, frontend sources) stays on the laptop,
# since CloudShell's home directory is limited to 1 GB.
INCLUDE_PREFIXES = (
    "backend/aws/",
    "backend/database/",
    "backend/rag/",
    "backend/requirements-lambda.txt",
    "backend/__init__.py",
    "infra/",
    "scripts/",
    "docs/",
    "env-template.txt",
    "README.md",
)
# backend/database/json/ and CIROH-Hub/ ARE included: build_corpus_from_json.py
# rebuilds the knowledge base from them in CloudShell when there is no
# Azure access.
EXCLUDE_PARTS = (
    "backend/database/GitHub-CIROH-CodeRepos/",
    "backend/database/HydroShare-CIROH-Datasets/",
    "__pycache__/",
    "cdk.out/",
    ".venv/",
)
EXCLUDE_SUFFIXES = (".ipynb", ".pyc", ".csv", ".checkpoint.json", "hub_summaries_cache.json")
NEVER_INCLUDE = (".env",)


def run(cmd: list[str], cwd: Path, env: dict | None = None) -> None:
    print(f"$ {' '.join(cmd)}  (in {cwd.name})")
    result = subprocess.run(cmd, cwd=cwd, env=env, shell=(sys.platform == "win32"))
    if result.returncode != 0:
        sys.exit(f"Command failed: {' '.join(cmd)}")


def build_frontend() -> None:
    env = os.environ.copy()
    env["VITE_API_BASE_URL"] = ""  # same-origin: CloudFront routes /ask to the API
    if not (FRONTEND_DIR / "node_modules").exists():
        run(["npm", "install"], cwd=FRONTEND_DIR, env=env)
    run(["npm", "run", "build"], cwd=FRONTEND_DIR, env=env)


def export_corpus() -> None:
    run(
        [sys.executable, "migrate_to_bedrock.py", "--export", str(CORPUS_FILE)],
        cwd=REPO_ROOT / "backend" / "database",
    )


def repo_files() -> list[str]:
    """Tracked + untracked-but-not-ignored files, as repo-relative paths."""
    out = subprocess.run(
        ["git", "ls-files", "--cached", "--others", "--exclude-standard"],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
        check=True,
    ).stdout
    paths = set(line.strip() for line in out.splitlines() if line.strip())
    return sorted(p for p in paths if (REPO_ROOT / p).is_file())  # skip deleted-but-tracked


def wanted(path: str) -> bool:
    name = path.rsplit("/", 1)[-1]
    if name in NEVER_INCLUDE:
        return False
    if not path.startswith(INCLUDE_PREFIXES):
        return False
    if any(part in path for part in EXCLUDE_PARTS):
        return False
    return not path.endswith(EXCLUDE_SUFFIXES)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--skip-frontend", action="store_true", help="Don't rebuild frontend/dist.")
    parser.add_argument("--skip-corpus", action="store_true", help="Don't export/include the Azure corpus.")
    args = parser.parse_args()

    if not args.skip_frontend:
        build_frontend()
    if not args.skip_corpus:
        export_corpus()

    files = [f for f in repo_files() if wanted(f)]
    dist = FRONTEND_DIR / "dist"
    if dist.exists():
        files += [p.relative_to(REPO_ROOT).as_posix() for p in dist.rglob("*") if p.is_file()]
    else:
        print("WARNING: frontend/dist not found - the website won't be published.")
    if not args.skip_corpus and CORPUS_FILE.exists():
        files.append(CORPUS_FILE.relative_to(REPO_ROOT).as_posix())

    with zipfile.ZipFile(OUTPUT_ZIP, "w", zipfile.ZIP_DEFLATED) as zf:
        for rel in sorted(set(files)):
            if rel.endswith(".sh"):
                # CloudShell's bash fails on Windows (CRLF) line endings.
                data = (REPO_ROOT / rel).read_bytes().replace(b"\r\n", b"\n")
                zf.writestr(f"ciroh/{rel}", data)
            else:
                zf.write(REPO_ROOT / rel, f"ciroh/{rel}")

    size_mb = OUTPUT_ZIP.stat().st_size / 1e6
    print(f"\nCreated {OUTPUT_ZIP} ({len(files)} files, {size_mb:.1f} MB).")
    print("Next: upload it in CloudShell (Actions > Upload file) - see docs/AWS_DEPLOYMENT_CLOUDSHELL.md")


if __name__ == "__main__":
    main()
