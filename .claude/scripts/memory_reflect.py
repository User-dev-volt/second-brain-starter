"""
memory_reflect.py — Lightweight daily maintenance for the scheduled task.

The real synthesis (promotions, proposals) runs through the /daily-reflect slash
command, which routes expensive work through the Claude Code subscription rather
than the API. HABITS tracking was retired 2026-06-02, so this script no longer
mutates any files — it just notes whether yesterday's daily log exists and points
to /daily-reflect for the AI pass.

Kept as the SecondBrainDailyReflect Task Scheduler entry point.
"""

import sys
from datetime import date, timedelta, datetime
from pathlib import Path

SCRIPTS_DIR = Path(__file__).parent
sys.path.insert(0, str(SCRIPTS_DIR / "utils"))
import vault_router

BRAIN_ROOT = vault_router.BRAIN_ROOT


def reflect(target_date: date | None = None):
    yesterday = target_date or (date.today() - timedelta(days=1))
    print(
        f"[reflect] {datetime.now().strftime('%Y-%m-%d %H:%M')} — daily check for {yesterday}",
        file=sys.stderr,
    )

    log_path = BRAIN_ROOT / "00_Meta" / "daily" / f"{yesterday.isoformat()}.md"
    if log_path.exists():
        print(f"[reflect] Daily log present: {log_path}", file=sys.stderr)
    else:
        print(f"[reflect] No daily log found for {yesterday}.", file=sys.stderr)

    print("[reflect] Done. Run /daily-reflect for AI synthesis.", file=sys.stderr)


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Lightweight daily reflect check")
    parser.add_argument(
        "--date",
        help="Date to check (YYYY-MM-DD). Defaults to yesterday.",
        default=None,
    )
    args = parser.parse_args()

    target = date.fromisoformat(args.date) if args.date else None
    reflect(target)
