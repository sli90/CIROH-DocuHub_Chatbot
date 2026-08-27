#!/usr/bin/env python3
"""
Reads local_change_dashboard/mixed_docs/ and produces:
  - dashboard/formated_files/artifacts.json
  - dashboard/formated_files/content_chunks.json
  - dashboard/formated_files/content_chunks_delta.json  (chunks for new+updated only)
  - dashboard/formated_files/generation_report.json
  - dashboard/formated_files/_hashes.json  (internal change-tracking)

Only new/modified files are sent to the LLM for summarization.
Delta files are archived with a timestamp when the pipeline runs again.
Unchanged files carry forward their previous summary_data.

Usage:
    python dashboard/generate_formatted_files.py
    python dashboard/generate_formatted_files.py --summarize
    python dashboard/generate_formatted_files.py --mixed-docs PATH --output PATH
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

try:
    import yaml
except ImportError:
    yaml = None  # type: ignore[assignment]

try:
    from openai import OpenAI
except ImportError:
    OpenAI = None  # type: ignore[assignment]

try:
    from dotenv import load_dotenv

    load_dotenv(Path(__file__).resolve().parent.parent / ".env")
except ImportError:
    pass

# ── paths & constants ────────────────────────────────────────────────────────

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from sync_accounting import UsageAccumulator  # noqa: E402
from docuhub_paths import normalize_public_route_path  # noqa: E402

DEFAULT_MIXED_DOCS = ROOT / "local_change_dashboard" / "mixed_docs"
DEFAULT_OUTPUT = Path(__file__).resolve().parent / "formated_files"
BASE_URL = "https://hub.ciroh.org"

SKIP_DIRS = {".github", "node_modules", "__pycache__", ".git"}
SKIP_FILES = {
    "README.md",
    "CHANGELOG.md",
    "CONTRIBUTING.md",
    "SECURITY.md",
    "INSTALL.md",
    "GITHUB_LOGIN_FLOW.md",
    "release-notes-template.mdx",
    "RESOURCES_PAGE_DOCUMENTATION.md",
}
SKIP_PATH_PREFIXES = {
    "docs/publications/",
    "src/pages/publications/",
}

SECTION_ORDER = {"docs": 0, "blog": 1, "release-notes": 2, "src": 3}
CATEGORY_STEMS = {"index", "intro"}

SUMMARY_MODEL = os.getenv("SUMMARY_MODEL", "gpt-5.2")
MAX_CONTENT_CHARS = 120_000

SUMMARY_SYSTEM_MSG = (
    "You are a precise CIROH DocuHub summarizer. "
    "Return ONLY valid JSON. No prose, no markdown."
)


# ── frontmatter ──────────────────────────────────────────────────────────────


def _simple_parse_frontmatter(text: str) -> dict:
    """Minimal key-value parser used when PyYAML is missing."""
    fm: dict = {}
    for line in text.split("\n"):
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        if ":" not in line:
            continue
        key, _, val = line.partition(":")
        key, val = key.strip(), val.strip()
        if (val.startswith('"') and val.endswith('"')) or (
            val.startswith("'") and val.endswith("'")
        ):
            val = val[1:-1]
        elif val.startswith("[") and val.endswith("]"):
            items = val[1:-1].split(",")
            val = [i.strip().strip("\"'") for i in items if i.strip()]
        elif val.isdigit():
            val = int(val)
        fm[key] = val
    return fm


def parse_frontmatter(content: str) -> tuple[dict, str]:
    """Return (frontmatter_dict, body) from a markdown/mdx file."""
    if not content.startswith("---"):
        return {}, content

    end = content.find("\n---", 3)
    if end == -1:
        return {}, content

    fm_raw = content[3:end].strip()
    body = content[end + 4 :].strip()

    if yaml:
        try:
            fm = yaml.safe_load(fm_raw) or {}
        except Exception:
            fm = _simple_parse_frontmatter(fm_raw)
    else:
        fm = _simple_parse_frontmatter(fm_raw)

    return fm if isinstance(fm, dict) else {}, body


# ── content cleaning ─────────────────────────────────────────────────────────

_QUOTED_VAL = re.compile(r"""(?:'((?:[^'\\]|\\.)*)'|"((?:[^"\\]|\\.)*)")""")


