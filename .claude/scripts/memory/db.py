"""
db.py — SQLite abstraction for the memory search pipeline.

Uses:
  - sqlite-vec  (vec0 virtual table) for vector/KNN search
  - FTS5         for BM25 keyword search
  - A regular 'chunks' table for metadata

Install: pip install sqlite-vec

Schema:
  chunks(id, file_path, vault, chunk_index, content, token_count, file_mtime)
  chunks_fts  (FTS5, mirrors chunks.content)
  chunks_vec  (vec0, 384-dim float32)
"""

import re
import sqlite3
from pathlib import Path
from typing import Optional

import numpy as np

DB_PATH = Path(__file__).parent.parent.parent / "data" / "memory.db"


def _load_sqlite_vec(conn: sqlite3.Connection) -> None:
    """Load the sqlite-vec extension."""
    try:
        import sqlite_vec
        conn.enable_load_extension(True)
        sqlite_vec.load(conn)
        conn.enable_load_extension(False)
    except ImportError:
        raise RuntimeError(
            "sqlite-vec not installed. Run: pip install sqlite-vec"
        )


def open_db(db_path: Path = DB_PATH) -> sqlite3.Connection:
    """Open (or create) the memory database with all extensions loaded."""
    db_path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(db_path))
    conn.row_factory = sqlite3.Row
    _load_sqlite_vec(conn)
    _init_schema(conn)
    return conn


def _init_schema(conn: sqlite3.Connection) -> None:
    conn.executescript("""
        CREATE TABLE IF NOT EXISTS chunks (
            id          INTEGER PRIMARY KEY,
            file_path   TEXT NOT NULL,
            vault       TEXT NOT NULL,
            chunk_index INTEGER NOT NULL,
            content     TEXT NOT NULL,
            token_count INTEGER NOT NULL,
            file_mtime  REAL NOT NULL,
            UNIQUE(file_path, chunk_index)
        );

        CREATE VIRTUAL TABLE IF NOT EXISTS chunks_fts
            USING fts5(content, chunk_id UNINDEXED);

        CREATE VIRTUAL TABLE IF NOT EXISTS chunks_vec
            USING vec0(embedding float[384]);
    """)
    conn.commit()


# ---------------------------------------------------------------------------
# Write helpers
# ---------------------------------------------------------------------------

def get_indexed_mtimes(conn: sqlite3.Connection) -> dict[str, float]:
    """Return {file_path: max(file_mtime)} for all indexed files."""
    rows = conn.execute(
        "SELECT file_path, MAX(file_mtime) as mtime FROM chunks GROUP BY file_path"
    ).fetchall()
    return {row["file_path"]: row["mtime"] for row in rows}


def delete_file_chunks(conn: sqlite3.Connection, file_path: str) -> None:
    """Remove all chunks (and their FTS/vec rows) for a given file."""
    chunk_ids = [
        row[0]
        for row in conn.execute(
            "SELECT id FROM chunks WHERE file_path = ?", (file_path,)
        ).fetchall()
    ]
    if not chunk_ids:
        return

    placeholders = ",".join("?" * len(chunk_ids))
    conn.execute(f"DELETE FROM chunks_fts WHERE chunk_id IN ({placeholders})", chunk_ids)
    conn.execute(f"DELETE FROM chunks_vec WHERE rowid IN ({placeholders})", chunk_ids)
    conn.execute("DELETE FROM chunks WHERE file_path = ?", (file_path,))


def insert_chunk(
    conn: sqlite3.Connection,
    file_path: str,
    vault: str,
    chunk_index: int,
    content: str,
    token_count: int,
    file_mtime: float,
    embedding: np.ndarray,
) -> None:
    """Insert one chunk into all three tables atomically."""
    cur = conn.execute(
        """INSERT INTO chunks (file_path, vault, chunk_index, content, token_count, file_mtime)
           VALUES (?, ?, ?, ?, ?, ?)""",
        (file_path, vault, chunk_index, content, token_count, file_mtime),
    )
    chunk_id = cur.lastrowid

    conn.execute(
        "INSERT INTO chunks_fts(chunk_id, content) VALUES (?, ?)",
        (chunk_id, content),
    )
    conn.execute(
        "INSERT INTO chunks_vec(rowid, embedding) VALUES (?, ?)",
        (chunk_id, embedding.astype(np.float32).tobytes()),
    )


