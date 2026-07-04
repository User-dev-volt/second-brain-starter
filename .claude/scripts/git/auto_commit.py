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


def in_submodule(cwd: Path) -> bool:
    """True if cwd sits inside a git submodule (i.e. it has a superproject).

    Autosave must never commit INSIDE a submodule: load_config() in git_router
    walks UP parent dirs to find a .gitaccount, so an autosave whose cwd landed
    in a submodule (e.g. external/pob-engine) would resolve the SUPERPROJECT's
    config and then `git add -A; git commit` the submodule's own working tree,
    creating a stray [AutoSave] commit that moves the submodule HEAD off its
    pinned gitlink. A top-level repo has no superproject, so its normal
    root-cwd autosave is unaffected.
    """
    r = _git(["rev-parse", "--show-superproject-working-tree"], cwd)
    return r.returncode == 0 and bool(r.stdout.strip())


def has_changes(cwd: Path) -> bool:
    return bool(_git(["status", "--porcelain"], cwd).stdout.strip())


def stage_all(cwd: Path) -> bool:
    return _git(["add", "-A"], cwd).returncode == 0


def commit(cwd: Path, message: str) -> tuple[bool, str]:
    r = _git(["commit", "-m", message], cwd)
    return r.returncode == 0, (r.stdout + r.stderr).strip()


def push(cwd: Path, branch: str, push_branch: str | None = None) -> tuple[bool, str]:
    # push_branch (opt-in via "push_branch" in .gitaccount): back up commits to a DIFFERENT
    # remote branch via a local:remote refspec — e.g. push local "main" to origin/"autosave/main"
    # so AutoSave never advances origin/main. Absent → push the branch to its same-named remote
    # (original behaviour). First push to a not-yet-existing remote branch creates it (no --force).
    refspec = f"{branch}:{push_branch}" if push_branch and push_branch != branch else branch
    r = _git(["push", "origin", refspec], cwd)
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


def log_staged_snapshot(cwd: Path, config: dict, commit_msg: str) -> None:
    """Forensic AutoSave log (opt-in via "autosave_log": true in .gitaccount).

    Appends a timestamped record of EXACTLY what is about to be committed — the staged --stat
    plus the staged source diff — to .autosave-log/<repo>.log next to this script. Purpose: when
    a racing/phantom edit sneaks into an AutoSave snapshot, this captures the diff + timestamp
    after the fact so it can be correlated with whatever else was running. Best-effort only: any
    failure here MUST NOT block the commit (a logging bug can never cost a snapshot).
    """
    if not config.get("autosave_log"):
        return
    try:
        stat = _git(["diff", "--cached", "--stat"], cwd).stdout
        src_diff = _git(
            ["diff", "--cached", "--", "*.ts", "*.tsx", "*.js", "*.jsx", "*.rs"], cwd
        ).stdout
        ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        log_dir = GIT_DIR / ".autosave-log"
        log_dir.mkdir(parents=True, exist_ok=True)
        parts = [f"\n===== {ts}  [{cwd.name}]  {commit_msg} =====", stat.rstrip()]
        if src_diff.strip():
            parts.append("--- staged source diff (.ts/.tsx/.js/.jsx/.rs) ---")
            parts.append(src_diff.rstrip())
        with (log_dir / f"{cwd.name}.log").open("a", encoding="utf-8") as fh:
            fh.write("\n".join(parts) + "\n")
    except Exception:
        pass  # forensic logging must never break AutoSave


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
    autosave: bool = False,
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

    # Automatic autosave must NEVER commit inside a submodule (see in_submodule):
    # a --autosave whose cwd landed in one would `git add -A; git commit` the
    # submodule's working tree and knock its HEAD off the pinned gitlink. A
    # deliberate /gitpush (autosave=False) is left untouched; a superproject's own
    # root-cwd autosave has no superproject and is unaffected.
    if autosave and in_submodule(cwd):
        if verbose:
            print("git-auto: refused autosave inside a submodule (cwd has a superproject)")
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
    log_staged_snapshot(cwd, config, commit_msg)
    ok, output = commit(cwd, commit_msg)
    if not ok:
        result["error"] = f"commit failed: {output}"
        return result
    result["committed"] = True

    should_push = config.get("auto_push") and not commit_only
    if should_push:
        branch = config.get("branch", "main")
        # The push_branch redirect applies ONLY to the automatic Stop-hook autosave (--autosave),
        # so a deliberate /gitpush still publishes to origin/<branch>. No flag → normal push.
        push_branch = config.get("push_branch") if autosave else None
        ok, output = push(cwd, branch, push_branch)
        result["pushed"] = ok
        result["push_target"] = push_branch or branch
        if not ok:
            result["error"] = f"push failed: {output}"

    return result


if __name__ == "__main__":
    p = argparse.ArgumentParser(description="Auto-commit and push using .gitaccount config")
    p.add_argument("--cwd", default=".", help="Project directory")
    p.add_argument("--message", "-m", default=None, help="Custom commit message")
    p.add_argument("--commit-only", action="store_true", help="Commit but do not push")
    p.add_argument("--autosave", action="store_true",
                   help="Automatic Stop-hook autosave: honors .gitaccount push_branch (backup-branch redirect)")
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
        autosave=args.autosave,
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
        if r["pushed"]:
            pushed_str = f"pushed → origin/{r.get('push_target', 'main')}"
        else:
            pushed_str = "not pushed (auto_push=false or --commit-only)"
        print(f"git-auto: committed + {pushed_str}")
    else:
        if args.verbose:
            print("git-auto: nothing to commit")
