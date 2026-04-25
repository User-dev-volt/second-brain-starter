"""
capture.py — Append a structured idea entry to the ideas backlog.

Usage:
  python capture.py "<idea text>" [--project <name>] [--category <cat>]

Categories: game-mechanic, product, business, feature, other
"""

import sys
import argparse
from datetime import datetime
from pathlib import Path

VAULT_ROOT = Path(r"D:\Obsidian Brain\Brain")
BACKLOG = VAULT_ROOT / "00_Meta" / "ideas" / "_backlog.md"

SURFACE_HINTS = {
    "game-mechanic": "working on game systems, enemy AI, or world-building",
    "product": "reviewing the product roadmap or planning features",
    "business": "evaluating business model or monetization strategy",
    "feature": "planning the next sprint for the relevant project",
    "other": "doing a weekly review",
}

CWD_CATEGORY_MAP = {
    "godot": "game-mechanic",
    "gamecreation": "game-mechanic",
    "game": "game-mechanic",
    "moviebuilder": "product",
    "work": "product",
    "product": "product",
}


def infer_category(project: str, cwd: str) -> str:
    combined = (project + " " + cwd).lower()
    for keyword, cat in CWD_CATEGORY_MAP.items():
        if keyword in combined:
            return cat
    return "other"


def infer_title(idea: str) -> str:
    words = idea.strip().split()[:8]
    return " ".join(words) + ("..." if len(idea.split()) > 8 else "")


def capture(idea: str, project: str = "", category: str = "", cwd: str = "") -> Path:
    BACKLOG.parent.mkdir(parents=True, exist_ok=True)

    if not category:
        category = infer_category(project, cwd)

    ts = datetime.now().strftime("%Y-%m-%d %H:%M")
    title = infer_title(idea)
    source = project if project else "unattributed"
    surface = SURFACE_HINTS.get(category, SURFACE_HINTS["other"])

    cat_label = category.replace("-", " ").title()
    entry = (
        f"\n## [{ts}] {cat_label} — {title}\n"
        f"**Source project:** {source}\n"
        f"**Category:** {category}\n"
        f"**Idea:** {idea.strip()}\n"
        f"**Surface when:** {surface}\n"
    )

    with open(BACKLOG, "a", encoding="utf-8") as f:
        f.write(entry)

    return BACKLOG


def main():
    parser = argparse.ArgumentParser(description="Capture an idea to the backlog")
    parser.add_argument("idea", help="The idea text")
    parser.add_argument("--project", default="", help="Source project name")
    parser.add_argument("--category", default="",
                        choices=["game-mechanic", "product", "business", "feature", "other", ""],
                        help="Idea category")
    parser.add_argument("--cwd", default="", help="Current working directory (for auto-detection)")
    args = parser.parse_args()

    import os
    cwd = args.cwd or os.getcwd()
    path = capture(args.idea, args.project, args.category, cwd)
    print(f"Captured -> {path}")


if __name__ == "__main__":
    main()
