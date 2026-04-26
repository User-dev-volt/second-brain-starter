#!/usr/bin/env python3
"""
session-end-flush.py — Saves session summary, updates project snapshot, and appends
domain learnings on session end.

Claude Code hook: Stop
Runs after every Claude response. Uses a per-session marker so the expensive
Claude API extraction only runs once (on the first Stop after >= 2 user messages).
Project snapshot "Last Touched" is updated on every Stop.
"""
import json
import os
import re
import sys
import tempfile
from datetime import datetime
from pathlib import Path

HOOKS_DIR = Path(__file__).parent
UTILS_DIR = HOOKS_DIR.parent / "scripts" / "utils"
sys.path.insert(0, str(UTILS_DIR))

from vault_router import get_daily_log, get_project_snapshot, get_learnings_file, VAULT_ROOT


def marker_path(session_id: str) -> Path:
    return Path(tempfile.gettempdir()) / f"second-brain-flushed-{session_id}"


def already_flushed(session_id: str) -> bool:
    p = marker_path(session_id)
    if p.exists():
        return True
    try:
        p.touch()
    except Exception:
        pass
    return False


def count_user_messages(transcript_path: str) -> int:
    """Count user messages in the JSONL transcript."""
    try:
        path = Path(transcript_path).expanduser()
        if not path.exists():
            return 0
        count = 0
        with path.open(encoding="utf-8", errors="replace") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    entry = json.loads(line)
                    # Claude Code format: {"type": "user", "message": {"role": "user", ...}}
                    if entry.get("type") == "user" and "message" in entry:
                        count += 1
                except json.JSONDecodeError:
                    pass
        return count
    except Exception:
        return 0


def read_transcript_tail(transcript_path: str, last_n: int = 20) -> str:
    """Read the last N messages from the transcript as text."""
    try:
        path = Path(transcript_path).expanduser()
        if not path.exists():
            return ""
        parts = []
        with path.open(encoding="utf-8", errors="replace") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    entry = json.loads(line)
                    # Claude Code format: top-level "type" is "user" or "assistant"
                    # with content nested inside "message"
                    entry_type = entry.get("type", "")
                    if entry_type not in ("user", "assistant"):
                        continue
                    message = entry.get("message", {})
                    role = message.get("role", entry_type)
                    content = message.get("content", "")
                    if isinstance(content, list):
                        content = " ".join(
                            c.get("text", "") for c in content
                            if isinstance(c, dict) and c.get("type") == "text"
                        )
                    if role and content:
                        parts.append(f"{role.upper()}: {content[:2000]}")
                except json.JSONDecodeError:
                    pass
        return "\n\n".join(parts[-last_n:])
    except Exception:
        return ""


def extract_with_claude(transcript_text: str) -> str:
    """Call Claude API to extract session summary."""
    api_key = os.environ.get("ANTHROPIC_API_KEY", "")
    if not api_key:
        return "⚠️ ANTHROPIC_API_KEY not set — skipped AI extraction."

    try:
        import anthropic

        client = anthropic.Anthropic(api_key=api_key)
        response = client.messages.create(
            model="claude-haiku-4-5-20251001",
            max_tokens=512,
            system=(
                "You are a note-taking assistant. Summarize this session for a developer's personal log. "
                "Output bullet points under these headers:\n"
                "**Decisions:** key choices made\n"
                "**Lessons:** reusable patterns, API findings, or best practices discovered (technical only — skip project-specific one-offs)\n"
                "**Next Actions:** the single most important next physical step\n"
                "Be concise. Skip filler. If a category has nothing, omit it."
            ),
            messages=[{"role": "user", "content": transcript_text}],
        )
        return response.content[0].text.strip()
    except Exception as e:
        return f"⚠️ Extraction failed: {e}"


def parse_section(extracted: str, header: str) -> str:
    """Extract bullet content under a **Header:** section from extracted text."""
    pattern = rf"\*\*{re.escape(header)}:\*\*\s*(.*?)(?=\*\*\w|\Z)"
    match = re.search(pattern, extracted, re.DOTALL)
    if not match:
        return ""
    return match.group(1).strip()


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


