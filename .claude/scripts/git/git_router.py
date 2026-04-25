#!/usr/bin/env python3
"""
git_router.py — Load per-project git config and route pushes to the correct GitHub account.

Each project root may contain a .gitaccount JSON file:
{
  "account":       "alec-personal",   # SSH alias from ssh_manager (required)
  "auto_commit":   true,              # stage + commit on SessionEnd
  "auto_push":     true,              # push after committing
  "branch":        "main",            # branch to push to
  "commit_prefix": "[AutoSave]"       # prefix for auto-generated commit messages
}
"""
import json
import re
import subprocess
from pathlib import Path

GITACCOUNT_FILE = ".gitaccount"
DEFAULTS = {
    "account": None,
    "auto_commit": True,
    "auto_push": True,
    "branch": "main",
    "commit_prefix": "[AutoSave]",
}


def load_config(cwd: str | Path) -> dict | None:
    """Return merged config dict for the project at cwd, or None if not configured."""
    cwd = Path(cwd)

    # Search cwd then parent dirs (handles being in a subdirectory)
    path = None
    for candidate_dir in [cwd] + list(cwd.parents):
        candidate = candidate_dir / GITACCOUNT_FILE
        if candidate.exists():
            path = candidate
            break

    if path is None:
        return None

    try:
        raw = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        # Fallback: simple key=value format
        raw = {}
        for line in path.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                k, _, v = line.partition("=")
                val = v.strip().strip('"').strip("'")
                # Coerce booleans
                if val.lower() in ("true", "yes", "1"):
                    val = True
                elif val.lower() in ("false", "no", "0"):
                    val = False
                raw[k.strip()] = val

    config = {**DEFAULTS, **raw}
    if config["account"]:
        config["host"] = f"github-{config['account']}"
    return config


def get_remote_url(cwd: Path) -> str | None:
    r = subprocess.run(
        ["git", "remote", "get-url", "origin"],
        capture_output=True, text=True, cwd=str(cwd),
    )
    return r.stdout.strip() if r.returncode == 0 else None


def rewrite_remote_for_account(cwd: Path, config: dict) -> bool:
    """Rewrite origin remote URL to use the SSH host alias. Returns True if changed."""
    host = config.get("host")
    if not host:
        return False

    url = get_remote_url(cwd)
    if not url or "github.com" not in url:
        return False

    if f"git@{host}:" in url:
        return False  # Already correct

    # git@github.com:user/repo.git  →  git@github-alec-personal:user/repo.git
    routed = re.sub(r"git@github\.com:", f"git@{host}:", url)
    if routed == url:
        return False

    subprocess.run(
        ["git", "remote", "set-url", "origin", routed],
        capture_output=True, cwd=str(cwd),
    )
    return True
