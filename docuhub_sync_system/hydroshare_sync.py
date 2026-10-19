"""Incrementally build HydroShare artifacts and chunks for the CIROH Hub.

The module is deliberately generation-only: it never connects to PostgreSQL,
creates embeddings, or deactivates rows.  Public HydroShare resources can be
read anonymously.  ``HYDROSHARE_USERNAME`` and ``HYDROSHARE_PASSWORD`` are
used only when both values are present.

The discovery and extraction code accepts injected clients/sessions so the
behavior can be tested without network access.
"""
from __future__ import annotations

import hashlib
import html
import json
import os
import re
import xml.etree.ElementTree as ET
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable

try:  # Optional until a live HydroShare synchronization is requested.
    from hsclient import HydroShare
except ImportError:  # pragma: no cover - exercised in environments without hsclient
    HydroShare = None

try:
    import requests
except ImportError:  # pragma: no cover - project requirements normally provide it
    requests = None


HYDROSHARE_ARTIFACT_TYPE_ID = 3
CIROH_COMMUNITY_ID = "4"
STATE_SCHEMA_VERSION = 1
CHUNK_SCHEMA_VERSION = 1
ARTIFACT_SCHEMA_VERSION = 2
MAX_ARTIFACT_SUMMARY_CHARS = 12_000
MAX_README_CHUNK_CHARS = 12_000
# Refuse a discovery result that would remove at least five prior resources and
# at least 25% of the prior snapshot.  The absolute floor avoids obstructing
# normal cleanup in tiny development snapshots; the ratio catches partial,
# non-empty production results that an empty-result-only guard would miss.
LARGE_REMOVAL_MINIMUM_COUNT = 5
LARGE_REMOVAL_FRACTION = 0.25
RESOURCE_ID_RE = re.compile(r"^[0-9a-f]{32}$")
RESOURCE_ID_IN_URL_RE = re.compile(r"/resource/([0-9a-fA-F]{32})")
URL_RE = re.compile(r'https?://[^\s<>\"]+')

PORTAL_CATEGORY_SUBJECTS: dict[str, tuple[str, ...]] = {
    "Apps": ("nwm_portal_app", "ciroh_hub_app"),
    "Datasets": ("ciroh_portal_data", "ciroh_hub_data"),
    "Courses": ("nwm_portal_module", "ciroh_hub_module"),
    "Presentations": (
        "ciroh_portal_presentation",
        "ciroh_hub_presentation",
    ),
    "Events": ("ciroh_hub_event",),
    "Notebooks": ("ciroh_hub_notebook",),
}
PORTAL_CATEGORY_ORDER = tuple(PORTAL_CATEGORY_SUBJECTS)

HYDROSHARE_CHUNK_TYPES = (
    "Abstract",
    "Spatial Coverage",
    "Temporal Coverage",
    "Variable Metadata",
    "Data Services Info",
    "File Description",
    "Collection Contents",
    "Subject Keywords",
    "Related Resources Context",
    "Citation",
    "Creator",
    "Contributor",
    "Funding Agency",
    "Additional Metadata",
    "Readme File",
)

NS = {
    "dc": "http://purl.org/dc/elements/1.1/",
    "dcterms": "http://purl.org/dc/terms/",
    "hsterms": "https://www.hydroshare.org/terms/",
    "rdf": "http://www.w3.org/1999/02/22-rdf-syntax-ns#",
}


@dataclass(frozen=True)
class HydroShareSyncConfig:
    """Filesystem locations used by the HydroShare generation stage."""

    root: Path
    artifact_output: Path | None = None
    chunk_output: Path | None = None
    report_output: Path | None = None
    state_path: Path | None = None
    corpus_dir: Path | None = None
    community_id: str = CIROH_COMMUNITY_ID

    def resolved(self) -> "HydroShareSyncConfig":
        root = self.root.resolve()
        formatted = root / "dashboard" / "formated_files"
        local = root / "local_change_dashboard"
        return HydroShareSyncConfig(
            root=root,
            artifact_output=(
                self.artifact_output or formatted / "hydroshare_artifacts.json"
            ).resolve(),
            chunk_output=(
                self.chunk_output or formatted / "hydroshare_chunks.json"
            ).resolve(),
            report_output=(
                self.report_output
                or formatted / "hydroshare_generation_report.json"
            ).resolve(),
            state_path=(
                self.state_path or local / "hydroshare_sync.json"
            ).resolve(),
            corpus_dir=(
                self.corpus_dir or local / "hydroshare_corpus"
            ).resolve(),
            community_id=str(self.community_id),
        )


def create_hydroshare_client(
    username: str | None = None,
    password: str | None = None,
) -> Any:
    """Create an anonymous or optionally authenticated ``hsclient`` client."""

    if HydroShare is None:
        raise RuntimeError(
            "Live HydroShare synchronization requires the optional 'hsclient' "
            "package. Install the project requirements first."
        )
    username = username or os.getenv("HYDROSHARE_USERNAME")
    password = password or os.getenv("HYDROSHARE_PASSWORD")
    if bool(username) != bool(password):
        raise ValueError(
            "HYDROSHARE_USERNAME and HYDROSHARE_PASSWORD must be provided together"
        )
    return HydroShare(username=username, password=password) if username else HydroShare()


def _http_session(session: Any | None) -> Any:
    if session is not None:
        return session
    if requests is None:
        raise RuntimeError("The 'requests' package is required for community discovery")
    return requests.Session()


def _load_json(path: Path, default: Any) -> Any:
    if not path.exists():
        return default
    try:
        with path.open("r", encoding="utf-8") as handle:
            return json.load(handle)
    except (OSError, json.JSONDecodeError):
        return default


