"""
context_builder.py — Assembles vault memory into a context string for session injection.
"""
import sys
import os
from pathlib import Path
from datetime import datetime

# Ensure vault_router is importable when this module is used from hooks
sys.path.insert(0, str(Path(__file__).parent))
from vault_router import route, VAULT_ROOT


def read_file_safe(path, max_lines: int = None, head: bool = False) -> str:
    """Read a file, return empty string if missing or unreadable.

    max_lines caps the content. By default the most-recent (tail) lines are kept,
    which is right for append-at-bottom files (daily logs, LEARNINGS). Pass
    head=True to keep the FIRST N lines instead — right for files whose current
    state lives at the top (Snapshot.md: Status / Current Focus / Next Action),
    where the growing tail (Decision Log, Session History) is what we want to drop.
    """
    try:
        text = Path(path).read_text(encoding="utf-8", errors="replace")
        if max_lines:
            lines = text.splitlines()
            text = "\n".join(lines[:max_lines] if head else lines[-max_lines:])
        return text.strip()
    except Exception:
        return ""


# Signatures of captured tool-less refusals. The session-end / daily-reflect
# hook sometimes fires in a context with no filesystem access, and Claude's
# "I can't run this — here's what I can do instead" reply gets logged as a
# session summary. Pure noise that would otherwise be re-injected into every
# future session, so drop any SessionEnd block whose body matches these.
_REFUSAL_SIGNATURES = (
    "i cannot execute",
    "what i can do instead",
    "i need to pause here",
    "no python runtime",
    "without filesystem access",
    "language model without",
    "which would be most useful right now",
)


def filter_refusal_blocks(text: str) -> str:
    """Drop '## [SessionEnd:...]' sections whose body is a captured refusal."""
    current: list[str] = []
    blocks: list[str] = []

    def flush():
        if not current:
            return
        is_session_end = current[0].lstrip().startswith("## [SessionEnd")
        body = "\n".join(current).lower()
        if is_session_end and any(sig in body for sig in _REFUSAL_SIGNATURES):
            return  # skip this block entirely
        blocks.append("\n".join(current))

    for line in text.splitlines():
        if line.lstrip().startswith("## [SessionEnd"):
            flush()
            current = [line]
        else:
            current.append(line)
    flush()
    return "\n".join(blocks).strip()


def get_last_daily_logs(n: int = 3) -> str:
    """Read the last n daily logs (most recent first), captured-refusal blocks
    removed, then the most-recent 80 lines of what remains for each."""
    daily_dir = VAULT_ROOT / "00_Meta" / "daily"
    if not daily_dir.exists():
        return ""

    logs = sorted(daily_dir.glob("*.md"), reverse=True)[:n]
    parts = []
    for log_path in logs:
        raw = read_file_safe(log_path)
        if not raw:
            continue
        cleaned = filter_refusal_blocks(raw)
        cleaned = "\n".join(cleaned.splitlines()[-80:]).strip()
        if cleaned:
            parts.append(f"### {log_path.stem}\n{cleaned}")
    return "\n\n".join(parts)


def build_context(cwd: str) -> str:
    """
    Build full memory context string for a given working directory.
    Returns empty string if vault is unreachable.
    """
    try:
        r = route(cwd)
    except Exception:
        return ""

    sections = []

    # Core memory: SOUL, USER, MEMORY
    for file_path in r["core_memory"]:
        content = read_file_safe(file_path)
        if content:
            name = Path(file_path).stem
            sections.append(f"## {name}\n{content}")

    # Project snapshot (if cwd matches a known project) — head-capped: the current
    # state (Status / Current Focus / Next Action) lives at the top; the tail
    # (Decision Log, Session History) grows unbounded and is dropped from injection.
    if r["project_snapshot"]:
        content = read_file_safe(r["project_snapshot"], max_lines=120, head=True)
        if content:
            project_name = Path(r["project_snapshot"]).parent.name
            sections.append(f"## Project Snapshot: {project_name}\n{content}")

    # Domain-specific learnings (Godot, Products, ComfyUI, AI, etc.)
    if r["learnings_file"]:
        content = read_file_safe(r["learnings_file"], max_lines=200)
        if content:
            domain = Path(r["learnings_file"]).parent.name
            sections.append(f"## {domain} Learnings\n{content}")

    # Last 3 daily logs
    daily = get_last_daily_logs(3)
    if daily:
        sections.append(f"## Recent Daily Logs\n{daily}")

    if not sections:
        return ""

    header = (
        f"<!-- Second Brain Memory — {datetime.now().strftime('%Y-%m-%d %H:%M')} -->\n"
        f"<!-- Vault: {r['vault_root']} | CWD: {cwd} -->"
    )
    body = "\n\n---\n\n".join(sections)
    return f"{header}\n\n{body}"


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    cwd = sys.argv[1] if len(sys.argv) > 1 else os.getcwd()
    print(build_context(cwd))
