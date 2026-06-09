"""
register_tasks.py — Register Windows Scheduled Tasks for the Second Brain.

Run once as Administrator:
    python .claude/scripts/setup/register_tasks.py

To remove tasks:
    python .claude/scripts/setup/register_tasks.py --remove
"""

import argparse
import subprocess
import sys
from pathlib import Path

# ── Paths ────────────────────────────────────────────────────────────────────
# Resolve relative to the repo root (two levels up from this file)
REPO_ROOT = Path(__file__).resolve().parents[3]
SCRIPTS_DIR = REPO_ROOT / ".claude" / "scripts"
PYTHON = REPO_ROOT / ".venv" / "Scripts" / "python.exe"

# Fall back to system python if venv doesn't exist yet
if not PYTHON.exists():
    PYTHON = Path(sys.executable)

# ── Task definitions ─────────────────────────────────────────────────────────
# (name, script, schedule, /mo interval or None, start time, end time or None)
# NOTE: Heartbeat was retired 2026-06-02 (proactive monitor + HABITS removed).
# heartbeat.py remains on disk but is intentionally NOT scheduled.
TASKS = [
    {
        "name": "SecondBrainDailyReflect",  # root path; matches the live task we kept
        # Headless claude -p "/daily-reflect" (replaces print-only memory_reflect.py
        # as the scheduled entry point, 2026-06-09)
        "script": SCRIPTS_DIR / "run_daily_reflect.py",
        "schedule": "daily",
        "interval": None,
        "start": "08:00",
        "end": None,
        "kill_at_end": False,
    },
]


def register(task: dict) -> bool:
    cmd = [
        "schtasks", "/create",
        "/tn", task["name"],
        "/tr", f'"{PYTHON}" "{task["script"]}"',
        "/sc", task["schedule"],
        "/st", task["start"],
        "/f",  # overwrite if exists
    ]
    if task["interval"]:
        cmd += ["/mo", task["interval"]]
    if task["end"]:
        cmd += ["/et", task["end"]]
    if task["kill_at_end"]:
        cmd += ["/k"]

    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode == 0:
        print(f"  OK   {task['name']}")
        return True
    else:
        print(f"  FAIL {task['name']}: {result.stderr.strip() or result.stdout.strip()}")
        return False


def remove(task: dict) -> bool:
    result = subprocess.run(
        ["schtasks", "/delete", "/tn", task["name"], "/f"],
        capture_output=True, text=True,
    )
    if result.returncode == 0:
        print(f"  Removed  {task['name']}")
        return True
    else:
        print(f"  SKIP     {task['name']}: {result.stderr.strip() or result.stdout.strip()}")
        return False


def main() -> None:
    parser = argparse.ArgumentParser(description="Manage Second Brain scheduled tasks.")
    parser.add_argument("--remove", action="store_true", help="Delete all tasks instead of creating them.")
    args = parser.parse_args()

    if args.remove:
        print("Removing scheduled tasks...")
        for task in TASKS:
            remove(task)
    else:
        print(f"Using Python: {PYTHON}")
        print(f"Scripts dir:  {SCRIPTS_DIR}")
        print()
        print("Registering scheduled tasks (requires Administrator)...")
        ok = all(register(task) for task in TASKS)
        print()
        if ok:
            print("All tasks registered. Verify in Task Scheduler under SecondBrain\\.")
            print()
            print("To test manually:")
            print(f'  python "{SCRIPTS_DIR / "heartbeat.py"}"')
            print(f'  python "{SCRIPTS_DIR / "memory_reflect.py"}"')
        else:
            print("Some tasks failed. Re-run as Administrator.")
            sys.exit(1)


if __name__ == "__main__":
    main()
