"""
run_daily_reflect.py — Headless nightly /daily-reflect.

Scheduled-task entry point (SecondBrainDailyReflect). Spawns a headless Claude Code
session in the second-brain-starter repo and runs the /daily-reflect command, so
proposal synthesis happens automatically instead of waiting for a manual session.
Output is logged to .claude/data/logs/daily-reflect-YYYY-MM-DD.log.

Replaces memory_reflect.py (which only printed a reminder) as the scheduled entry
point — memory_reflect.py remains for manual checks.
"""
import subprocess
import sys
from datetime import datetime
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
LOG_DIR = REPO_ROOT / ".claude" / "data" / "logs"
BRAIN = r"D:\Brain"
TIMEOUT_S = 30 * 60


def main() -> int:
    LOG_DIR.mkdir(parents=True, exist_ok=True)
    log_path = LOG_DIR / f"daily-reflect-{datetime.now():%Y-%m-%d}.log"

    cmd = [
        "cmd", "/c", "claude",
        "-p", "/daily-reflect",
        "--add-dir", BRAIN,
        "--permission-mode", "acceptEdits",
    ]

    with log_path.open("a", encoding="utf-8") as log:
        log.write(f"\n=== run_daily_reflect {datetime.now():%Y-%m-%d %H:%M} ===\n")
        log.flush()
        try:
            result = subprocess.run(
                cmd,
                cwd=REPO_ROOT,
                stdout=log,
                stderr=subprocess.STDOUT,
                timeout=TIMEOUT_S,
            )
            log.write(f"\n=== exit code {result.returncode} ===\n")
            return result.returncode
        except subprocess.TimeoutExpired:
            log.write(f"\n=== TIMEOUT after {TIMEOUT_S}s ===\n")
            return 1
        except Exception as e:
            log.write(f"\n=== FAILED to launch: {e} ===\n")
            return 1


if __name__ == "__main__":
    sys.exit(main())
