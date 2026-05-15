#!/usr/bin/env python3
"""
memory_reflect_loader.py — Assembles the daily synthesis prompt for /daily-reflect.

Pure file reader — no API calls. Loads the past 30 days of enriched session logs,
current identity documents, and existing proposals, then prints a structured prompt
to stdout for Claude Code to consume via the /daily-reflect slash command.
"""
import sys
from datetime import date, timedelta
from pathlib import Path

SCRIPTS_DIR = Path(__file__).parent
sys.path.insert(0, str(SCRIPTS_DIR / "utils"))
from vault_router import VAULT_ROOT

META = VAULT_ROOT / "00_Meta"
PROPOSALS_PATH = META / "proposals" / "identity_proposals.md"
DAILY_DIR = META / "daily"


def _read(path: Path) -> str:
    if path.exists():
        return path.read_text(encoding="utf-8")
    return f"_(not found: {path})_"


def _load_logs(days: int = 30) -> list[tuple[str, str]]:
    """Load up to `days` daily logs. Returns list of (date_str, content) sorted oldest-first."""
    today = date.today()
    logs = []
    for i in range(days, 0, -1):
        d = today - timedelta(days=i)
        path = DAILY_DIR / f"{d.isoformat()}.md"
        if path.exists():
            logs.append((d.isoformat(), path.read_text(encoding="utf-8")))
    return logs


def _load_proposals_suppression_context() -> str:
    """Load implemented and rejected proposals for suppression context."""
    if not PROPOSALS_PATH.exists():
        return "_(none)_"
    text = PROPOSALS_PATH.read_text(encoding="utf-8")
    # Walk blocks and keep only implemented/rejected entries
    lines_out = []
    current_block: list[str] = []
    for line in text.splitlines():
        current_block.append(line)
        if line.strip().startswith("**Status:**"):
            status = line.split("**Status:**")[-1].strip()
            if status.startswith("implemented") or status.startswith("rejected"):
                lines_out.extend(current_block)
                lines_out.append("")
            current_block = []
    return "\n".join(lines_out) if lines_out else "_(none)_"


def main():
    logs = _load_logs(30)
    yesterday_str = (date.today() - timedelta(days=1)).isoformat()

    yesterday_content = next((c for d, c in logs if d == yesterday_str), None)

    soul = _read(META / "SOUL.md")
    user = _read(META / "user.md")
    intent = _read(META / "intent.md")
    workflow = _read(META / "workflow.md")
    proposals_ctx = _load_proposals_suppression_context()

    print("=" * 70)
    print("DAILY REFLECT — SYNTHESIS CONTEXT")
    print(f"Primary date: {yesterday_str}")
    print(f"Log window: {len(logs)} day(s) loaded")
    print("=" * 70)

    print("\n## IDENTITY DOCUMENTS\n")
    print(f"### soul.md\n{soul}\n")
    print(f"### user.md\n{user}\n")
    print(f"### intent.md\n{intent}\n")
    print(f"### workflow.md\n{workflow}\n")

    print("\n## EXISTING PROPOSALS (implemented + rejected — for suppression)\n")
    print(proposals_ctx)

    print("\n## SESSION LOGS\n")
    if yesterday_content:
        print(f"### {yesterday_str} (PRIMARY — yesterday)\n{yesterday_content}\n")
    else:
        print(f"_(no log found for {yesterday_str})_\n")

    other_logs = [(d, c) for d, c in logs if d != yesterday_str]
    if other_logs:
        print("### Supporting context (last 30 days)\n")
        for d, c in other_logs:
            print(f"#### {d}\n{c}\n")

    print("\n## END OF CONTEXT")
    print("=" * 70)


if __name__ == "__main__":
    main()
