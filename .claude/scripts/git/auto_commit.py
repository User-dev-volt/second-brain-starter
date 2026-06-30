#!/usr/bin/env python3
"""
auto_commit.py — Stage, commit, and push project changes using the account in .gitaccount.

Called by session-end-flush.py on every Stop hook (fast-paths if no changes or no config).
Also invoked directly by the /gitpush skill.

Usage:
  python auto_commit.py --cwd <path>
  python auto_commit.py --cwd <path> --message "custom message"
  python auto_commit.py --cwd <path> --commit-only
  python auto_commit.py --cwd <path> --setup        # rewrite remote URL + validate
"""
import argparse
import subprocess
import sys
from datetime import datetime
from pathlib import Path

GIT_DIR = Path(__file__).parent
sys.path.insert(0, str(GIT_DIR))

from git_router import load_config, rewrite_remote_for_account
from ssh_manager import detect_keys, update_ssh_config


def _git(args: list[str], cwd: Path, **kwargs) -> subprocess.CompletedProcess:
    return subprocess.run(["git"] + args, capture_output=True, text=True, cwd=str(cwd), **kwargs)


def is_git_repo(cwd: Path) -> bool:
    return _git(["rev-parse", "--git-dir"], cwd).returncode == 0


def has_changes(cwd: Path) -> bool:
    return bool(_git(["status", "--porcelain"], cwd).stdout.strip())


def stage_all(cwd: Path) -> bool:
    return _git(["add", "-A"], cwd).returncode == 0


def commit(cwd: Path, message: str) -> tuple[bool, str]:
    r = _git(["commit", "-m", message], cwd)
    return r.returncode == 0, (r.stdout + r.stderr).strip()


def push(cwd: Path, branch: str) -> tuple[bool, str]:
    r = _git(["push", "origin", branch], cwd)
    return r.returncode == 0, (r.stdout + r.stderr).strip()


def run_pre_commit_check(cwd: Path, command: str, timeout: int) -> tuple[bool, str]:
    """Run a project's pre-commit safety gate (e.g. build/test). Returns (passed, detail).

    Only an exit code of 0 permits the commit; a non-zero exit or a timeout blocks it, so a
    build/test-failing state is never auto-committed or pushed. Configured per project via the
    "pre_commit_check" key in .gitaccount; repos that don't set it are unaffected (no-op).
    """
    try:
        proc = subprocess.run(
            command, shell=True, cwd=str(cwd),
            capture_output=True, text=True, timeout=timeout,
        )
    except subprocess.TimeoutExpired:
        return False, f"pre_commit_check timed out after {timeout}s"
    if proc.returncode == 0:
        return True, "passed"
    detail = (proc.stdout + proc.stderr).strip()
    return False, detail[-1500:] if detail else f"exit code {proc.returncode}"


def setup_project(cwd: Path) -> None:
    """One-time setup: update SSH config and rewrite remote URL for this project."""
    keys = detect_keys()
    print(update_ssh_config(keys))

    config = load_config(cwd)
    if not config:
        print("\nNo .gitaccount found in this project.")
        print("Create one at the project root — see .gitaccount.example for format.")
        return

    changed = rewrite_remote_for_account(cwd, config)
    if changed:
        from git_router import get_remote_url
        new_url = get_remote_url(cwd)
        print(f"\nRemote URL updated to: {new_url}")
    else:
        from git_router import get_remote_url
        url = get_remote_url(cwd)
        print(f"\nRemote URL already correct: {url}")

    print(f"Account: {config['account']}  Branch: {config['branch']}")


def auto_commit_push(
    cwd: str | Path,
    message: str | None = None,
    commit_only: bool = False,
    verbose: bool = False,
) -> dict:
    """
    Core logic. Returns result dict:
      skipped    — no .gitaccount or not a git repo
      committed  — a commit was made
      pushed     — pushed to remote
      error      — error string or None
    """
    cwd = Path(cwd)
    result = {"skipped": True, "committed": False, "pushed": False, "error": None}

    if not is_git_repo(cwd):
        return result

    config = load_config(cwd)
    if not config:
        return result  # Project not managed

    result["skipped"] = False

    if not config.get("auto_commit"):
        if verbose:
            print("git-auto: auto_commit=false in .gitaccount, skipped")
        return result

    if not has_changes(cwd):
        if verbose:
            print("git-auto: no changes to commit")
        return result

    # Optional per-project safety gate: run a build/test check (configured via
    # "pre_commit_check" in .gitaccount) and skip the commit if it fails, so a broken
    # state is never auto-committed/pushed. No-op for repos that don't set the key.
    check_cmd = config.get("pre_commit_check")
    if check_cmd:
        check_timeout = int(config.get("pre_commit_check_timeout", 240))
        passed, detail = run_pre_commit_check(cwd, check_cmd, check_timeout)
        if not passed:
            result["error"] = (
                "pre_commit_check failed - commit skipped; changes left uncommitted in the "
                f"working tree, will retry next Stop. Detail: {detail}"
            )
            if verbose:
                print(f"git-auto: {result['error']}")
            return result

    # Ensure remote URL uses SSH host alias before committing
    rewrite_remote_for_account(cwd, config)

    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M")
    prefix = config.get("commit_prefix", "[AutoSave]")
    commit_msg = message or f"{prefix} {timestamp}"

    stage_all(cwd)
    ok, output = commit(cwd, commit_msg)
    if not ok:
        result["error"] = f"commit failed: {output}"
        return result
    result["committed"] = True

    should_push = config.get("auto_push") and not commit_only
    if should_push:
        branch = config.get("branch", "main")
        ok, output = push(cwd, branch)
        result["pushed"] = ok
        if not ok:
            result["error"] = f"push failed: {output}"

    return result


if __name__ == "__main__":
    p = argparse.ArgumentParser(description="Auto-commit and push using .gitaccount config")
    p.add_argument("--cwd", default=".", help="Project directory")
    p.add_argument("--message", "-m", default=None, help="Custom commit message")
    p.add_argument("--commit-only", action="store_true", help="Commit but do not push")
    p.add_argument("--setup", action="store_true", help="One-time setup: update SSH config + rewrite remote")
    p.add_argument("--verbose", "-v", action="store_true")
    args = p.parse_args()

    cwd = Path(args.cwd).resolve()

    if args.setup:
        setup_project(cwd)
        sys.exit(0)

    r = auto_commit_push(
        cwd=cwd,
        message=args.message,
        commit_only=args.commit_only,
        verbose=args.verbose,
    )

    if r["skipped"]:
        if args.verbose:
            print("git-auto: skipped (no .gitaccount or not a git repo)")
        sys.exit(0)
    elif r["error"]:
        print(f"git-auto ERROR: {r['error']}", file=sys.stderr)
        sys.exit(1)
    elif r["committed"]:
        pushed_str = "pushed" if r["pushed"] else "not pushed (auto_push=false or --commit-only)"
        print(f"git-auto: committed + {pushed_str}")
    else:
        if args.verbose:
            print("git-auto: nothing to commit")
