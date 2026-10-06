"""Rebuild the knowledge-base corpus from the repo's source files (no Azure needed).

Reproduces what PopulateDB.ipynb does to fill the database - same artifact
and chunk types (with the same ids the chunk JSON files reference), same
summary_data / metadata / retrieval_metadata_text payloads, same parent
relationships - but writes the result to corpus_export.json.gz (the format
migrate_to_bedrock.py --export produces) instead of into Postgres.
migrate_to_bedrock.py then embeds it with Titan and loads it into Aurora.

Sources (all in this folder):
    json/publication_artifacts.json + json/publication_chunks.json
    json/hub_artifacts.json         + json/hub_chunks.json
    json/dataset_artifacts.json     + json/dataset_chunks.json
    json/coderepo_artifacts.json    + json/coderepo_chunks.json
    CIROH-Hub/                      (the .mdx pages, for Hub page summaries)

CIROH Hub page summaries are the only LLM step: PopulateDB generated them
with OpenAI from each page's .mdx file; here Bedrock generates them with
the same prompt (BEDROCK_CHAT_MODEL_ID, falling back to Amazon Nova Pro if
the Claude model isn't enabled in the account). Results are cached in
hub_summaries_cache.json, so re-runs don't pay for them again.

Usage (AWS credentials needed only for the summaries):
    python build_corpus_from_json.py                  # full build
    python build_corpus_from_json.py --skip-summaries # offline dry build (Hub pages get no summary)
"""

from __future__ import annotations

import argparse
import gzip
import json
import re
import sys
from collections import Counter
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.append(str(HERE.parent))

JSON_DIR = HERE / "json"
HUB_ROOT_NAME = "CIROH-Hub"
HUB_ROOT = HERE / HUB_ROOT_NAME
HUB_BASE_URL = "https://hub.ciroh.org"
OUTPUT_PATH = HERE / "corpus_export.json.gz"
SUMMARY_CACHE_PATH = HERE / "hub_summaries_cache.json"
FALLBACK_SUMMARY_MODEL = "us.amazon.nova-pro-v1:0"
MAX_MDX_CHARS = 120_000

# ---------------------------------------------------------------------------
# Catalogs. Ids match the live database the chunk JSON files were built
# against (PopulateDB.ipynb cell 8, plus the dataset/code-repo types added
# later - ids taken from HydroShare_Datasets.ipynb / GitHub_CodeRepos.ipynb
# outputs). Course/Presentation fill 27-41 in PopulateDB's order.
# ---------------------------------------------------------------------------
HUB, PUB, DATASET, REPO, COURSE, PRESENTATION = 1, 2, 3, 4, 5, 6
ARTIFACT_TYPES = {
    HUB: "CIROH Hub Page",
    PUB: "Publication",
    DATASET: "Dataset",
    REPO: "GitHub Repository",
    COURSE: "Course",
    PRESENTATION: "Presentation",
}
CHUNK_TYPES = [
    (1, HUB, "Section"), (2, HUB, "Subsection"), (3, HUB, "Subsubsection"),
    (4, PUB, "Background"), (5, PUB, "Research Goal"), (6, PUB, "Problem"), (7, PUB, "Method"),
    (8, PUB, "Data"), (9, PUB, "Result"), (10, PUB, "Discussion-Limitation"), (11, PUB, "Conclusion"),
    (12, DATASET, "Abstract"), (13, DATASET, "Spatial Coverage"), (14, DATASET, "Temporal Coverage"),
    (15, DATASET, "Variable Metadata"), (16, DATASET, "Data Services Info"),
    (17, DATASET, "File Description"), (18, DATASET, "Collection Contents"),
    (19, DATASET, "Subject Keywords"), (20, DATASET, "Related Resources Context"),
    (21, REPO, "Project Overview"), (22, REPO, "Installation Setup"), (23, REPO, "Usage Examples"),
    (24, REPO, "Repository Structure"), (25, REPO, "Contributing Guidelines"),
    (26, REPO, "License Citation"),
    (27, COURSE, "Problem Statement"), (28, COURSE, "Module Overview"), (29, COURSE, "Topic Covered"),
    (30, COURSE, "Prerequisites"), (31, COURSE, "Learning Objective"),
    (32, COURSE, "Suggested Implementation"), (33, COURSE, "Target Audience"),
    (34, COURSE, "Author"), (35, COURSE, "Tools Needed"), (36, COURSE, "Expected Effort"),
    (37, COURSE, "Citation"),
    (38, PRESENTATION, "Abstract"), (39, PRESENTATION, "Subject Keywords"),
    (40, PRESENTATION, "Collection Contents"), (41, PRESENTATION, "Related Resources Context"),
    (42, DATASET, "Citation"), (43, DATASET, "Creator"), (44, DATASET, "Contributor"),
    (45, DATASET, "Funding Agency"), (46, DATASET, "Additional Metadata"),
    (47, DATASET, "Readme File"),
    (48, REPO, "Documentation Section"), (49, REPO, "Notebook Section"),
    (50, REPO, "Configuration / Deployment"), (51, REPO, "Change Log / Release Notes"),
]
PUB_CHUNK_TYPE_IDS = {name: cid for cid, atype, name in CHUNK_TYPES if atype == PUB}
HUB_FILE_CHUNK_TYPE = {1: 1, 2: 2, 3: 3}  # hub_chunks.json idChunkType -> Section/Subsection/Subsubsection


