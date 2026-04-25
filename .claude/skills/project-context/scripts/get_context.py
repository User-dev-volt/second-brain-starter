"""
get_context.py — Aggregate context for a named project.

Usage:
  python get_context.py <project-slug>

Outputs a markdown context brief to stdout.
"""

import sys
import json
import subprocess
from datetime import datetime
from pathlib import Path

# Resolve paths relative to script location
SKILL_DIR = Path(__file__).parent.parent
SCRIPTS_DIR = SKILL_DIR.parent.parent / "scripts"
PROJECT_LIST = SKILL_DIR / "references" / "project-list.md"

VAULT_ROOT = Path(r"D:\Obsidian Brain\Brain")


def load_snapshot(slug: str) -> str | None:
    snapshot = VAULT_ROOT / "10_Active_Projects" / slug / "Snapshot.md"
    if snapshot.exists():
        return snapshot.read_text(encoding="utf-8")
    return None


def get_last_daily_entries(n: int = 3) -> str:
    daily_dir = VAULT_ROOT / "00_Meta" / "daily"
    if not daily_dir.exists():
        return ""
    logs = sorted(daily_dir.glob("*.md"), reverse=True)[:n]
    entries = []
    for log in logs:
        entries.append(f"### {log.stem}\n" + log.read_text(encoding="utf-8")[-2000:])
    return "\n\n".join(entries)


def run_memory_search(query: str) -> str:
    search_script = SCRIPTS_DIR / "memory" / "memory_search.py"
    if not search_script.exists():
        return "(memory search not available)"
    try:
        result = subprocess.run(
            [sys.executable, str(search_script), query, "--top", "5"],
            capture_output=True, text=True, timeout=15
        )
        return result.stdout.strip() or "(no results)"
    except Exception as e:
        return f"(search failed: {e})"


def get_github_activity(days: int = 7) -> str:
    query_script = SCRIPTS_DIR / "query.py"
    if not query_script.exists():
        return "(query.py not found)"
    try:
        result = subprocess.run(
            [sys.executable, str(query_script), "github", "activity", "--days", str(days)],
            capture_output=True, text=True, timeout=20
        )
        return result.stdout.strip() or "(no recent activity)"
    except Exception as e:
        return f"(GitHub fetch failed: {e})"


def main():
    if len(sys.argv) < 2:
        print("Usage: get_context.py <project-slug>", file=sys.stderr)
        sys.exit(1)

    slug = sys.argv[1]
    today = datetime.now().strftime("%Y-%m-%d")

    snapshot = load_snapshot(slug)
    if not snapshot:
        print(f"No snapshot found for '{slug}'.")
        print(f"Expected: {VAULT_ROOT / '10_Active_Projects' / slug / 'Snapshot.md'}")
        sys.exit(0)

    memory_results = run_memory_search(slug)
    github_activity = get_github_activity()

    output = f"""## {slug} — Context Brief
_{today}_

{snapshot}

---

### Related Learnings (Memory Search)
{memory_results}

---

### Recent GitHub Activity (last 7 days)
{github_activity}
"""
    print(output)


if __name__ == "__main__":
    main()
