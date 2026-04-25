"""
asset_cataloger.py — Catalog ComfyUI-generated assets into the vault.

After each generation, appends an entry to:
  D:\\Obsidian Brain\\Brain\\20_Reference\\GameDev\\assets\\_catalog.md

Also maintains a JSON index at .claude/data/state/asset-catalog.json
for fast lookups without reading markdown.

Usage:
  python asset_cataloger.py log --filename warrior_001.png \\
      --workflow workflows/character_sprite_v3.json \\
      --prompt "pixel art warrior, top-down RPG, 16x16" \\
      --notes "High quality at CFG 7.5, steps 20"

  python asset_cataloger.py search "warrior"
  python asset_cataloger.py list --limit 20
"""

import sys
import json
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "utils"))
import vault_router

VAULT_ROOT = vault_router.VAULT_ROOT
CATALOG_MD = VAULT_ROOT / "20_Reference" / "GameDev" / "assets" / "_catalog.md"
CATALOG_JSON = Path(__file__).parent.parent.parent / "data" / "state" / "asset-catalog.json"


def _load_json_index() -> list[dict]:
    CATALOG_JSON.parent.mkdir(parents=True, exist_ok=True)
    if CATALOG_JSON.exists():
        return json.loads(CATALOG_JSON.read_text(encoding="utf-8"))
    return []


def _save_json_index(entries: list[dict]):
    CATALOG_JSON.parent.mkdir(parents=True, exist_ok=True)
    CATALOG_JSON.write_text(json.dumps(entries, indent=2), encoding="utf-8")


def log_asset(
    filename: str,
    workflow: str = "",
    prompt: str = "",
    notes: str = "",
    dest_path: str = "",
    tags: list[str] = None,
) -> dict:
    """
    Append a generated asset to the markdown catalog and JSON index.
    Returns the entry dict.
    """
    CATALOG_MD.parent.mkdir(parents=True, exist_ok=True)

    date_str = datetime.now().strftime("%Y-%m-%d")
    stem = Path(filename).stem

    entry = {
        "date": date_str,
        "filename": filename,
        "workflow": workflow,
        "prompt": prompt,
        "notes": notes,
        "dest_path": dest_path,
        "tags": tags or [],
    }

    # --- Markdown entry ---
    if not CATALOG_MD.exists():
        CATALOG_MD.write_text("# Asset Catalog\n\n", encoding="utf-8")

    md_entry = f"\n## {date_str} — {stem}\n"
    if workflow:
        md_entry += f"- **Workflow:** `{workflow}`\n"
    if prompt:
        md_entry += f"- **Prompt:** \"{prompt}\"\n"
    if dest_path:
        md_entry += f"- **Output:** `{dest_path}`\n"
    if notes:
        md_entry += f"- **Notes:** {notes}\n"
    if tags:
        md_entry += f"- **Tags:** {', '.join(tags)}\n"

    with open(CATALOG_MD, "a", encoding="utf-8") as f:
        f.write(md_entry)

    # --- JSON index ---
    entries = _load_json_index()
    entries.append(entry)
    _save_json_index(entries)

    return entry


def search_assets(query: str) -> list[dict]:
    """Return catalog entries where query appears in filename, prompt, notes, or tags."""
    q = query.lower()
    results = []
    for e in _load_json_index():
        searchable = " ".join([
            e.get("filename", ""),
            e.get("prompt", ""),
            e.get("notes", ""),
            " ".join(e.get("tags", [])),
        ]).lower()
        if q in searchable:
            results.append(e)
    return results


def list_assets(limit: int = 20) -> list[dict]:
    """Return the most recent N catalog entries."""
    entries = _load_json_index()
    return entries[-limit:]


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Asset catalog for ComfyUI outputs")
    sub = parser.add_subparsers(dest="cmd")

    p_log = sub.add_parser("log", help="Log a generated asset")
    p_log.add_argument("--filename", required=True)
    p_log.add_argument("--workflow", default="")
    p_log.add_argument("--prompt", default="")
    p_log.add_argument("--notes", default="")
    p_log.add_argument("--dest", default="", dest="dest_path")
    p_log.add_argument("--tags", nargs="*", default=[])

    p_search = sub.add_parser("search", help="Search the asset catalog")
    p_search.add_argument("query")

    p_list = sub.add_parser("list", help="List recent assets")
    p_list.add_argument("--limit", type=int, default=20)

    args = parser.parse_args()

    if args.cmd == "log":
        entry = log_asset(
            filename=args.filename,
            workflow=args.workflow,
            prompt=args.prompt,
            notes=args.notes,
            dest_path=args.dest_path,
            tags=args.tags,
        )
        print(f"Logged: {entry['filename']} on {entry['date']}")
        print(f"Catalog: {CATALOG_MD}")

    elif args.cmd == "search":
        results = search_assets(args.query)
        if not results:
            print(f"No assets matching '{args.query}'")
        else:
            for e in results:
                print(f"  [{e['date']}] {e['filename']}")
                if e.get("prompt"):
                    print(f"    Prompt: {e['prompt'][:80]}")

    elif args.cmd == "list":
        assets = list_assets(args.limit)
        if not assets:
            print("No assets cataloged yet.")
        else:
            for e in assets:
                print(f"  [{e['date']}] {e['filename']}")

    else:
        parser.print_help()