def _extract_quoted(line: str, key: str) -> str | None:
    """Pull the first quoted string after *key*: in a JS object-literal line."""
    m = re.search(rf"{key}\s*:\s*" + _QUOTED_VAL.pattern, line)
    if not m:
        return None
    raw = m.group(1) if m.group(1) is not None else m.group(2)
    return raw.replace("\\'", "'").replace('\\"', '"')


def _extract_cards_from_block(block_lines: list[str]) -> list[tuple[str, str]]:
    """Return [(cardTitle, cardDescription), ...] found in an export block."""
    cards: list[tuple[str, str]] = []
    cur_title: str | None = None
    cur_desc: str | None = None
    for ln in block_lines:
        t = _extract_quoted(ln, "cardTitle")
        if t is not None:
            cur_title = t
        d = _extract_quoted(ln, "cardDescription")
        if d is not None:
            cur_desc = d
        if cur_title and cur_desc:
            cards.append((cur_title, cur_desc))
            cur_title = cur_desc = None
    return cards


def _expand_steps_cards(text: str, card_data: dict[str, list[tuple[str, str]]]) -> str:
    """Replace <StepsCards steps={varName} .../> with markdown list items."""

    def _replacer(m: re.Match) -> str:
        var = m.group(1)
        cards = card_data.get(var)
        if not cards:
            return ""
        return "\n".join(f"- **{title}**: {desc}" for title, desc in cards)

    return re.sub(
        r"<StepsCards\s[^>]*?steps=\{(\w+)\}[^>]*/\s*>",
        _replacer,
        text,
        flags=re.DOTALL,
    )