def _load(name: str):
    with (JSON_DIR / name).open(encoding="utf-8") as fh:
        return json.load(fh)


def sanitize(obj):
    """Recursively strip NUL characters (Postgres TEXT/JSONB can't store them)."""
    if isinstance(obj, dict):
        return {k: sanitize(v) for k, v in obj.items()}
    if isinstance(obj, list):
        return [sanitize(v) for v in obj]
    if isinstance(obj, str):
        return obj.replace("\x00", "")
    return obj


def clean(value) -> str:
    return "" if value is None else str(value).replace("\x00", "").strip()


class CorpusBuilder:
    def __init__(self) -> None:
        self.artifacts: list[dict] = []
        self.chunks: list[dict] = []
        self.errors: list[str] = []

    def add_artifact(self, *, atype, title, url, parent, summary_data, metadata, last_updated=None) -> int:
        idartifact = len(self.artifacts) + 1
        self.artifacts.append(
            {
                "idartifact": idartifact,
                "idartifacttype": atype,
                "title": title,
                "url": url,
                "idartifactparent": parent,
                "summary_data": summary_data,
                "metadata": metadata,
                "last_updated": last_updated,
                "isactive": True,
            }
        )
        return idartifact

    def add_chunk(self, *, idartifact, idchunktype, order, chunk_text, metadata) -> int:
        idchunk = len(self.chunks) + 1
        self.chunks.append(
            {
                "idchunk": idchunk,
                "idartifact": idartifact,
                "idchunktype": idchunktype,
                "idchunkparent": None,
                "order": order,
                "chunk_text": chunk_text,
                "metadata": metadata,
            }
        )
        return idchunk

    def set_chunk_parent(self, idchunk: int, parent: int) -> None:
        self.chunks[idchunk - 1]["idchunkparent"] = parent

    # -- Publications (PopulateDB cells 10-17) ------------------------------
    def load_publications(self) -> None:
        meta = _load("publication_artifacts.json").get("records", [])
        chunk_recs = _load("publication_chunks.json").get("records", [])

        def is_corr(pid):
            return isinstance(pid, str) and pid.endswith("-corrigendum")

        pid_to_id: dict[str, int] = {}
        ordered = [r for r in meta if r.get("paper_id") and not is_corr(r["paper_id"])]
        ordered += [r for r in meta if r.get("paper_id") and is_corr(r["paper_id"])]
        for rec in ordered:
            pid = rec["paper_id"]
            if not rec.get("url"):
                self.errors.append(f"publication {pid}: empty url, skipped")
                continue
            parent = None
            if is_corr(pid):
                parent = pid_to_id.get(pid.replace("-corrigendum", ""))
                if parent is None:
                    self.errors.append(f"publication {pid}: parent paper missing, skipped")
                    continue
            keywords = rec.get("keywords") if isinstance(rec.get("keywords"), list) else []
            authors = rec.get("authors", []) or []
            metadata = {
                "paper_id": pid,
                "year": rec.get("year", ""),
                "doi": rec.get("doi", ""),
                "journal": rec.get("journal", ""),
                "url": rec.get("url", ""),
                "authors": authors,
                "title": rec.get("title", ""),
            }
            summary = {
                "entities": [],
                "keywords": keywords,
                "summary_text": rec.get("abstract") or "",
                "document_type": "Publication",
            }
            author_names = [clean(a.get("author")) for a in authors if isinstance(a, dict) and clean(a.get("author"))]
            affiliations = sorted({clean(a.get("affiliation")) for a in authors if isinstance(a, dict) and clean(a.get("affiliation"))})
            metadata["retrieval_metadata_text"] = _lines(
                "Artifact type: Publication",
                "Document type: Publication",
                _opt("Journal", metadata["journal"]),
                _opt("Year", metadata["year"]),
                _opt("DOI", metadata["doi"]),
                _opt("Authors", "; ".join(author_names)),
                _opt("Affiliations", "; ".join(affiliations)),
            )
            pid_to_id[pid] = self.add_artifact(
                atype=PUB, title=rec.get("title") or "", url=rec["url"], parent=parent,
                summary_data=summary, metadata=metadata,
            )

        for rec in chunk_recs:
            idartifact = pid_to_id.get(rec.get("paper_id"))
            if idartifact is None:
                continue
            for ch in rec.get("chunks") or []:
                ctype = PUB_CHUNK_TYPE_IDS.get((ch.get("chunk_type") or "").strip())
                text = ch.get("text") or ""
                try:
                    order = int(str(ch.get("chunk_id", "")).split("__")[-1])
                except ValueError:
                    order = None
                if ctype is None or not text.strip() or order is None:
                    self.errors.append(f"publication chunk {ch.get('chunk_id')}: skipped (type/text/order)")
                    continue
                self.add_chunk(
                    idartifact=idartifact, idchunktype=ctype, order=order, chunk_text=text,
                    metadata={
                        "section_hint": ch.get("section_hint") or "",
                        "supporting_quote": ch.get("supporting_quote") or [],
                        "type_specific": {},
                    },
                )

    # -- CIROH Hub pages (cells 20-36) ----------------------------------------
    def load_hub(self, summaries: dict[str, dict]) -> None:
        records = _load("hub_artifacts.json")
        chunks = _load("hub_chunks.json")

        src_to_id: dict[int, int] = {}
        for rec in records:  # parents always precede children in this file
            if not rec.get("URL"):
                self.errors.append(f"hub page {rec.get('idArtifact')}: empty URL, skipped")
                continue
            summary = summaries.get(rec["URL"])
            tags = rec.get("tags", []) or []
            description = rec.get("description", "") or ""
            last_updated_src = rec.get("Last updated date", "") or ""
            metadata = {
                "ciroh_hub": {
                    "source_id": rec.get("idArtifact"),
                    "parent_source_id": rec.get("idArtifactParent"),
                    "description": description,
                    "tags": tags,
                    "source_last_updated": last_updated_src,
                }
            }
            entities = (summary or {}).get("entities") or []
            metadata["retrieval_metadata_text"] = _lines(
                "Artifact type: CIROH Hub Page",
                "Document type: " + ((summary or {}).get("document_type") or ""),
                _opt("Entities", ", ".join(str(e) for e in entities)),
                _opt("Tags", ", ".join(str(t) for t in tags)),
                _opt("Description", description),
                _opt("Last updated", last_updated_src),
            )
            try:
                last_updated = datetime.strptime(last_updated_src.strip(), "%m/%d/%Y").isoformat()
            except ValueError:
                last_updated = None
            parent_src = rec.get("idArtifactParent")
            src_to_id[rec["idArtifact"]] = self.add_artifact(
                atype=HUB, title=rec.get("Title") or "", url=rec["URL"],
                parent=src_to_id.get(parent_src) if parent_src is not None else None,
                summary_data=summary, metadata=metadata, last_updated=last_updated,
            )

        self._load_child_chunks(
            chunks, src_to_id,
            type_of=lambda ch: HUB_FILE_CHUNK_TYPE.get(ch.get("idChunkType")),
            text_of=lambda ch: clean(ch.get("chunk_text")),
            keep=lambda ch, text: bool(text or clean(ch.get("title"))),  # header-only chunks allowed
            metadata_of=lambda ch: {
                "section_hint": clean(ch.get("title")),
                "supporting_quote": [],
                "type_specific": {},
            },
            label="hub",
        )

    # -- HydroShare datasets (cells 38-45) ------------------------------------
    def load_datasets(self) -> None:
        records = _load("dataset_artifacts.json")
        src_to_id: dict[int, int] = {}
        for rec in records:
            if not clean(rec.get("URL")):
                self.errors.append(f"dataset {rec.get('idArtifact')}: empty URL, skipped")
                continue
            ds = {
                k: rec.get(k)
                for k in (
                    "resource_type", "identifier", "language", "doi", "date_created",
                    "date_last_updated", "published", "immutable", "public", "discoverable", "shareable",
                )
            }
            ds = {"source_idartifact": rec.get("idArtifact"), "resource_id": rec.get("resource_id"), **ds}
            keywords = rec.get("keywords") if isinstance(rec.get("keywords"), list) else []
            doc_type = clean(rec.get("document_type")) or "Dataset"
            metadata = {"dataset": ds}
            metadata["retrieval_metadata_text"] = _lines(
                "Artifact type: Dataset",
                "Document type: " + doc_type,
                _opt("Resource type", ds["resource_type"]),
                _opt("DOI", ds["doi"]),
                _opt("Language", ds["language"]),
                *[_present(label, ds[key]) for label, key in (
                    ("Published", "published"), ("Public", "public"), ("Discoverable", "discoverable"),
                    ("Immutable", "immutable"), ("Shareable", "shareable"),
                )],
                _opt("Date created", ds["date_created"]),
                _opt("Last updated", ds["date_last_updated"]),
            )
            src_to_id[rec["idArtifact"]] = self.add_artifact(
                atype=DATASET, title=clean(rec.get("Title")), url=clean(rec.get("URL")), parent=None,
                summary_data={
                    "entities": [], "keywords": keywords,
                    "summary_text": clean(rec.get("abstract")), "document_type": doc_type,
                },
                metadata=metadata,
            )
        self._load_source_chunks(_load("dataset_chunks.json"), src_to_id, "dataset")

    # -- GitHub repositories (cells 49-57) ------------------------------------
    def load_repos(self) -> None:
        records = [
            r for r in _load("coderepo_artifacts.json")
            if r.get("artifact_role") == "repository" and r.get("idArtifactParent") is None
        ]
        src_to_id: dict[int, int] = {}
        for rec in records:
            if not clean(rec.get("Title")) or not clean(rec.get("URL")):
                self.errors.append(f"repo {rec.get('idArtifact')}: empty title/URL, skipped")
                continue
            gh = {
                "source_idartifact": rec.get("idArtifact"),
                **{k: rec.get(k) for k in (
                    "artifact_role", "full_name", "description", "default_branch", "frozen_commit_sha",
                    "language", "created_at", "updated_at", "pushed_at", "contributors_summary",
                    "selected_files_summary",
                )},
                "topics": rec.get("topics") or [],
            }
            s = rec.get("summary_data") or {}
            summary = {
                "entities": s.get("entities") or [],
                "keywords": s.get("keywords") or [],
                "summary_text": clean(s.get("summary_text")),
                "document_type": clean(s.get("document_type")) or "code repository",
            }
            contributors = (gh.get("contributors_summary") or {})
            files = (gh.get("selected_files_summary") or {})
            logins = [clean(c.get("login")) for c in contributors.get("top_contributors") or [] if isinstance(c, dict) and clean(c.get("login"))]
            extensions = files.get("downloaded_extensions") or {}
            metadata = {"github_repo": gh}
            metadata["retrieval_metadata_text"] = _lines(
                "Artifact type: GitHub Repository",
                "Document type: " + summary["document_type"],
                _opt("Repository full name", gh.get("full_name")),
                _opt("Description", gh.get("description")),
                _opt("Primary language", gh.get("language")),
                _opt("Topics", ", ".join(str(t) for t in gh["topics"])),
                _opt("Default branch", gh.get("default_branch")),
                _opt("Top contributors", ", ".join(logins)),
                _opt("Contributors count", contributors.get("contributors_count")),
                _opt("Downloaded file extensions", ", ".join(f"{k}={v}" for k, v in extensions.items())),
                _opt("Sample downloaded paths", "; ".join(str(p) for p in files.get("sample_downloaded_paths") or [])),
            )
            src_to_id[rec["idArtifact"]] = self.add_artifact(
                atype=REPO, title=clean(rec["Title"]), url=clean(rec["URL"]), parent=None,
                summary_data=summary, metadata=metadata,
            )
        self._load_source_chunks(_load("coderepo_chunks.json"), src_to_id, "repo")

    # -- shared chunk loaders --------------------------------------------------
    def _load_source_chunks(self, chunks, src_to_id, label) -> None:
        """Dataset / code-repo chunks: JSON idChunkType is already the catalog id."""
        self._load_child_chunks(
            chunks, src_to_id,
            type_of=lambda ch: ch.get("idChunkType"),
            text_of=lambda ch: clean(ch.get("chunk_text")),
            keep=lambda ch, text: bool(text),
            metadata_of=lambda ch: {
                "source_chunk_id": ch.get("idChunk"),
                "source_artifact_id": ch.get("idArtifact"),
                "section_hint": clean(ch.get("section_hint")),
                "supporting_quote": ch.get("supporting_quote") or [],
                "type_specific": ch.get("type_specific") or {},
            },
            label=label,
        )

    def _load_child_chunks(self, chunks, src_to_id, *, type_of, text_of, keep, metadata_of, label) -> None:
        src_chunk_to_id: dict[tuple, int] = {}
        edges = []
        for ch in chunks:
            idartifact = src_to_id.get(ch.get("idArtifact"))
            ctype = type_of(ch)
            text = text_of(ch)
            if idartifact is None or ctype is None or ch.get("order") is None or not keep(ch, text):
                self.errors.append(f"{label} chunk {ch.get('idChunk')}: skipped (artifact/type/order/text)")
                continue
            new_id = self.add_chunk(
                idartifact=idartifact, idchunktype=int(ctype), order=int(ch["order"]),
                chunk_text=text, metadata=metadata_of(ch),
            )
            src_chunk_to_id[(ch["idArtifact"], ch.get("idChunk"))] = new_id
            if ch.get("idChunkParent") is not None:
                edges.append((new_id, (ch["idArtifact"], ch["idChunkParent"])))
        for child, parent_key in edges:
            parent = src_chunk_to_id.get(parent_key)
            if parent is not None:
                self.set_chunk_parent(child, parent)


