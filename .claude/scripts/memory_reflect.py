"""
memory_reflect.py — Lightweight daily maintenance: archive HABITS, reset for today.

The AI synthesis (promotions, proposals) has moved to the /daily-reflect slash command,
which routes expensive work through the Claude Code subscription rather than the API.

This script handles only the non-AI daily chores:
  1. Note whether yesterday's log exists
  2. Archive yesterday's HABITS checklist into HABITS.md history section
  3. Reset HABITS.md pillars to unchecked for today

Run manually or keep as a Task Scheduler job for the HABITS reset only.
For full synthesis, open a terminal and run /daily-reflect.
"""

import re
import sys
from datetime import date, timedelta, datetime
from pathlib import Path

SCRIPTS_DIR = Path(__file__).parent
sys.path.insert(0, str(SCRIPTS_DIR / "utils"))
import vault_router

VAULT_ROOT = vault_router.VAULT_ROOT


def _archive_and_reset_habits(yesterday: date):
    """
    Archive yesterday's checklist state into HABITS.md ## History section,
    then reset all pillars to unchecked for today.
    """
    habits_path = VAULT_ROOT / "00_Meta" / "HABITS.md"
    if not habits_path.exists():
        return

    content = habits_path.read_text(encoding="utf-8")

    pillar_pattern = r"- \[([ x])\] \*\*(.+?)\*\*"
    pillars = re.findall(pillar_pattern, content)

    if pillars:
        archive_lines = [f"\n### {yesterday.isoformat()}"]
        for checked, name in pillars:
            status = "✓" if checked == "x" else "✗"
            archive_lines.append(f"- {status} {name}")
        archive_block = "\n".join(archive_lines)

        if "## History" in content:
            content = content.replace("## History", f"## History{archive_block}")
        else:
            content += f"\n## History{archive_block}\n"

    content = re.sub(r"- \[x\] \*\*", "- [ ] **", content)
    habits_path.write_text(content, encoding="utf-8")
    print(f"[reflect] HABITS archived for {yesterday} and reset.", file=sys.stderr)


def reflect(target_date: date | None = None):
    yesterday = target_date or (date.today() - timedelta(days=1))
    print(
        f"[reflect] {datetime.now().strftime('%Y-%m-%d %H:%M')} — archiving habits for {yesterday}",
        file=sys.stderr,
    )

    log_path = VAULT_ROOT / "00_Meta" / "daily" / f"{yesterday.isoformat()}.md"
    if not log_path.exists():
        print(f"[reflect] No daily log found for {yesterday}.", file=sys.stderr)

    _archive_and_reset_habits(yesterday)
    print("[reflect] Done. Run /daily-reflect for AI synthesis.", file=sys.stderr)


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Archive HABITS for a given date")
    parser.add_argument(
        "--date",
        help="Date to archive (YYYY-MM-DD). Defaults to yesterday.",
        default=None,
    )
    args = parser.parse_args()

    target = None
    if args.date:
        target = date.fromisoformat(args.date)

    reflect(target)