def clean_content(text: str) -> str:
    """Remove import/export blocks, JSX/HTML tags; convert <Link> to markdown.

    Text-bearing fields (cardTitle / cardDescription) inside ``export const``
    blocks are extracted and re-inserted where the corresponding
    ``<StepsCards>`` component is rendered.
    """
    lines = text.split("\n")
    out: list[str] = []
    in_export = False
    depth = 0
    export_buf: list[str] = []
    export_var: str | None = None
    card_data: dict[str, list[tuple[str, str]]] = {}

    for line in lines:
        stripped = line.strip()

        if re.match(r"^import\s+", stripped):
            continue

        if not in_export and re.match(
            r"^export\s+(const|let|var|function|default)\b", stripped
        ):
            var_m = re.match(r"^export\s+const\s+(\w+)\s*=", stripped)
            export_var = var_m.group(1) if var_m else None
            export_buf = [stripped]
            depth = (
                stripped.count("[")
                + stripped.count("{")
                - stripped.count("]")
                - stripped.count("}")
            )
            if depth > 0:
                in_export = True
            else:
                cards = _extract_cards_from_block(export_buf)
                if export_var and cards:
                    card_data[export_var] = cards
                export_var = None
                export_buf = []
            continue

        if in_export:
            export_buf.append(stripped)
            depth += (
                stripped.count("[")
                + stripped.count("{")
                - stripped.count("]")
                - stripped.count("}")
            )
            if depth <= 0:
                in_export = False
                cards = _extract_cards_from_block(export_buf)
                if export_var and cards:
                    card_data[export_var] = cards
                export_var = None
                export_buf = []
            continue

        out.append(line)

    text = "\n".join(out)

    if card_data:
        text = _expand_steps_cards(text, card_data)

    text = re.sub(r"<!--.*?-->", "", text, flags=re.DOTALL)

    text = re.sub(
        r'<Link\s[^>]*?to=["\']([^"\']+)["\'][^>]*>(.*?)</Link>',
        r"[\2](\1)",
        text,
        flags=re.DOTALL,
    )
    text = re.sub(
        r'<a\s[^>]*?href=["\']([^"\']+)["\'][^>]*>(.*?)</a>',
        r"[\2](\1)",
        text,
        flags=re.DOTALL,
    )

    text = re.sub(r"\{useBaseUrl\([^)]*\)\}", "", text)
    text = re.sub(r"<\w+(?:\s[^>]*)?\s*/>", "", text)
    text = re.sub(r"<(?!/)\w+(?:\s[^>]*)?>", "", text)
    text = re.sub(r"</\w+>", "", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


# ── chunking by headings ────────────────────────────────────────────────────


def split_into_chunks(body: str, title: str) -> list[tuple[str, str, int]]:
    """
    Split cleaned body by markdown headings.
    Returns [(chunk_title, chunk_text, heading_level), ...].
    heading_level 0 = intro, 1 = #, 2 = ##, etc.
    """
    heading_re = re.compile(r"^(#{1,6})\s+(.+)$", re.MULTILINE)
    positions = [
        (m.start(), len(m.group(1)), m.group(2).strip())
        for m in heading_re.finditer(body)
    ]

    if not positions:
        return [(title, body.strip(), 0)]

    chunks: list[tuple[str, str, int]] = []
    first_pos, first_lvl, first_heading = positions[0]

    intro_text = body[:first_pos].strip()

    if first_lvl == 1:
        next_pos = positions[1][0] if len(positions) > 1 else len(body)
        heading_body = body[first_pos:next_pos]
        heading_body = re.sub(r"^#\s+.+\n?", "", heading_body).strip()
        combined = (
            f"{intro_text}\n\n{heading_body}".strip() if intro_text else heading_body
        )
        chunks.append((title, combined, 0))
        start_idx = 1
    else:
        chunks.append((title, intro_text, 0))
        start_idx = 0

    for i in range(start_idx, len(positions)):
        pos, level, heading = positions[i]
        end = positions[i + 1][0] if i + 1 < len(positions) else len(body)
        section = body[pos:end]
        section = re.sub(r"^#{1,6}\s+.+\n?", "", section).strip()
        chunks.append((heading, section, level))

    return chunks


# ── URL construction ─────────────────────────────────────────────────────────


def build_url(fm: dict, rel_path: str) -> str:
    """Build the public DocuHub URL for a page."""
    section = rel_path.split("/")[0] if "/" in rel_path else ""
    slug = fm.get("slug")

    if slug and section in ("blog", "release-notes"):
        return f"{BASE_URL}/{section}/{slug}/"

    path = fm.get("path", "")
    if path:
        path = str(path).strip()
        if path == "/":
            return f"{BASE_URL}/"
        path = normalize_public_route_path(path)
        if path.endswith("/index"):
            path = path[: -len("/index")]
        return f"{BASE_URL}/{path}/"

    p = rel_path.replace("\\", "/")
    p = re.sub(r"\.(mdx?|md)$", "", p)
    if p.endswith("/index"):
        p = p.rsplit("/", 1)[0]
    return f"{BASE_URL}/{p}/"


# ── parent resolution ────────────────────────────────────────────────────────


def _category_file(directory: str, known: dict[str, int]) -> str | None:
    """Find the index/intro file that represents a directory."""
    for name in ("index.mdx", "index.md", "intro.mdx", "intro.md"):
        candidate = f"{directory}/{name}"
        if candidate in known:
            return candidate
    return None


# ── hashing ──────────────────────────────────────────────────────────────────


def _content_hash(raw: str) -> str:
    """SHA-256 of raw file content, truncated to 16 hex chars."""
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()[:16]


def _load_hashes(output_dir: Path) -> dict[str, str]:
    """Load {URL: hash} from _hashes.json."""
    p = output_dir / "_hashes.json"
    if p.exists():
        try:
            with open(p, encoding="utf-8") as f:
                return json.load(f)
        except (json.JSONDecodeError, KeyError):
            pass
    return {}


def _save_hashes(output_dir: Path, hashes: dict[str, str]) -> None:
    with open(output_dir / "_hashes.json", "w", encoding="utf-8") as f:
        json.dump(hashes, f, indent=2, ensure_ascii=False)


def _load_prev_artifacts(output_dir: Path) -> dict[str, dict]:
    """Load previous artifacts.json as {URL: artifact_dict}."""
    p = output_dir / "artifacts.json"
    if p.exists():
        try:
            with open(p, encoding="utf-8") as f:
                return {a["URL"]: a for a in json.load(f) if "URL" in a}
        except (json.JSONDecodeError, KeyError):
            pass
    return {}


# ── LLM summarization ───────────────────────────────────────────────────────


def _truncate(text: str, max_chars: int = MAX_CONTENT_CHARS) -> str:
    text = text.replace("\x00", "")
    if len(text) <= max_chars:
        return text
    head = text[: int(max_chars * 0.7)]
    tail = text[-int(max_chars * 0.3) :]
    return head + "\n\n...\n\n" + tail


def _build_summary_prompt(content: str) -> str:
    content = _truncate(content)
    return f"""
# ROLE & GOAL
You are an AI Knowledge Architect specializing in hydrology and scientific computing for the Cooperative Institute for Research to Operations in Hydrology (CIROH). Your task is to process the content of a webpage from CIROH's DocuHub documentation site.

# CONTEXT
The output you generate will be stored in a PostgreSQL database to power a Retrieval-Augmented Generation (RAG) system. Specifically, your response will populate a `JSONB` field. The `summary_text` within your JSON response will be used to create a 3072-dimension vector embedding for semantic search. Therefore, the summary must be information-dense, conceptually accurate, and optimized to be found by user queries about CIROH's products, services, policies, and research activities.

# CONTENT TO ANALYZE
---
**[BEGINNING OF MARKDOWN CONTENT]**

{content}

**[END OF MARKDOWN CONTENT]**
---

# INSTRUCTIONS
Based on the content provided above, generate a single JSON object. Follow these rules precisely:

1.  **Focus on "What" and "Why"**: The `summary_text` should clearly identify the page's core purpose. Is it a product description, a tutorial, a policy document, a release note, or a blog post?
2.  **Extract Named Entities**: The `entities` array must include all specific names of products, services, tools, technologies, standards, or key collaborators mentioned (e.g., "NextGen in A Box", "Research Datastream", "Hydrofabric", "NOAA", "BYU Hydroinformatics Courses").
3.  **Capture Key Concepts**: The `keywords` array should capture the main technical or thematic concepts, not just proper nouns (e.g., "hydrologic modeling", "flood inundation mapping", "water quality", "data management", "cloud computing", "machine learning").
4.  **Synthesize, Don't Quote**: Do not copy sentences directly from the text. Synthesize the information in your own words to create a coherent and semantically rich summary.
5.  **Be Dense and Direct**: Start the summary directly with the subject. Avoid introductory phrases. For example, instead of writing "This page describes NextGen In A Box...", you must write "NextGen In A Box is a community-accessible...". Be direct and objective.

# REQUIRED OUTPUT FORMAT
Generate a single, valid JSON object with this structure (no extra keys):

{{
  "summary_text": "",
  "keywords": [],
  "entities": [],
  "document_type": ""
}}
""".strip()


def _summarize_one(
    client: object, content: str, usage_tracker: UsageAccumulator
) -> dict | None:
    """Call LLM and return summary_data dict, or None on failure."""
    usage_tracker.record_request()
    try:
        prompt = _build_summary_prompt(content)
        resp = client.responses.create(  # type: ignore[union-attr]
            model=SUMMARY_MODEL,
            input=[
                {"role": "system", "content": SUMMARY_SYSTEM_MSG},
                {"role": "user", "content": prompt},
            ],
            text={"format": {"type": "json_object"}, "verbosity": "medium"},
            reasoning={"effort": "low"},
        )
        usage_tracker.add_response(resp)
        raw = (resp.output_text or "").strip()
        data = json.loads(raw)
        return {
            "summary_text": data.get("summary_text") or "",
            "keywords": (
                data.get("keywords") if isinstance(data.get("keywords"), list) else []
            ),
            "entities": (
                data.get("entities") if isinstance(data.get("entities"), list) else []
            ),
            "document_type": data.get("document_type") or "",
        }
    except Exception as exc:
        usage_tracker.record_error()
        print(f"    LLM error: {exc}", file=sys.stderr)
        return None


# ── file collection ──────────────────────────────────────────────────────────


def collect_files(mixed_docs: Path) -> list[tuple[str, Path]]:
    """Walk mixed_docs and return (rel_path, abs_path) pairs."""
    files: list[tuple[str, Path]] = []
    for root, dirs, filenames in os.walk(mixed_docs):
        dirs[:] = [d for d in dirs if d not in SKIP_DIRS]
        for fname in sorted(filenames):
            if fname in SKIP_FILES:
                continue
            if not fname.endswith((".md", ".mdx")):
                continue
            abs_path = Path(root) / fname
            rel_path = str(abs_path.relative_to(mixed_docs)).replace("\\", "/")
            if any(rel_path.startswith(prefix) for prefix in SKIP_PATH_PREFIXES):
                continue
            files.append((rel_path, abs_path))
    return files


# ── sort key ─────────────────────────────────────────────────────────────────


def _sort_key(rp: str) -> tuple:
    """Depth-first: category pages before siblings and subdirectories."""
    parts = rp.split("/")
    section_idx = SECTION_ORDER.get(parts[0], 99)
    key: list = [section_idx]
    for i, part in enumerate(parts):
        is_file = i == len(parts) - 1
        if is_file:
            stem = Path(part).stem
            key.append((0, part) if stem in CATEGORY_STEMS else (1, part))
        else:
            key.append((2, part))
    return tuple(key)


# ── main generation ──────────────────────────────────────────────────────────


def generate(mixed_docs: Path, output_dir: Path, *, summarize: bool = False) -> int:
    """Produce artifacts.json, content_chunks.json, generation_report.json."""

    output_dir.mkdir(parents=True, exist_ok=True)

    # ── load previous state ──
    prev_hashes = _load_hashes(output_dir)
    prev_artifacts = _load_prev_artifacts(output_dir)

    # ── collect files and compute hashes ──
    files = collect_files(mixed_docs)
    print(f"Found {len(files)} markdown files in {mixed_docs}")

    raw_contents: dict[str, str] = {}
    file_data: dict[str, dict] = {}

    for rel_path, abs_path in files:
        try:
            raw = abs_path.read_text(encoding="utf-8")
        except Exception as exc:
            print(f"  WARN  cannot read {rel_path}: {exc}", file=sys.stderr)
            continue
        raw_contents[rel_path] = raw
        fm, body = parse_frontmatter(raw)
        file_data[rel_path] = {
            "frontmatter": fm,
            "clean_body": clean_content(body),
        }

    sorted_paths = sorted(file_data, key=_sort_key)

    # ── classify files: new / modified / unchanged / deleted ──
    # First build a temporary URL for each file so we can compare with prev_hashes
    url_for_path: dict[str, str] = {}
    for rp in sorted_paths:
        url_for_path[rp] = build_url(file_data[rp]["frontmatter"], rp)

    current_hashes: dict[str, str] = {}  # URL -> hash
    new_urls: list[str] = []
    updated_urls: list[str] = []
    unchanged_urls: list[str] = []

    for rp in sorted_paths:
        url = url_for_path[rp]
        h = _content_hash(raw_contents[rp])
        current_hashes[url] = h

        if url not in prev_hashes:
            new_urls.append(url)
        elif prev_hashes[url] != h:
            updated_urls.append(url)
        else:
            unchanged_urls.append(url)

    prev_url_set = set(prev_hashes.keys())
    current_url_set = set(current_hashes.keys())
    deleted_urls = sorted(prev_url_set - current_url_set)
    needs_summary = set(new_urls) | set(updated_urls)

    print(
        f"  New: {len(new_urls)}, Updated: {len(updated_urls)}, "
        f"Unchanged: {len(unchanged_urls)}, Deleted: {len(deleted_urls)}"
    )

    # ── build artifacts (always all files, for correct IDs + parents) ──
    artifacts: list[dict] = []
    path_to_id: dict[str, int] = {}
    aid = 0

    for rel_path in sorted_paths:
        fm = file_data[rel_path]["frontmatter"]
        aid += 1
        url = url_for_path[rel_path]

        title = fm.get("title", "")
        if not title:
            stem = Path(rel_path).stem
            if stem in ("index", "intro"):
                stem = Path(rel_path).parent.name
            title = stem.replace("-", " ").replace("_", " ").title()

        description = fm.get("description") or ""
        tags = fm.get("tags", fm.get("keywords", []))
        if isinstance(tags, str):
            tags = [t.strip() for t in tags.split(",")]
        elif not isinstance(tags, list):
            tags = []

        last_updated = fm.get("Last updated date") or ""

        # Carry forward summary_data for unchanged files
        prev_summary = None
        if url not in needs_summary and url in prev_artifacts:
            prev_summary = prev_artifacts[url].get("summary_data")

        artifacts.append(
            {
                "idArtifact": aid,
                "idArtifactType": 1,
                "Title": title,
                "URL": url,
                "idArtifactParent": None,
                "description": str(description),
                "tags": tags,
                "Last updated date": str(last_updated),
                "summary_data": prev_summary,
                "_rel": rel_path,
            }
        )
        path_to_id[rel_path] = aid

    # ── resolve parent-child ──
    for art in artifacts:
        rel = art["_rel"]
        parts = rel.split("/")
        stem = Path(parts[-1]).stem

        if stem in ("index", "intro"):
            if len(parts) >= 3:
                parent_dir = "/".join(parts[:-2])
                pf = _category_file(parent_dir, path_to_id)
                if pf:
                    art["idArtifactParent"] = path_to_id[pf]
        else:
            cur_dir = "/".join(parts[:-1])
            pf = _category_file(cur_dir, path_to_id)
            if pf:
                art["idArtifactParent"] = path_to_id[pf]

    # ── build content_chunks ──
    chunks: list[dict] = []
    cid = 0

    for art in artifacts:
        rel = art["_rel"]
        clean_body = file_data[rel]["clean_body"]
        sections = split_into_chunks(clean_body, art["Title"])
        first_cid: int | None = None

        for order, (sec_title, sec_text, hlevel) in enumerate(sections):
            cid += 1
            if order == 0:
                first_cid = cid
                chunk_type = 1
                parent = None
            else:
                chunk_type = 2
                parent = first_cid

            chunks.append(
                {
                    "idArtifact": art["idArtifact"],
                    "idChunk": cid,
                    "order": order + 1,
                    "idChunkType": chunk_type,
                    "title": sec_title,
                    "chunk_text": sec_text,
                    "idChunkParent": parent,
                }
            )

    # ── LLM summarization for new/modified files only ──
    # Also pick up unchanged files whose summary is still null
    if summarize:
        for art in artifacts:
            if art["URL"] not in needs_summary and art["summary_data"] is None:
                needs_summary.add(art["URL"])

    summary_errors: list[str] = []
    summarized_count = 0
    summary_usage = UsageAccumulator("summarization", SUMMARY_MODEL)

    if summarize and needs_summary:
        if OpenAI is None:
            print(
                "  WARN  openai package not installed, skipping summaries",
                file=sys.stderr,
            )
        elif not os.environ.get("OPENAI_API_KEY"):
            print("  WARN  OPENAI_API_KEY not set, skipping summaries", file=sys.stderr)
        else:
            client = OpenAI()
            to_summarize = [a for a in artifacts if a["URL"] in needs_summary]
            print(
                f"  Summarizing {len(to_summarize)} artifacts with {SUMMARY_MODEL}..."
            )
            t0 = time.perf_counter()

            for i, art in enumerate(to_summarize, 1):
                rel = art["_rel"]
                clean_body = file_data[rel]["clean_body"]

                result = _summarize_one(client, clean_body, summary_usage)
                if result:
                    art["summary_data"] = result
                    summarized_count += 1
                else:
                    summary_errors.append(art["URL"])

                if i % 10 == 0 or i == len(to_summarize):
                    elapsed = time.perf_counter() - t0
                    print(f"    [{i}/{len(to_summarize)}] {elapsed:.1f}s")

            print(f"  Summarized {summarized_count}, errors {len(summary_errors)}")

    # ── strip internal fields ──
    for art in artifacts:
        del art["_rel"]

    # ── report ──
    pending = sorted(a["URL"] for a in artifacts if a.get("summary_data") is None)

    report = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "total_artifacts": len(artifacts),
        "total_chunks": len(chunks),
        "new_files": sorted(new_urls),
        "updated_files": sorted(updated_urls),
        "deleted_files": sorted(deleted_urls),
        "new_count": len(new_urls),
        "updated_count": len(updated_urls),
        "deleted_count": len(deleted_urls),
        "summarized_count": summarized_count,
        "summary_errors": summary_errors,
        "pending_summaries": pending,
        "openai_usage": summary_usage.report(),
    }

    # ── delta files: only new + updated ──
    changed_urls = set(new_urls) | set(updated_urls)
    changed_ids = {a["idArtifact"] for a in artifacts if a["URL"] in changed_urls}

    delta = {
        "generated_at": report["generated_at"],
        "new": [a for a in artifacts if a["URL"] in new_urls],
        "updated": [a for a in artifacts if a["URL"] in updated_urls],
        "deleted": sorted(deleted_urls),
    }

    chunks_delta = {
        "generated_at": report["generated_at"],
        "chunks": [c for c in chunks if c["idArtifact"] in changed_ids],
    }

    # ── archive previous delta & report before overwriting ──
    stamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    for archivable in (
        "artifacts_delta.json",
        "content_chunks_delta.json",
        "generation_report.json",
    ):
        src = output_dir / archivable
        if src.exists():
            stem, ext = archivable.rsplit(".", 1)
            dst = output_dir / f"{stem}_{stamp}.{ext}"
            src.rename(dst)

    # ── write outputs ──
    for name, data in [
        ("artifacts.json", artifacts),
        ("content_chunks.json", chunks),
        ("generation_report.json", report),
        ("artifacts_delta.json", delta),
        ("content_chunks_delta.json", chunks_delta),
    ]:
        with open(output_dir / name, "w", encoding="utf-8") as fh:
            json.dump(data, fh, indent=2, ensure_ascii=False)

    _save_hashes(output_dir, current_hashes)

    print(f"Generated {len(artifacts)} artifacts, {len(chunks)} chunks")
    if deleted_urls:
        print(f"Deleted ({len(deleted_urls)}):")
        for u in deleted_urls:
            print(f"  - {u}")
    if new_urls:
        print(f"New ({len(new_urls)}):")
        for u in new_urls:
            print(f"  + {u}")
    if updated_urls:
        print(f"Updated ({len(updated_urls)}):")
        for u in updated_urls:
            print(f"  ~ {u}")
    if pending:
        print(f"Pending summaries: {len(pending)}")

    return 0


# ── CLI ──────────────────────────────────────────────────────────────────────


def main() -> int:
    ap = argparse.ArgumentParser(
        description="Generate artifacts.json & content_chunks.json from mixed_docs"
    )
    ap.add_argument(
        "--mixed-docs",
        type=Path,
        default=DEFAULT_MIXED_DOCS,
        help="Path to the mixed_docs directory",
    )
    ap.add_argument(
        "--output",
        type=Path,
        default=DEFAULT_OUTPUT,
        help="Output directory for JSON files",
    )
    ap.add_argument(
        "--summarize",
        action="store_true",
        help="Call LLM to generate summary_data for new/modified artifacts",
    )
    args = ap.parse_args()

    if not args.mixed_docs.exists():
        print(f"Error: mixed_docs not found: {args.mixed_docs}", file=sys.stderr)
        return 1

    return generate(args.mixed_docs, args.output, summarize=args.summarize)


if __name__ == "__main__":
    sys.exit(main())
