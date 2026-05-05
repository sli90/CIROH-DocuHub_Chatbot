"""
Generate chunks.json from CIROH DocuHub MDX frontmatter.

Walks docs/ to find all index.mdx and intro.mdx files, parses their YAML
frontmatter, and produces a structured JSON file with IDs, titles, URLs,
parent-child relationships, descriptions, and tags.
"""

import json
import os
import re

try:
    import yaml
    HAS_YAML = True
except ImportError:
    HAS_YAML = False

DOCS_DIR = os.path.join(os.path.dirname(__file__), "..", "docs")
OUTPUT_PATH = os.path.join(os.path.dirname(__file__), "chunks.json")
BASE_URL = "https://docs.ciroh.org/docs/"


def discover_files(docs_dir):
    """Walk docs/ and collect all .mdx file paths."""
    results = []
    for dirpath, _dirnames, filenames in os.walk(docs_dir):
        for fname in filenames:
            if fname.endswith(".mdx"):
                results.append(os.path.join(dirpath, fname))
    return results


def virtual_path(filepath, docs_dir):
    """Compute the virtual path relative to docs/.

    - index.mdx / intro.mdx → containing folder (e.g. products/ngiab)
    - other .mdx files → folder + filename stem (e.g. contribute/repository)
    """
    fname = os.path.basename(filepath)
    rel_dir = os.path.relpath(os.path.dirname(filepath), docs_dir).replace(os.sep, "/")
    if rel_dir == ".":
        rel_dir = ""

    if fname in ("index.mdx", "intro.mdx"):
        return rel_dir
    else:
        stem = os.path.splitext(fname)[0]
        return (rel_dir + "/" + stem) if rel_dir else stem


def extract_frontmatter_text(content):
    """Extract the raw YAML text between --- markers."""
    match = re.match(r"^---\s*\n(.*?)\n---", content, re.DOTALL)
    if match:
        return match.group(1)
    return None


def parse_tags_fallback(raw_text):
    """Parse tags from frontmatter text using regex (fallback when PyYAML unavailable)."""
    # Inline array: tags: [A, B, C] or tags: ["A", "B"]
    inline = re.search(r'^tags\s*:\s*\[([^\]]*)\]', raw_text, re.MULTILINE)
    if inline:
        items = inline.group(1).split(",")
        return [item.strip().strip('"').strip("'") for item in items if item.strip()]

    # Block-style tags:
    #   - A
    #   - B
    block = re.search(r'^tags\s*:\s*\n((?:\s+-\s+.+\n?)+)', raw_text, re.MULTILINE)
    if block:
        return [m.strip() for m in re.findall(r'^\s+-\s+(.+)', block.group(1), re.MULTILINE)]

    return []


def parse_frontmatter_fallback(raw_text):
    """Parse frontmatter using regex when PyYAML is unavailable."""
    title_match = re.search(r'^title\s*:\s*"?([^"\n]+)"?\s*$', raw_text, re.MULTILINE)
    title = title_match.group(1).strip() if title_match else ""

    desc_match = re.search(r'^description\s*:\s*"?([^"\n]+)"?\s*$', raw_text, re.MULTILINE)
    description = desc_match.group(1).strip() if desc_match else ""

    tags = parse_tags_fallback(raw_text)

    date_match = re.search(r'^Last updated date\s*:\s*"?([^"\n]+)"?\s*$', raw_text, re.MULTILINE)
    last_updated = date_match.group(1).strip() if date_match else ""

    return {"title": title, "description": description, "tags": tags, "last_updated_date": last_updated}


def parse_frontmatter(content):
    """Parse frontmatter from file content, returning title, description, tags."""
    raw_text = extract_frontmatter_text(content)
    if raw_text is None:
        return {"title": "", "description": "", "tags": [], "last_updated_date": ""}

    if HAS_YAML:
        data = yaml.safe_load(raw_text)
        if not isinstance(data, dict):
            data = {}
        title = data.get("title", "")
        description = data.get("description", "")
        tags = data.get("tags", [])
        if not isinstance(tags, list):
            tags = [tags] if tags else []
        # Ensure all tags are strings
        tags = [str(t) for t in tags]
        last_updated = data.get("Last updated date", "")
        return {"title": str(title), "description": str(description) if description else "", "tags": tags, "last_updated_date": str(last_updated) if last_updated else ""}

    return parse_frontmatter_fallback(raw_text)


def build_chunks(docs_dir):
    """Build the full list of chunk records from docs/."""
    docs_dir = os.path.abspath(docs_dir)
    files = discover_files(docs_dir)

    # Build (vpath, filepath) pairs and sort by vpath
    entries = []
    for fpath in files:
        vpath = virtual_path(fpath, docs_dir)
        if vpath:  # skip empty (root-level docs/ itself, if any)
            entries.append((vpath, fpath))
    entries.sort(key=lambda x: x[0])

    # Build vpath -> id lookup
    vpath_to_id = {}
    for idx, (vpath, _) in enumerate(entries, start=1):
        vpath_to_id[vpath] = idx

    # Build records
    records = []
    for idx, (vpath, fpath) in enumerate(entries, start=1):
        with open(fpath, "r", encoding="utf-8") as f:
            content = f.read()

        fm = parse_frontmatter(content)

        # Determine parent vpath
        parent_vpath = "/".join(vpath.split("/")[:-1]) if "/" in vpath else None
        parent_id = vpath_to_id.get(parent_vpath) if parent_vpath else None

        records.append({
            "idArtifact": idx,
            "idArtifactType": 1,
            "Title": fm["title"],
            "URL": BASE_URL + vpath + "/",
            "idArtifactParent": parent_id,
            "description": fm["description"],
            "tags": fm["tags"],
            "Last updated date": fm["last_updated_date"],
        })

    return records


def main():
    records = build_chunks(DOCS_DIR)
    os.makedirs(os.path.dirname(OUTPUT_PATH), exist_ok=True)
    with open(OUTPUT_PATH, "w", encoding="utf-8") as f:
        json.dump(records, f, indent=2, ensure_ascii=False)
    print(f"Wrote {len(records)} records to {OUTPUT_PATH}")


if __name__ == "__main__":
    main()