def _opt(label: str, value) -> str | None:
    value = clean(value)
    return f"{label}: {value}" if value else None


def _present(label: str, value) -> str | None:
    # Mirrors the SQL `metadata->'dataset' ? key` checks (key present, even if false).
    if value is None:
        return None
    return f"{label}: {str(value).lower() if isinstance(value, bool) else value}"


def _lines(*parts) -> str:
    return "\n".join(p for p in parts if p)


# ---------------------------------------------------------------------------
# CIROH Hub page -> .mdx lookup (PopulateDB cells 27-30)
# ---------------------------------------------------------------------------
_frontmatter_cache: dict[str, re.Pattern] = {}


def _frontmatter_field(raw: str, field: str) -> str | None:
    text = raw.lstrip()
    if not text.startswith("---"):
        return None
    fm = []
    for line in text.splitlines()[1:]:
        if line.strip() == "---":
            break
        fm.append(line)
    pattern = _frontmatter_cache.setdefault(field, re.compile(rf"(?m)^\s*{re.escape(field)}\s*:\s*(.*?)\s*$"))
    m = pattern.search("\n".join(fm))
    if not m:
        return None
    return m.group(1).strip().strip('"').strip("'") or None


def _canon_slug(s: str) -> str:
    return re.sub(r"\s+", " ", (s or "").strip().strip('"').strip("'")).lower().strip()


