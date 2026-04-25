#!/usr/bin/env python3
"""
session-start-context.py — Injects vault memory into conversation on first message.

Claude Code hook: UserPromptSubmit
Output: {"additionalContext": "<memory context>"} or {"additionalContext": ""}
"""
import json
import os
import sys
import tempfile
from pathlib import Path

# Locate context_builder relative to this file
HOOKS_DIR = Path(__file__).parent
UTILS_DIR = HOOKS_DIR.parent / "scripts" / "utils"
sys.path.insert(0, str(UTILS_DIR))

from context_builder import build_context


def marker_path(session_id: str) -> Path:
    return Path(tempfile.gettempdir()) / f"second-brain-injected-{session_id}"


def already_injected(session_id: str) -> bool:
    """Return True if we've already injected context for this session."""
    p = marker_path(session_id)
    if p.exists():
        return True
    try:
        p.touch()
    except Exception:
        pass
    return False


def main():
    try:
        data = json.load(sys.stdin)
    except Exception:
        print(json.dumps({"additionalContext": ""}))
        return

    session_id = data.get("session_id", "unknown")
    cwd = data.get("cwd", os.getcwd())

    # Only inject once per session
    if already_injected(session_id):
        print(json.dumps({"additionalContext": ""}))
        return

    try:
        context = build_context(cwd)
        print(json.dumps({"additionalContext": context}))
    except Exception:
        # Never block a prompt due to hook failure
        print(json.dumps({"additionalContext": ""}))


if __name__ == "__main__":
    main()
