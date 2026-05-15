#!/usr/bin/env python3
"""
consistency_check.py — Double monotonicity check on intent.md entries.

Reads the current intent.md and returns a list of potential contradictions:
pairs of entries that would produce conflicting predictions for the same
tradeoff type.

Called by /daily-reflect and /weekly-dream slash commands.
Can also be run standalone to inspect the current intent model.

"Double monotonicity" here means: for any given tradeoff type, the set of
heuristics in intent.md should produce a consistent directional prediction.
If heuristic A says "always prefer X in tradeoff type T" and heuristic B
implies "sometimes prefer Y in tradeoff type T", that's a candidate
contradiction worth surfacing.

This module does NOT call Claude. It prepares structured input for Claude
Code to reason over during the slash command session.
"""
import re
import sys
from pathlib import Path

SCRIPTS_DIR = Path(__file__).parent
sys.path.insert(0, str(SCRIPTS_DIR / "utils"))
from vault_router import VAULT_ROOT

META = VAULT_ROOT / "00_Meta"

TRADEOFF_TYPES = [
    "control vs. convenience",
    "ownership vs. delegation",
    "speed vs. durability",
    "depth vs. breadth",
    "manual vs. automated",
    "local vs. cloud",
    "explicit vs. implicit",
]


def load_intent_entries(intent_path: Path) -> list[dict]:
    """
    Parse intent.md into a list of entry dicts.
    Each dict has: name, heuristic, tradeoff_type, confidence, standing_order, raw_block
    """
    if not intent_path.exists():
        return []

    text = intent_path.read_text(encoding="utf-8")
    entries = []

    # Split on ### headers (pattern name)
    blocks = re.split(r"\n(?=### )", text)
    for block in blocks:
        block = block.strip()
        if not block.startswith("### "):
            continue

        entry: dict = {"raw_block": block}

        name_match = re.match(r"### (.+)", block)
        entry["name"] = name_match.group(1).strip() if name_match else "unknown"

        for label, key in [
            ("Heuristic", "heuristic"),
            ("Tradeoff type", "tradeoff_type"),
            ("Confidence", "confidence"),
            ("Standing order", "standing_order"),
        ]:
            m = re.search(rf"\*\*{re.escape(label)}:\*\*\s*(.+?)(?=\n\*\*|\Z)", block, re.DOTALL)
            entry[key] = m.group(1).strip() if m else ""

        entries.append(entry)

    return entries


def group_by_tradeoff(entries: list[dict]) -> dict[str, list[dict]]:
    """Group entries by tradeoff type. Entries with no tradeoff_type go into 'unclassified'."""
    groups: dict[str, list[dict]] = {}
    for e in entries:
        tt = e.get("tradeoff_type", "").lower().strip() or "unclassified"
        groups.setdefault(tt, []).append(e)
    return groups


def format_for_claude(intent_path: Path | None = None) -> str:
    """
    Format intent.md entries as structured input for Claude Code's consistency check.
    Returns a string to be included in the slash command context.
    """
    path = intent_path or (META / "intent.md")
    entries = load_intent_entries(path)

    if not entries:
        return "## Consistency Check Input\n\n_(intent.md has no entries yet — nothing to check)_\n"

    groups = group_by_tradeoff(entries)

    lines = ["## Consistency Check Input\n"]
    lines.append(f"Total entries: {len(entries)}")
    lines.append(f"Tradeoff types covered: {len(groups)}\n")

    for tt, group in sorted(groups.items()):
        lines.append(f"### Tradeoff type: {tt} ({len(group)} entries)")
        for e in group:
            lines.append(f"  **{e['name']}**")
            if e.get("heuristic"):
                lines.append(f"  Heuristic: {e['heuristic']}")
            if e.get("confidence"):
                lines.append(f"  Confidence: {e['confidence']}")
            if e.get("standing_order"):
                lines.append(f"  Standing order: {e['standing_order']}")
            lines.append("")

    lines.append(
        "For each tradeoff type with 2+ entries: check whether the heuristics\n"
        "produce consistent directional predictions. If two entries would give\n"
        "conflicting advice for the same decision scenario, flag them as a\n"
        "'contradiction' proposal targeting intent.md.\n"
    )

    return "\n".join(lines)


def main():
    """Standalone: print consistency check input for inspection."""
    sys.stdout.reconfigure(encoding="utf-8")
    output = format_for_claude()
    print(output)


if __name__ == "__main__":
    main()
