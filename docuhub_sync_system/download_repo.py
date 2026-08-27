"""
Download / update the CIROH-UA/ciroh_hub repository using git clone/pull
so that full commit history is available for per-file date lookups.
"""
import json
import os
import subprocess
import urllib.request
from datetime import datetime

REPO = "CIROH-UA/ciroh_hub"
CLONE_URL = f"https://github.com/{REPO}.git"
OUT_DIR = os.getcwd()
TARGET_DIR = os.path.join(OUT_DIR, "ciroh_hub")
SYNC_FILE = os.path.join(OUT_DIR, "ciroh_hub_sync.json")


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


def api_get_json(url):
    req = urllib.request.Request(url, headers=_headers())
    with urllib.request.urlopen(req) as resp:
        data = resp.read().decode("utf-8")
        return json.loads(data)


def get_latest_commit():
    url = f"https://api.github.com/repos/{REPO}/commits?per_page=1"
    data = api_get_json(url)
    if not data:
        raise RuntimeError("No commits returned by GitHub API.")
    latest = data[0]
    sha = latest.get("sha")
    date = latest.get("commit", {}).get("committer", {}).get("date")
    if not sha or not date:
        raise RuntimeError("Could not parse latest commit data.")
    return sha, date


def compare_commits(base_sha, head_sha):
    cmp = f"{base_sha}...{head_sha}"
    url = f"https://api.github.com/repos/{REPO}/compare/{cmp}"
    data = api_get_json(url)
    files = data.get("files", [])
    return [
        {
            "filename": f.get("filename"),
            "status": f.get("status"),
            "additions": f.get("additions"),
            "deletions": f.get("deletions"),
            "changes": f.get("changes"),
        }
        for f in files
    ]


def load_sync():
    if not os.path.exists(SYNC_FILE):
        return None
    with open(SYNC_FILE, "r", encoding="utf-8") as f:
        return json.load(f)


def save_sync(data):
    with open(SYNC_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, sort_keys=True)


def _git_clone_url():
    """Build clone URL, embedding a token if available."""
    token = None
    if os.environ.get("CIROH_IGNORE_GITHUB_TOKEN") != "1":
        token = os.environ.get("GITHUB_TOKEN")
    if token:
        return f"https://x-access-token:{token}@github.com/{REPO}.git"
    return CLONE_URL


def _is_git_repo(path):
    return os.path.isdir(os.path.join(path, ".git"))


def _run_git(*args, cwd=None):
    cmd = ["git"] + list(args)
    result = subprocess.run(cmd, cwd=cwd, capture_output=True, text=True)
    if result.returncode != 0:
        msg = result.stderr.strip()
        raise RuntimeError(
            f"git {' '.join(args)} failed "
            f"(exit {result.returncode}):\n{msg}"
        )
    return result.stdout.strip()


def _local_head_sha():
    return _run_git("rev-parse", "HEAD", cwd=TARGET_DIR)


def main():
    _load_dotenv(os.path.join(OUT_DIR, ".env"))
    now_iso = datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ")

    print(f"Checking latest commit for {REPO} ...")
    latest_sha, latest_date = get_latest_commit()
    print(f"Latest commit: {latest_sha}")
    print(f"Latest commit date (UTC): {latest_date}")

    prev = load_sync()
    if prev:
        prev_sha = prev.get("last_sha")
        prev_date = prev.get("last_commit_date")
        if prev_sha:
            print(f"Previous commit: {prev_sha}")
            if prev_date:
                print(f"Previous commit date (UTC): {prev_date}")

    if (
        prev
        and prev.get("last_sha") == latest_sha
        and os.path.exists(TARGET_DIR)
        and _is_git_repo(TARGET_DIR)
    ):
        print("No new commits since the last sync. Skipping.")
        prev["last_checked"] = now_iso
        save_sync(prev)
        return

    changed_files = []
    if prev and prev.get("last_sha") and prev.get("last_sha") != latest_sha:
        print("Comparing commits for changed files ...")
        try:
            changed_files = compare_commits(prev["last_sha"], latest_sha)
            if changed_files:
                print("Changed files since last sync:")
                for f in changed_files:
                    print(f"- {f.get('status')}: {f.get('filename')}")
            else:
                print("No file-level changes reported by the compare API.")
        except Exception as exc:
            print(f"Compare failed: {exc}")

    clone_url = _git_clone_url()

    if _is_git_repo(TARGET_DIR):
        print(f"Pulling latest changes into {TARGET_DIR} ...")
        _run_git("fetch", "--all", cwd=TARGET_DIR)
        _run_git("reset", "--hard", "origin/main", cwd=TARGET_DIR)
    else:
        print(f"Cloning {REPO} into {TARGET_DIR} ...")
        _run_git("clone", clone_url, TARGET_DIR)

    head_sha = _local_head_sha()
    print(f"Local HEAD is now: {head_sha}")

    sync_data = {
        "repo": REPO,
        "last_sha": head_sha,
        "last_commit_date": latest_date,
        "last_checked": now_iso,
        "downloaded_at": now_iso,
        "previous_sha": prev.get("last_sha") if prev else None,
        "changed_files": changed_files,
    }
    save_sync(sync_data)
    print(f"Done. Repo is at: {TARGET_DIR}")


if __name__ == "__main__":
    main()