def _canon_page_path(value: str) -> str:
    value = (value or "").strip().replace("\\", "/").split("?", 1)[0].split("#", 1)[0]
    value = re.sub(r"/+", "/", value).strip("/")
    if value == "src/pages":
        value = ""
    elif value.startswith("src/pages/"):
        value = value[len("src/pages/"):].lstrip("/")
    return value.lower().strip("/")


def _index(root: Path, field: str, canon) -> dict[str, Path]:
    idx: dict[str, Path] = {}
    if not root.exists():
        return idx
    for p in sorted(root.rglob("*.mdx")):
        value = _frontmatter_field(p.read_text(encoding="utf-8", errors="replace"), field)
        if value is not None:
            idx.setdefault(canon(value), p)
    return idx


class MdxLocator:
    def __init__(self) -> None:
        self.blog = _index(HUB_ROOT / "blog", "slug", _canon_slug)
        self.release_notes = _index(HUB_ROOT / "release-notes", "slug", _canon_slug)
        self.generated = _index(HUB_ROOT / "_generated_js_pages", "path", _canon_page_path)
        self.src_pages = _index(HUB_ROOT / "src" / "pages", "path", _canon_page_path)

    def find(self, url: str) -> Path | None:
        folder = url.replace(HUB_BASE_URL, HUB_ROOT_NAME).replace("\\", "/")
        rel = folder[len(HUB_ROOT_NAME):] if folder.startswith(HUB_ROOT_NAME) else folder
        rel_path = _canon_page_path(rel)
        for idx in (self.generated, self.src_pages):
            hit = idx.get(rel_path)
            if hit is not None and hit.exists():
                return hit
        f = folder + ("" if folder.endswith("/") else "/")
        segment = folder.rstrip("/").split("/")[-1]
        if "/blog/" in f:
            return self.blog.get(_canon_slug(segment))
        if "/release-notes/" in f:
            return self.release_notes.get(_canon_slug(segment))
        if "/docs/" in f:
            # Case-sensitive path from the original (un-lowercased) URL.
            after = folder.rstrip("/").split("/docs", 1)[1].strip("/")
            sub = Path(after) if after else Path()
            docs = HUB_ROOT / "docs"
            candidates = []
            if sub.name:
                candidates.append(docs / sub.parent / f"{sub.name}.mdx")
            candidates += [docs / sub / "index.mdx", docs / sub / "intro.mdx"]
            return next((c for c in candidates if c.exists()), None)
        return None


