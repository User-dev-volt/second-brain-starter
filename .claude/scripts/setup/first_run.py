"""
first_run.py — Validate that the Second Brain environment is ready to run.

Run this after filling in .env to confirm every component is wired up:
    python .claude/scripts/setup/first_run.py

Checks (non-destructive):
  1. .env exists and required keys are set
  2. Vault root directory is reachable
  3. Python packages are importable
  4. Memory database exists (or flags that indexing is needed)
  5. Scheduled tasks are registered
  6. Heartbeat dry-run (--full to also run heartbeat.py)
"""

import importlib
import importlib.util
import os
import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[3]
ENV_PATH = REPO_ROOT / ".env"
SCRIPTS = REPO_ROOT / ".claude" / "scripts"
DB_PATH = REPO_ROOT / ".claude" / "data" / "memory.db"

REQUIRED_ENV_KEYS = ["SECOND_BRAIN_API_KEY", "GITHUB_PAT", "VAULT_ROOT"]
REQUIRED_PACKAGES = [
    "anthropic",
    "sentence_transformers",
    "sqlite_vec",
    "github",          # PyGithub
    "requests",
    "websocket",       # websocket-client
    "dotenv",          # python-dotenv
]

PASS = "[PASS]"
FAIL = "[FAIL]"
WARN = "[WARN]"


def check(label: str, ok: bool, detail: str = "") -> bool:
    status = PASS if ok else FAIL
    line = f"  {status}  {label}"
    if detail:
        line += f"\n         {detail}"
    print(line)
    return ok


def main() -> None:
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--full", action="store_true", help="Also run heartbeat.py --dry-run")
    args = parser.parse_args()

    # Load .env early so subsequent checks see the values
    if ENV_PATH.exists():
        from dotenv import load_dotenv
        load_dotenv(ENV_PATH)

    results = []

    # ── 1. .env ───────────────────────────────────────────────────────────────
    print("\n-- Environment --")
    results.append(check(".env file exists", ENV_PATH.exists(), str(ENV_PATH)))
    for key in REQUIRED_ENV_KEYS:
        val = os.environ.get(key, "")
        results.append(check(f"  {key} is set", bool(val) and not val.startswith("your_")))

    # ── 2. Vault ──────────────────────────────────────────────────────────────
    print("\n-- Vault --")
    vault_root = Path(os.environ.get("VAULT_ROOT", ""))
    results.append(check("VAULT_ROOT exists on disk", vault_root.is_dir(), str(vault_root)))

    # ── 3. Packages ───────────────────────────────────────────────────────────
    print("\n-- Python packages --")
    for pkg in REQUIRED_PACKAGES:
        ok = importlib.util.find_spec(pkg) is not None
        results.append(check(pkg, ok, "" if ok else f"pip install -r requirements.txt"))

    # ── 4. Memory database ───────────────────────────────────────────────────
    print("\n-- Memory database --")
    db_ok = DB_PATH.exists() and DB_PATH.stat().st_size > 0
    results.append(check(
        "memory.db exists and non-empty",
        db_ok,
        "" if db_ok else f"Run: python {SCRIPTS}/memory/memory_index.py --full",
    ))

    # ── 5. Scheduled tasks ────────────────────────────────────────────────────
    print("\n-- Scheduled tasks --")
    for task_name in ["SecondBrain\\Heartbeat", "SecondBrainDailyReflect"]:
        result = subprocess.run(
            ["schtasks", "/query", "/tn", task_name],
            capture_output=True, text=True,
        )
        registered = result.returncode == 0
        results.append(check(
            task_name,
            registered,
            "" if registered else f"Run as Admin: python {SCRIPTS}/setup/register_tasks.py",
        ))

    # ── 6. Optional heartbeat dry-run ─────────────────────────────────────────
    if args.full:
        print("\n-- Heartbeat dry-run --")
        r = subprocess.run(
            [sys.executable, str(SCRIPTS / "heartbeat.py"), "--dry-run"],
            capture_output=False,
        )
        results.append(check("heartbeat --dry-run", r.returncode == 0))

    # ── Summary ───────────────────────────────────────────────────────────────
    passed = sum(results)
    total = len(results)
    print(f"\n{'-'*70}")
    print(f"  {passed}/{total} checks passed")
    if passed == total:
        print("  Ready to go.")
    else:
        print(f"  {total - passed} issue(s) need attention (see above).")
    print()

    sys.exit(0 if passed == total else 1)


if __name__ == "__main__":
    main()
