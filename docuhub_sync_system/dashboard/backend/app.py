import hashlib
import hmac
import html
import ipaddress
import io
import json
import os
import re
import subprocess
import sys
import threading
import zipfile
from datetime import datetime, timedelta, timezone

try:
    import yaml
except ImportError:
    yaml = None

from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import JSONResponse, StreamingResponse
from fastapi.middleware.cors import CORSMiddleware

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from sync_accounting import (  # noqa: E402
    build_synchronization_report,
    new_sync_id,
    utc_now_iso,
    write_synchronization_report,
)
from sync_pipeline import (  # noqa: E402
    SyncStepError,
    callback_step,
    database_step,
    generation_step,
    github_repository_database_step,
    github_repository_generation_step,
    repository_sync_steps,
    run_sync_steps,
)
from docuhub_paths import public_route_from_mixed_doc_path  # noqa: E402

DEFAULT_CHANGES = os.path.join(ROOT, "local_change_dashboard", "changes.json")
DEFAULT_REPO = os.path.join(ROOT, "ciroh_hub")
DEFAULT_EXTERNAL = os.path.join(ROOT, "local_change_dashboard", "external_repos.json")
DEFAULT_MIXED_EXPORT = os.path.join(ROOT, "local_change_dashboard", "mixed_docs")
DEFAULT_MIXED_MANIFEST = os.path.join(ROOT, "local_change_dashboard", "mixed_docs_manifest.json")
DEFAULT_LOCAL_CONTENT_MANIFEST = os.path.join(
    ROOT, "local_change_dashboard", "local_content_manifest.json"
)
SYNCHRONIZATION_OUTPUT_DIR = os.path.join(ROOT, "dashboard", "formated_files")
SYNCHRONIZATION_HISTORY_DIR = os.path.join(
    SYNCHRONIZATION_OUTPUT_DIR, "synchronization_reports"
)
BOOTSTRAP_SYNCHRONIZATION_HISTORY_DIR = os.path.join(
    ROOT, "dashboard", "bootstrap", "synchronization_reports"
)
MIXED_EXPORT_VERSION = 3
CHANGES_PATH = os.environ.get("CHANGES_JSON_PATH", DEFAULT_CHANGES)
REPO_ROOT = os.environ.get("REPO_ROOT_PATH", DEFAULT_REPO)
EXTERNAL_REPOS_PATH = os.environ.get("EXTERNAL_REPOS_PATH", DEFAULT_EXTERNAL)
MIXED_EXPORT_ROOT = os.environ.get("MIXED_EXPORT_ROOT", DEFAULT_MIXED_EXPORT)
MIXED_MANIFEST_PATH = os.environ.get("MIXED_MANIFEST_PATH", DEFAULT_MIXED_MANIFEST)
LOCAL_CONTENT_MANIFEST_PATH = os.environ.get(
    "LOCAL_CONTENT_MANIFEST_PATH", DEFAULT_LOCAL_CONTENT_MANIFEST
)
TREE_MAX_DEPTH = int(os.environ.get("TREE_MAX_DEPTH", "4"))
TREE_MAX_ENTRIES = int(os.environ.get("TREE_MAX_ENTRIES", "2500"))
TREE_EXCLUDES = {
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

FILE_TYPE_DEFS = [
    {"key": "md", "label": "MD", "extensions": {".md"}},
    {"key": "mdx", "label": "MDX", "extensions": {".mdx"}},
    {
        "key": "images",
        "label": "Images",
        "extensions": {".png", ".jpg", ".jpeg", ".gif", ".svg", ".webp", ".bmp", ".tif", ".tiff", ".ico"},
    },
    {
        "key": "page_components",
        "label": "Page Components",
        "extensions": {".js", ".jsx", ".mjs", ".cjs", ".ts", ".tsx", ".css", ".scss", ".sass", ".less"},
    },
    {"key": "yml", "label": "YML", "extensions": {".yml", ".yaml"}},
]
FILE_TYPE_KEYS = [cfg["key"] for cfg in FILE_TYPE_DEFS]
FILE_TYPE_EXT_LOOKUP = {
    ext: cfg["key"] for cfg in FILE_TYPE_DEFS for ext in cfg["extensions"]
}
MARKDOWN_EXTENSIONS = {".md", ".mdx"}
JS_ROUTE_EXTENSIONS = {".js", ".jsx", ".ts", ".tsx"}
JS_ROUTE_OUTPUT_DIR = "_generated_js_pages"
JS_ROUTE_PAGE_ALLOWLIST = {
    "src/pages/index.js",
    "src/pages/apps/index.js",
    "src/pages/community_products/index.js",
    "src/pages/contribute/index.js",
    "src/pages/contribute/develop.js",
    "src/pages/courses/index.js",
    "src/pages/datasets/index.js",
    "src/pages/events/index.js",
    "src/pages/notebooks/index.js",
    "src/pages/presentations/index.js",
    "src/pages/working-groups/index.js",
}
JS_ROUTE_TITLE_OVERRIDES = {
    "src/pages/index.js": "CIROH Hub",
}
JS_ROUTE_TEXT_KEYS = (
    "title",
    "description",
    "tagline",
    "label",
    "header",
    "summary",
    "name",
    "alt",
)

_ATTR_RE = re.compile(r'(\w+)\s*=\s*["\']([^"\']+)["\']')
_JS_STRING_TOKEN = r'(?:"((?:[^"\\]|\\.)*)"|\'((?:[^\'\\]|\\.)*)\'|`((?:[^`\\]|\\.)*)`)'
_JS_KEYED_STRING_RE = re.compile(
    rf"\b({'|'.join(JS_ROUTE_TEXT_KEYS)})\b\s*(?:=|:)\s*(?:\{{\s*)?{_JS_STRING_TOKEN}",
    re.I | re.S,
)
_JSX_TEXT_RE = re.compile(r">([^<>{}][^<>{]*?)<", re.S)
_JS_IMPORT_RE = re.compile(r"from\s+['\"]([^'\"]+)['\"]")
_LOCAL_CONTENT_MARKER = "<!-- generated-local-content -->"
_STRUCTURED_IGNORE_KEYS = {
    "icon",
    "iconurl",
    "image",
    "image_url",
    "initial",
    "logo",
    "orglogo",
    "width",
    "height",
}

app = FastAPI(title="CIROH Hub Change Intelligence API", version="0.2.0")

_allowed_origins = ["http://localhost:5173", "http://127.0.0.1:5173"]
_allowed_origins.extend(
    origin.strip()
    for origin in os.environ.get("DASHBOARD_ALLOWED_ORIGINS", "").split(",")
    if origin.strip()
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=list(dict.fromkeys(_allowed_origins)),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


def _load_changes():
    if not os.path.exists(CHANGES_PATH):
        return {
            "repo": "CIROH-UA/ciroh_hub",
            "last_checked": None,
            "latest_sha": None,
            "latest_commit_date": None,
            "latest_commit_message": None,
            "previous_sha": None,
            "changed_files_count": 0,
            "changed_files": [],
        }
    with open(CHANGES_PATH, "r", encoding="utf-8") as f:
        return json.load(f)


def _load_external():
    if not os.path.exists(EXTERNAL_REPOS_PATH):
        return {
            "last_checked": None,
            "total_repos": 0,
            "rendered_files": [],
            "repos": {},
            "errors": {},
        }
    with open(EXTERNAL_REPOS_PATH, "r", encoding="utf-8") as f:
        return json.load(f)


def _load_local_content_manifest():
    try:
        with open(LOCAL_CONTENT_MANIFEST_PATH, "r", encoding="utf-8") as f:
            manifest = json.load(f)
    except (OSError, json.JSONDecodeError):
        return {"version": 1, "excluded_prefixes": [], "pages": []}
    if not isinstance(manifest, dict):
        return {"version": 1, "excluded_prefixes": [], "pages": []}
    return manifest


def _local_rules_by_target():
    rules = {}
    for rule in _load_local_content_manifest().get("pages", []):
        if not isinstance(rule, dict):
            continue
        target = str(rule.get("target") or "").replace("\\", "/").lstrip("/")
        if target:
            rules[target] = rule
    return rules


def _is_excluded_content_path(path):
    normalized = str(path or "").replace("\\", "/").lstrip("/")
    prefixes = _load_local_content_manifest().get("excluded_prefixes", [])
    return any(normalized.startswith(str(prefix).lstrip("/")) for prefix in prefixes)


def _parse_iso(dt_str):
    if not dt_str:
        return None
    try:
        return datetime.fromisoformat(dt_str.replace("Z", "+00:00")).astimezone(timezone.utc)
    except ValueError:
        return None


def _init_counts(value=0):
    return {key: value for key in FILE_TYPE_KEYS}


def _classify_extension(path):
    _, ext = os.path.splitext(path or "")
    ext = ext.lower()
    if ext in FILE_TYPE_EXT_LOOKUP:
        return FILE_TYPE_EXT_LOOKUP[ext]
    if not ext:
        return "no_ext"
    return ext


def _label_for_key(key):
    for cfg in FILE_TYPE_DEFS:
        if cfg["key"] == key:
            return cfg["label"]
    if key == "no_ext":
        return "No Ext"
    if isinstance(key, str) and key.startswith("."):
        return key.upper()
    return str(key).upper()


def _is_excluded_path(path):
    parts = (path or "").replace("\\", "/").split("/")
    return any(part in TREE_EXCLUDES for part in parts if part)


def _scan_repo_totals(root_path):
    totals = _init_counts(0)
    total_files = 0
    if not os.path.isdir(root_path):
        return {"total": 0, "by_type": totals}
    for dirpath, dirnames, filenames in os.walk(root_path):
        dirnames[:] = [d for d in dirnames if d not in TREE_EXCLUDES]
        for name in filenames:
            total_files += 1
            key = _classify_extension(name)
            totals[key] = totals.get(key, 0) + 1
    return {"total": total_files, "by_type": totals}


def _scan_files_by_type(root_path):
    groups = {}
    if not os.path.isdir(root_path):
        return groups
    for dirpath, dirnames, filenames in os.walk(root_path):
        dirnames[:] = [d for d in dirnames if d not in TREE_EXCLUDES]
        for name in filenames:
            rel = os.path.relpath(os.path.join(dirpath, name), root_path).replace("\\", "/")
            key = _classify_extension(name)
            groups.setdefault(key, []).append(rel)
    for paths in groups.values():
        paths.sort()
    return groups


def _iter_markdown_files(root_path):
    if not os.path.isdir(root_path):
        return []
    for dirpath, dirnames, filenames in os.walk(root_path):
        dirnames[:] = [d for d in dirnames if d not in TREE_EXCLUDES]
        for name in filenames:
            _, ext = os.path.splitext(name)
            if ext.lower() not in MARKDOWN_EXTENSIONS:
                continue
            abs_path = os.path.join(dirpath, name)
            rel_path = os.path.relpath(abs_path, root_path).replace("\\", "/")
            if _is_excluded_content_path(rel_path):
                continue
            yield rel_path, abs_path


def _iter_js_route_files(root_path):
    if not os.path.isdir(root_path):
        return []
    for rel_path in sorted(JS_ROUTE_PAGE_ALLOWLIST):
        if _is_excluded_content_path(rel_path):
            continue
        abs_path = os.path.join(root_path, rel_path.replace("/", os.sep))
        _, ext = os.path.splitext(abs_path)
        if ext.lower() in JS_ROUTE_EXTENSIONS and os.path.isfile(abs_path):
            yield rel_path, abs_path


def _decode_js_string(raw):
    if raw is None:
        return ""
    text = raw
    replacements = {
        r"\n": " ",
        r"\r": " ",
        r"\t": " ",
        r"\'": "'",
        r'\"': '"',
        r"\`": "`",
        r"\\": "\\",
    }
    for old, new in replacements.items():
        text = text.replace(old, new)
    return html.unescape(text)


def _clean_js_text(text):
    text = _decode_js_string(text)
    text = re.sub(r"\{[^{}]*\}", " ", text)
    text = re.sub(r"<[^>]+>", " ", text)
    text = re.sub(r"\s+", " ", text).strip(" \t\r\n-:;,")
    if len(text) < 3:
        return ""
    if not re.search(r"[A-Za-z0-9]", text):
        return ""
    if text.endswith("$") or any(token in text for token in ("))}", ") : null}")):
        return ""
    lower = text.lower()
    if lower.startswith(("http://", "https://", "/img/", "./", "../", "@site/")):
        return ""
    if "tw-" in text or "dark:" in text or "clsx(" in text:
        return ""
    if re.fullmatch(r"[A-Za-z0-9_-]+", text) and ("-" in text or "_" in text):
        return ""
    return text


def _append_unique(lines, seen, text):
    cleaned = _clean_js_text(text)
    if not cleaned or cleaned in seen:
        return
    seen.add(cleaned)
    lines.append(cleaned)


def _js_match_value(match):
    for idx in (2, 3, 4):
        value = match.group(idx)
        if value is not None:
            return value
    return ""


def _extract_js_route_lines(content):
    lines = []
    seen = set()
    for match in _JS_KEYED_STRING_RE.finditer(content or ""):
        _append_unique(lines, seen, _js_match_value(match))
    for match in _JSX_TEXT_RE.finditer(content or ""):
        _append_unique(lines, seen, match.group(1))
    return lines


def _extract_all_js_strings(content):
    lines = []
    seen = set()
    for match in re.finditer(_JS_STRING_TOKEN, content or "", re.S):
        value = match.group(1) or match.group(2) or match.group(3) or ""
        _append_unique(lines, seen, value)
    return lines


def _static_js_tokens(content):
    punctuation = set("{}[]:,")
    i = 0
    while i < len(content):
        char = content[i]
        if char.isspace():
            i += 1
            continue
        if content.startswith("//", i):
            newline = content.find("\n", i + 2)
            i = len(content) if newline == -1 else newline + 1
            continue
        if content.startswith("/*", i):
            end = content.find("*/", i + 2)
            i = len(content) if end == -1 else end + 2
            continue
        if char in punctuation:
            yield (char, char)
            i += 1
            continue
        if char in {'"', "'", "`"}:
            quote = char
            i += 1
            raw = []
            while i < len(content):
                char = content[i]
                if char == "\\" and i + 1 < len(content):
                    raw.extend([char, content[i + 1]])
                    i += 2
                    continue
                if char == quote:
                    i += 1
                    break
                raw.append(char)
                i += 1
            yield ("value", _decode_js_string("".join(raw)))
            continue
        number = re.match(r"-?(?:\d+\.\d+|\d+)", content[i:])
        if number:
            raw = number.group(0)
            value = float(raw) if "." in raw else int(raw)
            yield ("value", value)
            i += len(raw)
            continue
        identifier = re.match(r"[A-Za-z_$][A-Za-z0-9_$-]*", content[i:])
        if identifier:
            raw = identifier.group(0)
            yield ("identifier", raw)
            i += len(raw)
            continue
        i += 1


class _StaticJsParser:
    def __init__(self, tokens):
        self.tokens = list(tokens)
        self.index = 0

    def _peek(self):
        if self.index >= len(self.tokens):
            return None
        return self.tokens[self.index]

    def _pop(self):
        token = self._peek()
        if token is not None:
            self.index += 1
        return token

    def parse(self):
        token = self._pop()
        if token is None:
            return None
        kind, value = token
        if kind == "[":
            items = []
            while self._peek() and self._peek()[0] != "]":
                items.append(self.parse())
                if self._peek() and self._peek()[0] == ",":
                    self._pop()
            if self._peek() and self._peek()[0] == "]":
                self._pop()
            return items
        if kind == "{":
            result = {}
            while self._peek() and self._peek()[0] != "}":
                key_token = self._pop()
                if key_token is None:
                    break
                key = str(key_token[1])
                if self._peek() and self._peek()[0] == ":":
                    self._pop()
                    result[key] = self.parse()
                else:
                    result[key] = key
                if self._peek() and self._peek()[0] == ",":
                    self._pop()
            if self._peek() and self._peek()[0] == "}":
                self._pop()
            return result
        if kind == "identifier":
            return {"true": True, "false": False, "null": None, "undefined": None}.get(
                value, value
            )
        return value


def _parse_static_js_literal(content):
    export = re.search(
        r"\bexport\s+(?:default|const\s+[A-Za-z_$][A-Za-z0-9_$]*\s*=)",
        content or "",
    )
    if not export:
        return None
    starts = [
        pos
        for pos in (
            content.find("[", export.end()),
            content.find("{", export.end()),
        )
        if pos != -1
    ]
    if not starts:
        return None
    start = min(starts)
    return _StaticJsParser(_static_js_tokens(content[start:])).parse()


def _field_label(key):
    raw = str(key).strip()
    if " " in raw:
        return raw
    label = re.sub(r"(?<!^)(?=[A-Z])", " ", raw).replace("_", " ")
    return label.strip().title()


def _format_scalar(key, value):
    if value is None or value == "":
        return ""
    value = str(value).strip()
    if not value:
        return ""
    if str(key).lower() in {
        "url",
        "link",
        "links",
        "github",
        "docs",
        "hydroshare",
        "zotero",
    }:
        return f"[{_field_label(key)}]({value})"
    return value


def _structured_markdown(value, level=3):
    lines = []
    if isinstance(value, list):
        for item in value:
            if isinstance(item, dict):
                lines.extend(_structured_markdown(item, level))
            elif isinstance(item, list):
                lines.extend(_structured_markdown(item, level))
            else:
                rendered = _format_scalar("value", item)
                if rendered:
                    lines.append(f"- {rendered}")
        return lines
    if not isinstance(value, dict):
        rendered = _format_scalar("value", value)
        return [rendered] if rendered else []

    if len(value) == 1:
        only_key, only_value = next(iter(value.items()))
        if isinstance(only_value, (dict, list)):
            lines.append(f"{'#' * level} {_field_label(only_key)}")
            lines.append("")
            lines.extend(_structured_markdown(only_value, level + 1))
            return lines

    heading_key = next((key for key in ("title", "name") if value.get(key)), None)
    if heading_key:
        lines.append(f"{'#' * level} {value[heading_key]}")
        lines.append("")

    for text_key in ("summary", "description", "quote"):
        rendered = _format_scalar(text_key, value.get(text_key))
        if rendered:
            lines.extend([rendered, ""])

    skipped = {heading_key, "summary", "description", "quote", "id"}
    for key, item in value.items():
        if key in skipped or str(key).lower() in _STRUCTURED_IGNORE_KEYS:
            continue
        label = _field_label(key)
        if isinstance(item, list):
            if not item:
                continue
            if all(not isinstance(entry, (dict, list)) for entry in item):
                lines.extend([f"**{label}:**", ""])
                for entry in item:
                    rendered = _format_scalar(key, entry)
                    if rendered:
                        lines.append(f"- {rendered}")
                lines.append("")
            else:
                lines.extend([f"{'#' * min(level + 1, 6)} {label}", ""])
                lines.extend(_structured_markdown(item, min(level + 2, 6)))
        elif isinstance(item, dict):
            lines.extend([f"**{label}:**", ""])
            for nested_key, nested_value in item.items():
                rendered = _format_scalar(nested_key, nested_value)
                if rendered:
                    lines.append(f"- {rendered}")
            lines.append("")
        else:
            rendered = _format_scalar(key, item)
            if rendered:
                lines.append(f"- **{label}:** {rendered}")
    return lines


def _render_structured_source(title, value):
    lines = [f"## {title}", ""]
    lines.extend(_structured_markdown(value))
    return "\n".join(lines).strip()


def _extract_component_markdown(title, content):
    lines = [f"## {title}", ""]
    text_lines = _extract_js_route_lines(content)
    lines.extend(f"- {line}" for line in text_lines)
    for match in re.finditer(r"\{\s*`((?:[^`\\]|\\.)*)`\s*\}", content or "", re.S):
        block = _decode_js_string(match.group(1)).strip()
        if "${" in block or "\n" not in block:
            continue
        if not re.search(r"\b(import|from|def|class|pip|conda|git|npm)\b", block):
            continue
        lines.extend(["", "```text", block, "```"])
    return "\n".join(lines).strip() if len(lines) > 2 else ""


def _render_blog_authors(content, source_abs, title):
    if not content.startswith("---"):
        return ""
    match = re.match(r"^---\s*\n(.*?)\n---", content, re.S)
    if not match:
        return ""
    frontmatter = {}
    if yaml is not None:
        try:
            frontmatter = yaml.safe_load(match.group(1)) or {}
        except Exception:
            frontmatter = {}
    author_ids = frontmatter.get("authors") if isinstance(frontmatter, dict) else None
    if isinstance(author_ids, str):
        author_ids = [author_ids]
    if not isinstance(author_ids, list) or not author_ids:
        return ""
    if yaml is None:
        return ""
    try:
        with open(source_abs, "r", encoding="utf-8") as f:
            authors = yaml.safe_load(f) or {}
    except Exception:
        return ""
    lines = [f"## {title}", ""]
    for author_id in author_ids:
        info = authors.get(author_id, {}) if isinstance(authors, dict) else {}
        name = info.get("name") or str(author_id)
        details = [info.get("title"), info.get("title2")]
        detail_text = ", ".join(str(item) for item in details if item)
        profile = info.get("url")
        rendered = f"- **{name}**"
        if detail_text:
            rendered += f" - {detail_text}"
        if profile:
            rendered += f" ([Profile]({profile}))"
        lines.append(rendered)
    return "\n".join(lines)


def _local_content_for_target(rel_path, target_content=""):
    normalized = str(rel_path or "").replace("\\", "/").lstrip("/")
    manifest = _load_local_content_manifest()
    rule = _local_rules_by_target().get(normalized, {})
    sources = list(rule.get("sources") or [])
    blog_rule = manifest.get("blog_authors") or {}
    blog_prefix = str(blog_rule.get("target_prefix") or "blog/").lstrip("/")
    if normalized.startswith(blog_prefix):
        sources.append(
            {
                "path": blog_rule.get("source", "blog/authors.yaml"),
                "kind": "blog_authors",
                "title": blog_rule.get("title", "Authors"),
            }
        )

    sections = []
    dependencies = []
    seen_paths = set()
    for source in sources:
        source_rel = str(source.get("path") or "").replace("\\", "/").lstrip("/")
        if not source_rel or source_rel in seen_paths:
            continue
        seen_paths.add(source_rel)
        source_abs = os.path.join(REPO_ROOT, source_rel.replace("/", os.sep))
        try:
            with open(source_abs, "r", encoding="utf-8") as f:
                source_content = f.read()
        except OSError:
            dependencies.append({"path": source_rel, "hash": None, "missing": True})
            continue
        source_hash = _sha256_text(source_content)
        dependencies.append({"path": source_rel, "hash": source_hash})
        kind = source.get("kind")
        title = source.get("title") or _title_from_path(source_rel)
        rendered = ""
        if kind == "json":
            try:
                rendered = _render_structured_source(title, json.loads(source_content))
            except json.JSONDecodeError:
                rendered = ""
        elif kind == "js_data":
            value = _parse_static_js_literal(source_content)
            if value not in (None, {}, []):
                rendered = _render_structured_source(title, value)
        elif kind == "jsx":
            rendered = _extract_component_markdown(title, source_content)
        elif kind == "blog_authors":
            rendered = _render_blog_authors(target_content, source_abs, title)
        if rendered:
            sections.append(rendered)
    return rule, sections, dependencies


def _inject_local_content(text, rule, sections):
    if not sections:
        return text
    rendered = f"\n\n{_LOCAL_CONTENT_MARKER}\n\n" + "\n\n".join(sections).strip() + "\n"
    component = rule.get("component") if isinstance(rule, dict) else None
    if component:
        pattern = re.compile(
            rf"(<{re.escape(component)}\b[^>]*\s*/>|<{re.escape(component)}\b[^>]*>.*?</{re.escape(component)}>)",
            re.S,
        )
        if pattern.search(text):
            return pattern.sub(lambda match: match.group(1) + rendered, text, count=1)
    if text.startswith("---") and not rule:
        match = re.match(r"^(---\s*\n.*?\n---)", text, re.S)
        if match:
            return text[: match.end()] + rendered + text[match.end() :]
    return text.rstrip() + rendered


def _resolve_js_import_path(import_path, source_rel_path):
    if import_path.startswith("@site/"):
        rel = import_path[len("@site/") :]
    elif import_path.startswith("."):
        rel = os.path.normpath(os.path.join(os.path.dirname(source_rel_path), import_path))
    else:
        return None
    rel = rel.replace("\\", "/")
    base, ext = os.path.splitext(rel)
    candidates = [rel] if ext else [rel + suffix for suffix in (".js", ".jsx", ".ts", ".tsx", ".json")]
    for candidate in candidates:
        abs_path = os.path.join(REPO_ROOT, candidate.replace("/", os.sep))
        if os.path.isfile(abs_path):
            return candidate, abs_path
    return None


def _extract_imported_data_text(content, source_rel_path):
    sections = []
    data_hash_parts = []
    for match in _JS_IMPORT_RE.finditer(content or ""):
        import_path = match.group(1)
        if "/src/data/" not in import_path and not import_path.startswith("@site/src/data/"):
            continue
        resolved = _resolve_js_import_path(import_path, source_rel_path)
        if not resolved:
            continue
        data_rel, data_abs = resolved
        try:
            with open(data_abs, "r", encoding="utf-8") as f:
                data_content = f.read()
        except OSError:
            continue
        data_hash_parts.append(data_content)
        try:
            if data_rel.lower().endswith(".json"):
                value = json.loads(data_content)
            else:
                value = _parse_static_js_literal(data_content)
        except (json.JSONDecodeError, ValueError):
            value = None
        lines = _structured_markdown(value) if value not in (None, {}, []) else []
        if lines:
            sections.append((data_rel, lines))
    return sections, "\n".join(data_hash_parts)


def _first_keyed_js_value(content, key):
    key_re = re.compile(
        rf"\b{re.escape(key)}\b\s*(?:=|:)\s*(?:\{{\s*)?{_JS_STRING_TOKEN}",
        re.I | re.S,
    )
    match = key_re.search(content or "")
    if not match:
        return None
    return _clean_js_text(match.group(1) or match.group(2) or match.group(3) or "")


def _js_route_path(rel_path):
    route = rel_path
    if route.startswith("src/pages/"):
        route = route[len("src/pages/") :]
    route = os.path.splitext(route)[0]
    if route == "index":
        return "/"
    if route.endswith("/index"):
        route = route[: -len("/index")]
    return route.strip("/")


def _js_route_output_rel(rel_path):
    route = _js_route_path(rel_path)
    stem = "home" if route == "/" else route.strip("/").replace("/", "__")
    return f"{JS_ROUTE_OUTPUT_DIR}/{stem}.mdx"


def _yaml_string(value):
    return json.dumps(str(value or ""), ensure_ascii=False)


def _render_js_route_markdown(
    rel_path,
    content,
    date_str,
    local_sections=None,
    local_dependency_paths=None,
):
    route = _js_route_path(rel_path)
    title = JS_ROUTE_TITLE_OVERRIDES.get(rel_path) or _first_keyed_js_value(content, "title") or _title_from_path(rel_path)
    description = (
        _first_keyed_js_value(content, "description")
        or _first_keyed_js_value(content, "tagline")
        or title
    )
    page_lines = _extract_js_route_lines(content)
    data_sections, _data_hash = _extract_imported_data_text(content, rel_path)
    local_dependency_paths = set(local_dependency_paths or [])
    data_sections = [
        section for section in data_sections if section[0] not in local_dependency_paths
    ]

    frontmatter = [
        "---",
        f"title: {_yaml_string(title)}",
        f"description: {_yaml_string(description)}",
        f'Last updated date: "{date_str or ""}"',
        f"path: {_yaml_string(route)}",
        "generated_from_js: true",
        f"source_path: {_yaml_string(rel_path)}",
        "---",
        "",
        f"# {title}",
        "",
    ]
    body = []
    for line in page_lines:
        if line == title:
            continue
        body.append(f"- {line}")
    for data_rel, lines in data_sections:
        body.extend(["", f"## Data from {data_rel}", ""])
        body.extend(lines)
    for section in local_sections or []:
        body.extend(["", section])
    if not body:
        body.append(f"- Rendered page source: {rel_path}")
    return "\n".join(frontmatter + body).rstrip() + "\n"


def _external_download_map(external):
    mapping = {}
    for entry in external.get("rendered_files") or []:
        repo = entry.get("external_repo")
        tracked = entry.get("tracked_path") or "README.md"
        downloaded = entry.get("downloaded_path")
        if repo and tracked and downloaded:
            mapping[(repo, tracked)] = downloaded
    return mapping


def _external_meta_map(external):
    meta = {}
    for entry in external.get("rendered_files") or []:
        repo = entry.get("external_repo")
        tracked = entry.get("tracked_path") or "README.md"
        if not repo:
            continue
        key = (repo, tracked)
        latest_sha = entry.get("latest_sha")
        latest_commit_date = entry.get("latest_commit_date")
        downloaded = entry.get("downloaded_path")
        existing = meta.get(key, {})
        if latest_sha or not existing.get("latest_sha"):
            existing["latest_sha"] = latest_sha
        if latest_commit_date or not existing.get("latest_commit_date"):
            existing["latest_commit_date"] = latest_commit_date
        if downloaded:
            existing["downloaded_path"] = downloaded
        meta[key] = existing
    return meta


def _resolve_external_path(attrs, download_root, external_map):
    owner = (attrs.get("username") or "").strip()
    repo = (attrs.get("repo") or "").strip()
    if not owner or not repo:
        return None, None, None
    owner_repo = f"{owner}/{repo}"
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
    rel_download = external_map.get((owner_repo, file_path))
    if not rel_download:
        rel_download = os.path.join(owner, repo, file_path).replace("\\", "/")
    abs_path = None
    if download_root:
        abs_path = os.path.join(download_root, rel_download.replace("/", os.sep))
    return owner_repo, file_path, abs_path


def _wiki_page_name(path):
    page = (path or "home").strip().strip("/")
    if page.endswith(".md"):
        page = page[:-3]
    return page or "home"


def _wiki_tracked_path(path):
    return f"wiki/{_wiki_page_name(path)}.md"


def _resolve_wiki_path(attrs, download_root, external_map):
    owner = (attrs.get("username") or "").strip()
    repo = (attrs.get("repo") or "").strip()
    if not owner or not repo:
        return None, None, None
    owner_repo = f"{owner}/{repo}"
    file_path = _wiki_tracked_path(attrs.get("path"))
    rel_download = external_map.get((owner_repo, file_path))
    if not rel_download:
        rel_download = os.path.join(owner, repo, file_path).replace("\\", "/")
    abs_path = None
    if download_root:
        abs_path = os.path.join(download_root, rel_download.replace("/", os.sep))
    return owner_repo, file_path, abs_path


def _extract_github_readme_refs(text):
    refs = []
    pattern = re.compile(r"<GitHubReadme\b[^>]*\/>|<GitHubReadme\b[^>]*>.*?</GitHubReadme>", re.S)
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
        refs.append({"repo": f"{owner}/{repo}", "path": file_path, "kind": "readme"})
    pattern = re.compile(r"<GitHubWikiPage\b[^>]*\/>|<GitHubWikiPage\b[^>]*>.*?</GitHubWikiPage>", re.S)
    for match in pattern.finditer(text or ""):
        tag = match.group(0)
        attrs = {m.group(1): m.group(2) for m in _ATTR_RE.finditer(tag)}
        owner = (attrs.get("username") or "").strip()
        repo = (attrs.get("repo") or "").strip()
        if not owner or not repo:
            continue
        refs.append(
            {
                "repo": f"{owner}/{repo}",
                "path": _wiki_tracked_path(attrs.get("path")),
                "kind": "wiki",
            }
        )
    return refs


def _sha256_text(text):
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def _format_last_updated(dt):
    if not dt:
        return None
    return dt.astimezone(timezone.utc).strftime("%m/%d/%Y")


def _title_from_path(rel_path):
    name = os.path.splitext(os.path.basename(rel_path or ""))[0]
    if not name:
        return "Untitled"
    return name.replace("-", " ").replace("_", " ").strip().title() or "Untitled"


def _ensure_frontmatter_last_updated(content, date_str, fallback_title):
    if not date_str:
        return content
    lines = content.splitlines()
    if lines and lines[0].strip() == "---":
        end_idx = None
        for idx in range(1, len(lines)):
            if lines[idx].strip() == "---":
                end_idx = idx
                break
        if end_idx is not None:
            frontmatter = lines[1:end_idx]
            keys = ("Last updated date", "Last updated data", "last_updated_date", "last_updated")
            updated = False
            for i, line in enumerate(frontmatter):
                for key in keys:
                    if re.match(rf"^{re.escape(key)}\s*:", line):
                        frontmatter[i] = f'{key}: "{date_str}"'
                        updated = True
                        break
                if updated:
                    break
            if not updated:
                frontmatter.append(f'Last updated date: "{date_str}"')
            rest = "\n".join(lines[end_idx + 1 :])
            return "\n".join(["---", *frontmatter, "---", rest]).rstrip() + "\n"
    # No frontmatter found; add minimal block
    title = _infer_title_from_content(content) or fallback_title
    frontmatter = [
        f'title: "{title}"',
        f'description: "{title}"',
        f'Last updated date: "{date_str}"',
    ]
    return "\n".join(["---", *frontmatter, "---", "", content.lstrip()]).rstrip() + "\n"


def _infer_title_from_content(content):
    for line in content.splitlines():
        stripped = line.strip()
        if stripped.startswith("# "):
            return stripped[2:].strip()
    return None


def _git_last_commit_date(repo_root, rel_path, cache):
    if not repo_root or not os.path.isdir(os.path.join(repo_root, ".git")):
        return None
    if rel_path in cache:
        return cache[rel_path]
    cmd = ["git", "-C", repo_root, "log", "-1", "--format=%cI", "--", rel_path]
    try:
        result = subprocess.run(
            cmd,
            check=True,
            capture_output=True,
            text=True,
            timeout=10,
        )
    except (subprocess.SubprocessError, FileNotFoundError):
        cache[rel_path] = None
        return None
    iso = result.stdout.strip()
    dt = _parse_iso(iso)
    cache[rel_path] = dt
    return dt


def _compute_last_updated(rel_path, abs_path, content, external_meta, git_cache):
    refs = _extract_github_readme_refs(content)
    external_dates = []
    for ref in refs:
        meta = external_meta.get((ref["repo"], ref["path"]), {})
        dt = _parse_iso(meta.get("latest_commit_date"))
        if dt:
            external_dates.append(dt)
    external_latest = max(external_dates) if external_dates else None
    local_dt = _git_last_commit_date(REPO_ROOT, rel_path, git_cache)
    if not local_dt:
        try:
            local_dt = datetime.fromtimestamp(os.path.getmtime(abs_path), tz=timezone.utc)
        except OSError:
            local_dt = None
    if external_latest and local_dt:
        return max(external_latest, local_dt)
    return external_latest or local_dt


def _include_local_dependency_dates(current_dt, dependencies, git_cache):
    dates = [current_dt] if current_dt else []
    for dependency in dependencies or []:
        rel_path = dependency.get("path")
        if not rel_path or dependency.get("missing"):
            continue
        dep_dt = _git_last_commit_date(REPO_ROOT, rel_path, git_cache)
        if not dep_dt:
            dep_abs = os.path.join(REPO_ROOT, rel_path.replace("/", os.sep))
            try:
                dep_dt = datetime.fromtimestamp(os.path.getmtime(dep_abs), tz=timezone.utc)
            except OSError:
                dep_dt = None
        if dep_dt:
            dates.append(dep_dt)
    return max(dates) if dates else None


def _load_manifest(path):
    if not path or not os.path.exists(path):
        return {}
    try:
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
    except (OSError, json.JSONDecodeError):
        return {}
    if not isinstance(data, dict) or data.get("version") != MIXED_EXPORT_VERSION:
        return {}
    return data


def _save_manifest(path, data):
    if not path:
        return
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, sort_keys=True)


def _merge_github_readme(text, external_map, download_root):
    if "GitHubReadme" not in text and "GitHubWikiPage" not in text:
        return text

    def replace_readme_tag(match):
        tag = match.group(0)
        attrs = {m.group(1): m.group(2) for m in _ATTR_RE.finditer(tag)}
        owner_repo, file_path, abs_path = _resolve_external_path(attrs, download_root, external_map)
        if not owner_repo or not file_path:
            return f"{tag}\n\n> External README reference missing username/repo.\n"
        content = None
        if abs_path and os.path.exists(abs_path):
            try:
                with open(abs_path, "r", encoding="utf-8") as f:
                    content = f.read()
            except OSError:
                content = None
        if content is None:
            return f"{tag}\n\n> External README not found for {owner_repo}/{file_path}\n"
        return f"{tag}\n\n{content.strip()}"

    def replace_wiki_tag(match):
        tag = match.group(0)
        attrs = {m.group(1): m.group(2) for m in _ATTR_RE.finditer(tag)}
        owner_repo, file_path, abs_path = _resolve_wiki_path(attrs, download_root, external_map)
        if not owner_repo or not file_path:
            return f"{tag}\n\n> External GitHub wiki reference missing username/repo.\n"
        content = None
        if abs_path and os.path.exists(abs_path):
            try:
                with open(abs_path, "r", encoding="utf-8") as f:
                    content = f.read()
            except OSError:
                content = None
        if content is None:
            return f"{tag}\n\n> External GitHub wiki page not found for {owner_repo}/{file_path}\n"
        pretty_path = file_path[len("wiki/") : -len(".md")] if file_path.startswith("wiki/") else file_path
        pretty_url = f"https://github.com/{owner_repo}/wiki/{pretty_path}"
        return f"{tag}\n\n> Content rendered from {pretty_url}\n\n{content.strip()}"

    readme_pattern = re.compile(r"<GitHubReadme\b[^>]*\/>|<GitHubReadme\b[^>]*>.*?</GitHubReadme>", re.S)
    wiki_pattern = re.compile(r"<GitHubWikiPage\b[^>]*\/>|<GitHubWikiPage\b[^>]*>.*?</GitHubWikiPage>", re.S)
    merged = readme_pattern.sub(replace_readme_tag, text)
    merged = wiki_pattern.sub(replace_wiki_tag, merged)
    return merged


# Match: import { ... } from "./cardContent" or './cardContent' (optional semicolon, single line or multiline)
_IMPORT_LOCAL_CARD_CONTENT_RE = re.compile(
    r'import\s*\{[\s\S]*?\}\s*from\s*["\']\.\/cardContent(?:\.js)?["\']\s*;?',
    re.MULTILINE,
)

# Match: import Identifier from 'path' or "path" (optional semicolon, optional comment)
_IMPORT_DEFAULT_RE = re.compile(
    r"^\s*import\s+(\w+)\s+from\s+['\"]([^'\"]+)['\"]\s*;?\s*(?://.*)?$",
    re.MULTILINE,
)


def _strip_js_imports_and_use_paths(js_content: str) -> str:
    """Remove import lines and replace imported identifiers with path strings (e.g. /img/...)."""
    lines = js_content.split("\n")
    rest_lines = []
    name_to_path = {}
    for line in lines:
        m = _IMPORT_DEFAULT_RE.match(line)
        if m:
            name, path = m.group(1), m.group(2)
            # @site/static/img/... -> /img/...
            if path.startswith("@site/static/"):
                path = "/" + path[len("@site/static/"):]
            elif path.startswith("@"):
                path = "/" + path.split("/", 1)[-1] if "/" in path else path
            name_to_path[name] = path
            continue
        rest_lines.append(line)
    rest = "\n".join(rest_lines)
    for name, path in name_to_path.items():
        # Replace identifier as whole word with quoted path string
        rest = re.sub(r"\b" + re.escape(name) + r"\b", repr(path), rest)
    return rest.strip()


def _inline_local_js_imports(content: str, repo_file_path: str) -> str:
    """If content imports from ./cardContent (or ./cardContent.js), inline that file's content (exports only, no import lines)."""
    if not _IMPORT_LOCAL_CARD_CONTENT_RE.search(content):
        return content
    dir_path = os.path.dirname(repo_file_path)
    js_path = os.path.join(dir_path, "cardContent.js")
    if not os.path.isfile(js_path):
        return content
    try:
        with open(js_path, "r", encoding="utf-8") as f:
            js_content = f.read()
    except OSError:
        return content
    js_inlined = _strip_js_imports_and_use_paths(js_content)
    return _IMPORT_LOCAL_CARD_CONTENT_RE.sub(js_inlined + "\n\n", content, count=1)


def _frontmatter_path_for_output_rel(rel_path):
    """Return the public route path represented by a mixed-doc file path.

    Docusaurus maps files below ``src/pages`` directly from the domain root,
    so ``src/pages/impact.mdx`` represents ``/impact`` rather than
    ``/src/pages/impact``.
    """
    return public_route_from_mixed_doc_path(rel_path)


def _add_path_frontmatter(output_root):
    """Add or update path: in YAML frontmatter of all .mdx/.md under output_root."""
    if not output_root or not os.path.isdir(output_root):
        return
    path_key_re = re.compile(r"^path:\s*.*$", re.MULTILINE)
    for root, _dirs, files in os.walk(output_root):
        for name in files:
            if not (name.endswith(".mdx") or name.endswith(".md")):
                continue
            filepath = os.path.join(root, name)
            try:
                with open(filepath, "r", encoding="utf-8") as f:
                    content = f.read()
            except OSError:
                continue
            if not content.startswith("---\n"):
                continue
            idx = content.find("\n---", 4)
            if idx == -1:
                continue
            frontmatter = content[4:idx]
            body = content[idx + 4 :]
            if re.search(r"^generated_from_js:\s*true\s*$", frontmatter, re.MULTILINE):
                continue
            rel = os.path.relpath(filepath, output_root)
            path_value = _frontmatter_path_for_output_rel(rel)
            path_line = f'path: "{path_value}"'
            if path_key_re.search(frontmatter):
                new_frontmatter = path_key_re.sub(path_line, frontmatter, count=1)
            else:
                new_frontmatter = frontmatter.rstrip()
                if new_frontmatter and not new_frontmatter.endswith("\n"):
                    new_frontmatter += "\n"
                new_frontmatter += path_line + "\n"
            new_content = "---\n" + new_frontmatter + "\n---" + body
            if new_content != content:
                try:
                    with open(filepath, "w", encoding="utf-8") as f:
                        f.write(new_content)
                except OSError:
                    pass


def _write_mixed_markdown(output_root, external_map, external_meta, download_root, external_last_checked=None, force=False):
    if not output_root:
        return {"written": 0, "skipped": 0, "removed": 0, "total": 0}
    os.makedirs(output_root, exist_ok=True)

    manifest = _load_manifest(MIXED_MANIFEST_PATH)
    prev_files = {} if force else (manifest.get("files", {}) if isinstance(manifest, dict) else {})
    next_files = {}
    written = 0
    skipped = 0
    git_cache = {}

    for rel_path, abs_path in _iter_markdown_files(REPO_ROOT):
        try:
            with open(abs_path, "r", encoding="utf-8") as f:
                content = f.read()
        except OSError:
            continue
        local_rule, local_sections, local_dependencies = _local_content_for_target(
            rel_path, content
        )
        dependency_state = json.dumps(
            local_dependencies, sort_keys=True, ensure_ascii=False
        )
        local_hash = _sha256_text(content + "\n" + dependency_state)
        refs = _extract_github_readme_refs(content)
        external_refs = []
        for ref in refs:
            meta = external_meta.get((ref["repo"], ref["path"]), {})
            external_refs.append(
                {
                    "repo": ref["repo"],
                    "path": ref["path"],
                    "latest_sha": meta.get("latest_sha"),
                }
            )
        external_refs.sort(key=lambda r: (r["repo"], r["path"]))

        prev = prev_files.get(rel_path, {})
        should_update = True
        if (
            prev
            and prev.get("local_hash") == local_hash
            and prev.get("external_refs") == external_refs
            and prev.get("local_dependencies") == local_dependencies
        ):
            should_update = False

        if should_update:
            last_updated_dt = _compute_last_updated(rel_path, abs_path, content, external_meta, git_cache)
            last_updated_dt = _include_local_dependency_dates(
                last_updated_dt, local_dependencies, git_cache
            )
            date_str = _format_last_updated(last_updated_dt)
            with_meta = _ensure_frontmatter_last_updated(content, date_str, _title_from_path(rel_path))
            merged = _merge_github_readme(with_meta, external_map, download_root)
            merged = _inline_local_js_imports(merged, abs_path)
            merged = _inject_local_content(merged, local_rule, local_sections)
            target_path = os.path.join(output_root, rel_path.replace("/", os.sep))
            os.makedirs(os.path.dirname(target_path), exist_ok=True)
            try:
                with open(target_path, "w", encoding="utf-8") as f:
                    f.write(merged)
                written += 1
            except OSError:
                continue
        else:
            skipped += 1

        next_files[rel_path] = {
            "local_hash": local_hash,
            "external_refs": external_refs,
            "local_dependencies": local_dependencies,
            "output_rel": rel_path,
        }

    for rel_path, abs_path in _iter_js_route_files(REPO_ROOT):
        try:
            with open(abs_path, "r", encoding="utf-8") as f:
                content = f.read()
        except OSError:
            continue
        data_sections, data_hash = _extract_imported_data_text(content, rel_path)
        _local_rule, local_sections, local_dependencies = _local_content_for_target(
            rel_path, content
        )
        dependency_state = json.dumps(
            local_dependencies, sort_keys=True, ensure_ascii=False
        )
        local_hash = _sha256_text(
            content + "\n" + data_hash + "\n" + dependency_state
        )
        output_rel = _js_route_output_rel(rel_path)

        prev = prev_files.get(rel_path, {})
        should_update = True
        if (
            prev
            and prev.get("local_hash") == local_hash
            and prev.get("output_rel") == output_rel
            and prev.get("source_type") == "js_route"
            and prev.get("local_dependencies") == local_dependencies
        ):
            should_update = False

        if should_update:
            last_updated_dt = _compute_last_updated(rel_path, abs_path, content, external_meta, git_cache)
            last_updated_dt = _include_local_dependency_dates(
                last_updated_dt, local_dependencies, git_cache
            )
            date_str = _format_last_updated(last_updated_dt)
            generated = _render_js_route_markdown(
                rel_path,
                content,
                date_str,
                local_sections=local_sections,
                local_dependency_paths=[dep.get("path") for dep in local_dependencies],
            )
            target_path = os.path.join(output_root, output_rel.replace("/", os.sep))
            os.makedirs(os.path.dirname(target_path), exist_ok=True)
            try:
                with open(target_path, "w", encoding="utf-8") as f:
                    f.write(generated)
                written += 1
            except OSError:
                continue
        else:
            skipped += 1

        next_files[rel_path] = {
            "local_hash": local_hash,
            "external_refs": [],
            "output_rel": output_rel,
            "source_type": "js_route",
            "imported_data_files": [data_rel for data_rel, _lines in data_sections],
            "local_dependencies": local_dependencies,
        }

    removed = 0
    for rel_path, prev in prev_files.items():
        if rel_path in next_files:
            continue
        target_rel = prev.get("output_rel") if isinstance(prev, dict) else None
        if not target_rel:
            target_rel = rel_path
        target_path = os.path.join(output_root, target_rel.replace("/", os.sep))
        if os.path.exists(target_path):
            try:
                os.remove(target_path)
                removed += 1
            except OSError:
                continue

    manifest_out = {
        "version": MIXED_EXPORT_VERSION,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "repo_root": REPO_ROOT,
        "output_root": output_root,
        "external_last_checked": external_last_checked,
        "files": next_files,
    }
    _save_manifest(MIXED_MANIFEST_PATH, manifest_out)
    total = len(next_files)

    # Add/update path in frontmatter for all MD/MDX in mixed_docs
    _add_path_frontmatter(output_root)

    return {"written": written, "skipped": skipped, "removed": removed, "total": total}


def _changes_by_type(changed_files):
    counts = {key: {"changed": 0, "deleted": 0} for key in FILE_TYPE_KEYS}
    for entry in changed_files or []:
        filename = entry.get("filename") or ""
        status = (entry.get("status") or "").lower()
        key = _classify_extension(filename)
        if key not in counts:
            counts[key] = {"changed": 0, "deleted": 0}
        if status == "removed":
            counts[key]["deleted"] += 1
        else:
            counts[key]["changed"] += 1
    totals = {
        "changed": sum(v["changed"] for v in counts.values()),
        "deleted": sum(v["deleted"] for v in counts.values()),
    }
    return {"by_type": counts, "totals": totals}


def _git_changed_files_since(repo_root, since_dt):
    if not repo_root or not os.path.isdir(os.path.join(repo_root, ".git")):
        return set(), None
    since_arg = since_dt.strftime("%Y-%m-%dT%H:%M:%SZ")
    cmd = ["git", "-C", repo_root, "log", "--name-only", "--pretty=format:", "--since", since_arg]
    try:
        result = subprocess.run(
            cmd,
            check=True,
            capture_output=True,
            text=True,
            timeout=20,
        )
    except (subprocess.SubprocessError, FileNotFoundError):
        return set(), None
    files = set()
    for line in result.stdout.splitlines():
        path = line.strip()
        if not path or _is_excluded_path(path):
            continue
        files.add(path)
    return files, "git"


def _counts_for_files(files):
    counts = _init_counts(0)
    for path in files:
        key = _classify_extension(path)
        counts[key] = counts.get(key, 0) + 1
    return {"total": len(files), "by_type": counts}


def _external_md_index(external):
    entries = external.get("rendered_files") or []
    index = {}
    for entry in entries:
        repo = entry.get("external_repo")
        tracked = entry.get("tracked_path") or "README.md"
        if not repo:
            continue
        key = (repo, tracked)
        latest = _parse_iso(entry.get("latest_commit_date"))
        record = index.get(key)
        if not record:
            index[key] = {"latest": latest, "changed": entry.get("change_state") == "changed"}
            continue
        if latest and (not record["latest"] or latest > record["latest"]):
            record["latest"] = latest
        if entry.get("change_state") == "changed":
            record["changed"] = True
    return index


def _build_file_stats(changes, external):
    now = datetime.now(timezone.utc)
    daily_start = now - timedelta(days=1)
    weekly_start = now - timedelta(days=7)

    repo_totals = _scan_repo_totals(REPO_ROOT)
    changes_rollup = _changes_by_type(changes.get("changed_files"))

    daily_files, daily_source = _git_changed_files_since(REPO_ROOT, daily_start)
    weekly_files, weekly_source = _git_changed_files_since(REPO_ROOT, weekly_start)

    daily_counts = _counts_for_files(daily_files) if daily_source else {"total": None, "by_type": {}}
    weekly_counts = _counts_for_files(weekly_files) if weekly_source else {"total": None, "by_type": {}}

    external_index = _external_md_index(external)
    external_total = len(external_index)
    external_changed = sum(1 for info in external_index.values() if info["changed"])
    external_daily = sum(1 for info in external_index.values() if info["latest"] and info["latest"] >= daily_start)
    external_weekly = sum(1 for info in external_index.values() if info["latest"] and info["latest"] >= weekly_start)

    rows = []
    all_keys = set()
    all_keys.update(repo_totals["by_type"].keys())
    all_keys.update(changes_rollup["by_type"].keys())
    all_keys.update(daily_counts["by_type"].keys())
    all_keys.update(weekly_counts["by_type"].keys())
    known_keys = FILE_TYPE_KEYS
    other_keys = sorted(key for key in all_keys if key not in known_keys)
    ordered_keys = [*known_keys, *other_keys]
    for key in ordered_keys:
        rows.append(
            {
                "key": key,
                "label": _label_for_key(key),
                "total": repo_totals["by_type"].get(key, 0),
                "changed": changes_rollup["by_type"].get(key, {}).get("changed", 0),
                "deleted": changes_rollup["by_type"].get(key, {}).get("deleted", 0),
                "daily": None if daily_counts["total"] is None else daily_counts["by_type"].get(key, 0),
                "weekly": None if weekly_counts["total"] is None else weekly_counts["by_type"].get(key, 0),
            }
        )

    rows.append(
        {
            "key": "external_md",
            "label": "External MD",
            "total": external_total,
            "changed": external_changed,
            "deleted": 0,
            "daily": external_daily,
            "weekly": external_weekly,
        }
    )

    total_changed = changes_rollup["totals"]["changed"]
    total_deleted = changes_rollup["totals"]["deleted"]
    total_daily = daily_counts["total"]
    total_weekly = weekly_counts["total"]

    rows.append(
        {
            "key": "total",
            "label": "Total",
            "total": repo_totals["total"] + external_total,
            "changed": total_changed,
            "deleted": total_deleted,
            "daily": total_daily,
            "weekly": total_weekly,
        }
    )

    change_profile = {
        "total_changes": changes.get("changed_files_count") or 0,
        "by_type": {
            key: {
                "changed": data["changed"],
                "deleted": data["deleted"],
                "total": data["changed"] + data["deleted"],
            }
            for key, data in changes_rollup["by_type"].items()
        },
    }

    return {
        "generated_at": now.isoformat(),
        "last_checked": changes.get("last_checked"),
        "external_last_checked": external.get("last_checked"),
        "windows": {
            "daily_start": daily_start.isoformat(),
            "weekly_start": weekly_start.isoformat(),
            "now": now.isoformat(),
        },
        "profile": {
            "total_files": repo_totals["total"],
            "md": repo_totals["by_type"]["md"],
            "mdx": repo_totals["by_type"]["mdx"],
            "images": repo_totals["by_type"]["images"],
            "page_components": repo_totals["by_type"]["page_components"],
            "yml": repo_totals["by_type"]["yml"],
        },
        "change_profile": change_profile,
        "table": {
            "rows": rows,
            "sources": {
                "daily": daily_source or "unavailable",
                "weekly": weekly_source or "unavailable",
                "external": "external_repos",
                "totals": "filesystem",
            },
        },
    }


def _status_counts(changed_files):
    counts = {"added": 0, "modified": 0, "removed": 0, "renamed": 0, "other": 0}
    for f in changed_files or []:
        status = (f.get("status") or "").lower()
        if status in counts:
            counts[status] += 1
        else:
            counts["other"] += 1
    return counts


def _top_paths(changed_files, limit=6):
    buckets = {}
    for f in changed_files or []:
        path = f.get("filename") or ""
        if "/" in path:
            key = path.split("/")[0]
        else:
            key = "(root)"
        buckets[key] = buckets.get(key, 0) + 1
    ranked = sorted(buckets.items(), key=lambda kv: kv[1], reverse=True)
    return [{"path": k, "count": v} for k, v in ranked[:limit]]


def _scan_tree(root_path):
    entries = []
    truncated = False

    def walk(path, depth):
        nonlocal truncated
        if truncated or depth > TREE_MAX_DEPTH:
            return
        try:
            with os.scandir(path) as it:
                items = sorted(
                    [e for e in it if e.name not in TREE_EXCLUDES],
                    key=lambda e: (not e.is_dir(follow_symlinks=False), e.name.lower()),
                )
        except OSError:
            return
        for entry in items:
            if truncated:
                return
            rel = os.path.relpath(entry.path, root_path).replace("\\", "/")
            entry_type = "dir" if entry.is_dir(follow_symlinks=False) else "file"
            entries.append({"path": rel, "type": entry_type, "depth": depth})
            if len(entries) >= TREE_MAX_ENTRIES:
                truncated = True
                return
            if entry_type == "dir":
                walk(entry.path, depth + 1)

    if os.path.isdir(root_path):
        walk(root_path, 0)

    return {
        "root": os.path.basename(root_path.rstrip("\\/")) or root_path,
        "max_depth": TREE_MAX_DEPTH,
        "truncated": truncated,
        "entries": entries,
    }


def _metrics(changes):
    changed = changes.get("changed_files_count") or 0
    latest_commit = _parse_iso(changes.get("latest_commit_date"))
    last_checked = _parse_iso(changes.get("last_checked"))

    now = datetime.now(timezone.utc)
    freshness_hours = None
    if latest_commit:
        freshness_hours = max(0, int((now - latest_commit).total_seconds() / 3600))

    momentum = min(100, 25 + changed * 12)
    if freshness_hours is not None:
        momentum = max(10, momentum - int(freshness_hours / 12))

    cadence = "weekly"
    if last_checked and latest_commit:
        delta_days = (now - last_checked).days
        cadence = "weekly" if delta_days >= 6 else "recent"

    return {
        "signal_score": min(100, momentum),
        "freshness_hours": freshness_hours,
        "cadence": cadence,
    }


def _operator_mode():
    return "token" if os.environ.get("DASHBOARD_OPERATOR_TOKEN") else "local_only"


def _request_is_loopback(request):
    host = request.client.host if request.client else ""
    try:
        return ipaddress.ip_address(host).is_loopback
    except ValueError:
        return host == "localhost"


def _require_operator(request):
    configured_token = os.environ.get("DASHBOARD_OPERATOR_TOKEN")
    if configured_token:
        provided_token = request.headers.get("x-ciroh-operator-key", "")
        authorization = request.headers.get("authorization", "")
        if not provided_token and authorization.lower().startswith("bearer "):
            provided_token = authorization[7:].strip()
        if not provided_token or not hmac.compare_digest(provided_token, configured_token):
            raise HTTPException(status_code=401, detail="A valid operator key is required.")
        return
    if not _request_is_loopback(request):
        raise HTTPException(
            status_code=403,
            detail="Pipeline execution is local-only unless DASHBOARD_OPERATOR_TOKEN is configured.",
        )


@app.get("/api/health")
def health():
    return {
        "status": "ok",
        "time": datetime.now(timezone.utc).isoformat(),
        "operator_mode": _operator_mode(),
    }


@app.get("/api/changes")
def changes():
    return _load_changes()


@app.get("/api/summary")
def summary():
    changes = _load_changes()
    external = _load_external()
    return {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "changes": changes,
        "status_counts": _status_counts(changes.get("changed_files")),
        "top_paths": _top_paths(changes.get("changed_files")),
        "metrics": _metrics(changes),
        "file_stats": _build_file_stats(changes, external),
    }


@app.get("/api/tree")
def tree():
    return _scan_tree(REPO_ROOT)


@app.get("/api/file-type")
def file_type(key: str):
    groups = _scan_files_by_type(REPO_ROOT)
    files = groups.get(key, [])
    return {
        "key": key,
        "label": _label_for_key(key),
        "total": len(files),
        "files": files,
    }


@app.get("/api/export-markdown")
def export_markdown():
    external = _load_external()
    external_map = _external_download_map(external)
    external_meta = _external_meta_map(external)
    download_root = external.get("download_root") or os.path.join(ROOT, "local_change_dashboard", "external_repo_files")
    git_cache = {}

    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, "w", compression=zipfile.ZIP_DEFLATED) as zf:
        for rel_path, abs_path in _iter_markdown_files(REPO_ROOT):
            try:
                with open(abs_path, "r", encoding="utf-8") as f:
                    content = f.read()
            except OSError:
                continue
            local_rule, local_sections, local_dependencies = _local_content_for_target(
                rel_path, content
            )
            last_updated_dt = _compute_last_updated(rel_path, abs_path, content, external_meta, git_cache)
            last_updated_dt = _include_local_dependency_dates(
                last_updated_dt, local_dependencies, git_cache
            )
            date_str = _format_last_updated(last_updated_dt)
            with_meta = _ensure_frontmatter_last_updated(content, date_str, _title_from_path(rel_path))
            merged = _merge_github_readme(with_meta, external_map, download_root)
            merged = _inline_local_js_imports(merged, abs_path)
            merged = _inject_local_content(merged, local_rule, local_sections)
            zf.writestr(rel_path, merged)

    buffer.seek(0)
    stamp = datetime.now(timezone.utc).strftime("%Y%m%d")
    filename = f"ciroh_markdown_export_{stamp}.zip"
    return StreamingResponse(
        buffer,
        media_type="application/zip",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


@app.post("/api/export-markdown-folder")
def export_markdown_folder(force: bool = False):
    external = _load_external()
    external_map = _external_download_map(external)
    external_meta = _external_meta_map(external)
    download_root = external.get("download_root") or os.path.join(ROOT, "local_change_dashboard", "external_repo_files")
    counts = _write_mixed_markdown(
        MIXED_EXPORT_ROOT,
        external_map,
        external_meta,
        download_root,
        external.get("last_checked"),
        force,
    )
    return {"output_root": MIXED_EXPORT_ROOT, **counts}


@app.get("/api/external")
def external():
    return _load_external()


# ── Pipeline runner (background task + polling) ──────────────────────

_pipeline_state: dict = {
    "running": False,
    "step": 0,
    "total": 6,
    "label": "",
    "error": None,
    "result": None,
    "sync_id": None,
    "started_at": None,
    "completed_at": None,
    "failed_step": None,
    "failed_label": None,
    "options": {"include_github_repositories": False},
}
_pipeline_lock = threading.Lock()

def _merge_dashboard_documents():
    ext = _load_external()
    ext_map = _external_download_map(ext)
    ext_meta = _external_meta_map(ext)
    download_root = ext.get("download_root") or os.path.join(
        ROOT, "local_change_dashboard", "external_repo_files"
    )
    return _write_mixed_markdown(
        MIXED_EXPORT_ROOT,
        ext_map,
        ext_meta,
        download_root,
        ext.get("last_checked"),
        False,
    )


def _dashboard_pipeline_steps(include_github_repositories=False):
    steps = [*repository_sync_steps(root=ROOT)]
    next_step = 4
    if include_github_repositories:
        steps.append(github_repository_generation_step(next_step, root=ROOT))
        next_step += 1
    steps.extend([
        callback_step(
            next_step,
            "merge_documents",
            "Merging documents...",
            _merge_dashboard_documents,
        ),
        generation_step(next_step + 1, root=ROOT, summarize=True),
        database_step(
            next_step + 2, expected_artifact_type=1, root=ROOT
        ),
    ])
    if include_github_repositories:
        steps.append(
            github_repository_database_step(next_step + 3, root=ROOT)
        )
    return steps


def _load_pipeline_report(filename):
    path = os.path.join(SYNCHRONIZATION_OUTPUT_DIR, filename)
    try:
        with open(path, "r", encoding="utf-8") as f:
            payload = json.load(f)
        return payload if isinstance(payload, dict) else {}
    except (OSError, json.JSONDecodeError):
        return {}


def _pipeline_report_mtime_ns(filename):
    try:
        return os.stat(os.path.join(SYNCHRONIZATION_OUTPUT_DIR, filename)).st_mtime_ns
    except OSError:
        return None


def _synchronization_summary(report):
    content = report.get("content") or {}
    usage = report.get("openai_usage") or {}
    database = report.get("database") or {}
    metadata = report.get("metadata") or {}
    github_repositories = metadata.get("github_repositories") or {}
    duration_seconds = report.get("duration_seconds")
    if duration_seconds is None:
        try:
            started = datetime.fromisoformat(str(report.get("started_at")).replace("Z", "+00:00"))
            completed = datetime.fromisoformat(str(report.get("completed_at")).replace("Z", "+00:00"))
            duration_seconds = max(0.0, round((completed - started).total_seconds(), 3))
        except (TypeError, ValueError):
            pass
    return {
        "sync_id": report.get("sync_id"),
        "mode": report.get("mode"),
        "status": report.get("status") or "unknown",
        "started_at": report.get("started_at"),
        "completed_at": report.get("completed_at"),
        "duration_seconds": duration_seconds,
        "total_artifacts": content.get("total_artifacts", 0),
        "new_count": content.get("new_count", 0),
        "updated_count": content.get("updated_count", 0),
        "deleted_count": content.get("deleted_count", 0),
        "total_chunks": content.get("total_chunks", 0),
        "summary_error_count": content.get("summary_error_count", 0),
        "openai_tokens": usage.get("total_tokens", 0),
        "estimated_cost_usd": usage.get("estimated_cost_usd"),
        "db_upserted": database.get("upserted_artifacts", 0),
        "db_deactivated": database.get("deactivated_artifacts", 0),
        "db_chunks": database.get("chunks_inserted", 0),
        "failed_step": metadata.get("failed_step"),
        "failed_label": metadata.get("failed_label"),
        "completed_steps": metadata.get("completed_steps") or [],
        "github_artifacts": github_repositories.get("total_artifacts", 0),
        "github_repositories_requested": metadata.get(
            "github_repository_artifacts_requested", False
        ),
        "error": report.get("error"),
    }


def _load_synchronization_history(limit=20):
    reports_by_id = {}
    # Bundled history makes a fresh clone useful immediately. Runtime reports
    # are loaded last so a teammate's local copy wins for the same sync ID.
    for history_dir in (
        BOOTSTRAP_SYNCHRONIZATION_HISTORY_DIR,
        SYNCHRONIZATION_HISTORY_DIR,
    ):
        try:
            filenames = [
                name
                for name in os.listdir(history_dir)
                if name.startswith("sync_") and name.endswith(".json")
            ]
        except OSError:
            continue
        for filename in filenames:
            path = os.path.join(history_dir, filename)
            try:
                with open(path, "r", encoding="utf-8") as handle:
                    report = json.load(handle)
                if isinstance(report, dict):
                    summary = _synchronization_summary(report)
                    key = summary.get("sync_id") or filename
                    reports_by_id[key] = summary
            except (OSError, json.JSONDecodeError):
                continue
    reports = list(reports_by_id.values())
    reports.sort(
        key=lambda report: report.get("completed_at") or report.get("started_at") or "",
        reverse=True,
    )
    return reports[: max(1, min(int(limit or 20), 100))]


def _load_synchronization_detail(sync_id):
    if not re.fullmatch(r"[A-Za-z0-9_.-]{1,120}", sync_id or ""):
        return None
    # Prefer runtime detail, then fall back to the read-only bundled seed.
    for history_dir in (
        SYNCHRONIZATION_HISTORY_DIR,
        BOOTSTRAP_SYNCHRONIZATION_HISTORY_DIR,
    ):
        path = os.path.join(history_dir, f"sync_{sync_id}.json")
        try:
            with open(path, "r", encoding="utf-8") as handle:
                report = json.load(handle)
            if isinstance(report, dict):
                return report
        except (OSError, json.JSONDecodeError):
            continue
    return None


def _github_repository_report_summary(report, db_report=None):
    db_report = db_report or {}
    database_completed = db_report.get("status") == "completed"
    return {
        "requested": True,
        "status": report.get("status"),
        "total_artifacts": report.get("total_artifacts", 0),
        "total_chunks": report.get("total_chunks", 0),
        "new_count": report.get("new_count", 0),
        "updated_count": report.get("updated_count", 0),
        "deleted_count": report.get("deleted_count", 0),
        "summarized_count": report.get("summarized_count", 0),
        "reused_summary_count": report.get("reused_summary_count", 0),
        "chunked_repository_count": report.get("chunked_repository_count", 0),
        "reused_chunk_repository_count": report.get(
            "reused_chunk_repository_count", 0
        ),
        "chunk_classification_error_count": len(
            report.get("chunk_classification_errors") or []
        ),
        "pending_summary_count": len(report.get("pending_summaries") or []),
        "database_update_performed": database_completed,
        "database": {
            "status": db_report.get("status"),
            "upserted_artifacts": db_report.get("upserted_artifacts", 0),
            "deactivated_artifacts": db_report.get("deactivated_artifacts", 0),
            "chunks_inserted": db_report.get("chunks_inserted", 0),
            "unchanged_artifacts": (
                (db_report.get("reconciliation") or {}).get(
                    "unchanged_artifacts", 0
                )
            ),
        },
        "chunk_generation_status": report.get("chunk_generation_status"),
    }


def _finalize_dashboard_pipeline(
    sync_id, started_at, completed_steps, include_github_repositories=False
):
    generation_report = _load_pipeline_report("generation_report.json")
    db_report = _load_pipeline_report("db_update_result.json")
    github_db_report = (
        _load_pipeline_report("github_repository_db_update_result.json")
        if include_github_repositories
        else {}
    )
    github_report = (
        _load_pipeline_report("github_repository_generation_report.json")
        if include_github_repositories
        else {}
    )
    metadata = {
        "completed_steps": sorted(completed_steps),
        "github_repository_artifacts_requested": include_github_repositories,
        "github_repository_database_update_performed": (
            github_db_report.get("status") == "completed"
        ),
    }
    if github_report:
        metadata["github_repositories"] = _github_repository_report_summary(
            github_report, github_db_report
        )
    completed_at = utc_now_iso()
    sync_report = build_synchronization_report(
        sync_id=sync_id,
        mode="dashboard_pipeline",
        started_at=started_at,
        completed_at=completed_at,
        status="completed",
        generation_report=generation_report,
        db_report=db_report,
        additional_usage_reports=[
            github_report.get("openai_usage"),
            github_db_report.get("openai_usage"),
        ],
        metadata=metadata,
    )
    sync_report_path = write_synchronization_report(
        SYNCHRONIZATION_OUTPUT_DIR, sync_report
    )
    result = _synchronization_summary(sync_report)
    result["synchronization_report"] = str(sync_report_path)
    return result


def _run_pipeline(include_github_repositories=False):
    sync_id = new_sync_id()
    started_at = utc_now_iso()
    completed_steps = set()
    github_report_filename = "github_repository_generation_report.json"
    github_report_mtime_ns = _pipeline_report_mtime_ns(github_report_filename)
    github_db_report_filename = "github_repository_db_update_result.json"
    github_db_report_mtime_ns = _pipeline_report_mtime_ns(
        github_db_report_filename
    )
    steps = _dashboard_pipeline_steps(include_github_repositories)
    _pipeline_state.update(
        sync_id=sync_id,
        started_at=started_at,
        completed_at=None,
        failed_step=None,
        failed_label=None,
        total=len(steps),
        options={"include_github_repositories": include_github_repositories},
    )

    def on_step_start(step):
        _pipeline_state["step"] = step.number
        _pipeline_state["label"] = step.label

    try:
        run_sync_steps(
            steps,
            on_step_start=on_step_start,
            on_step_complete=lambda result: completed_steps.add(result.key),
        )
    except SyncStepError as exc:
        error = str(exc)
        completed_at = utc_now_iso()
        _pipeline_state.update(
            error=error,
            completed_at=completed_at,
            failed_step=exc.step.key,
            failed_label=exc.step.label,
        )
        generation_report = (
            _load_pipeline_report("generation_report.json")
            if "generate_artifacts" in completed_steps
            else {}
        )
        db_report = (
            _load_pipeline_report("db_update_result.json")
            if (
                "update_database" in completed_steps
                or exc.step.key == "update_database"
            )
            else {}
        )
        github_report = (
            _load_pipeline_report(github_report_filename)
            if include_github_repositories
            and (
                "generate_github_repository_artifacts" in completed_steps
                or (
                    exc.step.key == "generate_github_repository_artifacts"
                    and _pipeline_report_mtime_ns(github_report_filename)
                    != github_report_mtime_ns
                )
            )
            else {}
        )
        github_db_report = (
            _load_pipeline_report(github_db_report_filename)
            if include_github_repositories
            and (
                "update_github_repository_database" in completed_steps
                or (
                    exc.step.key == "update_github_repository_database"
                    and _pipeline_report_mtime_ns(github_db_report_filename)
                    != github_db_report_mtime_ns
                )
            )
            else {}
        )
        failure_metadata = {
            "completed_steps": sorted(completed_steps),
            "failed_step": exc.step.key,
            "failed_label": exc.step.label,
            "github_repository_artifacts_requested": include_github_repositories,
            "github_repository_database_update_performed": (
                github_db_report.get("status") == "completed"
            ),
        }
        if github_report:
            failure_metadata["github_repositories"] = (
                _github_repository_report_summary(
                    github_report, github_db_report
                )
            )
        failed_report = build_synchronization_report(
            sync_id=sync_id,
            mode="dashboard_pipeline",
            started_at=started_at,
            completed_at=completed_at,
            status="failed",
            generation_report=generation_report,
            db_report=db_report,
            additional_usage_reports=[
                github_report.get("openai_usage"),
                github_db_report.get("openai_usage"),
            ],
            error=error,
            metadata=failure_metadata,
        )
        try:
            write_synchronization_report(
                SYNCHRONIZATION_OUTPUT_DIR, failed_report
            )
            _pipeline_state["result"] = _synchronization_summary(failed_report)
        finally:
            _pipeline_state["running"] = False
        return
    except Exception as exc:
        error = str(exc)
        completed_at = utc_now_iso()
        github_report = (
            _load_pipeline_report(github_report_filename)
            if include_github_repositories
            and "generate_github_repository_artifacts" in completed_steps
            else {}
        )
        github_db_report = (
            _load_pipeline_report(github_db_report_filename)
            if include_github_repositories
            and "update_github_repository_database" in completed_steps
            else {}
        )
        failure_metadata = {
            "completed_steps": sorted(completed_steps),
            "failed_step": "unexpected_error",
            "failed_label": "Unexpected pipeline error",
            "github_repository_artifacts_requested": include_github_repositories,
            "github_repository_database_update_performed": (
                github_db_report.get("status") == "completed"
            ),
        }
        if github_report:
            failure_metadata["github_repositories"] = (
                _github_repository_report_summary(
                    github_report, github_db_report
                )
            )
        failed_report = build_synchronization_report(
            sync_id=sync_id,
            mode="dashboard_pipeline",
            started_at=started_at,
            completed_at=completed_at,
            status="failed",
            additional_usage_reports=[
                github_report.get("openai_usage"),
                github_db_report.get("openai_usage"),
            ],
            error=error,
            metadata=failure_metadata,
        )
        try:
            write_synchronization_report(SYNCHRONIZATION_OUTPUT_DIR, failed_report)
            _pipeline_state.update(
                error=error,
                result=_synchronization_summary(failed_report),
                completed_at=completed_at,
                failed_step="unexpected_error",
                failed_label="Unexpected pipeline error",
            )
        finally:
            _pipeline_state["running"] = False
        return

    try:
        _pipeline_state["result"] = _finalize_dashboard_pipeline(
            sync_id,
            started_at,
            completed_steps,
            include_github_repositories,
        )
        _pipeline_state["completed_at"] = _pipeline_state["result"].get("completed_at")
        _pipeline_state["label"] = "Done"
    except Exception as exc:
        _pipeline_state["error"] = str(exc)
    finally:
        _pipeline_state["running"] = False


@app.post("/api/run-pipeline")
def run_pipeline(request: Request, include_github_repositories: bool = False):
    _require_operator(request)
    with _pipeline_lock:
        if _pipeline_state["running"]:
            return JSONResponse(
                status_code=409,
                content={"status": "already_running", "step": _pipeline_state["step"],
                         "label": _pipeline_state["label"]},
            )
        pipeline_total = len(
            _dashboard_pipeline_steps(include_github_repositories)
        )
        _pipeline_state.update(
            running=True, step=0, total=pipeline_total, label="Starting...",
            error=None, result=None, sync_id=None, started_at=None,
            completed_at=None, failed_step=None, failed_label=None,
            options={"include_github_repositories": include_github_repositories},
        )
    t = threading.Thread(
        target=_run_pipeline,
        args=(include_github_repositories,),
        daemon=True,
    )
    t.start()
    return {"status": "started"}


@app.get("/api/pipeline-status")
def pipeline_status():
    return dict(_pipeline_state)


@app.get("/api/synchronizations")
def synchronization_history(limit: int = 20):
    items = _load_synchronization_history(limit=limit)
    return {"items": items, "count": len(items)}


@app.get("/api/synchronizations/{sync_id}")
def synchronization_detail(sync_id: str):
    report = _load_synchronization_detail(sync_id)
    if report is None:
        raise HTTPException(status_code=404, detail="Synchronization report not found.")
    return report
