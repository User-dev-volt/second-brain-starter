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


def _get_api_key() -> str:
    """Read API key from env (SECOND_BRAIN_API_KEY preferred, ANTHROPIC_API_KEY fallback), then registry."""
    key = os.environ.get("SECOND_BRAIN_API_KEY") or os.environ.get("ANTHROPIC_API_KEY", "")
    if not key:
        try:
            import winreg
            with winreg.OpenKey(winreg.HKEY_CURRENT_USER, "Environment") as reg:
                try:
                    key, _ = winreg.QueryValueEx(reg, "SECOND_BRAIN_API_KEY")
                except FileNotFoundError:
                    key, _ = winreg.QueryValueEx(reg, "ANTHROPIC_API_KEY")
        except Exception:
            pass
    return key


def detect_session_mode(cwd: str, transcript_text: str) -> str:
    """Classify the session: 'bmad' (methodology-driven dev), 'work' (day-job /
    Excel), or 'freeform' (everything else). Used to pick the extraction prompt
    so BMAD's prescribed rituals don't pollute the intent signal."""
    try:
        cwd_path = Path(cwd)
        for parent in [cwd_path, *cwd_path.parents]:
            if (parent / "_bmad").is_dir() or (parent / "_bmad-output").is_dir():
                return "bmad"
    except Exception:
        pass

    t = transcript_text.lower()
    bmad_markers = (
        "/bmad-", "bmad-story-loop", "sprint-status.yaml", "_bmad-output",
        "story-context", "gds-code-review", "/gds-",
    )
    if any(m in t for m in bmad_markers):
        return "bmad"

    cwd_l = str(cwd).lower()
    work_cwd_markers = ("amentum", "drive return")
    work_text_markers = (".xlsx", ".xlsm", "power query", "pivot table", "excel workbook")
    if any(m in cwd_l for m in work_cwd_markers) or any(m in t for m in work_text_markers):
        return "work"

    return "freeform"


MODE_PROMPTS = {
    "bmad": (
        "MODE: BMAD. This session executed Alec's BMAD methodology. The following are "
        "PRESCRIBED steps that repeat by design — do NOT report them as intent signals, "
        "AI gaps, or scope expansions: story-first authoring, parallel/exhaustive artifact "
        "loading, adversarial multi-layer code review with a different LLM, pre-existing "
        "failure baseline cataloguing, patch/defer/dismiss triage gates, sprint status "
        "updates. ONLY report: (1) deviations from the methodology, (2) choices the "
        "methodology leaves open (architecture, scope, naming, data-model decisions), "
        "(3) Alec redirecting an agent, (4) edits to the BMAD workflow itself — those "
        "are the highest-value signal.\n\n"
    ),
    "work": (
        "MODE: WORK (day job, typically Excel/data/reporting — not software development). "
        "Focus extraction on: data-handling decisions, formatting and reporting "
        "preferences, recurring spreadsheet/report patterns, and how Alec structures "
        "deliverables for colleagues. Skip software-engineering framing.\n\n"
    ),
    "freeform": "",
}


def extract_with_claude(transcript_text: str, cwd: str = "", mode: str = "freeform") -> str:
    """Call Claude API to extract session summary with enriched intent signals (Stage 1) and
    traditional summary sections (Stage 2). The prompt adapts to the detected session mode."""
    api_key = _get_api_key()
    if not api_key:
        return "⚠️ ANTHROPIC_API_KEY not set — skipped AI extraction."

    project_name = Path(cwd).name if cwd else "unknown"

    try:
        import anthropic

        client = anthropic.Anthropic(api_key=api_key)
        response = client.messages.create(
            model="claude-haiku-4-5-20251001",
            max_tokens=800,
            system=(
                "You are a behavioral intent logger for a developer's second brain. "
                + MODE_PROMPTS.get(mode, "")
                + "Analyze this session transcript and output TWO sections in order:\n\n"
                "--- SECTION 1: Intent signals ---\n"
                f"Project: {project_name}\n"
                f"Session mode (detected): {mode}\n"
                "Session goal: [one line — what this session set out to accomplish]\n"
                "Session type: designing | building | debugging | exploring\n\n"
                "**Critical moments:**\n"
                "(Any 'actually', 'wait', 'stop', or mid-session self-correction)\n"
                "- [what was happening] → [what was corrected to] — \"[words used]\"\n"
                "If none, write: (none)\n\n"
                "**AI choices + responses:**\n"
                "(Binary or multiple-choice questions the AI asked, and what the user picked)\n"
                "- Offered: [option A] vs [option B] → Chose: [choice] — \"[reason if stated]\"\n"
                "  Tradeoff: [control vs. convenience | ownership vs. delegation | speed vs. durability | depth vs. breadth | manual vs. automated | local vs. cloud | explicit vs. implicit]\n"
                "If none, write: (none)\n\n"
                "**AI gaps (Claude default → Alec preference):**\n"
                "(Where Claude was heading in one direction and the user redirected)\n"
                "- Claude heading toward: [X] → Alec redirected to: [Y]\n"
                "  Gap type: [tradeoff type]\n"
                "If none, write: (none)\n\n"
                "**Scope expansions (unprompted additions):**\n"
                "(Things the user added that weren't in the original request)\n"
                "- Added: [what] — [context]\n"
                "If none, write: (none)\n\n"
                "**Scope constraints (explicit deferrals):**\n"
                "(Things the user explicitly said to skip or defer)\n"
                "- Deferred: [what] — \"[reason]\"\n"
                "If none, write: (none)\n\n"
                "**Pattern confirmations / overrides:**\n"
                "(Moments where the assistant cited an intent pattern or Standing Order — "
                "e.g. \"Per your [pattern]...\" — and the user accepted or overrode it)\n"
                "- Pattern confirmed: [name] — [context]\n"
                "- Pattern overridden: [name] → [what the user chose instead] — \"[words used]\"\n"
                "If none, write: (none)\n\n"
                "--- SECTION 2: Session summary ---\n"
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

    mode = detect_session_mode(cwd, transcript_text)
    extracted = extract_with_claude(transcript_text, cwd=cwd, mode=mode)

    # Write full enriched summary (Stage 1 intent signals + Stage 2 summary) to daily log
    append_to_daily_log(extracted, f"SessionEnd:{mode}")

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