# ---------------------------------------------------------------------------
# Hub summaries via Bedrock (PopulateDB cell 31 prompt)
# ---------------------------------------------------------------------------
SUMMARY_SYSTEM = "You are a precise CIROH Hub summarizer. Return ONLY valid JSON. No prose, no markdown."
SUMMARY_SCHEMA = {
    "type": "object",
    "properties": {
        "summary_text": {"type": "string"},
        "keywords": {"type": "array", "items": {"type": "string"}},
        "entities": {"type": "array", "items": {"type": "string"}},
        "document_type": {"type": "string"},
    },
    "required": ["summary_text", "keywords", "entities", "document_type"],
}


def _summary_prompt(markdown_content: str) -> str:
    return f"""
# ROLE & GOAL
You are an AI Knowledge Architect specializing in hydrology and scientific computing for the Cooperative Institute for Research to Operations in Hydrology (CIROH). Your task is to process the content of a webpage from CIROH's Hub documentation site.

# CONTEXT
The output you generate will be stored in a PostgreSQL database to power a Retrieval-Augmented Generation (RAG) system. The `summary_text` within your response will be used to create a vector embedding for semantic search. Therefore, the summary must be information-dense, conceptually accurate, and optimized to be found by user queries about CIROH's products, services, policies, and research activities.

# CONTENT TO ANALYZE
---
**[BEGINNING OF MARKDOWN CONTENT]**

{markdown_content}

**[END OF MARKDOWN CONTENT]**
---

# INSTRUCTIONS
Based on the content provided above, generate a single JSON object. Follow these rules precisely:

1.  **Focus on "What" and "Why"**: The `summary_text` should clearly identify the page's core purpose. Is it a product description, a tutorial, a policy document, a release note, or a blog post?
2.  **Extract Named Entities**: The `entities` array must include all specific names of products, services, tools, technologies, standards, or key collaborators mentioned (e.g., "NextGen in A Box", "Research Datastream", "Hydrofabric", "NOAA", "BYU Hydroinformatics Courses").
3.  **Capture Key Concepts**: The `keywords` array should capture the main technical or thematic concepts, not just proper nouns (e.g., "hydrologic modeling", "flood inundation mapping", "water quality", "data management", "cloud computing", "machine learning").
4.  **Synthesize, Don't Quote**: Do not copy sentences directly from the text. Synthesize the information in your own words to create a coherent and semantically rich summary.
5.  **Be Dense and Direct**: Start the summary directly with the subject. Avoid introductory phrases. For example, instead of writing "This page describes NextGen In A Box...", you must write "NextGen In A Box is a community-accessible...". Be direct and objective.
""".strip()


