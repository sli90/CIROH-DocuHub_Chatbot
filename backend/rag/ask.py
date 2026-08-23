"""Draft (non-final) CIROH RAG entry point.

Consolidates the Jupyter notebook pipelines into a script, using the
mentor's ask.py as the structural reference:

    embed question -> retrieve (top-down and/or bottom-up) -> LLM answer

This is a first cut for local testing, not the finished hybrid design.
Neighbor/ancestor expansion from the notebook is not fully ported yet.

Usage:
    python ask.py "What is NextGen In A Box?"
    python ask.py "..." --mode top_down --model gpt-5.5
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from collections import defaultdict
from pathlib import Path
from statistics import median

from dotenv import load_dotenv
from openai import OpenAI

HERE = Path(__file__).resolve().parent
load_dotenv(HERE / ".env")
load_dotenv(HERE.parent.parent / ".env")
os.environ.setdefault("POSTGRES_SCHEMA", "CIROH_AIBot")

sys.path.append(str(HERE.parent))
from database.database import DatabaseManager  # noqa: E402

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
EMBEDDING_MODEL = os.getenv("EMBEDDING_MODEL", "text-embedding-3-large")
DEFAULT_MODEL = os.getenv("ANSWER_MODEL", "gpt-5.5")

# Rough public list prices; labeled "estimated" in the API response.
EMBEDDING_USD_PER_M = float(os.getenv("EMBEDDING_USD_PER_M", "0.13"))
LLM_INPUT_USD_PER_M = float(os.getenv("LLM_INPUT_USD_PER_M", "1.25"))
LLM_OUTPUT_USD_PER_M = float(os.getenv("LLM_OUTPUT_USD_PER_M", "10.00"))

SYSTEM_MSG = (
    "You are an expert AI assistant for the CIROH knowledge base. "
    "Answer the user's question using only the provided context. "
    "If the answer cannot be supported by the context, say so clearly. "
    "When relevant, synthesize information across multiple artifacts. "
    "Some context blocks contain local document segments, while others "
    "contain thematic evidence extracted from artifacts. "
    "Do not use external knowledge."
)

HYBRID_ROUTER_MSG = (
    "You route questions for a CIROH RAG system. Do not answer the question. "
    "Choose exactly one retrieval path."
)

QUESTION_TYPE_LABELS = {
    "top_down": "Overview Question",
    "bottom_up": "Specific Question",
    "both": "Overview Question / Specific Question",
}


class UsageMeter:
    """Accumulate OpenAI token usage and an estimated USD cost."""

    def __init__(self):
        self.embedding_tokens = 0
        self.input_tokens = 0
        self.output_tokens = 0
        self.calls = []

    def add_embedding(self, usage, label="embedding"):
        tokens = _usage_value(usage, "prompt_tokens", "input_tokens")
        self.embedding_tokens += tokens
        self.calls.append({"label": label, "type": "embedding", "tokens": tokens})

    def add_llm(self, usage, label="llm"):
        inp = _usage_value(usage, "input_tokens", "prompt_tokens")
        out = _usage_value(usage, "output_tokens", "completion_tokens")
        self.input_tokens += inp
        self.output_tokens += out
        self.calls.append(
            {"label": label, "type": "llm", "input_tokens": inp, "output_tokens": out}
        )

    def summary(self):
        embed_cost = self.embedding_tokens * EMBEDDING_USD_PER_M / 1_000_000
        llm_cost = (
            self.input_tokens * LLM_INPUT_USD_PER_M
            + self.output_tokens * LLM_OUTPUT_USD_PER_M
        ) / 1_000_000
        return {
            "embedding_tokens": self.embedding_tokens,
            "input_tokens": self.input_tokens,
            "output_tokens": self.output_tokens,
            "total_tokens": self.embedding_tokens + self.input_tokens + self.output_tokens,
            "estimated_usd": round(embed_cost + llm_cost, 6),
            "estimated": True,
            "calls": self.calls,
        }


def _usage_value(usage, *names):
    if usage is None:
        return 0
    if isinstance(usage, dict):
        for name in names:
            if usage.get(name) is not None:
                return int(usage[name])
        return 0
    for name in names:
        value = getattr(usage, name, None)
        if value is not None:
            return int(value)
    return 0


def _db():
    return DatabaseManager()


def get_embedding(text, meter=None, dimensions=1792, model=None):
    response = client.embeddings.create(
        input=text,
        model=model or EMBEDDING_MODEL,
        dimensions=dimensions,
    )
    if meter is not None:
        meter.add_embedding(getattr(response, "usage", None))
    return response.data[0].embedding


def get_breadcrumb(artifact_id):
    query = """
    WITH RECURSIVE breadcrumb_path AS (
        SELECT idartifact, title, idartifactparent, 1 AS depth
        FROM tblartifacts
        WHERE idartifact = %s
        UNION ALL
        SELECT a.idartifact, a.title, a.idartifactparent, bp.depth + 1
        FROM tblartifacts a
        JOIN breadcrumb_path bp ON a.idartifact = bp.idartifactparent
    )
    SELECT string_agg(title, ' > ' ORDER BY depth DESC) AS breadcrumb
    FROM breadcrumb_path;
    """
    with _db() as db:
        result = db.execute_query(query, params=(artifact_id,), fetch=True)
    if result and result[0] and result[0].get("breadcrumb"):
        return result[0]["breadcrumb"]
    return None


def query_artifacts(question_embedding, max_relevant_artifacts=6):
    query = """
    SELECT
        a.idartifact,
        a.idartifacttype,
        at.typename AS artifact_type_name,
        a.title,
        a.url,
        a.summary_data ->> 'summary_text' AS summary,
        COALESCE(a.summary_data -> 'keywords', '[]'::jsonb) AS keywords,
        COALESCE(a.metadata ->> 'retrieval_metadata_text', '') AS retrieval_metadata_text,
        (a.embedding <=> %s::vector) AS distance
    FROM tblartifacts a
    JOIN tblartifacttypes at ON at.idartifacttype = a.idartifacttype
    WHERE a.summary_data IS NOT NULL
      AND a.embedding IS NOT NULL
      AND a.isactive = TRUE
    ORDER BY a.embedding <=> %s::vector
    LIMIT %s;
    """
    with _db() as db:
        return db.execute_query(
            query,
            params=(question_embedding, question_embedding, max_relevant_artifacts),
            fetch=True,
        ) or []


def query_chunks_for_artifact(question_embedding, artifact_id, max_chunks_per_artifact=4):
    query = """
    SELECT
        c.idchunk,
        c.idartifact,
        c.idchunkparent,
        c."order",
        ct.typename AS chunk_type,
        c.chunk_text,
        c.metadata,
        c.embedding <=> %s::vector AS distance
    FROM tblchunks c
    JOIN tblchunktypes ct ON ct.idchunktype = c.idchunktype
    WHERE c.idartifact = %s
      AND c.embedding IS NOT NULL
    ORDER BY c.embedding <=> %s::vector
    LIMIT %s;
    """
    with _db() as db:
        return db.execute_query(
            query,
            params=(
                question_embedding,
                artifact_id,
                question_embedding,
                max_chunks_per_artifact,
            ),
            fetch=True,
        ) or []


def query_top_chunks_global(question_embedding, max_relevant_chunks=12):
    query = """
    SELECT
        c.idchunk,
        c.idartifact,
        c.idchunkparent,
        c."order",
        ct.typename AS chunk_type,
        c.chunk_text,
        c.metadata,
        (c.embedding <=> %s::vector) AS distance,
        a.title AS artifact_title,
        a.url AS artifact_url,
        at.typename AS artifact_type_name
    FROM tblchunks c
    JOIN tblartifacts a ON a.idartifact = c.idartifact
    JOIN tblchunktypes ct ON ct.idchunktype = c.idchunktype
    JOIN tblartifacttypes at ON at.idartifacttype = a.idartifacttype
    WHERE c.embedding IS NOT NULL
      AND a.isactive = TRUE
    ORDER BY c.embedding <=> %s::vector
    LIMIT %s;
    """
    with _db() as db:
        return db.execute_query(
            query,
            params=(question_embedding, question_embedding, max_relevant_chunks),
            fetch=True,
        ) or []


def fetch_artifacts_by_ids(artifact_ids):
    if not artifact_ids:
        return []
    query = """
    WITH requested_ids AS (
        SELECT * FROM unnest(%s::int[]) WITH ORDINALITY AS t(idartifact, ord)
    )
    SELECT
        a.idartifact,
        a.idartifacttype,
        at.typename AS artifact_type_name,
        a.title,
        a.url,
        a.summary_data ->> 'summary_text' AS summary,
        COALESCE(a.summary_data -> 'keywords', '[]'::jsonb) AS keywords,
        COALESCE(a.metadata ->> 'retrieval_metadata_text', '') AS retrieval_metadata_text,
        r.ord
    FROM requested_ids r
    JOIN tblartifacts a ON a.idartifact = r.idartifact
    JOIN tblartifacttypes at ON at.idartifacttype = a.idartifacttype
    WHERE a.isactive = TRUE
    ORDER BY r.ord;
    """
    with _db() as db:
        return db.execute_query(query, params=(artifact_ids,), fetch=True) or []


def adaptive_artifact_pruning(
    artifact_rows,
    retrieval_mode="exploratory",
    min_keep=2,
    max_considered_for_cut=5,
    robust_gap_multiplier=3.0,
    min_gap_share=0.45,
):
    if not artifact_rows:
        return artifact_rows, {"applied": False, "reason": "no_rows"}

    rows = sorted(artifact_rows, key=lambda r: r["distance"])
    mode = (retrieval_mode or "exploratory").strip().lower()
    if mode not in {"focused", "synthesis", "exploratory"}:
        mode = "exploratory"

    if mode == "focused":
        effective_min_keep = max(1, min_keep)
        effective_max_considered = max_considered_for_cut
        effective_multiplier = robust_gap_multiplier
        effective_share = min_gap_share
    elif mode == "synthesis":
        effective_min_keep = max(2, min_keep)
        effective_max_considered = max(max_considered_for_cut, 6)
        effective_multiplier = robust_gap_multiplier * 1.2
        effective_share = max(min_gap_share, 0.50)
    else:
        effective_min_keep = max(3, min_keep)
        effective_max_considered = max(max_considered_for_cut, 6)
        effective_multiplier = robust_gap_multiplier * 1.35
        effective_share = max(min_gap_share, 0.55)

    if len(rows) <= effective_min_keep:
        return rows, {"applied": False, "reason": "too_few_rows", "retrieval_mode": mode}

    distances = [r["distance"] for r in rows]
    gaps = [distances[i + 1] - distances[i] for i in range(len(distances) - 1)]
    start_idx = effective_min_keep - 1
    end_idx = min(len(gaps), effective_max_considered)
    if start_idx >= end_idx:
        return rows, {"applied": False, "reason": "no_candidate_cut_positions"}

    candidate_indices = list(range(start_idx, end_idx))
    candidate_gaps = [gaps[i] for i in candidate_indices]
    med_gap = median(candidate_gaps)
    mad_gap = median([abs(g - med_gap) for g in candidate_gaps])
    best_idx = max(candidate_indices, key=lambda i: gaps[i])
    best_gap = gaps[best_idx]
    spread = distances[min(end_idx, len(distances) - 1)] - distances[0]
    gap_share = best_gap / (spread + 1e-9)
    robust_score = float("inf") if mad_gap == 0 and best_gap > med_gap else (
        0.0 if mad_gap == 0 else (best_gap - med_gap) / mad_gap
    )

    if robust_score >= effective_multiplier and gap_share >= effective_share:
        return rows[: best_idx + 1], {
            "applied": True,
            "reason": "strong_gap_detected",
            "retrieval_mode": mode,
            "cut_after_rank": best_idx + 1,
        }
    return rows, {"applied": False, "reason": "no_strong_gap", "retrieval_mode": mode}


def group_seed_chunks_by_artifact(
    chunk_rows, max_seed_chunks_per_artifact=2, max_artifacts_bottomup=6
):
    if not chunk_rows:
        return [], {}
    grouped = defaultdict(list)
    for row in chunk_rows:
        grouped[row["idartifact"]].append(row)
    for aid in grouped:
        grouped[aid] = sorted(
            grouped[aid], key=lambda r: (r["distance"], r.get("order") or 0, r["idchunk"])
        )
    ranked = sorted(grouped.keys(), key=lambda aid: grouped[aid][0]["distance"])
    ranked = ranked[:max_artifacts_bottomup]
    return ranked, {aid: grouped[aid][:max_seed_chunks_per_artifact] for aid in ranked}


def build_artifact_context_block(row):
    breadcrumb = get_breadcrumb(row["idartifact"]) or ""
    parts = []
    if row.get("title"):
        parts.append(f"Artifact title: {row['title']}")
    if breadcrumb:
        parts.append(f"Breadcrumb: {breadcrumb}")
    if row.get("url"):
        parts.append(f"URL: {row['url']}")
    if row.get("summary"):
        parts.append(f"Artifact summary:\n{row['summary']}")
    keywords = row.get("keywords") or []
    if isinstance(keywords, list) and keywords:
        parts.append("Keywords: " + ", ".join(str(k) for k in keywords if k))
    if row.get("retrieval_metadata_text"):
        parts.append(row["retrieval_metadata_text"])
    return "\n".join(parts)


def build_chunk_context_block(artifact_row, chunk_rows):
    header = build_artifact_context_block(artifact_row)
    evidence = []
    for ch in chunk_rows:
        block = [f"Chunk type: {ch.get('chunk_type', '')}"]
        if ch.get("chunk_text"):
            block.append("Chunk text:")
            block.append(ch["chunk_text"])
        evidence.append("\n".join(block))
    if not evidence:
        return header
    return header + "\n\nSelected evidence:\n\n" + "\n\n---\n\n".join(evidence)


def classify_query_scope(question, meter=None, model=None):
    """Notebook classifier used to prune top-down artifact lists."""
    prompt = f"""
