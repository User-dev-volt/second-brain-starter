"""
obsidian.py — Read/write utilities for Alec's Obsidian vault.

All operations route through vault_router.py to resolve the correct paths.
Vault root: D:\\Obsidian Brain\\Brain\\

Operations:
  append_to_daily(text)               — Append timestamped entry to today's daily log
  update_project_snapshot(slug, fields) — Update fields in a project snapshot
  get_project_context(slug)           — Return full project snapshot as string
  update_project_index()              — Rebuild 10_Active_Projects/_index.md
  capture_idea(idea, source_project)  — Append to 00_Meta/ideas/_backlog.md
  log_learning(learning, category)    — Append to 20_Reference/GameDev/learnings/<category>.md
"""

import sys
import os
import json
import re
from datetime import datetime
from pathlib import Path

# Resolve vault_router from sibling utils/
sys.path.insert(0, str(Path(__file__).parent.parent / "utils"))
import vault_router

# Resolve guardrails from sibling security/
sys.path.insert(0, str(Path(__file__).parent.parent / "security"))
from guardrails import assert_file_write

VAULT_ROOT = vault_router.VAULT_ROOT


# ---------------------------------------------------------------------------
# safe_write — append-only, vault-boundary-checked file writer
# ---------------------------------------------------------------------------

def safe_write(path: Path, content: str, mode: str = "a") -> None:
    """
    Write `content` to `path` only if:
      1. The path is inside the allowed vault directories (guardrails check).
      2. mode is 'a' (append) or 'w' for new files that don't yet exist.

    Raises:
        PermissionError — if path is outside vault or if 'w' is used on an
                          existing file (use append; never overwrite vault notes).
    """
    assert_file_write(path)

    if mode == "w" and path.exists():
        raise PermissionError(
            f"safe_write: refusing to overwrite existing vault file '{path}'.\n"
            "Use mode='a' to append, or archive the file first."
        )

    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, mode, encoding="utf-8") as f:
        f.write(content)


# ---------------------------------------------------------------------------
# Daily log
# ---------------------------------------------------------------------------

def append_to_daily(text: str, prefix: str = "") -> Path:
    """Append a timestamped entry to today's daily log. Returns the log path."""
    date_str = datetime.now().strftime("%Y-%m-%d")
    log_path = vault_router.get_daily_log(date_str)

    timestamp = datetime.now().strftime("%H:%M")
    tag = f"[{prefix}] " if prefix else ""
    entry = f"\n## {timestamp} {tag}\n{text.strip()}\n"

    safe_write(log_path, entry)
    return log_path


# ---------------------------------------------------------------------------
# Project snapshots
# ---------------------------------------------------------------------------

def _snapshot_dir() -> Path:
    return VAULT_ROOT / "10_Active_Projects"


def _snapshot_path(slug: str) -> Path:
    return _snapshot_dir() / slug / "Snapshot.md"


def get_project_context(slug: str) -> str | None:
    """Return the full text of a project snapshot, or None if not found."""
    path = _snapshot_path(slug)
    if path.exists():
        return path.read_text(encoding="utf-8")
    return None


def update_project_snapshot(slug: str, fields: dict) -> Path:
    """
    Update named fields in a project snapshot.

    fields: dict of {field_name: value}
    Looks for lines matching '**<field>:**' and replaces their value.
    If a field isn't found, appends it at the end.
    Creates the snapshot from template if it doesn't exist.
    """
    path = _snapshot_path(slug)
    path.parent.mkdir(parents=True, exist_ok=True)

    if not path.exists():
        template = VAULT_ROOT / "00_Meta" / "Templates" / "Project_Snapshot.md"
        if template.exists():
            content = template.read_text(encoding="utf-8").replace("{{project}}", slug)
        else:
            content = f"# {slug}\n\n"
        safe_write(path, content, mode="w")

    content = path.read_text(encoding="utf-8")
    for field, value in fields.items():
        # Match **Field:** value (with optional trailing whitespace)
        pattern = rf"(\*\*{re.escape(field)}:\*\*\s*).*"
        replacement = rf"\g<1>{value}"
        new_content, count = re.subn(pattern, replacement, content)
        if count:
            content = new_content
        else:
            # Append field if not found
            content += f"\n**{field}:** {value}\n"

    # Always update last-touched timestamp
    ts_pattern = r"(\*\*Last Touched:\*\*\s*).*"
    now = datetime.now().strftime("%Y-%m-%d %H:%M")
    content, count = re.subn(ts_pattern, rf"\g<1>{now}", content)
    if not count:
        content += f"\n**Last Touched:** {now}\n"

    # Field-level update on existing file: boundary-check then write.
    assert_file_write(path)
    path.write_text(content, encoding="utf-8")
    return path


