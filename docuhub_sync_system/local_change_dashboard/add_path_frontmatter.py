"""
Add or update `path:` in YAML frontmatter of all .mdx and .md files under mixed_docs.
Path is relative to mixed_docs, without extension, with forward slashes.
Files under src/pages are relative to the public domain root.
Example: docs/contribute/index.mdx -> path: docs/contribute/index
Example: src/pages/impact.mdx -> path: impact
"""
import os
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from docuhub_paths import public_route_from_mixed_doc_path  # noqa: E402

MIXED_DOCS = os.path.join(os.path.dirname(__file__), "mixed_docs")


def get_path_from_file(filepath: str) -> str:
    """Return the public route path represented by a mixed-doc file."""
    rel = os.path.relpath(filepath, MIXED_DOCS)
    return public_route_from_mixed_doc_path(rel)


def process_file(filepath: str) -> bool:
    """Add or update path in frontmatter. Returns True if changed."""
    with open(filepath, "r", encoding="utf-8") as f:
        content = f.read()

    if not content.startswith("---\n"):
        return False

    end_marker = "\n---"
    idx = content.find(end_marker, 4)
    if idx == -1:
        return False

    frontmatter = content[4:idx]
    body = content[idx + 4 :]

    path_value = get_path_from_file(filepath)
    path_line = f'path: "{path_value}"'

    # Already has path?
    path_re = re.compile(r"^path:\s*.*$", re.MULTILINE)
    if path_re.search(frontmatter):
        new_frontmatter = path_re.sub(path_line, frontmatter, count=1)
    else:
        # Append path before the closing --- (after last key, newline)
        new_frontmatter = frontmatter.rstrip()
        if new_frontmatter and not new_frontmatter.endswith("\n"):
            new_frontmatter += "\n"
        new_frontmatter += path_line + "\n"

    new_content = "---\n" + new_frontmatter + end_marker + body
    if new_content != content:
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(new_content)
        return True
    return False


def main():
    count = 0
    for root, _dirs, files in os.walk(MIXED_DOCS):
        for name in files:
            if not (name.endswith(".mdx") or name.endswith(".md")):
                continue
            filepath = os.path.join(root, name)
            try:
                if process_file(filepath):
                    count += 1
                    print(get_path_from_file(filepath))
            except Exception as e:
                print(f"Error {filepath}: {e}")
    print(f"\nUpdated {count} files.")


if __name__ == "__main__":
    main()
