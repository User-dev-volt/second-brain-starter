#!/usr/bin/env python3
"""
weekly_dream_loader.py — Assembles the weekly dream synthesis prompt for /weekly-dream.

Pure file reader — no API calls. Loads the past 7 days of enriched session logs,
current identity documents, all proposals from the past 30 days (not just
implemented/rejected — the full picture for cross-session pattern synthesis),
then prints a structured prompt to stdout for Claude Code to consume via the
/weekly-dream slash command.

Differs from memory_reflect_loader.py in three ways:
  1. Primary window is 7 days (not 1 day highlighted + 29 supporting)
  2. Full proposal history loaded (not suppression context only) — weekly
     synthesis needs to see pending proposals to avoid re-proposing them
  3. Header signals this is a deep cross-session pass, not a daily reflect
"""
import sys
sys.stdout.reconfigure(encoding="utf-8")
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


def _load_logs(days: int) -> list[tuple[str, str]]:
    """Load up to `days` daily logs. Returns list of (date_str, content) sorted oldest-first."""
    today = date.today()
    logs = []
    for i in range(days, 0, -1):
        d = today - timedelta(days=i)
        path = DAILY_DIR / f"{d.isoformat()}.md"
        if path.exists():
            logs.append((d.isoformat(), path.read_text(encoding="utf-8")))
    return logs


def _load_full_proposals(days: int = 30) -> str:
    """Load full proposal history for cross-session synthesis context."""
    if not PROPOSALS_PATH.exists():
        return "_(none)_"
    text = PROPOSALS_PATH.read_text(encoding="utf-8")
    if not text.strip():
        return "_(none)_"
    return text


def main():
    week_logs = _load_logs(7)
    support_logs = _load_logs(30)

    today = date.today()
    week_start = (today - timedelta(days=7)).isoformat()
    week_end = (today - timedelta(days=1)).isoformat()

    soul = _read(META / "SOUL.md")
    user = _read(META / "user.md")
    intent = _read(META / "intent.md")
    workflow = _read(META / "workflow.md")
    proposals = _load_full_proposals(30)

    print("=" * 70)
    print("WEEKLY DREAM — SYNTHESIS CONTEXT")
    print(f"Week window: {week_start} → {week_end}")
    print(f"Primary logs: {len(week_logs)} day(s) | Supporting context: {len(support_logs)} day(s)")
    print("=" * 70)

    print("\n## IDENTITY DOCUMENTS\n")
    print(f"### soul.md\n{soul}\n")
    print(f"### user.md\n{user}\n")
    print(f"### intent.md\n{intent}\n")
    print(f"### workflow.md\n{workflow}\n")

    print("\n## ALL PROPOSALS (last 30 days — pending + implemented + rejected)\n")
    print(proposals)

    print("\n## THIS WEEK'S SESSION LOGS (primary synthesis window)\n")
    if week_logs:
        for d, c in week_logs:
            print(f"### {d}\n{c}\n")
    else:
        print("_(no logs found for this week)_\n")

    support_only = [(d, c) for d, c in support_logs if d not in {d for d, _ in week_logs}]
    if support_only:
        print("\n## OLDER CONTEXT (days 8–30 — cross-session reference only)\n")
        for d, c in support_only:
            print(f"#### {d}\n{c}\n")

    print("\n## END OF CONTEXT")
    print("=" * 70)


if __name__ == "__main__":
    main()