def update_snapshot_next_action(cwd: str, next_action_text: str):
    """Replace the ## Next Action section content in the project snapshot."""
    snapshot_path = get_project_snapshot(cwd)
    if not snapshot_path or not next_action_text.strip():
        return
    try:
        text = snapshot_path.read_text(encoding="utf-8")
        new_section = f"## Next Action\n{next_action_text.strip()}\n"
        # Match ## Next Action header + all content until next ## section or --- separator
        updated = re.sub(
            r"## Next Action\n.*?(?=\n## |\n---|\Z)",
            new_section,
            text,
            flags=re.DOTALL,
        )
        if updated != text:
            snapshot_path.write_text(updated, encoding="utf-8")
    except Exception as e:
        sys.stderr.write(f"second-brain: failed to update snapshot next action: {e}\n")


def append_to_learnings(cwd: str, lessons_text: str):
    """Append new lessons to the domain LEARNINGS.md file."""
    if not lessons_text.strip():
        return
    learnings_path = get_learnings_file(cwd)
    if not learnings_path:
        return
    try:
        today = datetime.now().strftime("%Y-%m-%d")
        timestamp = datetime.now().strftime("%H:%M")
        entry = f"\n### Session {today} {timestamp}\n{lessons_text.strip()}\n"
        with learnings_path.open("a", encoding="utf-8") as f:
            f.write(entry)
    except Exception as e:
        sys.stderr.write(f"second-brain: failed to append to learnings: {e}\n")


def append_to_daily_log(content: str, prefix: str):
    today = datetime.now().strftime("%Y-%m-%d")
    log_path = get_daily_log(today)

    timestamp = datetime.now().strftime("%H:%M")
    entry = f"\n## [{prefix}] {timestamp}\n\n{content}\n"

    try:
        with log_path.open("a", encoding="utf-8") as f:
            f.write(entry)
    except Exception as e:
        sys.stderr.write(f"second-brain: failed to write daily log: {e}\n")


def main():
    try:
        data = json.load(sys.stdin)
    except Exception:
        sys.exit(0)

    session_id = data.get("session_id", "unknown")
    cwd = data.get("cwd", os.getcwd())
    transcript_path = data.get("transcript_path", "")

    # Always update snapshot timestamp
    update_snapshot_timestamp(cwd)

    # Always attempt git auto-commit (fast no-op if no .gitaccount or no changes)
    run_git_auto_commit(cwd)

    # Full extraction: only once per session, only if substantial (>= 2 user messages)
    if already_flushed(session_id):
        sys.exit(0)

    msg_count = count_user_messages(transcript_path)
    if msg_count < 2:
        sys.exit(0)

    transcript_text = read_transcript_tail(transcript_path, last_n=20)
    if not transcript_text:
        sys.exit(0)

    extracted = extract_with_claude(transcript_text)

    # Write full summary to daily log
    append_to_daily_log(extracted, "SessionEnd")

    # Update Snapshot.md Next Action from extracted next actions
    next_actions = parse_section(extracted, "Next Actions")
    if next_actions:
        update_snapshot_next_action(cwd, next_actions)

    # Append lessons to domain LEARNINGS.md
    lessons = parse_section(extracted, "Lessons")
    if lessons:
        append_to_learnings(cwd, lessons)


def run_git_auto_commit(cwd: str) -> None:
    """Fire-and-forget auto-commit for projects with .gitaccount config."""
    import subprocess
    script = Path(__file__).parent.parent / "scripts" / "git" / "auto_commit.py"
    if not script.exists():
        return
    try:
        subprocess.run(
            [sys.executable, str(script), "--cwd", cwd],
            capture_output=True,
            timeout=30,
        )
    except Exception as e:
        sys.stderr.write(f"second-brain: git auto-commit failed: {e}\n")


if __name__ == "__main__":
    main()
