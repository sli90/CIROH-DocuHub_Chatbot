#!/usr/bin/env python3
import argparse
import json
import os
import re
from typing import List, Dict, Any, Tuple

HEADING_RE = re.compile(r'^(#{1,6})\s+(.*)\s*$')

def load_level1(path: str) -> List[Dict[str, Any]]:
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)
    if isinstance(data, dict) and "ciroh_repos_index" in data:
        items = data["ciroh_repos_index"]
    elif isinstance(data, list):
        items = data
    else:
        items = [data]
    return [x for x in items if isinstance(x, dict) and "metadata" in x and "content" in x]

def coalesce_parent_header(md_meta: Dict[str, Any]) -> str:
    if isinstance(md_meta, dict):
        if md_meta.get("section_header"):
            return md_meta["section_header"]
        if md_meta.get("title"):
            return f"# {md_meta['title']}"
    return "# Repository"

def split_markdown_sections(md: str) -> List[Tuple[str, List[str]]]:
    """
    Split markdown into sections based only on '## ' headings.

    Returns list of (heading_line, content_lines), where:
      heading_line = full '## ...' line
      content_lines = all lines until the next '##' (or end of file),
                      including any ###, ####, etc. inside.
    """
    lines = md.splitlines()
    sections: List[Tuple[str, List[str]]] = []

    in_code = False
    fence = None
    # positions of '##' headings: (line_index, heading_text)
    h2_positions: List[Tuple[int, str]] = []

    for i, line in enumerate(lines):
        # fenced code blocks
        fence_match = re.match(r'^(\s*)(`{3,}|~{3,})(.*)$', line)
        if fence_match:
            marker = fence_match.group(2)
            if not in_code:
                in_code = True
                fence = marker
            else:
                if fence == marker:
                    in_code = False
                    fence = None
            continue

        if in_code:
            continue

        m = HEADING_RE.match(line)
        if m:
            hashes, text = m.group(1), m.group(2)
            level = len(hashes)
            if level == 2:
                h2_positions.append((i, f"{hashes} {text}".strip()))

    # no '##' headings: optional behavior – here we just return empty
    if not h2_positions:
        return []

    for idx, (start_li, heading_text) in enumerate(h2_positions):
        if idx + 1 < len(h2_positions):
            end_li = h2_positions[idx + 1][0]
        else:
            end_li = len(lines)
        content_lines = lines[start_li + 1:end_li]
        sections.append((heading_text, content_lines))

    return sections

def build_level2_array(repo_obj: Dict[str, Any]) -> List[Dict[str, Any]]:
    meta = repo_obj.get("metadata", {})
    md = repo_obj.get("content", "") or ""
    parent_header = coalesce_parent_header(meta)

    base_meta = {
        "idurl": meta.get("idurl"),
        "title": meta.get("title"),
        "source": meta.get("source"),
        "section_header": parent_header,
        "parent_header": parent_header
    }

    sections = split_markdown_sections(md)
    level2: List[Dict[str, Any]] = []

    order = 1
    for heading, content_lines in sections:
        content = "\n".join(content_lines).strip()
        obj = {
            "metadata": {
                **base_meta,
                "order": order,
                "current_header": heading
            },
            "content": content
        }
        level2.append(obj)
        order += 1

    return level2

def sanitize_filename(name: str) -> str:
    name = name or "repo"
    name = name.strip().replace(" ", "_")
    return re.sub(r'[^A-Za-z0-9_.-]', "_", name)

def write_level2_file(out_path: str, arr: List[Dict[str, Any]]) -> None:
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(arr, f, ensure_ascii=False, indent=2)

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--input", required=True, help="Path to Level 1 JSON file")
    ap.add_argument("--outdir", help="Directory to write one Level-2 file per repo")
    ap.add_argument("--combined", help="Write a single combined Level-2 JSON array here")
    args = ap.parse_args()

    repos = load_level1(args.input)
    if not repos:
        raise SystemExit("No repository objects with {metadata, content} found in the Level 1 JSON.")

    combined_arr: List[Dict[str, Any]] = []

    if args.outdir:
        os.makedirs(args.outdir, exist_ok=True)

    for repo in repos:
        title = repo.get("metadata", {}).get("title") or "repo"
        idurl = repo.get("metadata", {}).get("idurl")
        level2 = build_level2_array(repo)

        if args.outdir:
            if isinstance(idurl, int):
                base = f"{idurl:03d}_{title}_level2.json"
            else:
                base = f"{title}_level2.json"
            base = sanitize_filename(base)
            out_path = os.path.join(args.outdir, base)
            write_level2_file(out_path, level2)

        if args.combined:
            combined_arr.extend(level2)

    if args.combined:
        with open(args.combined, "w", encoding="utf-8") as f:
            json.dump(combined_arr, f, ensure_ascii=False, indent=2)

if __name__ == "__main__":
    main()
