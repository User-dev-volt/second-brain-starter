"""
guardrails.py — Operation guardrails enforcing Alec's security boundaries.

Two checks every operation must pass before execution:
  1. check_operation(op_string) — hard-block dangerous shell/API operations
  2. check_file_write(path)     — vault boundary: only write inside Memory dirs

Usage:
    from security.guardrails import check_operation, check_file_write

    allowed, reason = check_operation("git push origin main")
    if not allowed:
        raise PermissionError(reason)

    if not check_file_write("/some/path/file.md"):
        raise PermissionError("Write outside vault boundary blocked")
"""

import re
import os
from pathlib import Path

# ---------------------------------------------------------------------------
# Import sanitize logger (reuse security event log)
# ---------------------------------------------------------------------------

try:
    from sanitize import log_security_event
except ImportError:
    import sys
    sys.path.insert(0, str(Path(__file__).parent))
    from sanitize import log_security_event


# ---------------------------------------------------------------------------
# Layer 1: Hard-blocked operation patterns
# ---------------------------------------------------------------------------
# These are NEVER allowed, regardless of context or user instruction.

_HARD_BLOCK_PATTERNS = [
    # VCS — require explicit confirmation outside this system
    (re.compile(r"\bgit\s+push\b", re.IGNORECASE),            "git-push-blocked"),
    (re.compile(r"\bgit\s+reset\s+--hard\b", re.IGNORECASE),  "git-reset-hard-blocked"),
    (re.compile(r"\bgit\s+force\b", re.IGNORECASE),            "git-force-blocked"),
    # File deletion — archive to _archive/ instead
    (re.compile(r"\brm\s+-[^\s]*f", re.IGNORECASE),           "rm-rf-blocked"),
    (re.compile(r"\bdel\s+/[sfqF]", re.IGNORECASE),           "windows-del-blocked"),
    (re.compile(r"\bos\.remove\b", re.IGNORECASE),             "os-remove-blocked"),
    (re.compile(r"\bshutil\.rmtree\b", re.IGNORECASE),        "rmtree-blocked"),
    (re.compile(r"\bPath\([^)]+\)\.unlink\b", re.IGNORECASE), "path-unlink-blocked"),
    # Outbound messaging — drafting not enabled
    (re.compile(r"\bsmtp\b.*\bsend\b", re.IGNORECASE),        "smtp-send-blocked"),
    (re.compile(r"\bsendmail\b", re.IGNORECASE),               "sendmail-blocked"),
    (re.compile(r"\brequests\.post.*discord", re.IGNORECASE),  "discord-post-blocked"),
    (re.compile(r"\brequests\.post.*slack", re.IGNORECASE),    "slack-post-blocked"),
    (re.compile(r"\btwilio\b.*\bsend\b", re.IGNORECASE),       "twilio-send-blocked"),
    # Social / external publish
    (re.compile(r"\btwitter\b.*\bpost\b", re.IGNORECASE),      "twitter-post-blocked"),
    (re.compile(r"\breddit\b.*\bsubmit\b", re.IGNORECASE),     "reddit-submit-blocked"),
]


def check_operation(operation: str) -> tuple[bool, str]:
    """
    Returns (allowed: bool, reason: str).

    Checks the operation string against hard-blocked patterns.
    Log every block attempt to security.log.
    """
    for pattern, name in _HARD_BLOCK_PATTERNS:
        if pattern.search(operation):
            msg = f"Hard-blocked operation '{name}' detected: {operation[:120]!r}"
            log_security_event(msg)
            return False, f"Hard-blocked: {name}"
    return True, "ok"


# ---------------------------------------------------------------------------
# Layer 2: Vault boundary enforcement
# ---------------------------------------------------------------------------
# Only allow file writes inside these directories. Cross-project memory lives in
# D:\Brain; per-project Snapshot.md files live with the code under D:\Projects.

_BRAIN_ROOT = Path(os.environ.get("BRAIN_ROOT") or os.environ.get("VAULT_ROOT") or r"D:\Brain")
_PROJECTS_ROOT = Path(os.environ.get("PROJECTS_ROOT") or r"D:\Projects")

_ALLOWED_WRITE_DIRS = [
    _BRAIN_ROOT / "00_Meta",
    _BRAIN_ROOT / "20_Reference",
    _PROJECTS_ROOT,
]


def check_file_write(path: str | Path) -> bool:
    """
    Returns True only if `path` is inside an allowed vault Memory directory.

    Logs and returns False for any path outside the vault.
    """
    try:
        abs_path = Path(os.path.abspath(path)).resolve()
    except (ValueError, OSError):
        log_security_event(f"Vault boundary: could not resolve path '{path}'")
        return False

    for allowed in _ALLOWED_WRITE_DIRS:
        try:
            abs_path.relative_to(allowed.resolve())
            return True
        except ValueError:
            continue

    log_security_event(f"Vault boundary violation: attempted write to '{abs_path}'")
    return False


def assert_file_write(path: str | Path) -> None:
    """Raise PermissionError if path is outside the vault boundary."""
    if not check_file_write(path):
        raise PermissionError(
            f"Write blocked: '{path}' is outside the allowed vault directories.\n"
            f"Allowed roots: {[str(d) for d in _ALLOWED_WRITE_DIRS]}"
        )


# ---------------------------------------------------------------------------
# CLI (smoke test)
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    import sys, json

    tests_op = [
        "git push origin main",
        "python heartbeat.py",
        "rm -rf /tmp/test",
        "requests.post('https://discord.com/api/webhooks/...', json=payload)",
        "obsidian.append_to_daily('session ended')",
    ]
    print("=== Operation checks ===")
    for op in tests_op:
        allowed, reason = check_operation(op)
        status = "ALLOW" if allowed else "BLOCK"
        print(f"  [{status}] {op[:60]!r} — {reason}")

    print("\n=== File write checks ===")
    test_paths = [
        r"D:\Brain\00_Meta\SOUL.md",
        r"D:\Projects\my-game\Snapshot.md",
        r"C:\Users\Alec\Desktop\secret.txt",
        r"D:\second-brain-starter\.claude\data\memory.db",
    ]
    for p in test_paths:
        result = check_file_write(p)
        status = "ALLOW" if result else "BLOCK"
        print(f"  [{status}] {p}")
