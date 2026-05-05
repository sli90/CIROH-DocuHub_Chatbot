"""
Generate content_chunks.json by using GPT-5.2 to identify sections, subsections,
and subsubsections in each .mdx file, then saving their content as chunks.

Reads artifacts.json for idArtifact mapping. Uses OpenAI API to intelligently
parse markdown headings (distinguishing real headings from # inside code blocks).
"""

import json
import os
import re
import time

from openai import OpenAI
from dotenv import load_dotenv

try:
    import yaml
    HAS_YAML = True
except ImportError:
    HAS_YAML = False

# --- Paths ---
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
DOCS_DIR = os.path.join(SCRIPT_DIR, "..", "docs")
BLOG_DIR = os.path.join(SCRIPT_DIR, "..", "blog")
RELEASE_NOTES_DIR = os.path.join(SCRIPT_DIR, "..", "release-notes")
ARTIFACTS_PATH = os.path.join(SCRIPT_DIR, "artifacts.json")
OUTPUT_PATH = os.path.join(SCRIPT_DIR, "content_chunks.json")
ENV_PATH = os.path.join(SCRIPT_DIR, "..", "..", "rag", ".env")

# --- Load environment ---
load_dotenv(ENV_PATH)
client = OpenAI(api_key=os.environ["OPENAI_API_KEY"])
MODEL = "gpt-5.2"

# --- Prompt ---
SYSTEM_MSG = """\
You are a precise document parser. You will receive the content of a Docusaurus MDX \
documentation page (with frontmatter already stripped). Your job is to split it into \
hierarchical chunks based on section headings.

Rules for identifying headings:
1. A heading is a line that starts with #, ##, or ### at the BEGINNING of a line, \
followed by a space and then the heading text.
2. IGNORE any # characters that appear inside code blocks (``` ... ```), inline code \
(`...`), JSX/HTML components, or comments.
3. IGNORE any # characters that appear in bash/shell code examples (e.g. "# this is a comment").
4. Map heading levels as follows:
   - # (h1) → idChunkType: 1 (section)
   - ## (h2) → idChunkType: 2 (subsection)
   - ### (h3) → idChunkType: 3 (subsubsection)
5. Headings deeper than ### (e.g. ####) should be treated as part of the content of \
their parent chunk, NOT as separate chunks.
6. Each chunk's content starts after its heading line and continues until the next \
heading of the same or higher level (or end of document).
7. Include ALL text content in chunks — code blocks, lists, paragraphs, etc. \
But strip import statements (lines starting with "import ") and JSX component tags \
(like <ComponentName ... />) that don't contain meaningful text content.
8. If there is content before the first heading, create a chunk with title "Introduction" \
and idChunkType 1.
9. Keep the content as-is (preserve markdown formatting) but trim leading/trailing whitespace.

Return a JSON object with a single key "chunks" containing an array. Each element:
{
  "title": "The heading text (without # prefix)",
  "idChunkType": 1 | 2 | 3,
  "chunk_text": "The full text content under this heading"
}

Order chunks by their appearance in the document. Do NOT nest them — return a flat list.
If the document has no meaningful content (only imports/components), return {"chunks": []}.\
"""


def discover_files(source_dir):
    """Walk a directory and collect all .mdx file paths."""
    results = []
    for dirpath, _dirnames, filenames in os.walk(source_dir):
        for fname in filenames:
            if fname.endswith(".mdx"):
                results.append(os.path.join(dirpath, fname))
    return results


def virtual_path(filepath, docs_dir):
    """Compute the virtual path relative to docs/."""
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


def get_slug_from_content(content):
    """Extract the slug field from frontmatter."""
    raw_text = extract_frontmatter_text(content)
    if raw_text is None:
        return ""

    if HAS_YAML:
        data = yaml.safe_load(raw_text)
        if isinstance(data, dict):
            return str(data.get("slug", ""))
        return ""

    slug_match = re.search(r'^slug\s*:\s*"?([^"\n]+)"?\s*$', raw_text, re.MULTILINE)
    return slug_match.group(1).strip() if slug_match else ""


def strip_frontmatter(content):
    """Remove YAML frontmatter from MDX content."""
    match = re.match(r"^---\s*\n.*?\n---\s*\n?", content, re.DOTALL)
    if match:
        return content[match.end():]
    return content


def extract_chunks_with_llm(mdx_content, artifact_title):
    """Use GPT-5.2 to extract section/subsection/subsubsection chunks."""
    body = strip_frontmatter(mdx_content)

    # Skip files with very little content
    stripped = body.strip()
    if not stripped or len(stripped) < 20:
        return []

    user_content = (
        f"Document title: {artifact_title}\n\n"
        "MDX_CONTENT_START\n"
        f"{body}\n"
        "MDX_CONTENT_END"
    )

    try:
        resp = client.responses.create(
            model=MODEL,
            input=[
                {"role": "system", "content": SYSTEM_MSG},
                {"role": "user", "content": user_content},
            ],
            text={"format": {"type": "json_object"}},
            reasoning={"effort": "low"},
            max_output_tokens=16000,
        )

        # Extract text from response
        raw = resp.output_text
        data = json.loads(raw)
        return data.get("chunks", [])

    except Exception as e:
        print(f"  ERROR: {e}")
        return []


