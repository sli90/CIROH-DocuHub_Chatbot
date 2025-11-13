#!/usr/bin/env python3
import json
import glob
import os
import argparse

def load_array(path):
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)
    if isinstance(data, list):
        return data
    raise ValueError(f"{path} does not contain a JSON array")

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--indir",
        default="data/level2",
        help="Directory containing *_level2.json files (default: data/level2)",
    )
    parser.add_argument(
        "--output",
        default="data/level2_all.json",
        help="Path for combined Level 2 JSON (default: data/level2_all.json)",
    )
    args = parser.parse_args()

    pattern = os.path.join(args.indir, "*_level2.json")
    files = sorted(glob.glob(pattern))

    if not files:
        print(f"No files matched pattern: {pattern}")
        return

    combined = []

    for fp in files:
        arr = load_array(fp)
        combined.extend(arr)

    # optional but nice: deterministic ordering
    def sort_key(obj):
        meta = obj.get("metadata", {})
        return (meta.get("idurl", 0), meta.get("order", 0))

    combined.sort(key=sort_key)

    os.makedirs(os.path.dirname(args.output), exist_ok=True)
    with open(args.output, "w", encoding="utf-8") as f:
        json.dump(combined, f, ensure_ascii=False, indent=2)

    print(f"Wrote {len(combined)} section objects to {args.output}")

if __name__ == "__main__":
    main()
