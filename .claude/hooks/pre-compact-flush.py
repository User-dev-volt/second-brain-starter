#!/usr/bin/env python3
"""
pre-compact-flush.py — Extracts key learnings from the conversation before compaction.

Claude Code hook: PreCompact
Calls Claude API to distill decisions, lessons, and next actions, then appends
them to today's daily log in the vault.
"""
import json
import os
import sys
from datetime import datetime
from pathlib import Path

HOOKS_DIR = Path(__file__).parent
UTILS_DIR = HOOKS_DIR.parent / "scripts" / "utils"
sys.path.insert(0, str(UTILS_DIR))

from vault_router import get_daily_log


def read_transcript(data: dict) -> str:
    """Extract readable transcript text from hook input."""
    # PreCompact may include a messages array directly
    messages = data.get("messages", [])
    if messages:
        parts = []
        for msg in messages:
            role = msg.get("role", "")
            content = msg.get("content", "")
            if isinstance(content, list):
                content = " ".join(
                    c.get("text", "") for c in content
                    if isinstance(c, dict) and c.get("type") == "text"
                )
            if role and content:
                parts.append(f"{role.upper()}: {content[:2000]}")
        return "\n\n".join(parts)

    # Fall back to transcript_path (JSONL file)
    transcript_path = data.get("transcript_path", "")
    if not transcript_path:
        return ""

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
                    msg = json.loads(line)
                    role = msg.get("role", "")
                    content = msg.get("content", "")
                    if isinstance(content, list):
                        content = " ".join(
                            c.get("text", "") for c in content
                            if isinstance(c, dict) and c.get("type") == "text"
                        )
                    if role and content:
                        parts.append(f"{role.upper()}: {content[:2000]}")
                except json.JSONDecodeError:
                    pass
        # Use last 40 exchanges to stay within API limits
        return "\n\n".join(parts[-40:])
    except Exception:
        return ""


def extract_with_claude(transcript_text: str) -> str:
    """Call Claude API to extract key learnings from the transcript."""
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
                "You are a note-taking assistant. Extract ONLY what is worth keeping "
                "from this conversation. Output bullet points under these headers:\n"
                "**Decisions:** key choices made\n"
                "**Lessons:** things that worked or didn't\n"
                "**Next Actions:** concrete next steps\n"
                "Be concise. Skip filler. If a category has nothing, omit it."
            ),
            messages=[{"role": "user", "content": transcript_text}],
        )
        return response.content[0].text.strip()
    except Exception as e:
        return f"⚠️ Extraction failed: {e}"


def append_to_daily_log(content: str, prefix: str, cwd: str):
    today = datetime.now().strftime("%Y-%m-%d")
    log_path = get_daily_log(today)

    timestamp = datetime.now().strftime("%H:%M")
    entry = f"\n## [{prefix}] {timestamp}\n\n{content}\n"

    try:
        with log_path.open("a", encoding="utf-8") as f:
            f.write(entry)
    except Exception as e:
        sys.stderr.write(f"second-brain: failed to write daily log: {e}\n")


def snapshot_bmad_state(cwd: str) -> str:
    """
    If a BMAD project is active in cwd, return a structured state snapshot
    to inject into the compaction summary so the orchestrator can recover.
    Returns empty string if no BMAD project detected.
    """
    cwd_path = Path(cwd)
    bmad_output = cwd_path / "_bmad-output"
    if not bmad_output.exists():
        return ""

    lines = ["=== BMAD_STATE_SNAPSHOT (survive compaction) ==="]
    lines.append(f"project_root: {cwd}")

    # project-intent.md
    intent = bmad_output / "project-intent.md"
    if intent.exists():
        lines.append("project_intent: PRESENT")

    # planning artifacts — read frontmatter stepsCompleted from each
    planning = bmad_output / "planning-artifacts"
    if planning.exists():
        for artifact in sorted(planning.glob("*.md")):
            try:
                text = artifact.read_text(encoding="utf-8", errors="replace")
                # Extract stepsCompleted or workflowStatus from frontmatter
                import re
                steps = re.search(r"stepsCompleted:\s*(.+)", text)
                status = re.search(r"workflowStatus:\s*(.+)", text)
                info = []
                if steps:
                    info.append(f"steps={steps.group(1).strip()}")
                if status:
                    info.append(f"status={status.group(1).strip()}")
                lines.append(f"artifact: {artifact.name} [{', '.join(info) if info else 'present'}]")
            except Exception:
                lines.append(f"artifact: {artifact.name}")

    # sprint-status.yaml
    sprint = bmad_output / "implementation-artifacts" / "sprint-status.yaml"
    if sprint.exists():
        try:
            sprint_text = sprint.read_text(encoding="utf-8", errors="replace")
            # Extract in-progress story if any
            import re
            in_progress = re.findall(r"(\S+):\s*in-progress", sprint_text)
            ready = re.findall(r"(\S+):\s*ready-for-dev", sprint_text)
            if in_progress:
                lines.append(f"sprint_in_progress: {in_progress}")
            if ready:
                lines.append(f"sprint_ready_for_dev: {ready[:3]}")  # first 3
        except Exception:
            lines.append("sprint_status: present")

    lines.append("RECOVERY_INSTRUCTION: On next turn, the BMAD Orchestrator must read")
    lines.append("project-intent.md and all planning artifact frontmatter to reconstruct")
    lines.append("state before continuing. Do NOT assume prior conversation memory is intact.")
    lines.append("=== END BMAD_STATE_SNAPSHOT ===")

    return "\n".join(lines)


def main():
    try:
        data = json.load(sys.stdin)
    except Exception:
        sys.exit(0)

    cwd = data.get("cwd", os.getcwd())
    transcript_text = read_transcript(data)

    # Always try to snapshot BMAD state for the compaction summary
    bmad_snapshot = snapshot_bmad_state(cwd)

    if not transcript_text:
        if bmad_snapshot:
            print(json.dumps({"additionalContext": bmad_snapshot}))
        sys.exit(0)

    extracted = extract_with_claude(transcript_text)
    append_to_daily_log(extracted, "PreCompact", cwd)

    # Output additionalContext so the compaction summary includes BMAD state
    if bmad_snapshot:
        print(json.dumps({"additionalContext": bmad_snapshot}))


if __name__ == "__main__":
    main()
