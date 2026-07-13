#!/usr/bin/env python3
"""
session-end-flush.py — AutoSave hook.

Claude Code hook: Stop. Runs after every Claude response and does two cheap things:
  1. Update the project snapshot's "Last Touched" date (if a snapshot exists).
  2. Fire-and-forget git auto-commit for projects with a .gitaccount config (AutoSave).

The per-session Claude extraction that used to write intent signals + a session
summary to the daily log (and auto-update Snapshot "Next Action" / LEARNINGS.md)
was removed 2026-07-13 when the intent system was archived. AutoSave is the only
thing this hook still does. See .claude/_archive/intent-system-2026-07-13/.
"""
import json
import os
import re
import subprocess
import sys
from datetime import datetime
from pathlib import Path

HOOKS_DIR = Path(__file__).parent
UTILS_DIR = HOOKS_DIR.parent / "scripts" / "utils"
sys.path.insert(0, str(UTILS_DIR))

from vault_router import get_project_snapshot


def update_snapshot_timestamp(cwd: str):
    """Update 'Last Touched' in the project snapshot if it exists."""
    snapshot_path = get_project_snapshot(cwd)
    if not snapshot_path:
        return
    try:
        text = snapshot_path.read_text(encoding="utf-8")
        today = datetime.now().strftime("%Y-%m-%d")
        updated = re.sub(
            r"(\*\*Last Touched:\*\*\s*)`.+?`",
            f"**Last Touched:** `{today}`",
            text,
        )
        if updated != text:
            snapshot_path.write_text(updated, encoding="utf-8")
    except Exception as e:
        sys.stderr.write(f"second-brain: failed to update snapshot timestamp: {e}\n")


def run_git_auto_commit(cwd: str) -> None:
    """Fire-and-forget auto-commit for projects with .gitaccount config."""
    script = Path(__file__).parent.parent / "scripts" / "git" / "auto_commit.py"
    if not script.exists():
        return
    try:
        subprocess.run(
            [sys.executable, str(script), "--cwd", cwd, "--autosave"],
            capture_output=True,
            # Generous ceiling: a project may run a build/test "pre_commit_check" gate
            # (see auto_commit.py / .gitaccount) before committing. No-gate repos finish
            # in well under a second, so this only bites when a gate is actually running.
            timeout=270,
        )
    except Exception as e:
        sys.stderr.write(f"second-brain: git auto-commit failed: {e}\n")


def main():
    try:
        data = json.load(sys.stdin)
    except Exception:
        sys.exit(0)

    cwd = data.get("cwd", os.getcwd())

    update_snapshot_timestamp(cwd)
    run_git_auto_commit(cwd)


if __name__ == "__main__":
    main()
