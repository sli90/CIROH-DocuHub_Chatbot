import argparse
import hashlib
import json
import os
import re
import sys
import shutil
import urllib.parse
import urllib.request
from datetime import datetime, timezone


EXCLUDES = {
    ".git",
    ".hg",
    ".svn",
    ".idea",
    ".vscode",
    "node_modules",
    "__pycache__",
    ".pytest_cache",
    ".mypy_cache",
    ".venv",
    "venv",
    "dist",
    "build",
    ".next",
    ".cache",
    "coverage",
}

SCAN_EXTENSIONS = {".mdx", ".md", ".js", ".jsx", ".tsx"}
LOCAL_DOC_EXTENSIONS = {".mdx", ".md"}
EXCLUDED_CONTENT_PREFIXES = {
    "docs/publications/",
    "src/pages/publications/",
}

PATH_ALIASES = {
    ("CIROH-UA/datastreamCLI", "python_tools/README.md"): "src/datastreamcli/README.md",
    (
        "CIROH-UA/ngen-datastream",
        "docs/nrds/CONTRIBUTE.md",
    ): "docs/nrds/contribute/CONTRIBUTING.md",
}


def _wiki_page_name(path):
    page = (path or "home").strip().strip("/")
    if page.endswith(".md"):
        page = page[:-3]
    return page or "home"


def _wiki_tracked_path(path):
    return f"wiki/{_wiki_page_name(path)}.md"

def _load_dotenv(path):
    if not path or not os.path.exists(path):
        return
    try:
        with open(path, "r", encoding="utf-8") as f:
            for raw in f:
                line = raw.strip()
                if not line or line.startswith("#") or "=" not in line:
                    continue
                key, value = line.split("=", 1)
                key = key.strip()
                value = value.strip().strip('"').strip("'")
                if key and key not in os.environ:
                    os.environ[key] = value
    except OSError:
        return


def _headers():
    headers = {"User-Agent": "Python"}
    token = None
    if os.environ.get("CIROH_IGNORE_GITHUB_TOKEN") != "1":
        token = os.environ.get("GITHUB_TOKEN")
    if token:
        headers["Authorization"] = f"Bearer {token}"
    return headers


def _get_json(url):
    req = urllib.request.Request(url, headers=_headers())
    with urllib.request.urlopen(req, timeout=60) as resp:
        return json.loads(resp.read().decode("utf-8"))

def _get_raw(url):
    headers = _headers()
    headers["Accept"] = "application/vnd.github.v3.raw"
    req = urllib.request.Request(url, headers=headers)
    with urllib.request.urlopen(req, timeout=60) as resp:
        return resp.read()


def _iter_source_files(root):
    for dirpath, dirnames, filenames in os.walk(root):
        dirnames[:] = [d for d in dirnames if d not in EXCLUDES]
        for name in filenames:
            _, ext = os.path.splitext(name)
            if ext.lower() in SCAN_EXTENSIONS:
                path = os.path.join(dirpath, name)
                rel_path = os.path.relpath(path, root).replace("\\", "/")
                if any(rel_path.startswith(prefix) for prefix in EXCLUDED_CONTENT_PREFIXES):
                    continue
                yield path


def _iter_local_docs(root):
    for dirpath, dirnames, filenames in os.walk(root):
        dirnames[:] = [d for d in dirnames if d not in EXCLUDES]
        for name in filenames:
            _, ext = os.path.splitext(name)
            if ext.lower() in LOCAL_DOC_EXTENSIONS:
                path = os.path.join(dirpath, name)
                rel_path = os.path.relpath(path, root).replace("\\", "/")
                if any(rel_path.startswith(prefix) for prefix in EXCLUDED_CONTENT_PREFIXES):
                    continue
                yield path


_ATTR_RE = re.compile(r'(\w+)\s*=\s*["\']([^"\']+)["\']')


