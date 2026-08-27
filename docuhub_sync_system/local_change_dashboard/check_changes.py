import json
import os
import urllib.request
from datetime import datetime

REPO = "CIROH-UA/ciroh_hub"
API_BASE = "https://api.github.com"
OUT_DIR = os.path.dirname(os.path.abspath(__file__))
STATE_PATH = os.path.join(OUT_DIR, "changes.json")


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


def _load_state():
    if not os.path.exists(STATE_PATH):
        return None
    with open(STATE_PATH, "r", encoding="utf-8") as f:
        return json.load(f)


def _save_state(data):
    with open(STATE_PATH, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, sort_keys=True)


def _latest_commit():
    url = f"{API_BASE}/repos/{REPO}/commits?per_page=1"
    data = _get_json(url)
    if not data:
        raise RuntimeError("No commits returned by GitHub API.")
    latest = data[0]
    sha = latest.get("sha")
    commit = latest.get("commit", {})
    date = commit.get("committer", {}).get("date")
    message = (commit.get("message") or "").splitlines()[0]
    if not sha or not date:
        raise RuntimeError("Could not parse latest commit data.")
    return sha, date, message


def _compare_commits(base_sha, head_sha):
    url = f"{API_BASE}/repos/{REPO}/compare/{base_sha}...{head_sha}"
    data = _get_json(url)
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


def main():
    now_iso = datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ")
    latest_sha, latest_date, latest_message = _latest_commit()

    prev = _load_state()
    prev_sha = prev.get("latest_sha") if prev else None

    changed_files = []
    if prev_sha and prev_sha != latest_sha:
        changed_files = _compare_commits(prev_sha, latest_sha)

    state = {
        "repo": REPO,
        "last_checked": now_iso,
        "latest_sha": latest_sha,
        "latest_commit_date": latest_date,
        "latest_commit_message": latest_message,
        "previous_sha": prev_sha,
        "changed_files_count": len(changed_files),
        "changed_files": changed_files,
    }

    _save_state(state)
    print("Saved:", STATE_PATH)
    print("Latest commit:", latest_sha)
    print("Changed files:", len(changed_files))


if __name__ == "__main__":
    main()