def update_project_index() -> Path:
    """Rebuild 10_Active_Projects/_index.md from all project snapshot files."""
    projects_dir = _snapshot_dir()
    index_path = projects_dir / "_index.md"

    rows = []
    for project_dir in sorted(projects_dir.iterdir()):
        if not project_dir.is_dir():
            continue
        snapshot = project_dir / "Snapshot.md"
        if not snapshot.exists():
            continue

        text = snapshot.read_text(encoding="utf-8")

        def extract(field: str) -> str:
            m = re.search(rf"\*\*{re.escape(field)}:\*\*\s*(.*)", text)
            return m.group(1).strip() if m else "—"

        rows.append({
            "name": project_dir.name,
            "phase": extract("Phase"),
            "momentum": extract("Momentum"),
            "last_touched": extract("Last Touched"),
            "next_action": extract("Next Action"),
        })

    now = datetime.now().strftime("%Y-%m-%d %H:%M")
    lines = [
        "# Active Projects Index",
        f"_Updated: {now}_",
        "",
        "| Project | Phase | Momentum | Last Touched | Next Action |",
        "|---------|-------|----------|--------------|-------------|",
    ]
    for r in rows:
        lines.append(
            f"| [{r['name']}]({r['name']}/Snapshot.md) | {r['phase']} | {r['momentum']} | {r['last_touched']} | {r['next_action']} |"
        )

    assert_file_write(index_path)
    index_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return index_path


# ---------------------------------------------------------------------------
# Idea capture
# ---------------------------------------------------------------------------

def capture_idea(idea: str, source_project: str = "") -> Path:
    """Append an idea to 00_Meta/ideas/_backlog.md."""
    backlog = VAULT_ROOT / "00_Meta" / "ideas" / "_backlog.md"
    backlog.parent.mkdir(parents=True, exist_ok=True)

    date_str = datetime.now().strftime("%Y-%m-%d %H:%M")
    source = f" _(from {source_project})_" if source_project else ""
    entry = f"\n- **{date_str}**{source}: {idea.strip()}\n"

    safe_write(backlog, entry)
    return backlog


# ---------------------------------------------------------------------------
# Learning log
# ---------------------------------------------------------------------------

def log_learning(learning: str, category: str = "general") -> Path:
    """
    Append a learning entry to 20_Reference/GameDev/learnings/<category>.md.
    Category examples: 'godot-csharp', 'comfyui', 'unity', 'general'
    """
    learnings_dir = VAULT_ROOT / "20_Reference" / "GameDev" / "learnings"
    learnings_dir.mkdir(parents=True, exist_ok=True)

    log_file = learnings_dir / f"{category}.md"
    date_str = datetime.now().strftime("%Y-%m-%d")

    if not log_file.exists():
        safe_write(log_file, f"# {category} Learnings\n\n", mode="w")

    entry = f"\n## {date_str}\n{learning.strip()}\n"
    safe_write(log_file, entry)

    return log_file


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Obsidian vault utilities")
    sub = parser.add_subparsers(dest="cmd")

    p_daily = sub.add_parser("daily", help="Append to today's daily log")
    p_daily.add_argument("text")
    p_daily.add_argument("--prefix", default="")

    p_snap = sub.add_parser("snapshot", help="Update a project snapshot")
    p_snap.add_argument("slug")
    p_snap.add_argument("fields", nargs="+", help="Key=Value pairs")

    p_ctx = sub.add_parser("context", help="Get project context")
    p_ctx.add_argument("slug")

    p_idx = sub.add_parser("index", help="Rebuild project index")

    p_idea = sub.add_parser("idea", help="Capture an idea")
    p_idea.add_argument("text")
    p_idea.add_argument("--project", default="")

    p_learn = sub.add_parser("learning", help="Log a learning")
    p_learn.add_argument("text")
    p_learn.add_argument("--category", default="general")

    args = parser.parse_args()

    if args.cmd == "daily":
        path = append_to_daily(args.text, args.prefix)
        print(f"Appended to {path}")

    elif args.cmd == "snapshot":
        fields = dict(kv.split("=", 1) for kv in args.fields)
        path = update_project_snapshot(args.slug, fields)
        print(f"Updated {path}")

    elif args.cmd == "context":
        ctx = get_project_context(args.slug)
        print(ctx or f"No snapshot found for '{args.slug}'")

    elif args.cmd == "index":
        path = update_project_index()
        print(f"Rebuilt {path}")

    elif args.cmd == "idea":
        path = capture_idea(args.text, args.project)
        print(f"Idea saved to {path}")

    elif args.cmd == "learning":
        path = log_learning(args.text, args.category)
        print(f"Learning saved to {path}")

    else:
        parser.print_help()