def _extract_repos(path):
    try:
        with open(path, "r", encoding="utf-8") as f:
            content = f.read()
    except OSError:
        return []

    repos = []
    if "GitHubReadme" in content and re.search(r"^\s*import\s+GitHubReadme\b", content, re.M):
        for match in re.finditer(r"<GitHubReadme\b[^>]*>", content):
            tag = match.group(0)
            attrs = {m.group(1): m.group(2) for m in _ATTR_RE.finditer(tag)}
            owner = (attrs.get("username") or "").strip()
            repo = (attrs.get("repo") or "").strip()
            if owner and repo:
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
                repos.append({"repo": f"{owner}/{repo}", "path": file_path, "kind": "readme"})
    if "GitHubWikiPage" in content and re.search(r"^\s*import\s+GitHubWikiPage\b", content, re.M):
        for match in re.finditer(r"<GitHubWikiPage\b[^>]*>", content):
            tag = match.group(0)
            attrs = {m.group(1): m.group(2) for m in _ATTR_RE.finditer(tag)}
            owner = (attrs.get("username") or "").strip()
            repo = (attrs.get("repo") or "").strip()
            if owner and repo:
                repos.append(
                    {
                        "repo": f"{owner}/{repo}",
                        "path": _wiki_tracked_path(attrs.get("path")),
                        "kind": "wiki",
                        "wiki_page": _wiki_page_name(attrs.get("path")),
                    }
                )
    return repos


_REPO_CACHE = {}
_WIKI_RAW_CACHE = {}


def _repo_meta(owner_repo):
    if owner_repo in _REPO_CACHE:
        return _REPO_CACHE[owner_repo]
    repo_url = f"https://api.github.com/repos/{owner_repo}"
    data = _get_json(repo_url)
    _REPO_CACHE[owner_repo] = data
    return data


def _wiki_raw_url(owner_repo, tracked_path):
    page = tracked_path
    if page.startswith("wiki/"):
        page = page[len("wiki/") :]
    if page.endswith(".md"):
        page = page[:-3]
    encoded = urllib.parse.quote(page, safe="/")
    return f"https://raw.githubusercontent.com/wiki/{owner_repo}/{encoded}.md"


def _get_wiki_raw(owner_repo, tracked_path):
    key = (owner_repo, tracked_path)
    if key not in _WIKI_RAW_CACHE:
        _WIKI_RAW_CACHE[key] = _get_raw(_wiki_raw_url(owner_repo, tracked_path))
    return _WIKI_RAW_CACHE[key]


def _latest_commit(owner_repo, file_path):
    if file_path.startswith("wiki/"):
        repo_data = _repo_meta(owner_repo)
        data = _get_wiki_raw(owner_repo, file_path)
        digest = hashlib.sha256(data).hexdigest()
        return {
            "latest_sha": digest,
            "latest_commit_date": None,
            "pushed_at": repo_data.get("pushed_at"),
            "updated_at": repo_data.get("updated_at"),
            "default_branch": repo_data.get("default_branch") or "main",
        }

    commits_url = f"https://api.github.com/repos/{owner_repo}/commits?per_page=1"
    lookup_path = PATH_ALIASES.get((owner_repo, file_path), file_path)
    if lookup_path:
        commits_url += "&" + urllib.parse.urlencode({"path": lookup_path})

    repo_data = _repo_meta(owner_repo)
    commits = _get_json(commits_url)

    latest_sha = None
    latest_date = None
    if commits:
        latest_sha = commits[0].get("sha")
        latest_date = (
            commits[0].get("commit", {})
            .get("committer", {})
            .get("date")
        )

    return {
        "latest_sha": latest_sha,
        "latest_commit_date": latest_date,
        "pushed_at": repo_data.get("pushed_at"),
        "updated_at": repo_data.get("updated_at"),
        "default_branch": repo_data.get("default_branch") or "main",
    }


def _change_state(prev_sha, latest_sha):
    if not prev_sha:
        return None, "baseline"
    if not latest_sha:
        return None, "unknown"
    return (prev_sha != latest_sha), "changed" if prev_sha != latest_sha else "unchanged"


def _load_previous(path):
    if not os.path.exists(path):
        return {}
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except (OSError, json.JSONDecodeError):
        return {}


def _should_resume_download(repo, file_path, prev_lookup, prev_errors, download_root):
    key = f"{repo}:{file_path}"
    if key in prev_errors or f"{key}:download" in prev_errors:
        return True
    prev_data = prev_lookup.get((repo, file_path), {})
    if not isinstance(prev_data, dict):
        return True
    if prev_data.get("download_error"):
        return True
    prev_downloaded = prev_data.get("downloaded_path")
    if not prev_downloaded:
        return True
    if download_root:
        disk_path = os.path.join(download_root, prev_downloaded.replace("/", os.sep))
        if not os.path.exists(disk_path):
            return True
    return False