# ---------------------------------------------------------------------------
# Search helpers
# ---------------------------------------------------------------------------

def vector_search(
    conn: sqlite3.Connection,
    query_vec: np.ndarray,
    top_k: int = 20,
    vault: Optional[str] = None,
) -> list[dict]:
    """
    KNN search via sqlite-vec. Returns list of {chunk_id, distance}.
    Vault filtering is applied post-join (sqlite-vec doesn't support WHERE on metadata).
    """
    rows = conn.execute(
        """
        SELECT cv.rowid AS chunk_id, cv.distance
        FROM chunks_vec cv
        JOIN chunks c ON c.id = cv.rowid
        WHERE cv.embedding MATCH ? AND cv.k = ?
        ORDER BY cv.distance
        """,
        (query_vec.astype(np.float32).tobytes(), top_k * 3),
    ).fetchall()

    results = [{"chunk_id": r["chunk_id"], "distance": r["distance"]} for r in rows]

    if vault and vault != "all":
        vault_chunk_ids = {
            row[0]
            for row in conn.execute(
                "SELECT id FROM chunks WHERE vault = ?", (vault,)
            ).fetchall()
        }
        results = [r for r in results if r["chunk_id"] in vault_chunk_ids]

    return results[:top_k]


def fts_search(
    conn: sqlite3.Connection,
    query: str,
    top_k: int = 20,
    vault: Optional[str] = None,
) -> list[dict]:
    """
    BM25 keyword search via FTS5. Returns list of {chunk_id, rank}.
    rank is negative (more negative = better match).
    """
    # Sanitize query for FTS5 (escape special chars)
    safe_query = _sanitize_fts_query(query)
    if not safe_query:
        return []

    vault_join = "JOIN chunks c ON c.id = fts.chunk_id" if vault and vault != "all" else ""
    vault_where = "AND c.vault = ?" if vault and vault != "all" else ""
    params: list = [safe_query, top_k * 3]
    if vault and vault != "all":
        params.insert(1, vault)  # vault param goes before limit

    sql = f"""
        SELECT fts.chunk_id, fts.rank
        FROM chunks_fts fts
        {vault_join}
        WHERE fts.content MATCH ?
        {vault_where}
        ORDER BY fts.rank
        LIMIT ?
    """
    # Rebuild params in correct order
    if vault and vault != "all":
        params = [safe_query, vault, top_k * 3]
    else:
        params = [safe_query, top_k * 3]

    try:
        rows = conn.execute(sql, params).fetchall()
    except sqlite3.OperationalError:
        return []

    return [{"chunk_id": r["chunk_id"], "rank": r["rank"]} for r in rows]


def get_chunks_by_ids(
    conn: sqlite3.Connection, chunk_ids: list[int]
) -> dict[int, dict]:
    """Fetch chunk metadata+content by id list. Returns {id: row_dict}."""
    if not chunk_ids:
        return {}
    placeholders = ",".join("?" * len(chunk_ids))
    rows = conn.execute(
        f"SELECT id, file_path, vault, chunk_index, content FROM chunks WHERE id IN ({placeholders})",
        chunk_ids,
    ).fetchall()
    return {r["id"]: dict(r) for r in rows}


def _sanitize_fts_query(query: str) -> str:
    """Strip FTS5 special syntax to avoid query parse errors."""
    safe = re.sub(r'["\^\*\(\)\{\}\[\]]', " ", query)
    safe = " ".join(safe.split())  # collapse whitespace
    return safe
