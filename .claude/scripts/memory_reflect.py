"""
memory_reflect.py — Daily reflection: promote yesterday's session log to long-term memory.

Runs daily at 8 AM EST (via Windows Task Scheduler — see setup_scheduler.bat).

Workflow:
  1. Load yesterday's daily log from 00_Meta/daily/YYYY-MM-DD.md
  2. Call Claude to identify items worth promoting:
       - decisions      → appended to MEMORY.md
       - learnings      → logged to 20_Reference/GameDev/learnings/<category>.md
       - ideas          → appended to 00_Meta/ideas/_backlog.md
  3. Archive yesterday's HABITS checklist into HABITS.md history section
  4. Reset HABITS.md pillars to unchecked for today
"""

import os
import sys
import json
from datetime import date, timedelta, datetime
from pathlib import Path

SCRIPTS_DIR = Path(__file__).parent
sys.path.insert(0, str(SCRIPTS_DIR / "utils"))
sys.path.insert(0, str(SCRIPTS_DIR / "integrations"))

import vault_router

VAULT_ROOT = vault_router.VAULT_ROOT


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _load_daily_log(for_date: date) -> str | None:
    """Load a daily log file. Returns None if it doesn't exist."""
    path = VAULT_ROOT / "00_Meta" / "daily" / f"{for_date.isoformat()}.md"
    if path.exists():
        return path.read_text(encoding="utf-8")
    return None


def _load_soul() -> str:
    path = VAULT_ROOT / "00_Meta" / "SOUL.md"
    return path.read_text(encoding="utf-8") if path.exists() else ""


def _append_to_memory_md(content: str):
    """Append a decision/fact to MEMORY.md."""
    memory_path = VAULT_ROOT / "00_Meta" / "MEMORY.md"
    today = date.today().isoformat()
    entry = f"\n## {today} — Promoted from daily log\n{content.strip()}\n"
    with open(memory_path, "a", encoding="utf-8") as f:
        f.write(entry)


# ---------------------------------------------------------------------------
# HABITS archive + reset
# ---------------------------------------------------------------------------

def _archive_and_reset_habits(yesterday: date):
    """
    Archive yesterday's checklist state into HABITS.md ## History section,
    then reset all pillars to unchecked for today.
    """
    import re

    habits_path = VAULT_ROOT / "00_Meta" / "HABITS.md"
    if not habits_path.exists():
        return

    content = habits_path.read_text(encoding="utf-8")

    # Extract current pillar states
    pillar_pattern = r"- \[([ x])\] \*\*(.+?)\*\*"
    pillars = re.findall(pillar_pattern, content)

    if pillars:
        archive_lines = [f"\n### {yesterday.isoformat()}"]
        for checked, name in pillars:
            status = "✓" if checked == "x" else "✗"
            archive_lines.append(f"- {status} {name}")
        archive_block = "\n".join(archive_lines)

        # Insert into ## History section (create if missing)
        if "## History" in content:
            content = content.replace("## History", f"## History{archive_block}")
        else:
            content += f"\n## History{archive_block}\n"

    # Reset all pillars to unchecked
    content = re.sub(r"- \[x\] \*\*", "- [ ] **", content)

    habits_path.write_text(content, encoding="utf-8")
    print(f"[reflect] HABITS archived for {yesterday} and reset.", file=sys.stderr)


# ---------------------------------------------------------------------------
# Parse Claude promotions
# ---------------------------------------------------------------------------

def _parse_promotions(response_text: str) -> list[dict]:
    """
    Parse Claude's JSON response into a list of promotion items.
    Each item: {"type": "learning"|"decision"|"idea", "content": str, "category": str, "source_project": str}
    """
    text = response_text.strip()
    if text.startswith("```"):
        text = text.split("```")[1]
        if text.startswith("json"):
            text = text[4:]

    try:
        data = json.loads(text)
        return data.get("promotions", [])
    except (json.JSONDecodeError, AttributeError):
        print(f"[reflect] Could not parse Claude response:\n{response_text[:300]}", file=sys.stderr)
        return []


