"""
One-time backfill of correct git-based last_updated dates.

The original pipeline downloaded the repo as a ZIP (no .git),
so _git_last_commit_date always returned None and fell back to
filesystem mtime (= the date the pipeline ran). This script
corrects those dates using real git commit history.

Usage:
    1. Ensure ciroh_hub/ is a git clone (run download_repo.py)
    2. python Andres_implementation/fix_last_updated.py
       or: python Andres_implementation/fix_last_updated.py --dry-run
"""
from __future__ import annotations

import json
import os
import re
import subprocess
import sys
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from database import DatabaseManager  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
REPO_DIR = ROOT / "ciroh_hub"
MIXED_DOCS = ROOT / "local_change_dashboard" / "mixed_docs"
EXTERNAL_REPOS_JSON = ROOT / "local_change_dashboard" / "external_repos.json"
BASE_URL = "https://docs.ciroh.org"

SKIP_DIRS = {".github", "node_modules", "__pycache__", ".git"}
SKIP_FILES = {
    "README.md", "CHANGELOG.md", "CONTRIBUTING.md", "SECURITY.md",
    "INSTALL.md", "GITHUB_LOGIN_FLOW.md", "release-notes-template.mdx",
    "RESOURCES_PAGE_DOCUMENTATION.md",
}


# ── frontmatter parsing (mirrors generate_formatted_files.py) ───────────────

def parse_frontmatter(text: str) -> dict:
    if not text.startswith("---"):
        return {}
    end = text.find("\n---", 3)
    if end == -1:
        return {}
    block = text[3:end].strip()
    try:
        import yaml
        return yaml.safe_load(block) or {}
    except Exception:
        pass
    fm: dict = {}
    for line in block.split("\n"):
        line = line.strip()
        if not line or line.startswith("#") or ":" not in line:
            continue
        key, _, val = line.partition(":")
        fm[key.strip()] = val.strip().strip('"').strip("'")
    return fm


# ── URL construction (mirrors generate_formatted_files.py) ──────────────────

def build_url(fm: dict, rel_path: str) -> str:
    section = rel_path.split("/")[0] if "/" in rel_path else ""
    slug = fm.get("slug")
    if slug and section in ("blog", "release-notes"):
        return f"{BASE_URL}/{section}/{slug}/"
    path = fm.get("path", "")
    if path:
        for suffix in ("/index", "/intro"):
            if path.endswith(suffix):
                path = path[: -len(suffix)]
                break
        return f"{BASE_URL}/{path}/"
    p = rel_path.replace("\\", "/")
    p = re.sub(r"\.(mdx?|md)$", "", p)
    if p.endswith("/index") or p.endswith("/intro"):
        p = p.rsplit("/", 1)[0]
    return f"{BASE_URL}/{p}/"


# ── git date lookup ─────────────────────────────────────────────────────────

def git_last_commit_date(
    repo_root: Path, rel_path: str,
) -> datetime | None:
    if not (repo_root / ".git").is_dir():
        return None
    try:
        cmd = [
            "git", "-C", str(repo_root),
            "log", "-1", "--format=%cI", "--", rel_path,
        ]
        result = subprocess.run(
            cmd, capture_output=True, text=True, timeout=10,
        )
        iso = result.stdout.strip()
        if not iso:
            return None
        return datetime.fromisoformat(iso)
    except Exception:
        return None


# ── external refs ───────────────────────────────────────────────────────────

_ATTR_RE = re.compile(r'(\w+)\s*=\s*["\']([^"\']*)["\']')


def extract_github_readme_refs(text: str) -> list[dict]:
    refs = []
    pat = (r"<GitHubReadme\b[^>]*\/>"
           r"|<GitHubReadme\b[^>]*>.*?</GitHubReadme>")
    pattern = re.compile(pat, re.S)
    for match in pattern.finditer(text or ""):
        tag = match.group(0)
        attrs = {m.group(1): m.group(2) for m in _ATTR_RE.finditer(tag)}
        owner = (attrs.get("username") or "").strip()
        repo = (attrs.get("repo") or "").strip()
        if not owner or not repo:
            continue
        file_path = (attrs.get("path") or "").strip().lstrip("/")
        subfolder = (attrs.get("subfolder") or "").strip().strip("/")
        readme_name = (attrs.get("readmeFileName") or "").strip()
        if not file_path:
            if readme_name:
                file_path = readme_name
                if subfolder:
                    file_path = f"{subfolder}/{file_path}"
            elif subfolder:
                file_path = f"{subfolder}/README.md"
            else:
                file_path = "README.md"
        refs.append({"repo": f"{owner}/{repo}", "path": file_path})
    return refs


