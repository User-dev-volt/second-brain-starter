"""
shared.py — Shared auth loader and security utilities for all integrations.

Responsibilities:
  - Load credentials from .env (python-dotenv) so API keys never appear in
    Claude context — only the resulting data objects are passed to the model.
  - Provide get_env() with clear error messages for missing vars.
  - Re-export sanitize() so integrations import from one place.
  - Provide a format_for_claude() helper that sanitizes a data dict and
    formats it as a labeled markdown block ready for context injection.

Usage:
    from integrations.shared import get_env, sanitize, format_for_claude

    token = get_env("GITHUB_PAT")
    safe_block = format_for_claude({"repo": "my-game", "commits": 3}, source="github")
"""

import os
import sys
from pathlib import Path

# Load .env from repo root (two levels up from this file)
_repo_root = Path(__file__).parent.parent.parent.parent
_env_file = _repo_root / ".env"

try:
    from dotenv import load_dotenv
    load_dotenv(dotenv_path=_env_file)
except ImportError:
    # python-dotenv not installed — fall through, os.environ still works
    # if vars are set at the system level
    pass

# Make security module importable from integrations
sys.path.insert(0, str(Path(__file__).parent.parent / "security"))
from sanitize import sanitize, sanitize_dict  # noqa: F401 (re-exported)


# ---------------------------------------------------------------------------
# Credential loader
# ---------------------------------------------------------------------------

def get_env(var: str, required: bool = True) -> str | None:
    """
    Return the value of an environment variable.

    If `required=True` and the variable is missing, raises a clear RuntimeError
    instead of silently returning None or leaking partial config to Claude.
    """
    value = os.environ.get(var)
    if value is None and required:
        raise RuntimeError(
            f"Missing required environment variable: {var}\n"
            f"Add it to {_env_file} — see .env.example for the full template."
        )
    return value


def get_vault_paths() -> dict[str, str]:
    """
    Return resolved brain paths from environment.
    Falls back to the D:\\Brain default if env vars aren't set.
    """
    default = r"D:\Brain"
    return {
        "vault_root": os.environ.get("BRAIN_ROOT") or os.environ.get("VAULT_ROOT", default),
        "comfyui_base": os.environ.get("COMFYUI_BASE_URL", "http://localhost:8188"),
    }


# ---------------------------------------------------------------------------
# Context formatting
# ---------------------------------------------------------------------------

def format_for_claude(data: dict, source: str, label: str = "") -> str:
    """
    Sanitize a data dict and format it as a labeled markdown block for
    injection into a Claude context.

    Example output:
        ## GitHub Activity
        <external-data source="github">
        **repo:** &lt;my-game&gt;
        **commits:** 3
        </external-data>

    Args:
        data:   Dict of key/value pairs from an external source.
        source: Source label for sanitization (e.g. "github", "comfyui").
        label:  Optional markdown heading. Defaults to the source name.
    """
    heading = label or source.title()
    safe = sanitize_dict(data, source)

    lines = [f"## {heading}"]
    for k, v in safe.items():
        lines.append(f"**{k}:** {v}")

    return "\n".join(lines)


def format_list_for_claude(items: list[dict], source: str, label: str = "") -> str:
    """
    Sanitize a list of dicts and format as a markdown list block.
    Each item becomes a bullet point with its key/value pairs.
    """
    heading = label or source.title()
    lines = [f"## {heading}"]
    for item in items:
        safe = sanitize_dict(item, source)
        bullet = " | ".join(f"**{k}:** {v}" for k, v in safe.items())
        lines.append(f"- {bullet}")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# CLI (smoke test)
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    print("Vault paths:", get_vault_paths())

    sample = {"repo": "my-game", "last_commit": "Add inventory system", "commits_today": 3}
    print("\n" + format_for_claude(sample, source="github", label="GitHub Activity"))

    sample_list = [
        {"title": "Fix collision bug", "number": 42},
        {"title": "Add save system <script>evil()</script>", "number": 43},
    ]
    print("\n" + format_list_for_claude(sample_list, source="github", label="Open Issues"))