# ---------------------------------------------------------------------------
# Main reflection
# ---------------------------------------------------------------------------

def reflect(target_date: date | None = None):
    yesterday = target_date or (date.today() - timedelta(days=1))
    print(f"[reflect] {datetime.now().strftime('%Y-%m-%d %H:%M')} — reflecting on {yesterday}", file=sys.stderr)

    # 1. Load yesterday's log
    log_text = _load_daily_log(yesterday)
    if not log_text:
        print(f"[reflect] No daily log found for {yesterday} — skipping.", file=sys.stderr)
        _archive_and_reset_habits(yesterday)
        return

    # 2. Call Claude
    try:
        import anthropic
    except ImportError:
        print("[reflect] anthropic package not installed.", file=sys.stderr)
        _archive_and_reset_habits(yesterday)
        return

    api_key = os.environ.get("ANTHROPIC_API_KEY", "")
    if not api_key:
        try:
            import winreg
            with winreg.OpenKey(winreg.HKEY_CURRENT_USER, "Environment") as reg:
                api_key, _ = winreg.QueryValueEx(reg, "ANTHROPIC_API_KEY")
        except Exception:
            pass
    if not api_key:
        print("[reflect] ANTHROPIC_API_KEY not set — skipped.", file=sys.stderr)
        _archive_and_reset_habits(yesterday)
        return
    client = anthropic.Anthropic(api_key=api_key)
    soul = _load_soul()

    prompt = f"""You are reviewing Alec's session log from {yesterday}. Identify items worth promoting to long-term memory.

Promote only genuinely important facts — be selective. Categories:
- "learning": a code pattern, technique, or workflow insight (add a "category" field: "godot-csharp", "comfyui", "unity", or "general")
- "decision": a key project or architectural decision that future sessions should know about
- "idea": a product or game mechanic idea worth capturing (add a "source_project" field if mentioned)

Session log:
{log_text}

Respond ONLY with valid JSON:
{{
  "promotions": [
    {{
      "type": "learning",
      "content": "...",
      "category": "godot-csharp"
    }},
    {{
      "type": "decision",
      "content": "..."
    }},
    {{
      "type": "idea",
      "content": "...",
      "source_project": "moviebuilder"
    }}
  ]
}}

Return an empty array if nothing is worth promoting."""

    try:
        response = client.messages.create(
            model="claude-sonnet-4-6",
            max_tokens=1024,
            system=soul or "You are Alec's AI second brain assistant.",
            messages=[{"role": "user", "content": prompt}],
        )
        promotions = _parse_promotions(response.content[0].text)
    except Exception as e:
        print(f"[reflect] Claude call failed: {e}", file=sys.stderr)
        promotions = []

    # 3. Apply promotions
    if not promotions:
        print("[reflect] Nothing to promote today.", file=sys.stderr)
    else:
        from obsidian import log_learning, capture_idea

        for item in promotions:
            ptype = item.get("type")
            content = item.get("content", "").strip()
            if not content:
                continue

            if ptype == "learning":
                category = item.get("category", "general")
                log_learning(content, category)
                print(f"[reflect] Promoted learning → {category}", file=sys.stderr)

            elif ptype == "decision":
                _append_to_memory_md(content)
                print("[reflect] Promoted decision → MEMORY.md", file=sys.stderr)

            elif ptype == "idea":
                source = item.get("source_project", "")
                capture_idea(content, source)
                print(f"[reflect] Promoted idea (source: {source or 'unknown'})", file=sys.stderr)

    # 4. Archive HABITS and reset for today
    _archive_and_reset_habits(yesterday)
    print("[reflect] Done.", file=sys.stderr)


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Run daily reflection for a given date")
    parser.add_argument(
        "--date",
        help="Date to reflect on (YYYY-MM-DD). Defaults to yesterday.",
        default=None,
    )
    args = parser.parse_args()

    target = None
    if args.date:
        target = date.fromisoformat(args.date)

    reflect(target)