def _download_readme(owner_repo, file_path, branch, download_root):
    requested_path = file_path.lstrip("/").replace("\\", "/")
    if requested_path.startswith("wiki/"):
        data = _get_wiki_raw(owner_repo, requested_path)
    else:
        safe_path = PATH_ALIASES.get((owner_repo, requested_path), requested_path)
        encoded = urllib.parse.quote(safe_path)
        url = f"https://api.github.com/repos/{owner_repo}/contents/{encoded}?ref={branch}"
        data = _get_raw(url)

    if "/" in owner_repo:
        owner, repo = owner_repo.split("/", 1)
        base_dir = os.path.join(download_root, owner, repo)
    else:
        base_dir = os.path.join(download_root, owner_repo)

    local_rel = requested_path.replace("/", os.sep)
    target_path = os.path.join(base_dir, local_rel)
    os.makedirs(os.path.dirname(target_path), exist_ok=True)
    with open(target_path, "wb") as f:
        f.write(data)

    rel_to_root = os.path.relpath(target_path, download_root).replace("\\", "/")
    return target_path, rel_to_root


def _is_external_doc(path):
    try:
        with open(path, "r", encoding="utf-8") as f:
            content = f.read()
    except OSError:
        return False
    return "GitHubReadme" in content or "GitHubWikiPage" in content