def _strip_frontmatter(mdx: str) -> str:
    text = mdx.lstrip()
    if not text.startswith("---"):
        return text
    lines = text.split("\n")
    for i in range(1, len(lines)):
        if lines[i].strip() == "---":
            return "\n".join(lines[i + 1:]).lstrip()
    return text


def _truncate(mdx: str) -> str:
    mdx = _strip_frontmatter(mdx.replace("\x00", ""))
    if len(mdx) <= MAX_MDX_CHARS:
        return mdx
    return mdx[: int(MAX_MDX_CHARS * 0.7)] + "\n\n...\n\n" + mdx[-int(MAX_MDX_CHARS * 0.3):]


class HubSummarizer:
    def __init__(self) -> None:
        from aws import bedrock_client

        self.bc = bedrock_client
        self.model = bedrock_client.CHAT_MODEL_ID

    def _call(self, prompt: str, model: str) -> dict:
        result = self.bc.converse_json(
            prompt,
            tool_name="save_page_summary",
            tool_description="Save the structured summary of a CIROH Hub page.",
            json_schema=SUMMARY_SCHEMA,
            system_prompt=SUMMARY_SYSTEM,
            max_tokens=1500,
            temperature=0.2,
            model_id=model,
        )
        return result["data"]

    def summarize(self, mdx_text: str) -> dict:
        prompt = _summary_prompt(_truncate(mdx_text))
        try:
            data = self._call(prompt, self.model)
        except Exception as e:  # noqa: BLE001 - model not enabled -> fall back once
            code = getattr(e, "response", {}).get("Error", {}).get("Code", "")
            if self.model == FALLBACK_SUMMARY_MODEL or code not in (
                "AccessDeniedException", "ResourceNotFoundException", "ValidationException",
            ):
                raise
            print(f"  {self.model} unavailable ({code}); using {FALLBACK_SUMMARY_MODEL} for summaries.")
            self.model = FALLBACK_SUMMARY_MODEL
            data = self._call(prompt, self.model)
        return {
            "summary_text": clean(data.get("summary_text")),
            "keywords": data.get("keywords") if isinstance(data.get("keywords"), list) else [],
            "entities": data.get("entities") if isinstance(data.get("entities"), list) else [],
            "document_type": clean(data.get("document_type")),
        }


