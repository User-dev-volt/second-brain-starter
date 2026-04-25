"""
embeddings.py — sentence-transformers wrapper for the memory search pipeline.

Uses BAAI/bge-small-en-v1.5 (384-dim, fast on CPU, ~130MB).
Model is downloaded to ~/.cache/huggingface/ on first run.

Install: pip install sentence-transformers
"""

from __future__ import annotations

import numpy as np

_model = None
MODEL_NAME = "BAAI/bge-small-en-v1.5"
EMBEDDING_DIM = 384


def _get_model():
    global _model
    if _model is None:
        import logging
        logging.getLogger("sentence_transformers").setLevel(logging.ERROR)
        logging.getLogger("transformers").setLevel(logging.ERROR)
        from sentence_transformers import SentenceTransformer
        _model = SentenceTransformer(MODEL_NAME, trust_remote_code=False)
    return _model


def embed(texts: list[str], batch_size: int = 32) -> list[np.ndarray]:
    """
    Embed a list of strings. Returns a list of float32 numpy arrays (shape: [384,]).
    Order matches the input list.
    """
    if not texts:
        return []
    model = _get_model()
    # encode() returns a 2D numpy array (n_texts, dim)
    matrix = model.encode(texts, batch_size=batch_size, show_progress_bar=False)
    return [matrix[i] for i in range(len(matrix))]


def embed_one(text: str) -> np.ndarray:
    """Embed a single string. Returns float32 numpy array of shape [384,]."""
    return embed([text])[0]


def as_blob(vec: np.ndarray) -> bytes:
    """Convert numpy float32 array to raw bytes for SQLite storage."""
    return vec.astype(np.float32).tobytes()


def from_blob(data: bytes) -> np.ndarray:
    """Convert raw bytes back to float32 numpy array."""
    return np.frombuffer(data, dtype=np.float32)