def _write_json_atomic(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(f".{path.name}.tmp")
    with temporary.open("w", encoding="utf-8", newline="\n") as handle:
        json.dump(payload, handle, ensure_ascii=False, indent=2, sort_keys=True)
        handle.write("\n")
    temporary.replace(path)


def _write_text_atomic(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(f".{path.name}.tmp")
    temporary.write_text(text, encoding="utf-8", newline="\n")
    temporary.replace(path)


def _clean_text(value: Any) -> str | None:
    if value is None:
        return None
    text = html.unescape(str(value)).replace("\x00", "").strip()
    return text or None


def _jsonable(value: Any) -> Any:
    if value is None or isinstance(value, (bool, int, float, str)):
        return value
    if isinstance(value, dict):
        return {str(key): _jsonable(item) for key, item in value.items()}
    if isinstance(value, (list, tuple, set)):
        return [_jsonable(item) for item in value]
    if hasattr(value, "model_dump"):
        return _jsonable(value.model_dump())
    if hasattr(value, "dict"):
        return _jsonable(value.dict())
    return str(value)


def _as_dict(value: Any) -> dict[str, Any]:
    result = _jsonable(value)
    return result if isinstance(result, dict) else {}


def _normalize_resource_id(value: Any) -> str | None:
    candidate = _clean_text(value)
    if not candidate:
        return None
    candidate = candidate.lower()
    return candidate if RESOURCE_ID_RE.fullmatch(candidate) else None


def _resource_id(record: Any) -> str | None:
    if isinstance(record, dict):
        for key in ("resource_id", "resourceId", "id", "short_id"):
            resource_id = _normalize_resource_id(record.get(key))
            if resource_id:
                return resource_id
        for key in ("url", "resource_url"):
            match = RESOURCE_ID_IN_URL_RE.search(str(record.get(key) or ""))
            if match:
                return match.group(1).lower()
        return None
    for key in ("resource_id", "resourceId", "id", "short_id"):
        resource_id = _normalize_resource_id(getattr(record, key, None))
        if resource_id:
            return resource_id
    for key in ("url", "resource_url"):
        match = RESOURCE_ID_IN_URL_RE.search(str(getattr(record, key, "") or ""))
        if match:
            return match.group(1).lower()
    return None


def _response_json(response: Any) -> Any:
    response.raise_for_status()
    payload = response.json()
    if isinstance(payload, str):
        payload = json.loads(payload)
    return payload


def discover_ciroh_community_resource_ids(
    session: Any,
    community_id: str = CIROH_COMMUNITY_ID,
) -> set[str]:
    """Discover resources in every group belonging to a HydroShare community."""

    response = session.get(
        f"https://www.hydroshare.org/community/{community_id}/", timeout=60
    )
    response.raise_for_status()
    match = re.search(
        r'<script[^>]*id=["\']community-app-data["\'][^>]*>(.*?)</script>',
        str(response.text),
        re.IGNORECASE | re.DOTALL,
    )
    if not match:
        raise RuntimeError("Could not locate HydroShare community-app-data")
    community = json.loads(html.unescape(match.group(1)).strip())
    group_ids = sorted(
        {
            str(member.get("id"))
            for member in community.get("members", [])
            if isinstance(member, dict) and member.get("id") is not None
        }
    )
    resource_ids: set[str] = set()
    for group_id in group_ids:
        page = 1
        while True:
            payload = _response_json(
                session.get(
                    "https://www.hydroshare.org/hsapi/resource/",
                    params={"group": group_id, "page": page, "count": 100},
                    timeout=60,
                )
            )
            if not isinstance(payload, dict):
                raise TypeError("Unexpected HydroShare group response")
            for record in payload.get("results") or []:
                resource_id = _resource_id(record)
                if resource_id:
                    resource_ids.add(resource_id)
            if not payload.get("next"):
                break
            page += 1
    return resource_ids


def discover_hydroshare_resources(
    client: Any,
    *,
    session: Any | None = None,
    community_id: str = CIROH_COMMUNITY_ID,
) -> dict[str, dict[str, Any]]:
    """Return unique resources and all CIROH portal category memberships."""

    discovered: dict[str, dict[str, Any]] = {}
    for category in PORTAL_CATEGORY_ORDER:
        for subject in PORTAL_CATEGORY_SUBJECTS[category]:
            for resource in client.search(subject=[subject]):
                resource_id = _resource_id(resource)
                if not resource_id:
                    continue
                entry = discovered.setdefault(
                    resource_id, {"resource": resource, "portal_types": set()}
                )
                entry["portal_types"].add(category)

    for resource_id in discover_ciroh_community_resource_ids(
        _http_session(session), community_id
    ):
        entry = discovered.setdefault(
            resource_id, {"resource": None, "portal_types": set()}
        )
        entry["portal_types"].add("Datasets")

    order = {name: index for index, name in enumerate(PORTAL_CATEGORY_ORDER)}
    return {
        resource_id: {
            "resource": entry["resource"],
            "portal_types": sorted(entry["portal_types"], key=order.__getitem__),
        }
        for resource_id, entry in sorted(discovered.items())
    }


def _attribute(value: Any, name: str, default: Any = None) -> Any:
    return value.get(name, default) if isinstance(value, dict) else getattr(value, name, default)


def _retrieve_string(client: Any, url: Any) -> str | None:
    if not url:
        return None
    if hasattr(client, "retrieve_string"):
        return _clean_text(client.retrieve_string(url))
    hs_session = getattr(client, "_hs_session", None)
    if hs_session is not None and hasattr(hs_session, "retrieve_string"):
        return _clean_text(hs_session.retrieve_string(url))
    return None


def _file_record(file_object: Any) -> dict[str, Any]:
    return {
        "file_name": _clean_text(_attribute(file_object, "name")),
        "file_path": _clean_text(_attribute(file_object, "path")),
        "extension": _clean_text(_attribute(file_object, "extension")),
        "checksum": _clean_text(_attribute(file_object, "checksum")),
        "url": _clean_text(_attribute(file_object, "url")),
    }


def extract_resource_snapshot(client: Any, resource_id: str) -> dict[str, Any]:
    """Fetch normalized metadata, inventory, XML, and small README text."""

    resource = client.resource(resource_id)
    metadata = _as_dict(_attribute(resource, "metadata", {}))
    system_method = _attribute(resource, "system_metadata")
    system_metadata = _as_dict(system_method() if callable(system_method) else system_method)
    raw_xml = _retrieve_string(client, _attribute(resource, "metadata_path")) or ""

    files: list[dict[str, Any]] = []
    readmes: list[dict[str, str]] = []
    files_method = _attribute(resource, "files")
    try:
        file_objects = files_method() if callable(files_method) else (files_method or [])
        for file_object in file_objects:
            record = _file_record(file_object)
            files.append(record)
            name = str(record.get("file_name") or "").lower()
            if name in {"readme", "readme.md", "readme.txt"}:
                text = _retrieve_string(client, record.get("url"))
                if text:
                    readmes.append({"file_name": record["file_name"] or "README", "text": text})
    except IndexError:
        # hsclient raises this for some valid CollectionResource/ToolResource objects.
        files = []

    files.sort(
        key=lambda item: (
            str(item.get("file_path") or "").lower(),
            str(item.get("file_name") or "").lower(),
        )
    )
    unique_readmes: list[dict[str, str]] = []
    seen_readme_text: set[str] = set()
    for readme in sorted(readmes, key=lambda item: item["file_name"].lower()):
        normalized = readme["text"].replace("\r\n", "\n").replace("\r", "\n").strip()
        if normalized and normalized not in seen_readme_text:
            seen_readme_text.add(normalized)
            unique_readmes.append({"file_name": readme["file_name"], "text": normalized})
    return {
        "metadata": metadata,
        "system_metadata": system_metadata,
        "file_inventory": files,
        "raw_metadata_xml": raw_xml,
        "readmes": unique_readmes,
    }


def _snapshot_fingerprint(snapshot: dict[str, Any], portal_types: list[str]) -> str:
    system_metadata = snapshot.get("system_metadata") or {}
    payload = {
        "date_last_updated": system_metadata.get("date_last_updated"),
        "metadata": snapshot.get("metadata") or {},
        "system_metadata": system_metadata,
        "file_checksums": [
            {
                "file_name": item.get("file_name"),
                "file_path": item.get("file_path"),
                "checksum": item.get("checksum"),
            }
            for item in snapshot.get("file_inventory") or []
        ],
        "portal_types": portal_types,
        "raw_metadata_xml": snapshot.get("raw_metadata_xml") or "",
        "readmes": snapshot.get("readmes") or [],
    }
    canonical = json.dumps(payload, sort_keys=True, ensure_ascii=False, separators=(",", ":"))
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def _infer_document_type(resource_type: str | None) -> str:
    if resource_type == "CollectionResource":
        return "HydroShare dataset collection"
    if resource_type == "ToolResource":
        return "HydroShare web app connector"
    return "HydroShare dataset resource"


def _bounded_artifact_summary(text: str) -> str:
    if len(text) <= MAX_ARTIFACT_SUMMARY_CHARS:
        return text
    suffix = "…"
    return text[: MAX_ARTIFACT_SUMMARY_CHARS - len(suffix)].rstrip() + suffix


def build_hydroshare_artifact(
    resource_id: str,
    artifact_id: int,
    snapshot: dict[str, Any],
    portal_types: list[str],
) -> dict[str, Any]:
    """Build the artifact shape expected by the existing database loader."""

    meta = snapshot.get("metadata") or {}
    system = snapshot.get("system_metadata") or {}
    resource_type = _clean_text(meta.get("type")) or "CompositeResource"
    title = _clean_text(meta.get("title")) or f"HydroShare Resource {resource_id}"
    abstract = _clean_text(meta.get("abstract")) or ""
    raw_subjects = meta.get("subjects") or []
    if not isinstance(raw_subjects, (list, tuple, set)):
        raw_subjects = [raw_subjects]
    keywords: list[str] = []
    for item in raw_subjects:
        value = _clean_text(item)
        if value and value not in keywords:
            keywords.append(value)
    document_type = _infer_document_type(resource_type)
    summary_text = _bounded_artifact_summary(
        f"{title}. {abstract}"
        if abstract
        else f"{title} is a {document_type} published through HydroShare."
    )
    return {
        "idArtifact": artifact_id,
        "idArtifactType": HYDROSHARE_ARTIFACT_TYPE_ID,
        "Title": title,
        # Canonical URL prevents duplicate database versions caused only by
        # legacy http/https or trailing-slash differences in source metadata.
        "URL": f"https://www.hydroshare.org/resource/{resource_id}/",
        "idArtifactParent": None,
        "abstract": abstract,
        "keywords": keywords,
        "document_type": document_type,
        # A deterministic metadata-derived summary makes the existing DB
        # loader generate artifact embeddings without spending LLM tokens.
        "summary_data": {
            "summary_text": summary_text,
            "keywords": keywords,
            "entities": ["HydroShare"],
            "document_type": document_type,
            "generation_method": "deterministic_hydroshare_metadata",
        },
        "artifact_role": "hydroshare_resource",
        "resource_id": resource_id,
        "resource_type": resource_type,
        "identifier": _clean_text(meta.get("identifier")),
        "language": _clean_text(meta.get("language")),
        "doi": _clean_text(system.get("doi")),
        "date_created": _clean_text(system.get("date_created")),
        "date_last_updated": _clean_text(
            system.get("date_last_updated") or meta.get("date_last_updated")
        ),
        "published": bool(system.get("published", False)),
        "immutable": bool(system.get("immutable", False)),
        "public": bool(system.get("public", False)),
        "discoverable": bool(system.get("discoverable", False)),
        "shareable": bool(system.get("shareable", False)),
        "hs_research_portal_types": list(portal_types),
    }


def _xml_qname(tag: str) -> str:
    if not tag.startswith("{"):
        return tag
    uri, local = tag[1:].split("}", 1)
    for prefix, namespace in NS.items():
        if uri == namespace:
            return f"{prefix}:{local}"
    return local


def _xml_value(element: ET.Element | None) -> str | None:
    if element is None:
        return None
    resource = element.attrib.get(f"{{{NS['rdf']}}}resource")
    return _clean_text(resource or "".join(element.itertext()))


def parse_hydroshare_xml(xml_text: str) -> dict[str, Any]:
    output: dict[str, Any] = {
        "typed_relations": [],
        "geospatial_relations": [],
        "collection_members": [],
        "described_by": [],
        "tool_config": None,
    }
    if not xml_text:
        return output
    try:
        root = ET.fromstring(xml_text)
    except ET.ParseError:
        return output
    resource = next(
        (
            child
            for child in root
            if _xml_qname(child.tag)
            in {
                "hsterms:CompositeResource",
                "hsterms:CollectionResource",
                "hsterms:ToolResource",
            }
        ),
        None,
    )
    if resource is None:
        return output
    resource_type = _xml_qname(resource.tag).split(":")[-1]

    relation_labels = {
        "references": "references",
        "isReferencedBy": "isReferencedBy",
        "isExecutedBy": "isExecutedBy",
        "hasPart": "hasPart",
        "isDescribedBy": "isDescribedBy",
        "source": "source",
        "isPartOf": "isPartOf",
    }
    seen_relations: set[tuple[str, str]] = set()
    for container in resource.findall(f"{{{NS['dc']}}}relation"):
        description = next(iter(container), None)
        if description is None:
            continue
        for relation in description:
            target = _xml_value(relation)
            if not target:
                continue
            qname = _xml_qname(relation.tag)
            label = relation_labels.get(qname.split(":")[-1], qname.split(":")[-1])
            key = (label, target)
            if key in seen_relations:
                continue
            seen_relations.add(key)
            record = {
                "label": label,
                "target": target,
                "target_resource_id": _resource_id({"url": target}),
            }
            output["typed_relations"].append(record)
            if label == "hasPart":
                output["collection_members"].append(record)
            elif label == "isDescribedBy":
                output["described_by"].append(target)

    for container in resource.findall(f"{{{NS['hsterms']}}}geospatialRelation"):
        description = next(iter(container), None)
        if description is None:
            continue
        name = None
        target = None
        for child in description:
            if _xml_qname(child.tag) == "hsterms:relation_name":
                name = _clean_text("".join(child.itertext()))
            else:
                target = _xml_value(child) or target
        if target:
            output["geospatial_relations"].append({"name": name, "target": target})

    if resource_type == "ToolResource":
        def tool_value(tag_name: str) -> str | None:
            parent = resource.find(f"{{{NS['hsterms']}}}{tag_name}")
            value = parent.find(f".//{{{NS['hsterms']}}}value") if parent is not None else None
            return _xml_value(value)

        output["tool_config"] = {
            "app_home_page_url": tool_value("AppHomePageUrl"),
            "request_url_base": tool_value("RequestUrlBase"),
            "request_url_base_file": tool_value("RequestUrlBaseFile"),
            "tool_version": tool_value("ToolVersion"),
            "testing_protocol_url": tool_value("TestingProtocolUrl"),
        }
    return output


def _normalize_relation_label(label: Any) -> str:
    normalized = _clean_text(label) or "related"
    return {
        "The content of this resource references": "references",
        "This resource is referenced by": "isReferencedBy",
        "The content of this resource can be executed by": "isExecutedBy",
        "This resource includes": "hasPart",
        "This collection is described by": "isDescribedBy",
        "The content of this resource is derived from": "source",
        "This resource is part of": "isPartOf",
    }.get(normalized, normalized)


def _relation_display(label: str) -> str:
    return {
        "references": "This resource references",
        "isReferencedBy": "This resource is referenced by",
        "isExecutedBy": "This resource can be executed by",
        "hasPart": "This resource includes",
        "isDescribedBy": "This resource is described by",
        "source": "This resource is derived from",
        "isPartOf": "This resource is part of",
    }.get(label, label)


def _file_category(extension: str) -> str:
    extension = extension.lower()
    if extension in {".py", ".ipynb", ".r", ".m", ".jl", ".java", ".cpp", ".c", ".sh"}:
        return "code_and_notebooks"
    if extension in {".tif", ".tiff", ".vrt", ".shp", ".gpkg", ".geojson", ".nc"}:
        return "geospatial_data"
    if extension in {".csv", ".tsv", ".xlsx", ".xls", ".parquet"}:
        return "tabular_data"
    if extension in {".pdf", ".md", ".txt", ".docx", ".pptx", ".ppt"}:
        return "documents"
    if extension in {".png", ".jpg", ".jpeg", ".gif", ".svg"}:
        return "images_media"
    if extension in {".zip", ".tar", ".gz", ".bz2", ".7z"}:
        return "archives"
    return "other"


def _spec(
    chunk_type: str,
    text: str,
    section: str,
    source_files: Iterable[str],
    source_fields: Iterable[str],
    **extra: Any,
) -> dict[str, Any]:
    return {
        "chunk_type_name": chunk_type,
        "chunk_text": text,
        "section_hint": section,
        "source_files": list(source_files),
        "source_fields": list(source_fields),
        "extra_type_specific": extra,
    }


def _split_readme_text(
    text: str,
    max_chars: int = MAX_README_CHUNK_CHARS,
) -> list[str]:
    """Split text deterministically at paragraph/line/word boundaries."""

    remaining = text.strip()
    pieces: list[str] = []
    while len(remaining) > max_chars:
        window = remaining[: max_chars + 1]
        candidates = (
            window.rfind("\n\n", 0, max_chars + 1),
            window.rfind("\n", 0, max_chars + 1),
            window.rfind(" ", 0, max_chars + 1),
        )
        split_at = next(
            (position for position in candidates if position >= max_chars // 2),
            max_chars,
        )
        piece = remaining[:split_at].strip()
        if not piece:  # Defensive progress guarantee for whitespace-heavy text.
            split_at = max_chars
            piece = remaining[:split_at]
        pieces.append(piece)
        remaining = remaining[split_at:].lstrip()
    if remaining:
        pieces.append(remaining)
    return pieces


def _readme_specs(readmes: list[dict[str, str]]) -> list[dict[str, Any]]:
    """Parse and safely split README sections while retaining their hierarchy.

    Temporary IDs are allocated globally across all README files.  The first
    piece of a section is its hierarchy node; continuation pieces and child
    headings point to that first piece.
    """

    specs: list[dict[str, Any]] = []
    heading = re.compile(r"^(#{1,6})\s+(.*\S)\s*$")
    rule = re.compile(r"^\s*([-*_])\1{2,}\s*$")
    next_local_id = 1

    for readme in readmes:
        source = readme["file_name"]
        sections: list[dict[str, Any]] = []
        stack: list[int] = []
        preamble: list[str] = []
        current_index: int | None = None

        for line in readme["text"].splitlines():
            match = heading.match(line)
            if match:
                level = len(match.group(1))
                while stack and int(sections[stack[-1]]["level"]) >= level:
                    stack.pop()
                parent_index = stack[-1] if stack else None
                sections.append(
                    {
                        "title": match.group(2).strip(),
                        "level": level,
                        "marker": match.group(1),
                        "parent_index": parent_index,
                        "lines": [],
                        "has_children": False,
                    }
                )
                current_index = len(sections) - 1
                if parent_index is not None:
                    sections[parent_index]["has_children"] = True
                stack.append(current_index)
            elif not rule.match(line):
                if current_index is None:
                    preamble.append(line)
                else:
                    sections[current_index]["lines"].append(line)

        if "\n".join(preamble).strip():
            # Insert the introduction before all headings and adjust indexes.
            sections.insert(
                0,
                {
                    "title": "README Introduction",
                    "level": 0,
                    "marker": None,
                    "parent_index": None,
                    "lines": preamble,
                    "has_children": False,
                },
            )
            for section in sections[1:]:
                parent_index = section["parent_index"]
                section["parent_index"] = (
                    int(parent_index) + 1 if parent_index is not None else None
                )

        first_piece_by_section: dict[int, int] = {}
        for section_index, section in enumerate(sections):
            body = "\n".join(section["lines"]).strip()
            has_body = bool(body)
            if not body and section["has_children"]:
                body = section["title"]
            if not body:
                continue
            pieces = _split_readme_text(body)
            parent_index = section["parent_index"]
            parent_local_id = (
                first_piece_by_section.get(int(parent_index))
                if parent_index is not None
                else None
            )
            section_first_id = next_local_id
            first_piece_by_section[section_index] = section_first_id
            for part_index, piece in enumerate(pieces, start=1):
                local_id = next_local_id
                next_local_id += 1
                item = _spec(
                    "Readme File",
                    piece,
                    section["title"],
                    [source],
                    ["readme_text"],
                    heading_level=section["level"],
                    heading_marker=section["marker"],
                    source_file=source,
                    readme_chunk_kind=(
                        "readme_introduction"
                        if section["level"] == 0
                        else "markdown_section"
                    ),
                    has_children=bool(section["has_children"]),
                    has_body=has_body,
                    part_index=part_index,
                    part_count=len(pieces),
                )
                item["temp_local_id"] = local_id
                item["temp_parent_local_id"] = (
                    parent_local_id if part_index == 1 else section_first_id
                )
                specs.append(item)
    return specs


def build_hydroshare_chunk_specs(resource_id: str, snapshot: dict[str, Any]) -> list[dict[str, Any]]:
    """Create deterministic notebook-equivalent chunk specifications."""

    meta = snapshot.get("metadata") or {}
    system = snapshot.get("system_metadata") or {}
    files = snapshot.get("file_inventory") or []
    xml = parse_hydroshare_xml(snapshot.get("raw_metadata_xml") or "")
    specs: list[dict[str, Any]] = []

    abstract = _clean_text(meta.get("abstract"))
    if abstract:
        specs.append(_spec("Abstract", abstract, "HydroShare abstract", ["meta_dump.json"], ["abstract"]))

    spatial = meta.get("spatial_coverage")
    if isinstance(spatial, dict):
        parts: list[str] = []
        if _clean_text(spatial.get("type")):
            parts.append(f"This resource has {_clean_text(spatial.get('type'))}-based spatial coverage.")
        north = spatial.get("northlimit", spatial.get("north"))
        south = spatial.get("southlimit", spatial.get("south"))
        east = spatial.get("eastlimit", spatial.get("east"))
        west = spatial.get("westlimit", spatial.get("west"))
        if any(value is not None for value in (north, south, east, west)):
            parts.append(f"Its bounding coordinates are north {north}, south {south}, east {east}, and west {west}.")
        if _clean_text(spatial.get("units")):
            parts.append(f"The coordinate units are {_clean_text(spatial.get('units'))}.")
        if _clean_text(spatial.get("projection")):
            parts.append(f"The reference system is {_clean_text(spatial.get('projection'))}.")
        if parts:
            specs.append(_spec("Spatial Coverage", " ".join(parts), "Spatial coverage", ["meta_dump.json"], ["spatial_coverage"]))
    for relation in xml["geospatial_relations"]:
        target = relation["target"]
        name = relation.get("name")
        text = f"This resource has a geospatial relation to {name} via {target}." if name else f"This resource has a geospatial relation via {target}."
        specs.append(_spec("Spatial Coverage", text, "Geospatial relation", ["raw_metadata.xml"], ["geospatial_relations"]))

    period = meta.get("period_coverage")
    if isinstance(period, dict):
        start, end = _clean_text(period.get("start")), _clean_text(period.get("end"))
        if start or end:
            text = (f"The temporal coverage of this resource spans from {start} to {end}." if start and end else f"The temporal coverage of this resource starts on {start}." if start else f"The temporal coverage of this resource ends on {end}.")
            specs.append(_spec("Temporal Coverage", text, "Temporal coverage", ["meta_dump.json"], ["period_coverage"]))

    # HydroShare resource types expose variable metadata under different keys.
    # Keep this permissive so CompositeResource science metadata can be indexed
    # without coupling generation to one hsclient model version.
    variable_values = meta.get("variables") or meta.get("variable_metadata") or []
    if isinstance(variable_values, dict):
        variable_values = [variable_values]
    if isinstance(variable_values, list):
        for index, variable in enumerate(variable_values, start=1):
            if isinstance(variable, dict):
                ordered_fields = (
                    ("name", "Variable"),
                    ("variable_name", "Variable"),
                    ("unit", "Unit"),
                    ("units", "Units"),
                    ("type", "Type"),
                    ("data_type", "Data type"),
                    ("shape", "Shape"),
                    ("description", "Description"),
                    ("missing_value_code", "Missing value code"),
                )
                parts: list[str] = []
                used: set[str] = set()
                for field, label in ordered_fields:
                    value = _clean_text(variable.get(field))
                    if value and label not in used:
                        used.add(label)
                        parts.append(f"{label}: {value}.")
                name = (
                    _clean_text(variable.get("name"))
                    or _clean_text(variable.get("variable_name"))
                    or f"Variable {index}"
                )
                text = " ".join(parts)
            else:
                name = f"Variable {index}"
                text = _clean_text(variable) or ""
            if text:
                specs.append(
                    _spec(
                        "Variable Metadata",
                        text,
                        name,
                        ["meta_dump.json"],
                        ["variables"],
                        variable_index=index,
                    )
                )

    content_types = [_clean_text(value) for value in system.get("content_types") or []]
    content_types = [value for value in content_types if value]
    if content_types:
        specs.append(_spec("Data Services Info", "This resource declares the following content types: " + ", ".join(content_types[:12]) + ".", "Content types", ["sys_meta_dump.json"], ["content_types"]))
    if any(str(item.get("extension") or "").lower() in {".tif", ".tiff", ".vrt", ".shp", ".gpkg", ".geojson", ".nc"} for item in files):
        for service in ("wms", "wcs"):
            endpoint = f"https://geoserver.hydroshare.org/geoserver/HS-{resource_id}/{service}?request=GetCapabilities"
            specs.append(_spec("Data Services Info", f"This resource exposes a {service.upper()} service endpoint at {endpoint}.", f"{service.upper()} service", ["file_inventory.json"], ["file_inventory"]))
    if isinstance(xml.get("tool_config"), dict):
        for field, label in (("app_home_page_url", "App home page"), ("request_url_base", "Resource launch pattern"), ("request_url_base_file", "File launch pattern"), ("tool_version", "Tool version"), ("testing_protocol_url", "Testing protocol URL")):
            value = _clean_text(xml["tool_config"].get(field))
            if value:
                specs.append(_spec("Data Services Info", f"{label}: {value}.", label, ["raw_metadata.xml"], ["tool_config"]))

    for item in files:
        name, path = _clean_text(item.get("file_name")), _clean_text(item.get("file_path"))
        if not name and not path:
            continue
        extension = (_clean_text(item.get("extension")) or "").lower()
        checksum = _clean_text(item.get("checksum"))
        parts = [value for value in (f"File name: {name}." if name else None, f"Path: {path}." if path else None, f"Extension: {extension}." if extension else None, f"Checksum: {checksum}." if checksum else None) if value]
        specs.append(_spec("File Description", " ".join(parts), name or "Repository file", ["file_inventory.json"], ["file_inventory"], file_name=name, file_path=path, extension=extension or None, checksum=checksum, file_category=_file_category(extension)))

    for member in xml["collection_members"]:
        specs.append(_spec("Collection Contents", f"This collection includes the member resource: {member['target']}.", "Collection member", ["raw_metadata.xml"], ["collection_members"], target_resource_id=member.get("target_resource_id")))
    for description in xml["described_by"]:
        specs.append(_spec("Collection Contents", f"This collection is described by: {description}.", "Collection description", ["raw_metadata.xml"], ["described_by"]))

    subjects = [_clean_text(value) for value in meta.get("subjects") or []]
    subjects = [value for value in subjects if value]
    if subjects:
        specs.append(_spec("Subject Keywords", "Subject keywords associated with this resource include " + ", ".join(subjects[:20]) + ".", "Subject keywords", ["meta_dump.json"], ["subjects"]))

    citation = _clean_text(meta.get("citation"))
    if citation:
        specs.append(_spec("Citation", f"Recommended citation: {citation}.", "Citation", ["meta_dump.json"], ["citation"]))
    rights = meta.get("rights")
    if isinstance(rights, dict):
        rights_parts = []
        if _clean_text(rights.get("statement")):
            rights_parts.append(f"License statement: {_clean_text(rights.get('statement')).rstrip('.')}.")
        if _clean_text(rights.get("url")):
            rights_parts.append(f"License URL: {_clean_text(rights.get('url')).rstrip('.')}.")
        if rights_parts:
            specs.append(_spec("Citation", " ".join(rights_parts), "License", ["meta_dump.json"], ["rights"]))

    for field, chunk_type, label in (("creators", "Creator", "Creator"), ("contributors", "Contributor", "Contributor")):
        for person in meta.get(field) or []:
            if not isinstance(person, dict) or not _clean_text(person.get("name")):
                continue
            name = _clean_text(person.get("name"))
            parts = [f"{label}: {name}."]
            for key, display in (("organization", "Organization"), ("email", "Email"), ("homepage", "Homepage"), ("address", "Address"), ("phone", "Phone")):
                value = _clean_text(person.get(key))
                if value:
                    parts.append(f"{display}: {value}.")
            specs.append(_spec(chunk_type, " ".join(parts), name, ["meta_dump.json"], [field], person_name=name))

    for award in meta.get("awards") or []:
        if not isinstance(award, dict):
            continue
        fields = (("funding_agency_name", "Funding agency"), ("title", "Award title"), ("number", "Award number"), ("funding_agency_url", "Funding agency URL"))
        parts = [f"{label}: {_clean_text(award.get(key))}." for key, label in fields if _clean_text(award.get(key))]
        if parts:
            agency = _clean_text(award.get("funding_agency_name")) or "Funding agency"
            specs.append(_spec("Funding Agency", " ".join(parts), agency, ["meta_dump.json"], ["awards"], award_number=_clean_text(award.get("number"))))

    additional = meta.get("additional_metadata")
    if isinstance(additional, dict):
        for key in sorted(additional, key=lambda value: str(value).lower()):
            name, value = _clean_text(key), _clean_text(additional[key])
            if name and value:
                specs.append(_spec("Additional Metadata", f"{name}: {value.rstrip('.')}.", name, ["meta_dump.json"], ["additional_metadata"], metadata_key=name, metadata_value=value))

    merged_relations: dict[tuple[str, str], dict[str, Any]] = {}
    for relation in meta.get("relations") or []:
        if not isinstance(relation, dict) or not _clean_text(relation.get("value")):
            continue
        label = _normalize_relation_label(relation.get("type"))
        target = _clean_text(relation.get("value"))
        merged_relations[(label, target)] = {"label": label, "target": target, "sources": ["meta_dump.json"]}
    for relation in xml["typed_relations"]:
        key = (relation["label"], relation["target"])
        if key in merged_relations:
            merged_relations[key]["sources"].append("raw_metadata.xml")
        else:
            merged_relations[key] = {"label": relation["label"], "target": relation["target"], "sources": ["raw_metadata.xml"]}
    for relation in merged_relations.values():
        urls = [match.rstrip(".,;:)]}>\"'") for match in URL_RE.findall(relation["target"])]
        specs.append(_spec("Related Resources Context", f"{_relation_display(relation['label'])}: {relation['target']}.", _relation_display(relation["label"]), relation["sources"], ["relations"], target_resource_id=_resource_id({"url": relation["target"]}), embedded_urls=urls))

    specs.extend(_readme_specs(snapshot.get("readmes") or []))
    return specs


def build_hydroshare_chunks(
    artifact_id: int,
    next_chunk_id: int,
    resource_id: str,
    snapshot: dict[str, Any],
) -> tuple[list[dict[str, Any]], int]:
    specs = build_hydroshare_chunk_specs(resource_id, snapshot)
    local_to_real = {
        int(item["temp_local_id"]): next_chunk_id + index
        for index, item in enumerate(specs)
        if item.get("temp_local_id") is not None
    }
    chunks: list[dict[str, Any]] = []
    for index, item in enumerate(specs):
        chunk_id = next_chunk_id + index
        type_specific = {
            "source_files": item["source_files"],
            "source_fields": item["source_fields"],
            **(item.get("extra_type_specific") or {}),
        }
        chunks.append(
            {
                "idArtifact": artifact_id,
                "idChunk": chunk_id,
                "order": index + 1,
                "idChunkType": None,
                "chunk_type_name": item["chunk_type_name"],
                "chunk_text": item["chunk_text"],
                "idChunkParent": local_to_real.get(item.get("temp_parent_local_id")),
                "section_hint": item["section_hint"],
                "supporting_quote": [],
                "source_artifact_id": artifact_id,
                "type_specific": type_specific,
            }
        )
    return chunks, next_chunk_id + len(chunks)


def _persist_snapshot(
    config: HydroShareSyncConfig,
    resource_id: str,
    fingerprint: str,
    snapshot: dict[str, Any],
    portal_types: list[str],
) -> Path:
    directory = config.corpus_dir / resource_id / "snapshots" / fingerprint
    _write_json_atomic(directory / "meta_dump.json", snapshot["metadata"])
    _write_json_atomic(directory / "sys_meta_dump.json", snapshot["system_metadata"])
    _write_json_atomic(directory / "file_inventory.json", snapshot["file_inventory"])
    _write_json_atomic(directory / "portal_types.json", portal_types)
    _write_text_atomic(directory / "raw_metadata.xml", snapshot["raw_metadata_xml"])
    for readme in snapshot["readmes"]:
        safe_name = Path(readme["file_name"]).name
        _write_text_atomic(directory / safe_name, readme["text"])
    return directory


def _discovery_shrink_guard(
    previous_resource_ids: Iterable[str],
    discovered_resource_ids: Iterable[str],
    *,
    allow_large_removals: bool,
) -> dict[str, Any]:
    """Describe whether discovery is too small to replace the prior snapshot."""

    previous = set(previous_resource_ids)
    discovered = set(discovered_resource_ids)
    removed = sorted(previous - discovered)
    removal_fraction = len(removed) / len(previous) if previous else 0.0
    empty_result = not discovered
    severe_shrink = (
        bool(previous)
        and len(removed) >= LARGE_REMOVAL_MINIMUM_COUNT
        and removal_fraction >= LARGE_REMOVAL_FRACTION
    )
    return {
        "allow_large_removals": bool(allow_large_removals),
        "minimum_removed_resources": LARGE_REMOVAL_MINIMUM_COUNT,
        "maximum_removal_fraction": LARGE_REMOVAL_FRACTION,
        "previous_resource_count": len(previous),
        "discovered_resource_count": len(discovered),
        "candidate_removed_count": len(removed),
        "candidate_removed_resource_ids": removed,
        "candidate_removal_fraction": removal_fraction,
        "empty_discovery": empty_result,
        "severe_shrink": severe_shrink,
        # An empty artifact snapshot cannot be prepared/applied safely and is
        # never accepted. The explicit override applies only to a verified,
        # severe but still non-empty shrink.
        "triggered": empty_result or (
            severe_shrink and not allow_large_removals
        ),
    }


def _is_inaccessible_resource_error(exc: BaseException) -> bool:
    """Return whether an exception represents a remote 401/403 response.

    ``hsclient`` currently wraps HTTP failures in ``RuntimeError`` in some
    code paths, while its underlying HTTP client may expose a response status
    directly in others.  Inspect both forms, including chained exceptions,
    but deliberately do not classify local ``PermissionError`` failures as a
    skippable remote-resource problem.
    """

    pending: list[BaseException] = [exc]
    seen: set[int] = set()
    while pending:
        current = pending.pop()
        if id(current) in seen:
            continue
        seen.add(id(current))

        if not isinstance(current, PermissionError):
            response = getattr(current, "response", None)
            status_code = getattr(response, "status_code", None)
            if status_code is None:
                status_code = getattr(current, "status_code", None)
            try:
                if int(status_code) in {401, 403}:
                    return True
            except (TypeError, ValueError):
                pass

            message = str(current).lower()
            if (
                re.search(r"\b(?:http(?:\s+status)?\s*)?(?:401|403)\b", message)
                or "unauthorized" in message
                or "unauthorised" in message
                or "forbidden" in message
                or "access denied" in message
                or "not authorized" in message
                or "not authorised" in message
            ):
                return True

        cause = getattr(current, "__cause__", None)
        context = getattr(current, "__context__", None)
        if isinstance(cause, BaseException):
            pending.append(cause)
        if isinstance(context, BaseException):
            pending.append(context)
    return False


def synchronize_hydroshare_resources(
    root: Path | str,
    username: str | None = None,
    password: str | None = None,
    client: Any | None = None,
    session: Any | None = None,
    *,
    force: bool = False,
    allow_large_removals: bool = False,
    config: HydroShareSyncConfig | None = None,
) -> dict[str, Any]:
    """Generate a complete HydroShare snapshot without updating a database.

    ``client`` and ``session`` are dependency-injection hooks.  When omitted,
    an anonymous ``hsclient.HydroShare`` client and a requests session are used.
    Discovery always refuses an empty result. It also refuses removal of at
    least five resources and at least 25% of the previous state. Set
    ``allow_large_removals=True`` only after confirming that a severe,
    non-empty shrink is intentional; it cannot override empty discovery.
    """

    started_at = datetime.now(timezone.utc).isoformat()
    config = (config or HydroShareSyncConfig(root=Path(root))).resolved()
    hydroshare = client or create_hydroshare_client(username, password)
    http = _http_session(session)
    previous_state = _load_json(config.state_path, {})
    previous_resources = previous_state.get("resources") or {}
    if not isinstance(previous_resources, dict):
        previous_resources = {}
    previous_artifacts_payload = _load_json(config.artifact_output, [])
    previous_artifacts = {
        str(item.get("resource_id")): item
        for item in previous_artifacts_payload
        if isinstance(item, dict) and item.get("resource_id")
    } if isinstance(previous_artifacts_payload, list) else {}
    previous_chunks_payload = _load_json(config.chunk_output, [])
    if not isinstance(previous_chunks_payload, list):
        previous_chunks_payload = []
    previous_chunks: dict[int, list[dict[str, Any]]] = {}
    for chunk in previous_chunks_payload:
        if not isinstance(chunk, dict):
            continue
        try:
            previous_chunks.setdefault(int(chunk["idArtifact"]), []).append(chunk)
        except (KeyError, TypeError, ValueError):
            continue

    known_artifact_ids = [int(item.get("idArtifact") or 0) for item in previous_artifacts.values()]
    known_artifact_ids.extend(int(item.get("artifact_id") or 0) for item in previous_resources.values() if isinstance(item, dict))
    next_artifact_id = max(known_artifact_ids + [int(previous_state.get("next_artifact_id") or 1) - 1, 0]) + 1
    known_chunk_ids = [int(item.get("idChunk") or 0) for item in previous_chunks_payload if isinstance(item, dict)]
    next_chunk_id = max(known_chunk_ids + [int(previous_state.get("next_chunk_id") or 1) - 1, 0]) + 1

    discovered = discover_hydroshare_resources(
        hydroshare, session=http, community_id=config.community_id
    )
    discovery_guard = _discovery_shrink_guard(
        previous_resources,
        discovered,
        allow_large_removals=allow_large_removals,
    )
    if discovery_guard["triggered"]:
        completed_at = datetime.now(timezone.utc).isoformat()
        reason = (
            "HydroShare discovery returned no resources"
            if discovery_guard["empty_discovery"]
            else (
                "HydroShare discovery would remove "
                f"{discovery_guard['candidate_removed_count']} of "
                f"{discovery_guard['previous_resource_count']} prior resources "
                f"({discovery_guard['candidate_removal_fraction']:.1%})"
            )
        )
        _write_json_atomic(
            config.report_output,
            {
                "schema_version": 1,
                "stage": "hydroshare_artifacts_and_chunks",
                "status": "failed",
                "started_at": started_at,
                "completed_at": completed_at,
                "community_id": config.community_id,
                "total_resources_discovered": len(discovered),
                "total_artifacts": len(previous_artifacts),
                "total_chunks": len(previous_chunks_payload),
                "removed_count": discovery_guard["candidate_removed_count"],
                "removed_resource_ids": discovery_guard[
                    "candidate_removed_resource_ids"
                ],
                "discovery_shrink_guard": discovery_guard,
                "database_update_performed": False,
                "inaccessible_count": 0,
                "inaccessible_resource_ids": [],
                "inaccessible_errors": [],
                "inaccessible_preserved_count": 0,
                "inaccessible_preserved_resource_ids": [],
                "inaccessible_skipped_count": 0,
                "inaccessible_skipped_resource_ids": [],
                "errors": [
                    {
                        "resource_id": None,
                        "error": f"{reason}; existing outputs were preserved",
                    }
                ],
            },
        )
        guidance = (
            "Empty discovery cannot be overridden; verify HydroShare discovery."
            if discovery_guard["empty_discovery"]
            else (
                "Verify discovery, then pass allow_large_removals=True only "
                "if the removals are intentional."
            )
        )
        raise RuntimeError(
            f"{reason}; refusing to replace the previous snapshot. {guidance}"
        )
    artifacts: list[dict[str, Any]] = []
    chunks: list[dict[str, Any]] = []
    resources_state: dict[str, dict[str, Any]] = {}
    new_ids: list[str] = []
    updated_ids: list[str] = []
    unchanged_ids: list[str] = []
    rebuilt_ids: list[str] = []
    reused_ids: list[str] = []
    inaccessible_errors: list[dict[str, Any]] = []
    inaccessible_preserved_ids: list[str] = []
    inaccessible_skipped_ids: list[str] = []
    errors: list[dict[str, str]] = []

    for resource_id, discovery in discovered.items():
        old_state_value = previous_resources.get(resource_id)
        old_state = old_state_value if isinstance(old_state_value, dict) else {}
        old_artifact = previous_artifacts.get(resource_id)
        try:
            old_artifact_id = (
                (old_artifact or {}).get("idArtifact") or old_state.get("artifact_id")
            )
            old_resource_chunks = previous_chunks.get(int(old_artifact_id), []) if old_artifact_id else []
        except Exception as exc:
            errors.append({"resource_id": resource_id, "error": str(exc)})
            continue

        try:
            snapshot = extract_resource_snapshot(hydroshare, resource_id)
        except Exception as exc:
            if not _is_inaccessible_resource_error(exc):
                errors.append({"resource_id": resource_id, "error": str(exc)})
                continue

            preserved = (
                old_artifact is not None
                and resource_id in previous_resources
                and isinstance(old_state_value, dict)
            )
            action = "skipped_new_resource"
            if preserved:
                artifacts.append(old_artifact)
                chunks.extend(
                    sorted(
                        old_resource_chunks,
                        key=lambda item: int(item.get("order") or 0),
                    )
                )
                resources_state[resource_id] = dict(old_state_value)
                reused_ids.append(resource_id)
                inaccessible_preserved_ids.append(resource_id)
                action = "preserved_previous_snapshot"
            else:
                inaccessible_skipped_ids.append(resource_id)
            inaccessible_errors.append(
                {
                    "resource_id": resource_id,
                    "error": str(exc) or type(exc).__name__,
                    "error_type": type(exc).__name__,
                    "action": action,
                }
            )
            continue

        try:
            portal_types = list(discovery["portal_types"])
            fingerprint = _snapshot_fingerprint(snapshot, portal_types)
            reusable = (
                not force
                and old_artifact is not None
                and old_state.get("fingerprint") == fingerprint
                and old_state.get("artifact_schema_version")
                == ARTIFACT_SCHEMA_VERSION
                and old_state.get("chunk_schema_version") == CHUNK_SCHEMA_VERSION
                and int(old_state.get("chunk_count") or 0) == len(old_resource_chunks)
            )
            if reusable:
                artifact = old_artifact
                resource_chunks = sorted(old_resource_chunks, key=lambda item: int(item.get("order") or 0))
                unchanged_ids.append(resource_id)
                reused_ids.append(resource_id)
                snapshot_directory = old_state.get("snapshot_directory")
            else:
                artifact_id = int(old_artifact_id) if old_artifact_id else next_artifact_id
                if not old_artifact_id:
                    next_artifact_id += 1
                artifact = build_hydroshare_artifact(
                    resource_id, artifact_id, snapshot, portal_types
                )
                resource_chunks, next_chunk_id = build_hydroshare_chunks(
                    artifact_id, next_chunk_id, resource_id, snapshot
                )
                snapshot_directory = str(
                    _persist_snapshot(config, resource_id, fingerprint, snapshot, portal_types)
                )
                rebuilt_ids.append(resource_id)
                (updated_ids if old_state or old_artifact else new_ids).append(resource_id)
            artifacts.append(artifact)
            chunks.extend(resource_chunks)
            resources_state[resource_id] = {
                "artifact_id": int(artifact["idArtifact"]),
                "fingerprint": fingerprint,
                "date_last_updated": artifact.get("date_last_updated"),
                "file_checksums": [
                    item.get("checksum")
                    for item in snapshot["file_inventory"]
                    if item.get("checksum")
                ],
                "hs_research_portal_types": portal_types,
                "artifact_schema_version": ARTIFACT_SCHEMA_VERSION,
                "chunk_schema_version": CHUNK_SCHEMA_VERSION,
                "chunk_count": len(resource_chunks),
                "snapshot_directory": snapshot_directory,
            }
        except Exception as exc:
            errors.append({"resource_id": resource_id, "error": str(exc)})

    removed_ids = sorted(set(previous_resources) - set(discovered))
    artifacts.sort(key=lambda item: str(item.get("resource_id") or ""))
    chunks.sort(key=lambda item: (int(item.get("idArtifact") or 0), int(item.get("order") or 0)))
    report = {
        "schema_version": 1,
        "stage": "hydroshare_artifacts_and_chunks",
        "status": "failed" if errors else "completed",
        "started_at": started_at,
        "completed_at": datetime.now(timezone.utc).isoformat(),
        "community_id": config.community_id,
        "anonymous_access": not bool(username or os.getenv("HYDROSHARE_USERNAME")),
        "total_resources_discovered": len(discovered),
        "total_artifacts": len(artifacts),
        "total_chunks": len(chunks),
        "new_count": len(new_ids),
        "updated_count": len(updated_ids),
        "unchanged_count": len(unchanged_ids),
        "removed_count": len(removed_ids),
        "rebuilt_count": len(rebuilt_ids),
        "reused_count": len(reused_ids),
        "new_resource_ids": new_ids,
        "updated_resource_ids": updated_ids,
        "unchanged_resource_ids": unchanged_ids,
        "removed_resource_ids": removed_ids,
        "inaccessible_count": len(inaccessible_errors),
        "inaccessible_resource_ids": [
            item["resource_id"] for item in inaccessible_errors
        ],
        "inaccessible_errors": inaccessible_errors,
        "inaccessible_preserved_count": len(inaccessible_preserved_ids),
        "inaccessible_preserved_resource_ids": inaccessible_preserved_ids,
        "inaccessible_skipped_count": len(inaccessible_skipped_ids),
        "inaccessible_skipped_resource_ids": inaccessible_skipped_ids,
        "errors": errors,
        "portal_category_counts": {
            category: sum(
                category in entry["portal_types"] for entry in discovered.values()
            )
            for category in PORTAL_CATEGORY_ORDER
        },
        "portal_membership_count": sum(
            len(entry["portal_types"]) for entry in discovered.values()
        ),
        "discovery_shrink_guard": discovery_guard,
        "artifact_output": str(config.artifact_output),
        "chunk_output": str(config.chunk_output),
        "state_path": str(config.state_path),
        "corpus_directory": str(config.corpus_dir),
        "database_update_performed": False,
        "chunk_type_resolution": {
            "idChunkType": None,
            "field": "chunk_type_name",
            "required_names": list(HYDROSHARE_CHUNK_TYPES),
            "database_resolution_performed": False,
        },
    }
    _write_json_atomic(config.report_output, report)
    if errors:
        raise RuntimeError(
            "HydroShare generation failed; artifact, chunk, and state outputs were "
            f"left unchanged. See {config.report_output}"
        )

    state = {
        "schema_version": STATE_SCHEMA_VERSION,
        "artifact_schema_version": ARTIFACT_SCHEMA_VERSION,
        "community_id": config.community_id,
        "next_artifact_id": next_artifact_id,
        "next_chunk_id": next_chunk_id,
        "artifact_output": str(config.artifact_output),
        "chunk_output": str(config.chunk_output),
        "resources": resources_state,
    }
    _write_json_atomic(config.artifact_output, artifacts)
    _write_json_atomic(config.chunk_output, chunks)
    _write_json_atomic(config.state_path, state)
    return report


__all__ = [
    "CIROH_COMMUNITY_ID",
    "HYDROSHARE_ARTIFACT_TYPE_ID",
    "HYDROSHARE_CHUNK_TYPES",
    "MAX_ARTIFACT_SUMMARY_CHARS",
    "MAX_README_CHUNK_CHARS",
    "HydroShareSyncConfig",
    "PORTAL_CATEGORY_SUBJECTS",
    "build_hydroshare_artifact",
    "build_hydroshare_chunks",
    "build_hydroshare_chunk_specs",
    "create_hydroshare_client",
    "discover_ciroh_community_resource_ids",
    "discover_hydroshare_resources",
    "extract_resource_snapshot",
    "synchronize_hydroshare_resources",
]
