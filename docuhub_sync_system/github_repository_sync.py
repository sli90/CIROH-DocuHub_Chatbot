"""Build CIROH GitHub repository artifacts with optional LLM descriptions.

This module ports the repository acquisition and repository-level summary logic
from ``v2-dev/backend/database/GitHub_CodeRepos.ipynb`` into a reusable,
incremental pipeline component.  It deliberately does not update PostgreSQL,
generate embeddings, or deactivate database rows.

Nothing runs on import.  The guarded CLI in ``run_github_repository_sync.py``
is the supported execution entry point.
"""
from __future__ import annotations

import hashlib
import html
import io
import json
import os
import re
import time
import zipfile
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Iterable
from urllib.parse import quote

try:
    import requests
except ImportError:  # Allows offline/unit-test imports before dependencies are installed.
    requests = None

from sync_accounting import UsageAccumulator, aggregate_usage, utc_now_iso


CODEREPO_ARTIFACT_TYPE_ID = 4
DEFAULT_OWNER = "CIROH-UA"
DEFAULT_SUMMARY_MODEL = "gpt-5.2"
SUMMARY_PROMPT_VERSION = 1
CHUNK_SCHEMA_VERSION = 1
CHUNK_CLASSIFIER_PROMPT_VERSION = 1
CHECKPOINT_SCHEMA_VERSION = 1

EXCLUDED_REPOS = {
    "subdomain-hub",
    "ciroh_hub",
    "ciroh_hub_staging",
    "ciroh-portal",
    "ciroh-ua_website",
    "docuhub-staging",
}
OPTIONAL_EXCLUDED_REPOS = {
    ".github",
    "ciroh-ua.github.io",
    "subdomain-ngiab",
    "teehr-may-2023-workshop",
}
SKIP_DIR_PREFIXES = {
    ".git/",
    ".github/",
    ".ipynb_checkpoints/",
    "__pycache__/",
    "node_modules/",
    "dist/",
    "build/",
    "_build/",
    "site/",
    ".venv/",
    "venv/",
    "env/",
    ".mypy_cache/",
    ".pytest_cache/",
}
ALLOWED_EXACT_FILENAMES = {
    "readme",
    "readme.md",
    "readme.rst",
    "readme.txt",
    "license",
    "license.md",
    "license.txt",
    "contributing",
    "contributing.md",
    "contributing.rst",
    "contributing.txt",
    "changelog",
    "changelog.md",
    "changelog.rst",
    "changelog.txt",
    "citation",
    "citation.md",
    "citation.txt",
    "citation.cff",
    "security.md",
    "code_of_conduct.md",
    "requirements.txt",
    "environment.yml",
    "environment.yaml",
    "pyproject.toml",
    "setup.py",
    "setup.cfg",
    "pipfile",
    "pipfile.lock",
}
ALLOWED_TEXT_EXTENSIONS = {
    ".md",
    ".markdown",
    ".rst",
    ".ipynb",
    ".cff",
    ".toml",
    ".yml",
    ".yaml",
    ".py",
}
ALLOWED_PATH_PREFIXES = {
    "docs/",
    "doc/",
    "documentation/",
    "examples/",
    "example/",
    "tutorials/",
    "tutorial/",
    "notebooks/",
    "notebook/",
    "workshop/",
    "workshops/",
}
EXCLUDED_NAME_SUBSTRINGS = {
    "checkpoint",
    "dummy",
    "placeholder",
    "deleteme",
    "tmp",
    "temp",
    "backup",
    "~",
}
EXCLUDED_RST_PATH_TOKENS = {"/api/", "/reference/", "/generated/", "_build/"}
SEMANTIC_PATH_TOKENS = {
    "script",
    "scripts",
    "notebook",
    "notebooks",
    "tutorial",
    "tutorials",
    "example",
    "examples",
    "demo",
    "demos",
    "exercise",
    "exercises",
    "lesson",
    "lessons",
    "lab",
    "labs",
    "training",
    "workflow",
    "workflows",
}
ALLOWED_SEMANTIC_FOLDER_EXTENSIONS = {
    ".ipynb",
    ".md",
    ".markdown",
    ".rst",
    ".txt",
    ".cff",
}

MAX_REPO_CONTEXT_CHARS = 350_000
MAX_TEXT_FILE_CHARS = 25_000
MAX_NOTEBOOK_MARKDOWN_CHARS = 35_000
MAX_CONFIG_FILE_CHARS = 12_000
MAX_FILES_IN_SUMMARY_CONTEXT = 80
MAX_SELECTED_FILE_BYTES = 10 * 1024 * 1024
SAFE_REPOSITORY_NAME = re.compile(r"^[A-Za-z0-9._-]+$")
MAX_TEXT_CHARS_PER_CHUNK = 12_000
MIN_CHUNK_TEXT_LENGTH = 40

REPOSITORY_CHUNK_TYPES = (
    "Project Overview",
    "Installation Setup",
    "Usage Examples",
    "Repository Structure",
    "Contributing Guidelines",
    "License Citation",
    "Documentation Section",
    "Notebook Section",
    "Configuration / Deployment",
    "Change Log / Release Notes",
)

SUMMARY_SYSTEM_MESSAGE = (
    "You are a precise CIROH code repository summarizer. "
    "Return ONLY valid JSON. No prose, no markdown."
)


@dataclass(frozen=True)
class RepositorySyncConfig:
    root: Path
    owner: str = DEFAULT_OWNER
    corpus_dir: Path | None = None
    artifact_output: Path | None = None
    chunk_output: Path | None = None
    report_output: Path | None = None
    state_path: Path | None = None
    checkpoint_path: Path | None = None
    summary_model: str = field(
        default_factory=lambda: os.getenv(
            "GITHUB_REPO_SUMMARY_MODEL",
            os.getenv("SUMMARY_MODEL", DEFAULT_SUMMARY_MODEL),
        )
    )
    excluded_repositories: frozenset[str] = field(
        default_factory=lambda: frozenset(EXCLUDED_REPOS | OPTIONAL_EXCLUDED_REPOS)
    )

    def resolved(self) -> "RepositorySyncConfig":
        root = self.root.resolve()
        formatted = root / "dashboard" / "formated_files"
        local_state = root / "local_change_dashboard"
        return RepositorySyncConfig(
            root=root,
            owner=self.owner,
            corpus_dir=(self.corpus_dir or local_state / "github_repository_corpus").resolve(),
            artifact_output=(
                self.artifact_output or formatted / "coderepo_artifacts.json"
            ).resolve(),
            chunk_output=(
                self.chunk_output or formatted / "coderepo_chunks.json"
            ).resolve(),
            report_output=(
                self.report_output
                or formatted / "github_repository_generation_report.json"
            ).resolve(),
            state_path=(
                self.state_path or local_state / "github_repository_sync.json"
            ).resolve(),
            checkpoint_path=(
                self.checkpoint_path
                or local_state / "github_repository_generation_checkpoint.json"
            ).resolve(),
            summary_model=self.summary_model,
            excluded_repositories=self.excluded_repositories,
        )


class GitHubClient:
    """Small GitHub REST client used by the repository artifact stage."""

    def __init__(self, token: str | None = None, session: Any | None = None):
        if session is None and requests is None:
            raise RuntimeError(
                "The 'requests' package is required for GitHub synchronization. "
                "Install the project's requirements before running it."
            )
        self.session = session or requests.Session()
        self.headers = {
            "Accept": "application/vnd.github+json",
            "X-GitHub-Api-Version": "2022-11-28",
            "User-Agent": "CIROH-DocuHub-Sync-System",
        }
        if token:
            self.headers["Authorization"] = f"Bearer {token}"

    def _get(self, url: str, *, params: dict | None = None):
        response = self.session.get(
            url, headers=self.headers, params=params, timeout=60
        )
        response.raise_for_status()
        return response

    def list_org_repositories(self, owner: str) -> list[dict]:
        repositories: list[dict] = []
        page = 1
        while True:
            response = self._get(
                f"https://api.github.com/orgs/{owner}/repos",
                params={
                    "type": "public",
                    "per_page": 100,
                    "page": page,
                    "sort": "full_name",
                    "direction": "asc",
                },
            )
            batch = response.json()
            if not batch:
                break
            repositories.extend(batch)
            page += 1
        return repositories

    def get_head_sha(self, owner: str, repository: str, branch: str) -> str | None:
        url = f"https://api.github.com/repos/{owner}/{repository}/commits/{branch}"
        try:
            return str(self._get(url).json()["sha"])
        except Exception as exc:
            if getattr(getattr(exc, "response", None), "status_code", None) == 409:
                return None
            raise

    def get_contributors(self, owner: str, repository: str) -> list[dict]:
        contributors: list[dict] = []
        page = 1
        while True:
            response = self._get(
                f"https://api.github.com/repos/{owner}/{repository}/contributors",
                params={"per_page": 100, "page": page},
            )
            batch = response.json()
            if not batch:
                break
            contributors.extend(
                {
                    "id": item.get("id"),
                    "login": item.get("login"),
                    "html_url": item.get("html_url"),
                    "type": item.get("type"),
                    "contributions": item.get("contributions"),
                }
                for item in batch
            )
            page += 1
        return contributors

    def download_snapshot(self, owner: str, repository: str, sha: str) -> bytes:
        return self._get(
            f"https://api.github.com/repos/{owner}/{repository}/zipball/{sha}"
        ).content


