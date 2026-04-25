"""
memory_search.py — Hybrid semantic + keyword search over Alec's vault.

Hybrid scoring: 0.7 × (normalized cosine similarity) + 0.3 × (normalized BM25)

Usage:
    python memory_search.py "Godot inventory system" --vault game --top 5
    python memory_search.py "MovieBuilder product market" --vault work
    python memory_search.py "project X last session decisions" --vault project
    python memory_search.py "comfyui workflow nodes" --top 10

Vault aliases:
    game    → gamedev area  (20_Reference/GameDev/)
    work    → products area (20_Reference/Products/, Market/)
    project → projects area (10_Active_Projects/)
    meta    → meta area     (00_Meta/)
    all     → all areas (default)
"""

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from db import open_db, vector_search, fts_search, get_chunks_by_ids
from embeddings import embed_one

VAULT_ALIASES = {
    "game": "gamedev",
    "work": "products",
    "project": "projects",
    "meta": "meta",
    "gamedev": "gamedev",
    "products": "products",
    "projects": "projects",
    "all": "all",
}

VEC_WEIGHT = 0.7
FTS_WEIGHT = 0.3


def _normalize(values: list[float], invert: bool = False) -> list[float]:
    """Min-max normalize to [0, 1]. If invert=True, flip so lower raw = higher score."""
    if not values:
        return []
    lo, hi = min(values), max(values)
    if hi == lo:
        return [1.0] * len(values)
    normalized = [(v - lo) / (hi - lo) for v in values]
    return [1.0 - n for n in normalized] if invert else normalized


def hybrid_search(
    query: str,
    vault: str = "all",
    top_k: int = 10,
) -> list[dict]:
    """
    Perform hybrid search and return top_k results ranked by combined score.

    Returns list of dicts:
        {chunk_id, file_path, vault, chunk_index, content, score, vec_score, fts_score}
    """
    conn = open_db()

    try:
        query_vec = embed_one(query)
        vec_results = vector_search(conn, query_vec, top_k=top_k * 2, vault=vault)
        fts_results = fts_search(conn, query, top_k=top_k * 2, vault=vault)
    finally:
        conn.close()

    # Build score maps: chunk_id → raw score
    vec_map: dict[int, float] = {r["chunk_id"]: r["distance"] for r in vec_results}
    fts_map: dict[int, float] = {r["chunk_id"]: r["rank"] for r in fts_results}

    all_ids = list(set(vec_map) | set(fts_map))
    if not all_ids:
        return []

    # Normalize vector distances (lower distance = better → invert)
    vec_ids = list(vec_map.keys())
    norm_vec = dict(zip(vec_ids, _normalize([vec_map[i] for i in vec_ids], invert=True)))

    # Normalize FTS ranks (more negative = better → invert after abs)
    fts_ids = list(fts_map.keys())
    # FTS5 rank is negative; make positive then normalize with invert
    norm_fts = dict(
        zip(fts_ids, _normalize([abs(fts_map[i]) for i in fts_ids], invert=True))
    )

    # Combine scores
    scored: list[tuple[float, int]] = []
    for cid in all_ids:
        v = norm_vec.get(cid, 0.0)
        f = norm_fts.get(cid, 0.0)
        combined = VEC_WEIGHT * v + FTS_WEIGHT * f
        scored.append((combined, cid))

    scored.sort(reverse=True)
    top_ids = [cid for _, cid in scored[:top_k]]

    conn = open_db()
    try:
        chunk_data = get_chunks_by_ids(conn, top_ids)
    finally:
        conn.close()

    results = []
    for score, cid in scored[:top_k]:
        if cid not in chunk_data:
            continue
        row = chunk_data[cid]
        results.append(
            {
                "chunk_id": cid,
                "file_path": row["file_path"],
                "vault": row["vault"],
                "chunk_index": row["chunk_index"],
                "content": row["content"],
                "score": round(score, 4),
                "vec_score": round(norm_vec.get(cid, 0.0), 4),
                "fts_score": round(norm_fts.get(cid, 0.0), 4),
            }
        )

    return results


def format_results(results: list[dict], show_scores: bool = False) -> str:
    if not results:
        return "No results found."

    lines = []
    for i, r in enumerate(results, 1):
        file_short = Path(r["file_path"]).name
        score_info = f" [score={r['score']}, vec={r['vec_score']}, fts={r['fts_score']}]" if show_scores else f" [score={r['score']}]"
        lines.append(f"\n{'-'*60}")
        lines.append(f"#{i}  {file_short}  •  vault={r['vault']}  •  chunk={r['chunk_index']}{score_info}")
        lines.append(f"    {r['file_path']}")
        lines.append("")
        # Indent content for readability
        for line in r["content"].splitlines()[:20]:  # cap at 20 lines
            lines.append(f"  {line}")
        if len(r["content"].splitlines()) > 20:
            lines.append("  [... truncated ...]")

    return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser(
        description="Hybrid semantic + keyword search over Alec's vault"
    )
    parser.add_argument("query", nargs="?", help="Search query")
    parser.add_argument(
        "--vault",
        default="all",
        help="Vault area: all (default), game, work, project, meta",
    )
    parser.add_argument("--top", type=int, default=5, help="Number of results (default: 5)")
    parser.add_argument("--scores", action="store_true", help="Show detailed score breakdown")
    parser.add_argument("--json", action="store_true", help="Output raw JSON")
    args = parser.parse_args()

    if not args.query:
        parser.print_help()
        sys.exit(1)

    vault = VAULT_ALIASES.get(args.vault, args.vault)
    if vault not in ("all", "meta", "projects", "gamedev", "products"):
        print(f"Unknown vault '{args.vault}'. Valid: all, game, work, project, meta")
        sys.exit(1)

    results = hybrid_search(args.query, vault=vault, top_k=args.top)

    if args.json:
        import json
        print(json.dumps(results, indent=2))
    else:
        print(format_results(results, show_scores=args.scores))


if __name__ == "__main__":
    main()
