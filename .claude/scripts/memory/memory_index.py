"""
memory_index.py — Incrementally index Alec's vault into the memory database.

Only re-indexes files whose mtime has changed since last run.
Run this periodically (e.g., before a session or via a scheduled task).

Usage:
    python memory_index.py              # index all vault areas
    python memory_index.py --vault game # index gamedev area only
    python memory_index.py --reset      # wipe and re-index everything
    python memory_index.py --stats      # show index stats and exit
"""

import argparse
import sqlite3
import sys
import time
from pathlib import Path

# Make sibling modules importable
sys.path.insert(0, str(Path(__file__).parent))

from chunker import chunk_file
from db import DB_PATH, delete_file_chunks, get_indexed_mtimes, insert_chunk, open_db
from embeddings import embed, EMBEDDING_DIM

VAULT_ROOT = Path(r"D:\Brain")

# Map vault label → list of directories to index
VAULT_AREAS: dict[str, list[Path]] = {
    "meta": [VAULT_ROOT / "00_Meta"],
    "projects": [VAULT_ROOT / "10_Active_Projects"],
    "gamedev": [VAULT_ROOT / "20_Reference" / "GameDev"],
    "products": [
        VAULT_ROOT / "20_Reference" / "Products",
        VAULT_ROOT / "20_Reference" / "Market",
    ],
}

# CLI alias → internal vault label (matches memory_search.py aliases)
VAULT_ALIASES = {
    "game": "gamedev",
    "work": "products",
    "project": "projects",
    "meta": "meta",
    "gamedev": "gamedev",
    "products": "products",
    "projects": "projects",
}


def collect_markdown_files(directories: list[Path]) -> list[Path]:
    """Return all .md files under the given directories (recursive)."""
    files: list[Path] = []
    for directory in directories:
        if directory.exists():
            files.extend(directory.rglob("*.md"))
    return files


def index_vault_area(
    conn: sqlite3.Connection,
    vault_label: str,
    indexed_mtimes: dict[str, float],
    verbose: bool = True,
) -> tuple[int, int]:
    """
    Index one vault area. Returns (files_indexed, chunks_written).
    Only processes files whose mtime differs from the stored value.
    """
    directories = VAULT_AREAS.get(vault_label, [])
    files = collect_markdown_files(directories)

    files_indexed = 0
    chunks_written = 0
    batch_texts: list[str] = []
    batch_meta: list[tuple] = []  # (file_path, vault, chunk_index, content, token_count, mtime)

    EMBED_BATCH = 64  # embed in batches of 64 for memory efficiency

    def flush_batch():
        nonlocal chunks_written
        if not batch_texts:
            return
        embeddings = embed(batch_texts)
        for (fp, v, ci, content, tc, mtime), vec in zip(batch_meta, embeddings):
            insert_chunk(conn, fp, v, ci, content, tc, mtime, vec)
            chunks_written += 1
        batch_texts.clear()
        batch_meta.clear()

    for file_path in files:
        fp_str = str(file_path)
        mtime = file_path.stat().st_mtime

        if fp_str in indexed_mtimes and abs(indexed_mtimes[fp_str] - mtime) < 0.01:
            continue  # Not modified since last index

        # File changed — remove old chunks and re-index
        delete_file_chunks(conn, fp_str)
        chunks = chunk_file(file_path)
        if not chunks:
            continue

        files_indexed += 1
        if verbose:
            print(f"  [{vault_label}] {file_path.name} -> {len(chunks)} chunks")

        for chunk in chunks:
            batch_texts.append(chunk.content)
            batch_meta.append(
                (fp_str, vault_label, chunk.chunk_index, chunk.content, chunk.token_count, mtime)
            )
            if len(batch_texts) >= EMBED_BATCH:
                flush_batch()

    flush_batch()
    conn.commit()
    return files_indexed, chunks_written


def print_stats(conn: sqlite3.Connection) -> None:
    total = conn.execute("SELECT COUNT(*) FROM chunks").fetchone()[0]
    print(f"\nIndex stats — {DB_PATH}")
    print(f"  Total chunks: {total:,}")
    rows = conn.execute(
        "SELECT vault, COUNT(*) as n FROM chunks GROUP BY vault ORDER BY vault"
    ).fetchall()
    for row in rows:
        print(f"  {row[0]:12s}: {row[1]:,} chunks")


def main():
    parser = argparse.ArgumentParser(description="Index Alec's vault into memory.db")
    parser.add_argument(
        "--vault",
        default="all",
        help="Vault area to index: all, game, work, project, meta, gamedev, products, projects",
    )
    parser.add_argument("--reset", action="store_true", help="Wipe and re-index everything")
    parser.add_argument("--stats", action="store_true", help="Show index stats and exit")
    parser.add_argument("--quiet", action="store_true", help="Suppress per-file output")
    args = parser.parse_args()

    conn = open_db()

    if args.stats:
        print_stats(conn)
        conn.close()
        return

    if args.reset:
        print("Resetting index...")
        conn.execute("DELETE FROM chunks")
        conn.execute("DELETE FROM chunks_fts")
        conn.execute("DELETE FROM chunks_vec")
        conn.commit()
        indexed_mtimes: dict[str, float] = {}
    else:
        indexed_mtimes = get_indexed_mtimes(conn)

    vault_arg = VAULT_ALIASES.get(args.vault, args.vault)
    areas = list(VAULT_AREAS.keys()) if vault_arg == "all" else [vault_arg]

    if vault_arg not in VAULT_AREAS and vault_arg != "all":
        print(f"Unknown vault '{args.vault}'. Choose from: all, {', '.join(VAULT_ALIASES)}")
        sys.exit(1)

    t0 = time.time()
    total_files = total_chunks = 0
    for area in areas:
        files, chunks = index_vault_area(conn, area, indexed_mtimes, verbose=not args.quiet)
        total_files += files
        total_chunks += chunks

    elapsed = time.time() - t0
    print(f"\nDone: {total_files} files re-indexed, {total_chunks} chunks written ({elapsed:.1f}s)")
    print_stats(conn)
    conn.close()


if __name__ == "__main__":
    main()
