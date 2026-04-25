"""
chunker.py — Markdown-aware text chunker for the memory search pipeline.

Splits markdown files into ~400-token chunks with 50-token overlap,
respecting header boundaries so chunks stay semantically coherent.
"""

import re
from dataclasses import dataclass
from pathlib import Path


# Rough BPE approximation: 1 word ≈ 1.3 tokens
def _approx_tokens(text: str) -> int:
    return int(len(text.split()) * 1.3)


TARGET_TOKENS = 400
OVERLAP_TOKENS = 50
_OVERLAP_WORDS = int(OVERLAP_TOKENS / 1.3)  # ~38 words


@dataclass
class Chunk:
    file_path: str
    chunk_index: int
    content: str
    token_count: int


def _split_by_headers(text: str) -> list[str]:
    """
    Split markdown into sections at each ATX header (# through ######).
    Returns a list of strings — each section starts with its header,
    or is preamble content that precedes the first header.
    """
    header_re = re.compile(r"^#{1,6}\s+", re.MULTILINE)
    positions = [m.start() for m in header_re.finditer(text)]

    if not positions:
        return [text.strip()] if text.strip() else []

    sections: list[str] = []

    # Preamble before first header
    if positions[0] > 0:
        preamble = text[: positions[0]].strip()
        if preamble:
            sections.append(preamble)

    for i, start in enumerate(positions):
        end = positions[i + 1] if i + 1 < len(positions) else len(text)
        section = text[start:end].strip()
        if section:
            sections.append(section)

    return sections


def _tail_words(text: str, n: int) -> str:
    """Return the last n words of text as an overlap seed."""
    words = text.split()
    return " ".join(words[-n:]) if len(words) > n else text


def chunk_text(text: str, file_path: str) -> list[Chunk]:
    """
    Chunk markdown text into ~400-token pieces with 50-token overlap.
    Header boundaries are respected — a section is never split mid-header.
    """
    if not text.strip():
        return []

    sections = _split_by_headers(text)
    chunks: list[Chunk] = []
    current: list[str] = []
    current_tokens = 0
    chunk_idx = 0

    def flush(overlap: str = "") -> None:
        nonlocal chunk_idx, current, current_tokens
        content = "\n\n".join(p for p in current if p).strip()
        if content:
            chunks.append(
                Chunk(
                    file_path=file_path,
                    chunk_index=chunk_idx,
                    content=content,
                    token_count=_approx_tokens(content),
                )
            )
            chunk_idx += 1
        current = [overlap] if overlap else []
        current_tokens = _approx_tokens(overlap) if overlap else 0

    for section in sections:
        section_tokens = _approx_tokens(section)

        if section_tokens > TARGET_TOKENS:
            # Section is too large on its own — flush what we have, then
            # split the section into paragraph-level sub-chunks.
            if current:
                flush()

            paragraphs = [p.strip() for p in section.split("\n\n") if p.strip()]
            for para in paragraphs:
                para_tokens = _approx_tokens(para)
                if current_tokens + para_tokens > TARGET_TOKENS and current:
                    content_so_far = "\n\n".join(current)
                    overlap = _tail_words(content_so_far, _OVERLAP_WORDS)
                    flush(overlap)
                current.append(para)
                current_tokens += para_tokens
        else:
            if current_tokens + section_tokens > TARGET_TOKENS and current:
                content_so_far = "\n\n".join(current)
                overlap = _tail_words(content_so_far, _OVERLAP_WORDS)
                flush(overlap)
            current.append(section)
            current_tokens += section_tokens

    if current:
        flush()

    return chunks


def chunk_file(path: Path) -> list[Chunk]:
    """Read and chunk a single markdown file."""
    try:
        text = path.read_text(encoding="utf-8", errors="replace")
    except Exception:
        return []
    return chunk_text(text, str(path))
