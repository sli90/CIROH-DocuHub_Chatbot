"""
Generate artifacts.json from CIROH DocuHub MDX frontmatter.

Walks docs/, blog/, and release-notes/ to find all .mdx files, parses their
YAML frontmatter, and produces a structured JSON file with IDs, titles, URLs,
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

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
DOCS_DIR = os.path.join(SCRIPT_DIR, "..", "docs")
BLOG_DIR = os.path.join(SCRIPT_DIR, "..", "blog")
RELEASE_NOTES_DIR = os.path.join(SCRIPT_DIR, "..", "release-notes")
OUTPUT_PATH = os.path.join(SCRIPT_DIR, "artifacts.json")

BASE_URLS = {
    "docs": "https://docs.ciroh.org/docs/",
    "blog": "https://docs.ciroh.org/blog/",
    "release-notes": "https://docs.ciroh.org/release-notes/",
}


def discover_files(source_dir):
    """Walk a directory and collect all .mdx file paths."""
    results = []
    for dirpath, _dirnames, filenames in os.walk(source_dir):
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

    slug_match = re.search(r'^slug\s*:\s*"?([^"\n]+)"?\s*$', raw_text, re.MULTILINE)
    slug = slug_match.group(1).strip() if slug_match else ""

    return {"title": title, "description": description, "tags": tags, "last_updated_date": last_updated, "slug": slug}


def parse_frontmatter(content):
    """Parse frontmatter from file content, returning title, description, tags, slug."""
    raw_text = extract_frontmatter_text(content)
    if raw_text is None:
        return {"title": "", "description": "", "tags": [], "last_updated_date": "", "slug": ""}

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
        slug = data.get("slug", "")
        return {
            "title": str(title),
            "description": str(description) if description else "",
            "tags": tags,
            "last_updated_date": str(last_updated) if last_updated else "",
            "slug": str(slug) if slug else "",
        }

    return parse_frontmatter_fallback(raw_text)


def build_docs_entries(docs_dir):
    """Build (vpath, filepath) entries for docs/ with hierarchical parent logic."""
    docs_dir = os.path.abspath(docs_dir)
    files = discover_files(docs_dir)

    entries = []
    for fpath in files:
        vpath = virtual_path(fpath, docs_dir)
        if vpath:
            entries.append((vpath, fpath))
    entries.sort(key=lambda x: x[0])
    return entries


def build_flat_entries(source_dir):
    """Build (slug, filepath) entries for blog/ or release-notes/ (flat, no hierarchy)."""
    source_dir = os.path.abspath(source_dir)
    if not os.path.isdir(source_dir):
        return []

    files = discover_files(source_dir)
    entries = []
    for fpath in files:
        with open(fpath, "r", encoding="utf-8") as f:
            content = f.read()
        fm = parse_frontmatter(content)
        slug = fm["slug"]
        if not slug:
            # Fall back to filename stem
            slug = os.path.splitext(os.path.basename(fpath))[0]
        entries.append((slug, fpath))
    entries.sort(key=lambda x: x[0])
    return entries


def build_all_records():
    """Build the full list of artifact records from docs/, blog/, and release-notes/."""
    records = []
    next_id = 1

    # --- docs/ (hierarchical) ---
    docs_entries = build_docs_entries(DOCS_DIR)

    # Build vpath -> id lookup (need to know IDs before building records for parent refs)
    vpath_to_id = {}
    for i, (vpath, _) in enumerate(docs_entries):
        vpath_to_id[vpath] = next_id + i

    for vpath, fpath in docs_entries:
        with open(fpath, "r", encoding="utf-8") as f:
            content = f.read()
        fm = parse_frontmatter(content)

        parent_vpath = "/".join(vpath.split("/")[:-1]) if "/" in vpath else None
        parent_id = vpath_to_id.get(parent_vpath) if parent_vpath else None

        records.append({
            "idArtifact": next_id,
            "idArtifactType": 1,
            "Title": fm["title"],
            "URL": BASE_URLS["docs"] + vpath + "/",
            "idArtifactParent": parent_id,
            "description": fm["description"],
            "tags": fm["tags"],
            "Last updated date": fm["last_updated_date"],
        })
        next_id += 1

    # --- blog/ (flat) ---
    blog_entries = build_flat_entries(BLOG_DIR)
    for slug, fpath in blog_entries:
        with open(fpath, "r", encoding="utf-8") as f:
            content = f.read()
        fm = parse_frontmatter(content)

        records.append({
            "idArtifact": next_id,
            "idArtifactType": 1,
            "Title": fm["title"],
            "URL": BASE_URLS["blog"] + slug + "/",
            "idArtifactParent": None,
            "description": fm["description"],
            "tags": fm["tags"],
            "Last updated date": fm["last_updated_date"],
        })
        next_id += 1

    # --- release-notes/ (flat) ---
    rn_entries = build_flat_entries(RELEASE_NOTES_DIR)
    for slug, fpath in rn_entries:
        with open(fpath, "r", encoding="utf-8") as f:
            content = f.read()
        fm = parse_frontmatter(content)

        records.append({
            "idArtifact": next_id,
            "idArtifactType": 1,
            "Title": fm["title"],
            "URL": BASE_URLS["release-notes"] + slug + "/",
            "idArtifactParent": None,
            "description": fm["description"],
            "tags": fm["tags"],
            "Last updated date": fm["last_updated_date"],
        })
        next_id += 1

    return records


def main():
    records = build_all_records()
    os.makedirs(os.path.dirname(OUTPUT_PATH), exist_ok=True)
    with open(OUTPUT_PATH, "w", encoding="utf-8") as f:
        json.dump(records, f, indent=2, ensure_ascii=False)
    print(f"Wrote {len(records)} records to {OUTPUT_PATH}")


if __name__ == "__main__":
    main()