def build_url_to_file_map():
    """Build a mapping from artifact URL to file path for all three sources."""
    url_to_file = {}

    # --- docs/ (hierarchical) ---
    docs_dir = os.path.abspath(DOCS_DIR)
    base_url_docs = "https://docs.ciroh.org/docs/"
    for fpath in discover_files(docs_dir):
        vpath = virtual_path(fpath, docs_dir)
        if vpath:
            url = base_url_docs + vpath + "/"
            url_to_file[url] = fpath

    # --- blog/ (flat, slug-based) ---
    blog_dir = os.path.abspath(BLOG_DIR)
    base_url_blog = "https://docs.ciroh.org/blog/"
    if os.path.isdir(blog_dir):
        for fpath in discover_files(blog_dir):
            with open(fpath, "r", encoding="utf-8") as f:
                content = f.read()
            slug = get_slug_from_content(content)
            if not slug:
                slug = os.path.splitext(os.path.basename(fpath))[0]
            url = base_url_blog + slug + "/"
            url_to_file[url] = fpath

    # --- release-notes/ (flat, slug-based) ---
    rn_dir = os.path.abspath(RELEASE_NOTES_DIR)
    base_url_rn = "https://docs.ciroh.org/release-notes/"
    if os.path.isdir(rn_dir):
        for fpath in discover_files(rn_dir):
            with open(fpath, "r", encoding="utf-8") as f:
                content = f.read()
            slug = get_slug_from_content(content)
            if not slug:
                slug = os.path.splitext(os.path.basename(fpath))[0]
            url = base_url_rn + slug + "/"
            url_to_file[url] = fpath

    return url_to_file


def compute_chunk_parents(chunks_for_artifact):
    """Compute idChunkParent for a list of chunks belonging to one artifact.

    - idChunkType 1 (section)       → idChunkParent = None
    - idChunkType 2 (subsection)    → idChunkParent = most recent type 1 chunk
    - idChunkType 3 (subsubsection) → idChunkParent = most recent type 2 chunk
    """
    last_section_id = None       # most recent type 1
    last_subsection_id = None    # most recent type 2

    for chunk in chunks_for_artifact:
        chunk_type = chunk["idChunkType"]
        chunk_id = chunk["idChunk"]

        if chunk_type == 1:
            chunk["idChunkParent"] = None
            last_section_id = chunk_id
            last_subsection_id = None  # reset subsection when new section starts
        elif chunk_type == 2:
            chunk["idChunkParent"] = last_section_id
            last_subsection_id = chunk_id
        elif chunk_type == 3:
            chunk["idChunkParent"] = last_subsection_id
        else:
            chunk["idChunkParent"] = None


def main():
    # Load artifacts
    with open(ARTIFACTS_PATH, "r", encoding="utf-8") as f:
        artifacts = json.load(f)

    # Build URL → file path mapping
    url_to_file = build_url_to_file_map()

    all_chunks = []
    global_chunk_id = 1

    for artifact in artifacts:
        artifact_id = artifact["idArtifact"]
        artifact_title = artifact["Title"]
        artifact_url = artifact["URL"]

        fpath = url_to_file.get(artifact_url)
        if not fpath:
            print(f"  SKIP artifact {artifact_id}: no file found for {artifact_url}")
            continue

        print(f"Processing artifact {artifact_id}/{len(artifacts)}: {artifact_title}")

        with open(fpath, "r", encoding="utf-8") as f:
            mdx_content = f.read()

        chunks = extract_chunks_with_llm(mdx_content, artifact_title)

        if not chunks:
            print(f"  No chunks extracted")
            continue

        # Build chunk records for this artifact
        artifact_chunks = []
        for order, chunk in enumerate(chunks, start=1):
            artifact_chunks.append({
                "idArtifact": artifact_id,
                "idChunk": global_chunk_id,
                "order": order,
                "idChunkType": chunk.get("idChunkType", 1),
                "title": chunk.get("title", ""),
                "chunk_text": chunk.get("chunk_text", ""),
            })
            global_chunk_id += 1

        # Compute idChunkParent within this artifact's chunks
        compute_chunk_parents(artifact_chunks)

        all_chunks.extend(artifact_chunks)

        print(f"  → {len(chunks)} chunks (global id now {global_chunk_id - 1})")

        # Small delay to respect rate limits
        time.sleep(0.2)

    # Write output
    with open(OUTPUT_PATH, "w", encoding="utf-8") as f:
        json.dump(all_chunks, f, indent=2, ensure_ascii=False)

    print(f"\nDone! Wrote {len(all_chunks)} chunks to {OUTPUT_PATH}")


if __name__ == "__main__":
    main()