Classify the following question into exactly one retrieval mode.

QUESTION:
{question}

Choose one:
- focused: answer likely lives in one artifact or a very small set
- synthesis: a defined topic that needs several related artifacts
- exploratory: broad comparison or survey across the corpus

Return exactly this JSON:
{{"label": "focused" | "synthesis" | "exploratory", "reason": ""}}
""".strip()
    resp = client.responses.create(
        model=model or DEFAULT_MODEL,
        input=[
            {"role": "system", "content": "Classify retrieval scope. Do not answer."},
            {"role": "user", "content": prompt},
        ],
        text={"format": {"type": "json_object"}, "verbosity": "low"},
        reasoning={"effort": "low"},
    )
    if meter is not None:
        meter.add_llm(getattr(resp, "usage", None), label="scope_classifier")
    try:
        data = json.loads((resp.output_text or "").strip())
    except json.JSONDecodeError:
        data = {}
    label = (data.get("label") or "exploratory").strip().lower()
    if label not in {"focused", "synthesis", "exploratory"}:
        label = "exploratory"
    return {"recommended_mode": label, "reason": data.get("reason") or ""}


def classify_hybrid_route(question, meter=None, model=None):
    """Pick top_down, bottom_up, or both. This is the missing notebook Hybrid cell."""
    prompt = f"""
