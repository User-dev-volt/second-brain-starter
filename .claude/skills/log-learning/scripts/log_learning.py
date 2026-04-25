"""
log_learning.py — Append a learning entry to the appropriate knowledge file.

Usage:
  python log_learning.py "<learning text>" [--category <cat>] [--cwd <path>]

Categories: godot-csharp, comfyui, unity, product, general
"""

import sys
import argparse
from datetime import datetime
from pathlib import Path

VAULT_ROOT = Path(r"D:\Obsidian Brain\Brain")

CATEGORY_PATHS = {
    "godot-csharp": VAULT_ROOT / "20_Reference" / "GameDev" / "learnings" / "godot-csharp.md",
    "comfyui":      VAULT_ROOT / "20_Reference" / "GameDev" / "learnings" / "comfyui.md",
    "unity":        VAULT_ROOT / "20_Reference" / "GameDev" / "learnings" / "unity.md",
    "product":      VAULT_ROOT / "20_Reference" / "Products" / "learnings" / "product.md",
    "general":      VAULT_ROOT / "20_Reference" / "GameDev" / "learnings" / "general.md",
}

CWD_CATEGORY_MAP = {
    "godot": "godot-csharp",
    "comfyui": "comfyui",
    "unity": "unity",
    "moviebuilder": "product",
    "work": "product",
    "product": "product",
}


def infer_category(cwd: str) -> str:
    cwd_lower = cwd.lower()
    for keyword, cat in CWD_CATEGORY_MAP.items():
        if keyword in cwd_lower:
            return cat
    return "general"


def log_learning(text: str, category: str = "general") -> Path:
    log_file = CATEGORY_PATHS.get(category, CATEGORY_PATHS["general"])
    log_file.parent.mkdir(parents=True, exist_ok=True)

    date_str = datetime.now().strftime("%Y-%m-%d")

    if not log_file.exists():
        display_name = category.replace("-", " ").title()
        log_file.write_text(f"# {display_name} Learnings\n\n", encoding="utf-8")

    entry = f"\n## {date_str}\n{text.strip()}\n"
    with open(log_file, "a", encoding="utf-8") as f:
        f.write(entry)

    return log_file


def main():
    parser = argparse.ArgumentParser(description="Log a learning to the knowledge base")
    parser.add_argument("learning", help="The learning text")
    parser.add_argument("--category", default="",
                        choices=list(CATEGORY_PATHS.keys()) + [""],
                        help="Knowledge category")
    parser.add_argument("--cwd", default="", help="CWD for auto-detection")
    args = parser.parse_args()

    import os
    cwd = args.cwd or os.getcwd()
    category = args.category or infer_category(cwd)

    path = log_learning(args.learning, category)
    print(f"Logged to {category} -> {path}")


if __name__ == "__main__":
    main()
