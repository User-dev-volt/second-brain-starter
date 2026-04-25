"""
vault_router.py — Maps the current working directory to the correct vault path and context area.

Alec currently has one vault: D:\\Obsidian Brain\\Brain\\
Game dev context → 20_Reference/GameDev/
Product context  → 20_Reference/Products/ and 20_Reference/Market/
AI/tooling       → 20_Reference/AI/
Cross-project    → 00_Meta/ (SOUL, USER, MEMORY, HEARTBEAT, HABITS)
"""

import os
from pathlib import Path

VAULT_ROOT = Path(r"D:\Obsidian Brain\Brain")

# Map directory name patterns to context areas within the vault
CONTEXT_ROUTES = {
    # Game engine / game dev projects
    "godot": "20_Reference/GameDev/godot-csharp",
    "unity": "20_Reference/GameDev",
    "comfyui": "20_Reference/GameDev/comfyui",
    "gamecreation": "20_Reference/GameDev",
    "game": "20_Reference/GameDev",
    "chimera": "20_Reference/GameDev/godot-csharp",
    # Product / work projects
    "moviebuilder": "20_Reference/Products",
    "lastepoch": "20_Reference/Products",
    "lebo": "20_Reference/Products",
    "optimizer": "20_Reference/Products",
    "work": "20_Reference/Products",
    "product": "20_Reference/Products",
    # AI / tooling / meta
    "second-brain": "20_Reference/AI",
    "bmad": "20_Reference/AI",
    "ai": "20_Reference/AI",
    # Default: cross-project meta
}

# Map context area paths → domain LEARNINGS.md file
LEARNINGS_MAP = {
    "20_Reference/GameDev/godot-csharp": VAULT_ROOT / "20_Reference/GameDev/godot-csharp/LEARNINGS.md",
    "20_Reference/GameDev/comfyui": VAULT_ROOT / "20_Reference/GameDev/comfyui/LEARNINGS.md",
    "20_Reference/GameDev": VAULT_ROOT / "20_Reference/GameDev/godot-csharp/LEARNINGS.md",
    "20_Reference/Products": VAULT_ROOT / "20_Reference/Products/LEARNINGS.md",
    "20_Reference/AI": VAULT_ROOT / "20_Reference/AI/LEARNINGS.md",
}

# Map directory name patterns to the GitHub PAT env var for that account
GITHUB_TOKEN_ROUTES = {
    "chimera": "GITHUB_PAT_CHIMERA",
    "project_chimera": "GITHUB_PAT_CHIMERA",
}

CORE_MEMORY_FILES = [
    VAULT_ROOT / "00_Meta" / "SOUL.md",
    VAULT_ROOT / "00_Meta" / "USER.md",
    VAULT_ROOT / "00_Meta" / "MEMORY.md",
]


def get_context_area(cwd: str) -> Path:
    """Return the most relevant vault subdirectory for the given working directory."""
    cwd_lower = cwd.lower().replace("\\", "/")
    for keyword, area in CONTEXT_ROUTES.items():
        if keyword in cwd_lower:
            return VAULT_ROOT / area
    return VAULT_ROOT / "00_Meta"


def get_learnings_file(cwd: str) -> Path | None:
    """Return the domain LEARNINGS.md path for the given working directory, or None."""
    cwd_lower = cwd.lower().replace("\\", "/")
    for keyword, area in CONTEXT_ROUTES.items():
        if keyword in cwd_lower:
            learnings = LEARNINGS_MAP.get(area)
            if learnings and learnings.exists():
                return learnings
    return None


def get_github_token_env(cwd: str) -> str:
    """Return the env var name for the GitHub PAT to use for the given cwd."""
    cwd_lower = cwd.lower().replace("\\", "/")
    for keyword, token_env in GITHUB_TOKEN_ROUTES.items():
        if keyword in cwd_lower:
            return token_env
    return "GITHUB_PAT"


def get_project_snapshot(cwd: str) -> Path | None:
    """Find a matching project snapshot by walking up the cwd for a known project folder."""
    projects_dir = VAULT_ROOT / "10_Active_Projects"
    known_projects = {p.name for p in projects_dir.iterdir() if p.is_dir()} if projects_dir.exists() else set()

    for part in reversed(Path(cwd).parts):
        if part in known_projects:
            snapshot = projects_dir / part / "Snapshot.md"
            return snapshot if snapshot.exists() else None

    return None


def get_daily_log(date_str: str) -> Path:
    """Return the path to today's daily log (creates parent dir if needed)."""
    daily_dir = VAULT_ROOT / "00_Meta" / "daily"
    daily_dir.mkdir(parents=True, exist_ok=True)
    return daily_dir / f"{date_str}.md"


def route(cwd: str) -> dict:
    """
    Main entry point. Returns a dict with resolved paths for the given cwd.

    Returns:
        {
            "vault_root": str,
            "core_memory": list[str],
            "context_area": str,
            "project_snapshot": str | None,
            "learnings_file": str | None,
        }
    """
    learnings = get_learnings_file(cwd)
    return {
        "vault_root": str(VAULT_ROOT),
        "core_memory": [str(f) for f in CORE_MEMORY_FILES],
        "context_area": str(get_context_area(cwd)),
        "project_snapshot": str(p) if (p := get_project_snapshot(cwd)) else None,
        "learnings_file": str(learnings) if learnings else None,
    }


if __name__ == "__main__":
    import sys
    import json

    cwd = sys.argv[1] if len(sys.argv) > 1 else os.getcwd()
    print(json.dumps(route(cwd), indent=2))
