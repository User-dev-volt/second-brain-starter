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
from standing_order_reader import get_standing_orders_context


def read_file_safe(path, max_lines: int = None) -> str:
    """Read a file, return empty string if missing or unreadable."""
    try:
        text = Path(path).read_text(encoding="utf-8", errors="replace")
        if max_lines:
            lines = text.splitlines()
            text = "\n".join(lines[-max_lines:])
        return text.strip()
    except Exception:
        return ""


def get_last_daily_logs(n: int = 3) -> str:
    """Read the last n daily logs (most recent first), last 100 lines each."""
    daily_dir = VAULT_ROOT / "00_Meta" / "daily"
    if not daily_dir.exists():
        return ""

    logs = sorted(daily_dir.glob("*.md"), reverse=True)[:n]
    parts = []
    for log_path in logs:
        content = read_file_safe(log_path, max_lines=100)
        if content:
            parts.append(f"### {log_path.stem}\n{content}")
    return "\n\n".join(parts)


def get_bmad_status_files(cwd: str) -> list[Path]:
    """
    If cwd is inside a BMAD project (has _bmad-output/ directory), return the
    paths to sprint-status.yaml, epics.md, and bmm/config.yaml so they can be
    pre-loaded once at session start — preventing repeated re-reads mid-session.
    Returns [] if not a BMAD project or files are missing.
    """
    cwd_path = Path(cwd)
    # Walk up until we find a directory containing _bmad-output/
    for parent in [cwd_path, *cwd_path.parents]:
        bmad_dir = parent / "_bmad-output"
        if bmad_dir.is_dir():
            candidates = [
                bmad_dir / "implementation-artifacts" / "sprint-status.yaml",
                bmad_dir / "planning-artifacts" / "epics.md",
                # bmm config never changes session-to-session — inject once
                parent / "_bmad" / "bmm" / "config.yaml",
            ]
            return [p for p in candidates if p.exists()]
    return []


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

    # Standing Orders — active agent directives from intent.md (injected early so
    # agents see directives before project-specific context)
    try:
        standing_orders = get_standing_orders_context(VAULT_ROOT)
        if standing_orders:
            sections.append(standing_orders)
    except Exception:
        pass

    # Project snapshot (if cwd matches a known project)
    if r["project_snapshot"]:
        content = read_file_safe(r["project_snapshot"])
        if content:
            project_name = Path(r["project_snapshot"]).parent.name
            sections.append(f"## Project Snapshot: {project_name}\n{content}")

    # Domain-specific learnings (Godot, Products, ComfyUI, AI, etc.)
    if r["learnings_file"]:
        content = read_file_safe(r["learnings_file"], max_lines=200)
        if content:
            domain = Path(r["learnings_file"]).parent.name
            sections.append(f"## {domain} Learnings\n{content}")

    # BMAD project: pre-load sprint-status + epics live from disk (once per session).
    # This prevents repeated re-reads mid-session without using stale summaries.
    bmad_files = get_bmad_status_files(cwd)
    if bmad_files:
        bmad_parts = []
        for f in bmad_files:
            content = read_file_safe(f)
            if content:
                bmad_parts.append(f"### {f.name}\n{content}")
        if bmad_parts:
            sections.append(
                "## BMAD Project Status (live — do not re-read these files during this session)\n\n"
                + "\n\n---\n\n".join(bmad_parts)
            )

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