def load_external_meta() -> dict:
    if not EXTERNAL_REPOS_JSON.exists():
        return {}
    try:
        with open(EXTERNAL_REPOS_JSON, "r", encoding="utf-8") as f:
            data = json.load(f)
    except (OSError, json.JSONDecodeError):
        return {}
    meta: dict = {}
    for entry in data.get("rendered_files") or []:
        repo = entry.get("external_repo")
        tracked = entry.get("tracked_path") or "README.md"
        if not repo:
            continue
        key = (repo, tracked)
        commit_date = entry.get("latest_commit_date")
        existing = meta.get(key, {})
        if commit_date or not existing.get("latest_commit_date"):
            existing["latest_commit_date"] = commit_date
        meta[key] = existing
    return meta


def _parse_iso(s: str | None) -> datetime | None:
    if not s:
        return None
    try:
        return datetime.fromisoformat(s)
    except Exception:
        return None


def compute_last_updated(
    rel_path: str,
    content: str,
    external_meta: dict,
) -> datetime | None:
    """Same logic as app.py _compute_last_updated, but against the cloned repo."""
    refs = extract_github_readme_refs(content)
    external_dates = []
    for ref in refs:
        meta = external_meta.get((ref["repo"], ref["path"]), {})
        dt = _parse_iso(meta.get("latest_commit_date"))
        if dt:
            external_dates.append(dt)
    external_latest = max(external_dates) if external_dates else None

    local_dt = git_last_commit_date(REPO_DIR, rel_path)

    if external_latest and local_dt:
        return max(external_latest, local_dt)
    return external_latest or local_dt


# ── file walking ────────────────────────────────────────────────────────────

def walk_markdown_files(root: Path):
    for dirpath, dirs, filenames in os.walk(root):
        dirs[:] = [d for d in dirs if d not in SKIP_DIRS]
        for fname in sorted(filenames):
            if fname in SKIP_FILES:
                continue
            if not fname.endswith((".md", ".mdx")):
                continue
            abs_path = Path(dirpath) / fname
            rel_path = str(abs_path.relative_to(root)).replace("\\", "/")
            yield rel_path, abs_path


# ── main ────────────────────────────────────────────────────────────────────

def main():
    dry_run = "--dry-run" in sys.argv

    if not (REPO_DIR / ".git").is_dir():
        print(f"ERROR: {REPO_DIR} is not a git repository.")
        print("Run the updated download_repo.py first to clone with git history.")
        sys.exit(1)

    print("Loading external repo metadata ...")
    external_meta = load_external_meta()
    print(f"  {len(external_meta)} external ref entries loaded.")

    source_dir = MIXED_DOCS if MIXED_DOCS.is_dir() else REPO_DIR
    print(f"Walking files in {source_dir} ...")

    url_to_date: dict[str, datetime] = {}
    for rel_path, abs_path in walk_markdown_files(source_dir):
        try:
            content = abs_path.read_text(encoding="utf-8")
        except OSError:
            continue
        fm = parse_frontmatter(content)
        url = build_url(fm, rel_path)
        dt = compute_last_updated(rel_path, content, external_meta)
        if dt:
            if dt.tzinfo is not None:
                dt = dt.replace(tzinfo=None)
            url_to_date[url] = dt

    print(f"  Computed dates for {len(url_to_date)} URLs.")

    print("Querying database for active artifacts ...")
    with DatabaseManager() as db:
        q = (
            "SELECT idartifact, url, last_updated "
            "FROM tblartifacts WHERE isactive = TRUE;"
        )
        rows = db.execute_query(q, fetch=True) or []
        print(f"  {len(rows)} active artifacts in DB.")

        updates = []
        for row in rows:
            url = row["url"]
            db_date = row["last_updated"]
            correct_date = url_to_date.get(url)
            if correct_date is None:
                continue
            if db_date is not None and db_date == correct_date:
                continue
            updates.append((correct_date, url, row["idartifact"], db_date))

        print(f"  {len(updates)} artifacts need date correction.")

        if not updates:
            print("Nothing to update. Done.")
            return

        if dry_run:
            print("\n[DRY RUN] Would update:")
            for correct, url, aid, old in updates[:20]:
                print(f"  id={aid}  {old} -> "
                      f"{correct}  {url}")
            if len(updates) > 20:
                extra = len(updates) - 20
                print(f"  ... and {extra} more.")
            return

        UPDATE_Q = (
            "UPDATE tblartifacts "
            "SET last_updated = %s "
            "WHERE idartifact = %s;"
        )
        for correct, url, aid, old in updates:
            db.execute_query(UPDATE_Q, (correct, aid))

        print(f"  Updated {len(updates)} artifacts.")
        print("Done.")


if __name__ == "__main__":
    main()