Choose the retrieval path for this CIROH knowledge-base question.

QUESTION:
{question}

Paths:
- top_down: the user needs a document, repo, dataset, page, or broad topic first
- bottom_up: the user wants a specific fact, number, procedure, or short how-to
- both: mixed, ambiguous, compound, or you are not sure

Return exactly this JSON:
{{"route": "top_down" | "bottom_up" | "both", "reason": ""}}
""".strip()
    resp = client.responses.create(
        model=model or DEFAULT_MODEL,
        input=[
            {"role": "system", "content": HYBRID_ROUTER_MSG},
            {"role": "user", "content": prompt},
        ],
        text={"format": {"type": "json_object"}, "verbosity": "low"},
        reasoning={"effort": "low"},
    )
    if meter is not None:
        meter.add_llm(getattr(resp, "usage", None), label="hybrid_router")
    try:
        data = json.loads((resp.output_text or "").strip())
    except json.JSONDecodeError:
        data = {}
    route = (data.get("route") or "both").strip().lower()
    if route not in {"top_down", "bottom_up", "both"}:
        route = "both"
    return {"route": route, "reason": data.get("reason") or ""}


def retrieve_top_down(question, embedding, meter=None, model=None):
    scope = classify_query_scope(question, meter=meter, model=model)
    artifacts = query_artifacts(embedding)
    artifacts, _pruning = adaptive_artifact_pruning(
        artifacts, retrieval_mode=scope["recommended_mode"]
    )
    blocks = []
    sources = []
    for art in artifacts:
        chunks = query_chunks_for_artifact(embedding, art["idartifact"])
        if chunks:
            blocks.append(build_chunk_context_block(art, chunks))
        else:
            blocks.append(build_artifact_context_block(art))
        sources.append(_source_from_artifact(art))
    return blocks, sources, {"scope": scope}


def retrieve_bottom_up(embedding):
    chunks = query_top_chunks_global(embedding)
    ranked_ids, seeds = group_seed_chunks_by_artifact(chunks)
    artifacts = {row["idartifact"]: row for row in fetch_artifacts_by_ids(ranked_ids)}
    blocks = []
    sources = []
    for aid in ranked_ids:
        art = artifacts.get(aid)
        seed_rows = seeds.get(aid, [])
        if art is None:
            continue
        if seed_rows:
            blocks.append(build_chunk_context_block(art, seed_rows))
        else:
            blocks.append(build_artifact_context_block(art))
        sources.append(_source_from_artifact(art))
    return blocks, sources, {"seed_artifacts": ranked_ids}


def _source_from_artifact(art):
    title = art.get("title") or art.get("artifact_title") or ""
    url = art.get("url") or art.get("artifact_url") or ""
    breadcrumb = get_breadcrumb(art["idartifact"]) or title
    return {
        "id": art["idartifact"],
        "title": breadcrumb,
        "url": url,
        "type": art.get("artifact_type_name"),
    }


def merge_retrieval(parts):
    blocks = []
    sources = []
    seen_ids = set()
    seen_blocks = set()
    for part_blocks, part_sources, _meta in parts:
        for block in part_blocks:
            if block and block not in seen_blocks:
                seen_blocks.add(block)
                blocks.append(block)
        for src in part_sources:
            if src["id"] not in seen_ids:
                seen_ids.add(src["id"])
                sources.append(src)
    return blocks, sources


def get_rag_answer(question, context_blocks, meter=None, model=None):
    if not context_blocks:
        return "I could not find relevant information in the CIROH knowledge base."
    context_str = "\n\n==============================\n\n".join(context_blocks)
    resp = client.responses.create(
        model=model or DEFAULT_MODEL,
        input=[
            {"role": "system", "content": SYSTEM_MSG},
            {"role": "user", "content": f"CONTEXT:\n{context_str}\n\nQUESTION:\n{question}"},
        ],
        text={"verbosity": "medium"},
        reasoning={"effort": "medium"},
    )
    if meter is not None:
        meter.add_llm(getattr(resp, "usage", None), label="answer")
    return resp.output_text or ""


def answer_question(question, mode="hybrid", model=None):
    """Public API used by FastAPI and the CLI."""
    meter = UsageMeter()
    model = model or DEFAULT_MODEL
    embedding = get_embedding(question, meter=meter)

    route_info = {"route": mode, "reason": "forced by caller"}
    if mode == "hybrid":
        route_info = classify_hybrid_route(question, meter=meter, model=model)
    route = route_info["route"] if mode == "hybrid" else mode
    if route not in {"top_down", "bottom_up", "both"}:
        route = "both"

    parts = []
    if route in {"top_down", "both"}:
        parts.append(retrieve_top_down(question, embedding, meter=meter, model=model))
    if route in {"bottom_up", "both"}:
        parts.append(retrieve_bottom_up(embedding))

    if route == "both":
        blocks, sources = merge_retrieval(parts)
    else:
        blocks, sources, _meta = parts[0] if parts else ([], [], {})

    answer = get_rag_answer(question, blocks, meter=meter, model=model)
    usage = meter.summary()
    return {
        "answer": answer,
        "sources": [s["title"] for s in sources],
        "links": [s["url"] for s in sources],
        "route": route,
        "question_type": QUESTION_TYPE_LABELS.get(route, "Overview Question / Specific Question"),
        "route_reason": route_info.get("reason") or "",
        "usage": usage,
        "success": True,
    }


def main():
    parser = argparse.ArgumentParser(description="Ask the CIROH knowledge base.")
    parser.add_argument("question", help="Your question (in quotes)")
    parser.add_argument(
        "--mode",
        default="hybrid",
        choices=["hybrid", "top_down", "bottom_up", "both"],
        help="Retrieval mode (default: hybrid)",
    )
    parser.add_argument("--model", default=DEFAULT_MODEL, help="LLM for answers")
    args = parser.parse_args()

    print(f"❓ {args.question}\n")
    result = answer_question(args.question, mode=args.mode, model=args.model)
    print("=" * 60)
    print(result["answer"])
    print("=" * 60)
    print(f"\nQuestion type: {result['question_type']}")
    print(f"Retrieval: {result['route']} — {result['route_reason']}")
    usage = result["usage"]
    print(
        f"Tokens: embed={usage['embedding_tokens']} "
        f"in={usage['input_tokens']} out={usage['output_tokens']} "
        f"est=${usage['estimated_usd']:.4f}"
    )
    print("\nSources:")
    for title, url in zip(result["sources"], result["links"]):
        print(f"  {title}")
        if url:
            print(f"      {url}")


if __name__ == "__main__":
    main()