def _load_json(path: Path, default: Any) -> Any:
    try:
        with path.open("r", encoding="utf-8") as handle:
            return json.load(handle)
    except (OSError, json.JSONDecodeError):
        return default


def _write_json_atomic(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(f".{path.name}.{os.getpid()}.tmp")
    temporary.write_text(
        json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )
    temporary.replace(path)


def _clean_text(value: Any) -> str | None:
    if value is None:
        return None
    cleaned = str(value).replace("\x00", "").strip()
    return cleaned or None


def _normalize_list(value: Any) -> list:
    return value if isinstance(value, list) else []


def _truncate_text(text: str, max_chars: int) -> str:
    text = str(text or "").replace("\x00", "").strip()
    if len(text) <= max_chars:
        return text
    return f"{text[: int(max_chars * 0.7)]}\n\n...\n\n{text[-int(max_chars * 0.3):]}"


def normalize_relative_path(relative_path: str) -> str:
    relative = relative_path.replace("\\", "/").strip()
    return relative[2:] if relative.startswith("./") else relative


def _normalize_path_segment(segment: str) -> str:
    segment = re.sub(r"^\d+[\._\- ]*", "", segment.lower().strip())
    segment = re.sub(r"[\._\-]+", " ", segment)
    return re.sub(r"\s+", " ", segment).strip()


def _has_semantic_folder_signal(relative_path: str) -> bool:
    parts = Path(normalize_relative_path(relative_path)).parts[:-1]
    return any(
        set(_normalize_path_segment(part).split()) & SEMANTIC_PATH_TOKENS
        for part in parts
    )


def classify_selection_reason(relative_path: str, repository_name: str) -> str | None:
    """Return the v2-dev selection-policy reason, or ``None`` to skip."""
    relative = normalize_relative_path(relative_path)
    lower = relative.lower()
    repository_lower = repository_name.strip().lower()
    filename = Path(lower).name
    suffix = Path(filename).suffix.lower()

    if any(lower.startswith(prefix) for prefix in SKIP_DIR_PREFIXES):
        return None
    if "/.ipynb_checkpoints/" in lower:
        return None
    if any(token in filename for token in EXCLUDED_NAME_SUBSTRINGS):
        return None
    if suffix == ".rst" and any(token in lower for token in EXCLUDED_RST_PATH_TOKENS):
        return None
    if suffix == ".rst" and repository_lower and filename.startswith(
        f"{repository_lower}."
    ):
        return None
    if filename == "license.txt" and any(
        token in lower
        for token in (
            "_build/",
            "/vendor/",
            "/vendors/",
            "/third_party/",
            "/third-party/",
            "/site-packages/",
            "/dist/",
            "/build/",
        )
    ):
        return None
    if filename in ALLOWED_EXACT_FILENAMES:
        return "allowed_exact_filename"
    if any(lower.startswith(prefix) for prefix in ALLOWED_PATH_PREFIXES):
        if suffix in ALLOWED_TEXT_EXTENSIONS:
            return "allowed_path_prefix"
    if _has_semantic_folder_signal(lower):
        if suffix in ALLOWED_SEMANTIC_FOLDER_EXTENSIONS:
            return "allowed_semantic_folder"
    if "/" not in lower and suffix in {".md", ".markdown", ".rst", ".cff"}:
        return "allowed_top_level_doc"
    if "/" not in lower and suffix == ".ipynb":
        return "allowed_top_level_notebook"
    return None


def extract_selected_files(
    zip_bytes: bytes, snapshot_dir: Path, repository_name: str
) -> list[dict]:
    """Extract selected text files from a GitHub zip into an immutable snapshot."""
    contents_dir = snapshot_dir / "contents"
    contents_dir.mkdir(parents=True, exist_ok=True)
    contents_root = contents_dir.resolve()
    manifest: list[dict] = []

    with zipfile.ZipFile(io.BytesIO(zip_bytes)) as archive:
        for member in (item for item in archive.infolist() if not item.is_dir()):
            parts = Path(member.filename).parts
            if len(parts) < 2:
                continue
            relative = Path(*parts[1:]).as_posix()
            reason = classify_selection_reason(relative, repository_name)
            skip_reason = None
            if reason and member.file_size > MAX_SELECTED_FILE_BYTES:
                skip_reason = "selected_file_too_large"
                reason = None

            if reason:
                target = (contents_dir / Path(relative)).resolve()
                if contents_root not in target.parents:
                    raise ValueError(f"Unsafe path in GitHub archive: {relative}")
                target.parent.mkdir(parents=True, exist_ok=True)
                with archive.open(member, "r") as source, target.open("wb") as output:
                    output.write(source.read())

            manifest.append(
                {
                    "path": relative,
                    "file_name": Path(relative).name,
                    "extension": Path(relative).suffix.lower(),
                    "size_bytes": member.file_size,
                    "downloaded": reason is not None,
                    "selection_reason": reason,
                    "skip_reason": skip_reason,
                }
            )
    return manifest


def _contributors_summary(contributors: list[dict], top_k: int = 10) -> dict:
    return {
        "contributors_count": len(contributors),
        "top_contributors": contributors[:top_k],
    }


def _repository_metadata(repo: dict, contributors: list[dict]) -> dict:
    license_info = repo.get("license") or {}
    return {
        "id": repo.get("id"),
        "name": repo.get("name"),
        "full_name": repo.get("full_name"),
        "html_url": repo.get("html_url"),
        "description": repo.get("description"),
        "homepage": repo.get("homepage"),
        "default_branch": repo.get("default_branch"),
        "created_at": repo.get("created_at"),
        "updated_at": repo.get("updated_at"),
        "pushed_at": repo.get("pushed_at"),
        "language": repo.get("language"),
        "topics": repo.get("topics", []),
        "fork": repo.get("fork", False),
        "archived": repo.get("archived", False),
        "disabled": repo.get("disabled", False),
        "visibility": repo.get("visibility"),
        "size_kb": repo.get("size"),
        "stargazers_count": repo.get("stargazers_count"),
        "watchers_count": repo.get("watchers_count"),
        "forks_count": repo.get("forks_count"),
        "open_issues_count": repo.get("open_issues_count"),
        "license": {
            "key": license_info.get("key"),
            "name": license_info.get("name"),
            "spdx_id": license_info.get("spdx_id"),
            "url": license_info.get("url"),
        }
        if license_info
        else None,
        "contributors_summary": _contributors_summary(contributors),
    }


def _metadata_fingerprint(repo: dict, head_sha: str) -> str:
    relevant = {
        "head_sha": head_sha,
        "name": repo.get("name"),
        "full_name": repo.get("full_name"),
        "html_url": repo.get("html_url"),
        "description": repo.get("description"),
        "default_branch": repo.get("default_branch"),
        "language": repo.get("language"),
        "topics": sorted(repo.get("topics") or []),
    }
    encoded = json.dumps(relevant, sort_keys=True, separators=(",", ":")).encode()
    return hashlib.sha256(encoded).hexdigest()


def _summarize_selected_files(manifest: list[dict]) -> dict:
    downloaded = [item for item in manifest if item.get("downloaded")]
    extensions: dict[str, int] = {}
    reasons: dict[str, int] = {}
    sample_paths: list[str] = []
    for item in downloaded:
        extension = _clean_text(item.get("extension")) or ""
        reason = _clean_text(item.get("selection_reason")) or ""
        extensions[extension] = extensions.get(extension, 0) + 1
        reasons[reason] = reasons.get(reason, 0) + 1
        if item.get("path") and len(sample_paths) < 20:
            sample_paths.append(str(item["path"]))
    return {
        "downloaded_files_count": len(downloaded),
        "downloaded_extensions": dict(sorted(extensions.items())),
        "selection_reason_counts": dict(sorted(reasons.items())),
        "sample_downloaded_paths": sample_paths,
    }


def _extract_notebook_markdown(path: Path) -> str:
    notebook = _load_json(path, {})
    blocks: list[str] = []
    for cell in notebook.get("cells", []) if isinstance(notebook, dict) else []:
        if cell.get("cell_type") != "markdown":
            continue
        source = cell.get("source", "")
        text = "".join(source) if isinstance(source, list) else str(source)
        text = text.replace("\x00", "").strip()
        if text:
            blocks.append(text)
    return "\n\n".join(blocks)


def _summarize_config_file(path: Path) -> str:
    text = path.read_text(encoding="utf-8", errors="replace").replace("\x00", "").strip()
    filename = path.name.lower()
    if filename == "requirements.txt":
        lines = [
            line.strip()
            for line in text.splitlines()
            if line.strip() and not line.strip().startswith("#")
        ]
        return "Python dependencies declared in requirements.txt:\n" + "\n".join(
            lines[:200]
        )
    if filename in {"environment.yml", "environment.yaml"}:
        return _truncate_text(f"Environment configuration:\n{text}", MAX_CONFIG_FILE_CHARS)
    return _truncate_text(
        f"Project/package configuration from {path.name}:\n{text}",
        MAX_CONFIG_FILE_CHARS,
    )


def _file_priority(record: dict) -> tuple[int, str]:
    path = str(record.get("path") or "").replace("\\", "/").lower()
    filename = Path(path).name
    suffix = Path(path).suffix.lower()
    if filename.startswith("readme"):
        return (0, path)
    if path in {"docs/index.rst", "docs/index.md", "docs/index.markdown"}:
        return (1, path)
    if suffix == ".ipynb":
        return (2, path)
    if path.startswith(tuple(ALLOWED_PATH_PREFIXES)):
        return (3, path)
    if filename in {
        "requirements.txt",
        "environment.yml",
        "environment.yaml",
        "pyproject.toml",
        "setup.py",
        "setup.cfg",
        "pipfile",
        "pipfile.lock",
    }:
        return (4, path)
    if filename.startswith(("contributing", "changelog", "citation", "license", "security")):
        return (5, path)
    return (9, path)


def _selected_file_content(snapshot_dir: Path, record: dict) -> str:
    relative = _clean_text(record.get("path"))
    if not relative:
        return ""
    path = snapshot_dir / "contents" / relative
    if not path.is_file():
        return ""
    suffix = path.suffix.lower()
    if suffix == ".ipynb":
        return _truncate_text(_extract_notebook_markdown(path), MAX_NOTEBOOK_MARKDOWN_CHARS)
    if path.name.lower() in {
        "requirements.txt",
        "environment.yml",
        "environment.yaml",
        "pyproject.toml",
        "setup.py",
        "setup.cfg",
        "pipfile",
        "pipfile.lock",
    }:
        return _summarize_config_file(path)
    if suffix in {".md", ".markdown", ".rst", ".txt", ".cff", ".py", ".toml", ".yml", ".yaml"}:
        return _truncate_text(
            path.read_text(encoding="utf-8", errors="replace"), MAX_TEXT_FILE_CHARS
        )
    return ""


def build_repository_summary_input(
    snapshot_dir: Path, repository_metadata: dict, manifest: list[dict]
) -> str:
    repository_name = _clean_text(repository_metadata.get("name")) or snapshot_dir.parent.name
    files = sorted(
        (item for item in manifest if item.get("downloaded")), key=_file_priority
    )[:MAX_FILES_IN_SUMMARY_CONTEXT]
    sections = [
        "\n".join(
            [
                f"Repository name: {repository_name}",
                f"Repository full name: {_clean_text(repository_metadata.get('full_name')) or ''}",
                f"Description: {_clean_text(repository_metadata.get('description')) or ''}",
                f"Primary language: {_clean_text(repository_metadata.get('language')) or ''}",
                f"Topics: {', '.join(_normalize_list(repository_metadata.get('topics')))}",
                f"Default branch: {_clean_text(repository_metadata.get('default_branch')) or ''}",
            ]
        )
    ]
    for record in files:
        content = _selected_file_content(snapshot_dir, record)
        if not content:
            continue
        sections.append(
            "\n--- FILE START ---\n"
            f"Path: {record.get('path') or ''}\n"
            f"Extension: {record.get('extension') or ''}\n"
            f"Selection reason: {record.get('selection_reason') or ''}\n"
            f"Content:\n{content}\n"
            "--- FILE END ---"
        )
    return _truncate_text("\n\n".join(sections), MAX_REPO_CONTEXT_CHARS)


def build_repository_summary_prompt(repository_context: str) -> str:
    """Return the repository-level prompt ported from the v2-dev notebook."""
    return f"""
# ROLE & GOAL
You are an AI Knowledge Architect specializing in hydrology, scientific computing, and research software for the Cooperative Institute for Research to Operations in Hydrology (CIROH). Your task is to summarize a GitHub code repository using an aggregated textual representation built from the repository metadata and selected files.

# CONTEXT
The output will populate a JSONB field called `summary_data` in a PostgreSQL database used by a Retrieval-Augmented Generation (RAG) system. The `summary_text` will later be embedded for semantic search. Therefore, the summary must help retrieve repositories relevant to user questions about hydrologic models, tools, workflows, tutorials, infrastructure, data access, scientific software, evaluation pipelines, deployment, and training materials.

# REPOSITORY CONTENT TO ANALYZE
---
**[BEGINNING OF REPOSITORY DOSSIER]**

{repository_context}

**[END OF REPOSITORY DOSSIER]**
---

# INSTRUCTIONS
Based on the content provided above, generate a single JSON object.

1. The `summary_text` must describe the repository as a whole, not just one file.
2. Infer the repository's main purpose from the combined evidence across README files, notebooks, docs, and configuration files.
3. Prioritize the repository's central purpose, core workflows, and major technical components. Do not let low-level implementation details from individual scripts or endpoint parameters dominate the summary.
4. The `keywords` array should capture major technical themes, workflows, tools, models, or capabilities.
5. The `entities` array should include specific named tools, frameworks, libraries, systems, hydrologic models, or platforms explicitly referenced in the repository content.
6. The `document_type` should be a concise characterization chosen from the repository evidence, such as "tutorial repository", "scientific software package", "deployment repository", "training materials repository", "data access utilities repository", "hydrologic modeling repository", etc.
7. Do not invent capabilities not supported by the repository content.
8. Be direct, factual, and information-dense.

# REQUIRED OUTPUT FORMAT
Generate a single valid JSON object with exactly this structure:

{{
  "summary_text": "",
  "keywords": [],
  "entities": [],
  "document_type": ""
}}
""".strip()


def summarize_repository(
    client: Any,
    repository_context: str,
    model: str,
    usage: UsageAccumulator,
) -> dict:
    usage.record_request()
    try:
        response = client.responses.create(
            model=model,
            input=[
                {"role": "system", "content": SUMMARY_SYSTEM_MESSAGE},
                {
                    "role": "user",
                    "content": build_repository_summary_prompt(repository_context),
                },
            ],
            text={"format": {"type": "json_object"}, "verbosity": "medium"},
            reasoning={"effort": "low"},
        )
        usage.add_response(response)
        data = json.loads((response.output_text or "").strip())
        return {
            "summary_text": data.get("summary_text") or "",
            "keywords": data.get("keywords")
            if isinstance(data.get("keywords"), list)
            else [],
            "entities": data.get("entities")
            if isinstance(data.get("entities"), list)
            else [],
            "document_type": data.get("document_type") or "",
        }
    except Exception:
        usage.record_error()
        raise


MD_HEADING_RE = re.compile(r"^(#{1,6})\s+(.*\S)\s*$")
MD_RULE_RE = re.compile(r"^\s*([-*_])\1{2,}\s*$")
RST_UNDERLINE_CHARS = set("=-~^\"`:+*#")
CONFIG_FILE_NAMES = {
    "requirements",
    "requirements.txt",
    "environment.yml",
    "environment.yaml",
    "pyproject.toml",
    "setup.py",
    "setup.cfg",
    "pipfile",
    "pipfile.lock",
    "dockerfile",
    "docker-compose.yml",
    "docker-compose.yaml",
}
CONTRIBUTING_FILE_NAMES = {
    "contributing",
    "contributing.md",
    "contributing.rst",
    "contributing.txt",
    "code_of_conduct.md",
}
CHANGELOG_FILE_NAMES = {
    "changelog",
    "changelog.md",
    "changelog.rst",
    "changelog.txt",
    "release-notes.md",
    "release_notes.md",
}
LICENSE_FILE_NAMES = {
    "license",
    "license.md",
    "license.txt",
    "citation",
    "citation.md",
    "citation.txt",
    "citation.cff",
    "terms.md",
    "terms.txt",
}
OVERVIEW_HEADING_HINTS = {
    "overview",
    "introduction",
    "about",
    "purpose",
    "motivation",
    "summary",
}
INSTALL_HEADING_HINTS = {
    "installation",
    "install",
    "setup",
    "getting started",
    "build and run",
    "build",
    "prepare the python environment",
}
USAGE_HEADING_HINTS = {
    "usage",
    "example",
    "examples",
    "quick start",
    "run",
    "workflow",
    "workflows",
    "tutorial",
    "steps",
    "how to run",
}
STRUCTURE_HEADING_HINTS = {
    "repository structure",
    "project structure",
    "contents",
    "what's here",
    "content of this resource",
    "folder structure",
}
CHUNK_CLASSIFIER_SYSTEM_MESSAGE = (
    "You are a precise classifier for GitHub repository chunks. "
    "Return ONLY valid JSON."
)
LLM_CLASSIFIABLE_CHUNK_TYPES = {
    "Project Overview",
    "Installation Setup",
    "Usage Examples",
    "Repository Structure",
    "Documentation Section",
}


def _clean_chunk_text(value: Any) -> str:
    cleaned = html.unescape(str(value or "").replace("\x00", ""))
    cleaned = cleaned.replace("\r\n", "\n").replace("\r", "\n")
    return re.sub(r"\n{3,}", "\n\n", cleaned).strip()


def _truncate_chunk(text: str, max_chars: int = MAX_TEXT_CHARS_PER_CHUNK) -> str:
    text = _clean_chunk_text(text)
    if len(text) <= max_chars:
        return text
    return text[:max_chars].rstrip() + "\n\n[TRUNCATED]"


def _normalized_heading(heading: str | None) -> str | None:
    heading = _clean_chunk_text(heading)
    return re.sub(r"\s+", " ", heading.lower()).strip() if heading else None


def _source_blob_url(full_name: str, sha: str, relative_path: str) -> str:
    safe_path = quote(relative_path.replace("\\", "/"), safe="/")
    return f"https://github.com/{full_name}/blob/{sha}/{safe_path}"


def classify_obvious_chunk_type(
    *, source_path: str, source_format: str, heading: str | None
) -> str | None:
    """Apply the deterministic chunk classifications from the v2-dev notebook."""
    path_lower = (source_path or "").lower().replace("\\", "/")
    filename = Path(path_lower).name
    heading_normalized = _normalized_heading(heading)
    if source_format == "notebook":
        return "Notebook Section"
    if filename in CONTRIBUTING_FILE_NAMES:
        return "Contributing Guidelines"
    if filename in CHANGELOG_FILE_NAMES:
        return "Change Log / Release Notes"
    if filename in LICENSE_FILE_NAMES:
        return "License Citation"
    if filename in CONFIG_FILE_NAMES:
        return "Configuration / Deployment"
    if any(
        token in path_lower
        for token in (
            "/deploy",
            "/deployment",
            "/docker",
            "/terraform",
            "/config",
            "/configs/",
            "/workflow",
            "/workflows",
            ".github/workflows/",
        )
    ):
        return "Configuration / Deployment"
    if not heading_normalized:
        return None
    if heading_normalized in OVERVIEW_HEADING_HINTS:
        return "Project Overview"
    if heading_normalized in INSTALL_HEADING_HINTS:
        return "Installation Setup"
    if heading_normalized in USAGE_HEADING_HINTS:
        return "Usage Examples"
    if heading_normalized in STRUCTURE_HEADING_HINTS:
        return "Repository Structure"
    if any(term in heading_normalized for term in ("contribut", "pull request", "issue tracker")):
        return "Contributing Guidelines"
    if any(term in heading_normalized for term in ("license", "citation", "terms")):
        return "License Citation"
    if any(term in heading_normalized for term in ("release", "changelog", "version history")):
        return "Change Log / Release Notes"
    if any(term in heading_normalized for term in ("install", "setup", "build")):
        return "Installation Setup"
    if any(term in heading_normalized for term in ("usage", "example", "tutorial", "workflow", "run")):
        return "Usage Examples"
    if any(term in heading_normalized for term in ("structure", "contents", "what's here")):
        return "Repository Structure"
    if any(term in heading_normalized for term in ("config", "configuration", "deployment", "environment")):
        return "Configuration / Deployment"
    return None


def build_chunk_classifier_prompt(
    *, repository_name: str, source_path: str, heading: str | None, chunk_text: str
) -> str:
    return f"""
# ROLE
Classify a repository chunk into exactly one chunk type.

# REPOSITORY
Repository: {repository_name}
Source path: {source_path}
Section heading: {heading or ''}

# CHUNK TEXT
---
{_truncate_chunk(chunk_text, 8000)}
---

# INSTRUCTIONS
Choose exactly one chunk type from this list:

- Project Overview
- Installation Setup
- Usage Examples
- Repository Structure
- Documentation Section

Use these meanings:
- Project Overview: repo purpose, scope, motivation, architecture, high-level description
- Installation Setup: install, setup, environment preparation, build prerequisites
- Usage Examples: examples, run instructions, workflows, demonstrations, practical execution
- Repository Structure: explanation of folders, files, layout, contents
- Documentation Section: technical or conceptual documentation that does not fit the above

Return exactly one JSON object with this structure:
{{
  "chunk_type": "",
  "reason": ""
}}
""".strip()


def classify_chunk_with_llm(
    client: Any,
    *,
    repository_name: str,
    source_path: str,
    heading: str | None,
    chunk_text: str,
    model: str,
    usage: UsageAccumulator,
) -> str:
    usage.record_request()
    try:
        response = client.responses.create(
            model=model,
            input=[
                {"role": "system", "content": CHUNK_CLASSIFIER_SYSTEM_MESSAGE},
                {
                    "role": "user",
                    "content": build_chunk_classifier_prompt(
                        repository_name=repository_name,
                        source_path=source_path,
                        heading=heading,
                        chunk_text=chunk_text,
                    ),
                },
            ],
            text={"format": {"type": "json_object"}, "verbosity": "low"},
            reasoning={"effort": "low"},
        )
        usage.add_response(response)
        data = json.loads((response.output_text or "").strip())
        chunk_type = _clean_text(data.get("chunk_type"))
        return (
            chunk_type
            if chunk_type in LLM_CLASSIFIABLE_CHUNK_TYPES
            else "Documentation Section"
        )
    except Exception:
        usage.record_error()
        raise


def parse_markdown_sections(text: str, source_file: str) -> list[dict]:
    lines = text.replace("\r\n", "\n").replace("\r", "\n").split("\n")
    specs: list[dict] = []
    next_local_id = 1
    preamble: list[str] = []
    current: dict | None = None
    stack: list[tuple[int, int]] = []
    inside_fence = False

    def cleaned_body(section_lines: list[str]) -> str:
        return "\n".join(
            line for line in section_lines if not MD_RULE_RE.match(line)
        ).strip()

    def add_intro() -> None:
        nonlocal next_local_id, preamble
        body = cleaned_body(preamble)
        if body:
            specs.append(
                {
                    "temp_local_id": next_local_id,
                    "temp_parent_local_id": None,
                    "chunk_text": _truncate_chunk(body),
                    "section_hint": "Introduction",
                    "heading": "Introduction",
                    "heading_level": 0,
                    "source_file": source_file,
                    "source_format": "markdown",
                }
            )
            next_local_id += 1
        preamble = []

    def flush_current() -> None:
        nonlocal current
        if current is None:
            return
        body = cleaned_body(current["lines"])
        if body or current.get("has_children"):
            specs.append(
                {
                    "temp_local_id": current["temp_local_id"],
                    "temp_parent_local_id": current["temp_parent_local_id"],
                    "chunk_text": _truncate_chunk(body or current["title"]),
                    "section_hint": current["title"],
                    "heading": current["title"],
                    "heading_level": current["heading_level"],
                    "source_file": source_file,
                    "source_format": "markdown",
                }
            )
        current = None

    for line in lines:
        if line.lstrip().startswith("```"):
            (preamble if current is None else current["lines"]).append(line)
            inside_fence = not inside_fence
            continue
        if inside_fence:
            (preamble if current is None else current["lines"]).append(line)
            continue
        match = MD_HEADING_RE.match(line)
        if not match:
            (preamble if current is None else current["lines"]).append(line)
            continue
        level = len(match.group(1))
        title = match.group(2).strip()
        if current is None and preamble:
            add_intro()
        if current is not None and level > current["heading_level"]:
            current["has_children"] = True
        flush_current()
        while stack and stack[-1][0] >= level:
            stack.pop()
        parent_id = stack[-1][1] if stack else None
        current = {
            "temp_local_id": next_local_id,
            "temp_parent_local_id": parent_id,
            "title": title,
            "heading_level": level,
            "lines": [],
            "has_children": False,
        }
        stack.append((level, next_local_id))
        next_local_id += 1
    if current is None and preamble:
        add_intro()
    else:
        flush_current()
    return specs


def parse_rst_sections(text: str, source_file: str) -> list[dict]:
    lines = text.replace("\r\n", "\n").replace("\r", "\n").split("\n")
    specs: list[dict] = []
    next_local_id = 2
    current_heading = "Introduction"
    current_level = 0
    current_lines: list[str] = []
    current_parent_id = None
    current_id = 1
    stack: list[tuple[int, int]] = []

    def level_for(underline: str) -> int:
        return {"=": 1, "-": 2, "~": 3, "^": 4, '"': 5, "`": 6}.get(
            underline[0] if underline else "-", 3
        )

    def flush() -> None:
        body = _clean_chunk_text("\n".join(current_lines))
        if body:
            specs.append(
                {
                    "temp_local_id": current_id,
                    "temp_parent_local_id": current_parent_id,
                    "chunk_text": _truncate_chunk(body),
                    "section_hint": current_heading,
                    "heading": current_heading,
                    "heading_level": current_level,
                    "source_file": source_file,
                    "source_format": "rst",
                }
            )

    index = 0
    while index < len(lines):
        if index + 1 < len(lines):
            title = lines[index].strip()
            underline = lines[index + 1].strip()
            if (
                title
                and underline
                and len(underline) >= len(title)
                and set(underline).issubset(RST_UNDERLINE_CHARS)
            ):
                flush()
                new_level = level_for(underline)
                while stack and stack[-1][0] >= new_level:
                    stack.pop()
                current_parent_id = stack[-1][1] if stack else None
                current_heading = title
                current_level = new_level
                current_lines = []
                current_id = next_local_id
                next_local_id += 1
                stack.append((new_level, current_id))
                index += 2
                continue
        current_lines.append(lines[index])
        index += 1
    flush()
    return specs


def parse_notebook_sections(path: Path, source_file: str) -> list[dict]:
    notebook = _load_json(path, {})
    cells = notebook.get("cells", []) if isinstance(notebook, dict) else []
    specs: list[dict] = []
    for index, cell in enumerate(cells):
        if not isinstance(cell, dict) or cell.get("cell_type") != "markdown":
            continue
        source = cell.get("source", [])
        markdown = "".join(source) if isinstance(source, list) else str(source)
        markdown = _clean_chunk_text(markdown)
        if len(markdown) < MIN_CHUNK_TEXT_LENGTH:
            continue
        section_hint = f"Notebook cell {index}"
        for line in markdown.splitlines():
            cleaned = _clean_text(line)
            if not cleaned:
                continue
            match = MD_HEADING_RE.match(cleaned)
            section_hint = (
                (_clean_text(match.group(2)) if match else cleaned[:120])
                or section_hint
            )
            break
        specs.append(
            {
                "temp_local_id": None,
                "temp_parent_local_id": None,
                "chunk_text": _truncate_chunk(markdown),
                "section_hint": section_hint,
                "heading": section_hint,
                "heading_level": None,
                "source_file": source_file,
                "source_format": "notebook",
                "extra_type_specific": {
                    "notebook_cell_type": "markdown",
                    "cell_index_start": index,
                    "cell_index_end": index,
                },
            }
        )
    return specs


def _source_format(relative_path: str) -> str:
    suffix = Path(relative_path).suffix.lower()
    filename = Path(relative_path).name.lower()
    if suffix == ".ipynb":
        return "notebook"
    if suffix == ".rst":
        return "rst"
    if filename in CONFIG_FILE_NAMES:
        return "config_text"
    if suffix in {".md", ".markdown", ".txt"}:
        return "markdown"
    if suffix in {".yml", ".yaml", ".toml"}:
        return "config_text"
    if suffix == ".py":
        return "python_code"
    return "plain_text"


def build_repository_chunk_specs(snapshot_dir: Path, artifact: dict) -> list[dict]:
    contents_dir = snapshot_dir / "contents"
    if not contents_dir.exists():
        return []
    specs: list[dict] = []
    files = sorted(
        (path for path in contents_dir.rglob("*") if path.is_file()),
        key=lambda path: str(path).lower(),
    )
    for path in files:
        relative = path.relative_to(contents_dir).as_posix()
        filename = path.name
        source_format = _source_format(relative)
        if source_format == "notebook":
            specs.extend(parse_notebook_sections(path, relative))
            continue
        text = _clean_chunk_text(path.read_text(encoding="utf-8", errors="replace"))
        if len(text) < MIN_CHUNK_TEXT_LENGTH:
            continue
        if source_format == "markdown":
            specs.extend(parse_markdown_sections(text, relative))
        elif source_format == "rst":
            specs.extend(parse_rst_sections(text, relative))
        elif source_format == "config_text":
            specs.append(
                {
                    "temp_local_id": None,
                    "temp_parent_local_id": None,
                    "chunk_text": _truncate_chunk(text),
                    "section_hint": filename,
                    "heading": filename,
                    "heading_level": None,
                    "source_file": relative,
                    "source_format": source_format,
                }
            )
        elif source_format == "plain_text" and filename.lower() in LICENSE_FILE_NAMES:
            specs.append(
                {
                    "temp_local_id": None,
                    "temp_parent_local_id": None,
                    "chunk_text": _truncate_chunk(text),
                    "section_hint": filename,
                    "heading": filename,
                    "heading_level": None,
                    "source_file": relative,
                    "source_format": source_format,
                    "forced_chunk_type_name": "License Citation",
                }
            )
        # Python source is useful for repository summaries but intentionally not
        # emitted as VectorRAG chunks, matching the v2-dev implementation.

    full_name = artifact.get("full_name")
    sha = artifact.get("frozen_commit_sha")
    for spec in specs:
        relative = spec["source_file"]
        spec.setdefault("extra_type_specific", {})
        spec["extra_type_specific"].update(
            {
                "path": relative,
                "source_file": Path(relative).name,
                "source_format": spec["source_format"],
                "source_url": (
                    _source_blob_url(full_name, sha, relative)
                    if full_name and sha
                    else None
                ),
            }
        )
    return specs


def generate_repository_chunks(
    *,
    snapshot_dir: Path,
    artifact: dict,
    next_chunk_id: int,
    llm_client: Any | None,
    model: str,
    classifier_usage: UsageAccumulator,
    classification_errors: list[dict],
) -> tuple[list[dict], int, int]:
    """Build chunks for one repository and return chunks, next ID, fallback count."""
    specs = build_repository_chunk_specs(snapshot_dir, artifact)
    assigned_ids = list(range(next_chunk_id, next_chunk_id + len(specs)))
    local_to_real = {
        (spec.get("source_file"), spec.get("temp_local_id")): chunk_id
        for spec, chunk_id in zip(specs, assigned_ids)
        if spec.get("temp_local_id") is not None
    }
    chunks: list[dict] = []
    fallback_count = 0
    repository_name = str(artifact.get("Title") or artifact.get("full_name") or "")
    artifact_id = int(artifact["idArtifact"])
    for order, (spec, chunk_id) in enumerate(zip(specs, assigned_ids), start=1):
        chunk_type = spec.get("forced_chunk_type_name") or classify_obvious_chunk_type(
            source_path=spec["source_file"],
            source_format=spec["source_format"],
            heading=spec.get("heading"),
        )
        if chunk_type is None and llm_client is not None:
            try:
                chunk_type = classify_chunk_with_llm(
                    llm_client,
                    repository_name=repository_name,
                    source_path=spec["source_file"],
                    heading=spec.get("heading"),
                    chunk_text=spec["chunk_text"],
                    model=model,
                    usage=classifier_usage,
                )
            except Exception as exc:
                classification_errors.append(
                    {
                        "full_name": artifact.get("full_name"),
                        "source_file": spec["source_file"],
                        "section_hint": spec.get("section_hint"),
                        "error": str(exc),
                    }
                )
        if chunk_type is None:
            chunk_type = "Documentation Section"
            fallback_count += 1
        parent_id = None
        if spec.get("temp_parent_local_id") is not None:
            parent_id = local_to_real.get(
                (spec["source_file"], spec["temp_parent_local_id"])
            )
        chunks.append(
            {
                "idArtifact": artifact_id,
                "idChunk": chunk_id,
                "order": order,
                # Numeric resolution is deliberately deferred to the DB loader.
                "idChunkType": None,
                "chunk_type_name": chunk_type,
                "chunk_text": spec["chunk_text"],
                "idChunkParent": parent_id,
                "section_hint": spec["section_hint"],
                "supporting_quote": [],
                "source_artifact_id": artifact_id,
                "type_specific": {
                    "source_file": Path(spec["source_file"]).name,
                    **(spec.get("extra_type_specific") or {}),
                },
            }
        )
    return chunks, next_chunk_id + len(specs), fallback_count


def _artifact_record(
    artifact_id: int,
    metadata: dict,
    archive_info: dict,
    manifest: list[dict],
    summary_data: dict | None,
) -> dict:
    repository_name = _clean_text(metadata.get("name")) or "unknown"
    full_name = _clean_text(metadata.get("full_name")) or f"{DEFAULT_OWNER}/{repository_name}"
    return {
        "idArtifact": artifact_id,
        "idArtifactType": CODEREPO_ARTIFACT_TYPE_ID,
        "Title": repository_name,
        "URL": _clean_text(metadata.get("html_url")) or f"https://github.com/{full_name}",
        "idArtifactParent": None,
        "description": _clean_text(metadata.get("description")),
        "topics": _normalize_list(metadata.get("topics")),
        "default_branch": _clean_text(metadata.get("default_branch")),
        "frozen_commit_sha": _clean_text(archive_info.get("frozen_commit_sha")),
        "language": _clean_text(metadata.get("language")),
        "created_at": _clean_text(metadata.get("created_at")),
        "updated_at": _clean_text(metadata.get("updated_at")),
        "pushed_at": _clean_text(metadata.get("pushed_at")),
        "contributors_summary": metadata.get("contributors_summary"),
        "full_name": full_name,
        "artifact_role": "repository",
        "selected_files_summary": _summarize_selected_files(manifest),
        "summary_data": summary_data,
    }


def _snapshot_paths(config: RepositorySyncConfig, repository: str, sha: str) -> tuple[Path, Path, Path]:
    snapshot_dir = config.corpus_dir / repository / "snapshots" / sha
    return (
        snapshot_dir,
        snapshot_dir / "repo_metadata.json",
        snapshot_dir / "files_manifest.json",
    )


def _acquire_snapshot(
    config: RepositorySyncConfig,
    github: Any,
    repo: dict,
    head_sha: str,
    *,
    force: bool,
) -> tuple[Path, dict, list[dict]]:
    repository = str(repo["name"])
    snapshot_dir, metadata_path, manifest_path = _snapshot_paths(
        config, repository, head_sha
    )
    if not force and metadata_path.exists() and manifest_path.exists():
        manifest = _load_json(manifest_path, [])
        contributors = _load_json(snapshot_dir / "contributors.json", [])
        if isinstance(manifest, list) and isinstance(contributors, list):
            metadata = _repository_metadata(repo, contributors)
            _write_json_atomic(metadata_path, metadata)
            return snapshot_dir, metadata, manifest

    owner = str((repo.get("owner") or {}).get("login") or config.owner)
    contributors = github.get_contributors(owner, repository)
    metadata = _repository_metadata(repo, contributors)
    archive_info = {
        "owner": owner,
        "repo_name": repository,
        "default_branch": repo.get("default_branch"),
        "frozen_commit_sha": head_sha,
        "downloaded_at_epoch": time.time(),
        "archive_format": "zip",
    }
    manifest = extract_selected_files(
        github.download_snapshot(owner, repository, head_sha),
        snapshot_dir,
        repository,
    )
    _write_json_atomic(metadata_path, metadata)
    _write_json_atomic(snapshot_dir / "archive_info.json", archive_info)
    _write_json_atomic(manifest_path, manifest)
    _write_json_atomic(snapshot_dir / "contributors.json", contributors)
    return snapshot_dir, metadata, manifest


def _checkpoint_compatibility(
    config: RepositorySyncConfig, summarize: bool
) -> dict[str, Any]:
    return {
        "schema_version": CHECKPOINT_SCHEMA_VERSION,
        "owner": config.owner,
        "summarize": summarize,
        "summary_model": config.summary_model,
        "summary_prompt_version": SUMMARY_PROMPT_VERSION,
        "chunk_schema_version": CHUNK_SCHEMA_VERSION,
        "chunk_classifier_prompt_version": CHUNK_CLASSIFIER_PROMPT_VERSION,
    }


def _checkpoint_entry_is_reusable(
    entry: Any,
    *,
    full_name: str,
    head_sha: str,
    metadata_fingerprint: str,
    summarize: bool,
) -> bool:
    if not isinstance(entry, dict):
        return False
    artifact = entry.get("artifact")
    chunks = entry.get("chunks")
    state = entry.get("state")
    if not isinstance(artifact, dict) or not isinstance(chunks, list):
        return False
    if not isinstance(state, dict):
        return False
    if entry.get("full_name") != full_name:
        return False
    if entry.get("head_sha") != head_sha:
        return False
    if entry.get("metadata_fingerprint") != metadata_fingerprint:
        return False
    if summarize and artifact.get("summary_data") is None:
        return False
    if not state.get("chunk_complete"):
        return False
    if int(state.get("chunk_count") or -1) != len(chunks):
        return False
    return True


def _write_repository_checkpoint(
    config: RepositorySyncConfig,
    *,
    compatibility: dict[str, Any],
    started_at: str,
    attempt_count: int,
    repositories: dict[str, dict],
    summary_usage: UsageAccumulator,
    classifier_usage: UsageAccumulator,
) -> None:
    _write_json_atomic(
        config.checkpoint_path,
        {
            "schema_version": CHECKPOINT_SCHEMA_VERSION,
            "status": "in_progress",
            "started_at": started_at,
            "updated_at": utc_now_iso(),
            "attempt_count": attempt_count,
            "compatibility": compatibility,
            "repositories": repositories,
            "summary_usage": summary_usage.report(),
            "classifier_usage": classifier_usage.report(),
        },
    )


def synchronize_repository_artifacts(
    config: RepositorySyncConfig,
    github: Any,
    *,
    llm_client: Any | None = None,
    summarize: bool = True,
    force: bool = False,
) -> dict:
    """Synchronize repository artifacts/chunks without touching the database."""
    config = config.resolved()
    if summarize and llm_client is None:
        raise ValueError("llm_client is required when summarize=True")

    summary_usage = UsageAccumulator(
        "github_repository_summarization", config.summary_model
    )
    classifier_usage = UsageAccumulator(
        "github_repository_chunk_classification", config.summary_model
    )
    checkpoint_compatibility = _checkpoint_compatibility(config, summarize)
    checkpoint = {} if force else _load_json(config.checkpoint_path, {})
    if (
        not isinstance(checkpoint, dict)
        or checkpoint.get("compatibility") != checkpoint_compatibility
    ):
        checkpoint = {}
    checkpoint_repositories = checkpoint.get("repositories") or {}
    if not isinstance(checkpoint_repositories, dict):
        checkpoint_repositories = {}
    started_at = str(checkpoint.get("started_at") or utc_now_iso())
    attempt_count = int(checkpoint.get("attempt_count") or 0) + 1
    if checkpoint:
        summary_usage.add_report(checkpoint.get("summary_usage"))
        classifier_usage.add_report(checkpoint.get("classifier_usage"))
    previous_state = _load_json(config.state_path, {})
    if not isinstance(previous_state, dict):
        previous_state = {}
    previous_repositories = previous_state.get("repositories") or {}
    if not isinstance(previous_repositories, dict):
        previous_repositories = {}
    previous_artifacts_payload = _load_json(config.artifact_output, [])
    if not isinstance(previous_artifacts_payload, list):
        previous_artifacts_payload = []
    previous_artifacts = {
        item.get("full_name"): item
        for item in previous_artifacts_payload
        if isinstance(item, dict) and item.get("full_name")
    }
    previous_chunks_payload = _load_json(config.chunk_output, [])
    if isinstance(previous_chunks_payload, dict):
        previous_chunks_payload = previous_chunks_payload.get("chunks") or []
    if not isinstance(previous_chunks_payload, list):
        previous_chunks_payload = []
    previous_chunks_by_artifact: dict[int, list[dict]] = {}
    for chunk in previous_chunks_payload:
        if not isinstance(chunk, dict):
            continue
        try:
            artifact_id = int(chunk.get("idArtifact"))
        except (TypeError, ValueError):
            continue
        previous_chunks_by_artifact.setdefault(artifact_id, []).append(chunk)
    for artifact_chunks in previous_chunks_by_artifact.values():
        artifact_chunks.sort(key=lambda item: int(item.get("order") or 0))

    known_artifact_ids = [
        int(item.get("idArtifact") or 0) for item in previous_artifacts.values()
    ]
    known_artifact_ids.extend(
        int(item.get("artifact_id") or 0)
        for item in previous_repositories.values()
        if isinstance(item, dict)
    )
    known_artifact_ids.extend(
        int((entry.get("artifact") or {}).get("idArtifact") or 0)
        for entry in checkpoint_repositories.values()
        if isinstance(entry, dict) and isinstance(entry.get("artifact"), dict)
    )
    reserved_next_id = int(previous_state.get("next_artifact_id") or 1)
    next_artifact_id = max(known_artifact_ids + [reserved_next_id - 1, 0]) + 1
    known_chunk_ids = [
        int(item.get("idChunk") or 0)
        for item in previous_chunks_payload
        if isinstance(item, dict)
    ]
    known_chunk_ids.extend(
        int(chunk.get("idChunk") or 0)
        for entry in checkpoint_repositories.values()
        if isinstance(entry, dict) and isinstance(entry.get("chunks"), list)
        for chunk in entry["chunks"]
        if isinstance(chunk, dict)
    )
    reserved_next_chunk_id = int(previous_state.get("next_chunk_id") or 1)
    next_chunk_id = max(
        known_chunk_ids + [reserved_next_chunk_id - 1, 0]
    ) + 1

    discovered = github.list_org_repositories(config.owner)
    selected = sorted(
        (
            repo
            for repo in discovered
            if repo.get("name") not in config.excluded_repositories
        ),
        key=lambda repo: str(repo.get("full_name") or repo.get("name") or "").lower(),
    )
    artifacts: list[dict] = []
    chunks: list[dict] = []
    new_state: dict[str, dict] = {}
    acquisition_errors: list[dict] = []
    summary_errors: list[dict] = []
    chunk_generation_errors: list[dict] = []
    chunk_classification_errors: list[dict] = []
    pending_summaries: list[str] = []
    new_repositories: list[str] = []
    updated_repositories: list[str] = []
    unchanged_repositories: list[str] = []
    summarized_repositories: list[str] = []
    reused_summaries: list[str] = []
    chunked_repositories: list[str] = []
    reused_chunk_repositories: list[str] = []
    resumed_checkpoint_repositories: list[str] = []
    deterministic_classification_fallback_count = 0

    for index, repo in enumerate(selected, start=1):
        repository = str(repo.get("name") or "").strip()
        full_name = str(repo.get("full_name") or f"{config.owner}/{repository}")
        owner = str((repo.get("owner") or {}).get("login") or config.owner)
        if not repository:
            acquisition_errors.append({"full_name": full_name, "error": "missing repository name"})
            continue
        if not SAFE_REPOSITORY_NAME.fullmatch(repository) or repository in {".", ".."}:
            acquisition_errors.append(
                {"full_name": full_name, "error": "unsafe repository name"}
            )
            continue
        print(f"[{index}/{len(selected)}] Inspecting {full_name}")
        try:
            head_sha = github.get_head_sha(
                owner, repository, str(repo.get("default_branch") or "main")
            )
            if not head_sha:
                print("  skipped: empty repository")
                continue
            fingerprint = _metadata_fingerprint(repo, head_sha)
            old_state = previous_repositories.get(full_name) or {}
            old_artifact = previous_artifacts.get(full_name)
            old_artifact_id = (
                old_artifact.get("idArtifact") if old_artifact else None
            ) or old_state.get("artifact_id")
            old_repository_chunks = (
                previous_chunks_by_artifact.get(int(old_artifact_id), [])
                if old_artifact_id
                else []
            )
            checkpoint_entry = checkpoint_repositories.get(full_name)
            if not force and _checkpoint_entry_is_reusable(
                checkpoint_entry,
                full_name=full_name,
                head_sha=head_sha,
                metadata_fingerprint=fingerprint,
                summarize=summarize,
            ):
                artifact = checkpoint_entry["artifact"]
                repository_chunks = checkpoint_entry["chunks"]
                state_entry = checkpoint_entry["state"]
                artifacts.append(artifact)
                chunks.extend(repository_chunks)
                new_state[full_name] = state_entry
                outcome = checkpoint_entry.get("outcome")
                if outcome == "new":
                    new_repositories.append(full_name)
                elif outcome == "updated":
                    updated_repositories.append(full_name)
                else:
                    unchanged_repositories.append(full_name)
                if checkpoint_entry.get("summary_generated"):
                    summarized_repositories.append(full_name)
                elif artifact.get("summary_data") is not None:
                    reused_summaries.append(full_name)
                if checkpoint_entry.get("chunks_generated"):
                    chunked_repositories.append(full_name)
                else:
                    reused_chunk_repositories.append(full_name)
                deterministic_classification_fallback_count += int(
                    checkpoint_entry.get("fallback_count") or 0
                )
                saved_classification_errors = checkpoint_entry.get(
                    "chunk_classification_errors"
                )
                if isinstance(saved_classification_errors, list):
                    chunk_classification_errors.extend(saved_classification_errors)
                resumed_checkpoint_repositories.append(full_name)
                print("  resumed from completed repository checkpoint")
                continue
            source_unchanged = (
                bool(old_state)
                and old_state.get("metadata_fingerprint") == fingerprint
            )
            summary_reusable = (
                not force
                and old_artifact is not None
                and source_unchanged
                and (old_artifact.get("summary_data") is not None or not summarize)
                and (
                    not summarize
                    or (
                        old_state.get("summary_model") == config.summary_model
                        and old_state.get("summary_prompt_version")
                        == SUMMARY_PROMPT_VERSION
                    )
                )
            )
            expected_old_chunk_count = int(old_state.get("chunk_count") or 0)
            classifier_compatible = not summarize or (
                old_state.get("chunk_classifier_llm_enabled") is True
                and old_state.get("chunk_classifier_model") == config.summary_model
                and old_state.get("chunk_classifier_prompt_version")
                == CHUNK_CLASSIFIER_PROMPT_VERSION
            )
            chunks_reusable = (
                not force
                and old_artifact is not None
                and old_state.get("head_sha") == head_sha
                and old_state.get("chunk_complete") is True
                and old_state.get("chunk_schema_version") == CHUNK_SCHEMA_VERSION
                and classifier_compatible
                and len(old_repository_chunks) == expected_old_chunk_count
            )

            if summary_reusable and chunks_reusable:
                artifacts.append(old_artifact)
                chunks.extend(old_repository_chunks)
                (unchanged_repositories if source_unchanged else updated_repositories).append(
                    full_name
                )
                if old_artifact.get("summary_data") is not None:
                    reused_summaries.append(full_name)
                reused_chunk_repositories.append(full_name)
                new_state[full_name] = dict(old_state)
                continue

            snapshot_dir, metadata, manifest = _acquire_snapshot(
                config, github, repo, head_sha, force=force
            )
            artifact_id = (
                int(old_artifact_id) if old_artifact_id else next_artifact_id
            )
            if not old_artifact_id:
                next_artifact_id += 1

            summary_data = old_artifact.get("summary_data") if summary_reusable else None
            summary_was_reused = summary_reusable and summary_data is not None
            summary_was_generated = False
            if summary_reusable:
                artifact = old_artifact
                if summary_was_reused:
                    reused_summaries.append(full_name)
            else:
                if summarize:
                    try:
                        context = build_repository_summary_input(
                            snapshot_dir, metadata, manifest
                        )
                        summary_data = summarize_repository(
                            llm_client, context, config.summary_model, summary_usage
                        )
                        summarized_repositories.append(full_name)
                        summary_was_generated = True
                    except Exception as exc:
                        summary_errors.append(
                            {"full_name": full_name, "error": str(exc)}
                        )
                artifact = _artifact_record(
                    artifact_id,
                    metadata,
                    {"frozen_commit_sha": head_sha},
                    manifest,
                    summary_data,
                )
            artifacts.append(artifact)

            repository_chunks: list[dict]
            chunks_were_generated = False
            fallback_count = 0
            classification_error_start = len(chunk_classification_errors)
            if chunks_reusable:
                repository_chunks = old_repository_chunks
                reused_chunk_repositories.append(full_name)
            else:
                try:
                    (
                        repository_chunks,
                        next_chunk_id,
                        fallback_count,
                    ) = generate_repository_chunks(
                        snapshot_dir=snapshot_dir,
                        artifact=artifact,
                        next_chunk_id=next_chunk_id,
                        llm_client=llm_client if summarize else None,
                        model=config.summary_model,
                        classifier_usage=classifier_usage,
                        classification_errors=chunk_classification_errors,
                    )
                    deterministic_classification_fallback_count += fallback_count
                    chunked_repositories.append(full_name)
                    chunks_were_generated = True
                except Exception as exc:
                    chunk_generation_errors.append(
                        {"full_name": full_name, "error": str(exc)}
                    )
                    continue
            chunks.extend(repository_chunks)

            if old_artifact is None and not old_state:
                outcome = "new"
                new_repositories.append(full_name)
            elif source_unchanged:
                outcome = "unchanged"
                unchanged_repositories.append(full_name)
            else:
                outcome = "updated"
                updated_repositories.append(full_name)
            if summary_data is None:
                pending_summaries.append(full_name)
            summary_model = (
                old_state.get("summary_model")
                if summary_reusable
                else (config.summary_model if summary_data else None)
            )
            summary_prompt_version = (
                old_state.get("summary_prompt_version")
                if summary_reusable
                else (SUMMARY_PROMPT_VERSION if summary_data else None)
            )
            chunk_classifier_model = (
                old_state.get("chunk_classifier_model")
                if chunks_reusable
                else (config.summary_model if summarize else None)
            )
            chunk_classifier_prompt_version = (
                old_state.get("chunk_classifier_prompt_version")
                if chunks_reusable
                else (CHUNK_CLASSIFIER_PROMPT_VERSION if summarize else None)
            )
            chunk_classifier_llm_enabled = (
                old_state.get("chunk_classifier_llm_enabled")
                if chunks_reusable
                else summarize
            )
            state_entry = {
                "head_sha": head_sha,
                "metadata_fingerprint": fingerprint,
                "artifact_id": artifact_id,
                "summary_complete": summary_data is not None,
                "summary_model": summary_model,
                "summary_prompt_version": summary_prompt_version,
                "chunk_complete": True,
                "chunk_count": len(repository_chunks),
                "chunk_schema_version": CHUNK_SCHEMA_VERSION,
                "chunk_classifier_model": chunk_classifier_model,
                "chunk_classifier_prompt_version": chunk_classifier_prompt_version,
                "chunk_classifier_llm_enabled": chunk_classifier_llm_enabled,
                "snapshot_directory": str(snapshot_dir),
            }
            new_state[full_name] = state_entry

            # A completed repository is made durable immediately. If the run is
            # interrupted later, its summaries/chunks and their usage are reused.
            if not summarize or summary_data is not None:
                checkpoint_repositories[full_name] = {
                    "full_name": full_name,
                    "head_sha": head_sha,
                    "metadata_fingerprint": fingerprint,
                    "artifact": artifact,
                    "chunks": repository_chunks,
                    "state": state_entry,
                    "outcome": outcome,
                    "summary_generated": summary_was_generated,
                    "chunks_generated": chunks_were_generated,
                    "fallback_count": fallback_count,
                    "chunk_classification_errors": chunk_classification_errors[
                        classification_error_start:
                    ],
                }
                _write_repository_checkpoint(
                    config,
                    compatibility=checkpoint_compatibility,
                    started_at=started_at,
                    attempt_count=attempt_count,
                    repositories=checkpoint_repositories,
                    summary_usage=summary_usage,
                    classifier_usage=classifier_usage,
                )
        except Exception as exc:
            acquisition_errors.append({"full_name": full_name, "error": str(exc)})

    deleted_repositories = sorted(set(previous_repositories) - set(new_state))
    artifacts.sort(key=lambda item: str(item.get("full_name") or "").lower())
    artifact_names_by_id = {
        int(artifact["idArtifact"]): str(artifact.get("full_name") or "")
        for artifact in artifacts
    }
    chunks.sort(
        key=lambda item: (
            artifact_names_by_id.get(int(item.get("idArtifact") or 0), "").lower(),
            int(item.get("order") or 0),
            int(item.get("idChunk") or 0),
        )
    )
    fatal_errors = acquisition_errors or chunk_generation_errors
    openai_usage = aggregate_usage(
        [summary_usage.report(), classifier_usage.report()]
    )

    report = {
        "schema_version": 1,
        "stage": "github_repository_artifacts_and_chunks",
        "status": "failed" if fatal_errors else "completed",
        "started_at": started_at,
        "completed_at": utc_now_iso(),
        "owner": config.owner,
        "summary_model": config.summary_model,
        "summary_prompt_version": SUMMARY_PROMPT_VERSION,
        "summarization_requested": summarize,
        "chunk_classification_llm_requested": summarize,
        "chunk_schema_version": CHUNK_SCHEMA_VERSION,
        "chunk_classifier_prompt_version": CHUNK_CLASSIFIER_PROMPT_VERSION,
        "total_repositories_discovered": len(discovered),
        "total_repositories_selected": len(selected),
        "total_artifacts": len(artifacts),
        "total_chunks": len(chunks),
        "new_count": len(new_repositories),
        "updated_count": len(updated_repositories),
        "unchanged_count": len(unchanged_repositories),
        "deleted_count": len(deleted_repositories),
        "summarized_count": len(summarized_repositories),
        "reused_summary_count": len(reused_summaries),
        "chunked_repository_count": len(chunked_repositories),
        "reused_chunk_repository_count": len(reused_chunk_repositories),
        "resumed_checkpoint_count": len(resumed_checkpoint_repositories),
        "resumed_checkpoint_repositories": resumed_checkpoint_repositories,
        "attempt_count": attempt_count,
        "deterministic_classification_fallback_count": (
            deterministic_classification_fallback_count
        ),
        "new_repositories": new_repositories,
        "updated_repositories": updated_repositories,
        "deleted_repositories": deleted_repositories,
        "pending_summaries": pending_summaries,
        "summary_errors": summary_errors,
        "acquisition_errors": acquisition_errors,
        "chunk_generation_errors": chunk_generation_errors,
        "chunk_classification_errors": chunk_classification_errors,
        "openai_usage": openai_usage,
        "artifact_output": str(config.artifact_output),
        "chunk_output": str(config.chunk_output),
        "corpus_directory": str(config.corpus_dir),
        "database_update_performed": False,
        "checkpoint_path": str(config.checkpoint_path),
        "chunk_generation_status": (
            "failed"
            if chunk_generation_errors
            else "completed_with_symbolic_types_pending_database_mapping"
        ),
        "chunk_type_resolution": {
            "idChunkType": None,
            "field": "chunk_type_name",
            "required_names": list(REPOSITORY_CHUNK_TYPES),
            "database_resolution_performed": False,
        },
    }
    _write_json_atomic(config.report_output, report)

    if fatal_errors:
        raise RuntimeError(
            "GitHub repository artifact/chunk generation failed; existing output/state files were "
            f"left unchanged. See {config.report_output}"
        )

    state_payload = {
        "schema_version": 1,
        "owner": config.owner,
        "updated_at": utc_now_iso(),
        "artifact_output": str(config.artifact_output),
        "chunk_output": str(config.chunk_output),
        "next_artifact_id": next_artifact_id,
        "next_chunk_id": next_chunk_id,
        "repositories": new_state,
    }
    _write_json_atomic(config.artifact_output, artifacts)
    _write_json_atomic(config.chunk_output, chunks)
    _write_json_atomic(config.state_path, state_payload)
    config.checkpoint_path.unlink(missing_ok=True)
    return report


def selected_repository_names(
    repositories: Iterable[dict], excluded: Iterable[str]
) -> list[str]:
    """Pure helper used by tests and previews."""
    exclusions = set(excluded)
    return sorted(
        str(repo.get("full_name") or repo.get("name"))
        for repo in repositories
        if repo.get("name") not in exclusions
    )