def build_hub_summaries(skip: bool, concurrency: int) -> dict[str, dict]:
    """{url: summary_data} for every Hub page whose .mdx can be found."""
    cache = json.loads(SUMMARY_CACHE_PATH.read_text(encoding="utf-8")) if SUMMARY_CACHE_PATH.exists() else {}
    locator = MdxLocator()
    records = _load("hub_artifacts.json")
    todo, missing = [], []
    for rec in records:
        url = rec.get("URL")
        if not url or url in cache:
            continue
        path = locator.find(url)
        (todo if path else missing).append((url, path))
    print(f"CIROH Hub pages: {len(records)} | cached summaries: {len(cache)} | "
          f"to summarize: {len(todo)} | no .mdx found (left unsummarized): {len(missing)}")
    if skip or not todo:
        return cache

    summarizer = HubSummarizer()
    print(f"Summarizing {len(todo)} pages with Bedrock ({summarizer.model})...")

    def work(item):
        url, path = item
        try:
            return url, summarizer.summarize(path.read_text(encoding="utf-8", errors="replace")), None
        except Exception as e:  # noqa: BLE001 - report and continue
            return url, None, str(e)

    done = 0
    with ThreadPoolExecutor(max_workers=concurrency) as pool:
        for url, summary, err in pool.map(work, todo):
            done += 1
            if summary and summary["summary_text"]:
                cache[url] = summary
            else:
                print(f"  failed: {url}: {err or 'empty summary'}")
            if done % 20 == 0 or done == len(todo):
                SUMMARY_CACHE_PATH.write_text(json.dumps(cache), encoding="utf-8")
                print(f"  {done}/{len(todo)}")
    return cache


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--skip-summaries", action="store_true", help="Don't call Bedrock for Hub page summaries.")
    parser.add_argument("--concurrency", type=int, default=4, help="Parallel summary calls.")
    parser.add_argument("--output", default=str(OUTPUT_PATH), help="Output file (.json.gz).")
    args = parser.parse_args()

    summaries = build_hub_summaries(args.skip_summaries, args.concurrency)

    builder = CorpusBuilder()
    builder.load_publications()
    builder.load_hub(summaries)
    builder.load_datasets()
    builder.load_repos()

    corpus = sanitize(
        {
            "artifact_types": [{"idartifacttype": k, "typename": v} for k, v in ARTIFACT_TYPES.items()],
            "chunk_types": [
                {"idchunktype": cid, "idartifacttype": atype, "typename": name} for cid, atype, name in CHUNK_TYPES
            ],
            "artifacts": builder.artifacts,
            "chunks": builder.chunks,
        }
    )
    out = Path(args.output)
    with gzip.open(out, "wt", encoding="utf-8") as fh:
        json.dump(corpus, fh)

    by_type = Counter(ARTIFACT_TYPES[a["idartifacttype"]] for a in builder.artifacts)
    unsummarized = sum(1 for a in builder.artifacts if a["summary_data"] is None)
    print(f"\nArtifacts: {len(builder.artifacts)} {dict(by_type)}")
    print(f"Chunks: {len(builder.chunks)} (with parent: {sum(1 for c in builder.chunks if c['idchunkparent'])})")
    print(f"Artifacts without summary (not searchable at page level): {unsummarized}")
    print(f"Skipped source rows: {len(builder.errors)}" + (f", e.g. {builder.errors[:3]}" if builder.errors else ""))
    print(f"Wrote {out} ({out.stat().st_size / 1e6:.1f} MB). Next: python migrate_to_bedrock.py")


if __name__ == "__main__":
    main()