def main():
    project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
    _load_dotenv(os.path.join(project_root, ".env"))
    default_root = os.path.join(project_root, "ciroh_hub")
    default_output = os.path.join(project_root, "local_change_dashboard", "external_repos.json")
    default_download_dir = os.path.join(project_root, "local_change_dashboard", "external_repo_files")

    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--root",
        default=default_root,
        help="Root of the repo to scan for GitHubReadme/GitHubWikiPage usage.",
    )
    parser.add_argument(
        "--output",
        default=default_output,
        help="Where to write the output JSON.",
    )
    parser.add_argument(
        "--download",
        action="store_true",
        help="Download raw content for each tracked external README/wiki file.",
    )
    parser.add_argument(
        "--download-changed",
        action="store_true",
        help="Only download files that changed since the last run (or are missing).",
    )
    parser.add_argument(
        "--download-dir",
        default=default_download_dir,
        help="Where to save downloaded README/wiki files when --download is set.",
    )
    parser.add_argument(
        "--download-local",
        action="store_true",
        help="Copy local docs/products markdown that do not use external GitHub components.",
    )
    parser.add_argument(
        "--local-docs-dir",
        default=os.path.join(project_root, "local_change_dashboard", "local_docs_products"),
        help="Where to save local docs/products files when --download-local is set.",
    )
    parser.add_argument(
        "--resume-failed",
        action="store_true",
        help="Only download files that previously failed or are missing on disk.",
    )
    args = parser.parse_args()

    repo_map = {}
    for path in _iter_source_files(args.root):
        for repo_info in _extract_repos(path):
            key = (repo_info["repo"], repo_info["path"])
            repo_map.setdefault(key, set()).add(os.path.relpath(path, args.root))

    prev = _load_previous(args.output)
    prev_repos = prev.get("repos", {}) if isinstance(prev, dict) else {}
    prev_errors = prev.get("errors", {}) if isinstance(prev, dict) else {}
    prev_lookup = {}
    for repo, data in prev_repos.items():
        if isinstance(data, dict) and "tracked_files" in data:
            for tracked in data.get("tracked_files", []):
                prev_lookup[(repo, tracked.get("path"))] = tracked
        elif isinstance(data, dict):
            prev_lookup[(repo, data.get("path"))] = data

    now_iso = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    results = {}
    errors = {}
    changed_repos = []
    rendered_files = []
    download_root = os.path.abspath(args.download_dir) if args.download else None
    downloaded_count = 0
    local_docs = []
    local_docs_errors = {}
    local_docs_root = os.path.join(args.root, "docs", "products")
    local_docs_download_root = os.path.abspath(args.local_docs_dir) if args.download_local else None

    for repo, file_path in sorted(repo_map.keys()):
        external_kind = "wiki" if file_path.startswith("wiki/") else "readme"
        try:
            latest = _latest_commit(repo, file_path)
            previous = prev_lookup.get((repo, file_path), {})
            prev_sha = previous.get("latest_sha")
            prev_date = previous.get("latest_commit_date")
            changed, change_state = _change_state(prev_sha, latest.get("latest_sha"))
            if changed:
                changed_repos.append(repo)
            downloaded_path = None
            download_error = None
            should_download = args.download and download_root
            if should_download and args.download_changed:
                should_download = (change_state in {"changed", "baseline", "unknown"}) or _should_resume_download(
                    repo,
                    file_path,
                    prev_lookup,
                    prev_errors,
                    download_root,
                )
            if should_download and args.resume_failed and not args.download_changed:
                should_download = _should_resume_download(
                    repo,
                    file_path,
                    prev_lookup,
                    prev_errors,
                    download_root,
                )
            if not should_download:
                downloaded_path = previous.get("downloaded_path")
                download_error = previous.get("download_error")
            if should_download:
                try:
                    _, downloaded_path = _download_readme(
                        repo,
                        file_path,
                        latest.get("default_branch") or "main",
                        download_root,
                    )
                    downloaded_count += 1
                except Exception as exc:
                    download_error = str(exc)
                    errors[f"{repo}:{file_path}:download"] = download_error
            results.setdefault(repo, {"tracked_files": []})
            results[repo]["tracked_files"].append(
                {
                    "path": file_path,
                    "external_kind": external_kind,
                    **latest,
                    "previous_sha": prev_sha,
                    "previous_commit_date": prev_date,
                    "changed": changed,
                    "change_state": change_state,
                    "sources": sorted(repo_map[(repo, file_path)]),
                    "downloaded_path": downloaded_path,
                    "download_error": download_error,
                }
            )
            for src in sorted(repo_map[(repo, file_path)]):
                rendered_files.append(
                    {
                        "path": src,
                        "external_repo": repo,
                        "external_kind": external_kind,
                        "tracked_path": file_path,
                        "changed": changed,
                        "change_state": change_state,
                        "latest_sha": latest.get("latest_sha"),
                        "latest_commit_date": latest.get("latest_commit_date"),
                        "previous_sha": prev_sha,
                        "previous_commit_date": prev_date,
                        "downloaded_path": downloaded_path,
                        "download_error": download_error,
                    }
                )
        except Exception as exc:
            errors[f"{repo}:{file_path}"] = str(exc)

    if args.download_local:
        if not os.path.isdir(local_docs_root):
            local_docs_errors["root"] = f"Local docs root not found: {local_docs_root}"
        else:
            for path in _iter_local_docs(local_docs_root):
                if _is_external_doc(path):
                    continue
                try:
                    rel_path = os.path.relpath(path, args.root).replace("\\", "/")
                    target_path = os.path.join(local_docs_download_root, rel_path.replace("/", os.sep))
                    os.makedirs(os.path.dirname(target_path), exist_ok=True)
                    shutil.copyfile(path, target_path)
                    local_docs.append(
                        {
                            "path": rel_path,
                            "downloaded_path": os.path.relpath(target_path, local_docs_download_root).replace("\\", "/"),
                        }
                    )
                except Exception as exc:
                    local_docs_errors[rel_path] = str(exc)

    out = {
        "last_checked": now_iso,
        "repo_root": os.path.abspath(args.root),
        "download_root": download_root,
        "downloaded_files": downloaded_count,
        "local_docs_root": os.path.abspath(local_docs_root),
        "local_docs_download_root": local_docs_download_root,
        "local_docs_count": len(local_docs),
        "total_repos": len(repo_map),
        "changed_repos": changed_repos,
        "rendered_files": rendered_files,
        "repos": results,
        "local_docs": local_docs,
        "local_docs_errors": local_docs_errors,
        "errors": errors,
    }

    os.makedirs(os.path.dirname(args.output), exist_ok=True)
    with open(args.output, "w", encoding="utf-8") as f:
        json.dump(out, f, indent=2, sort_keys=True)

    print("Saved:", args.output)
    print("Repos found:", len(repo_map))
    print("Changed repos:", len(changed_repos))
    if errors:
        print("Errors:", len(errors))


if __name__ == "__main__":
    sys.exit(main())
