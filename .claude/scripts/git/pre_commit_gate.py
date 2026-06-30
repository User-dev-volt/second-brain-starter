#!/usr/bin/env python3
"""
pre_commit_gate.py - AutoSave safety gate for a TypeScript/Vite project (built for LEBOv2).

WHY THIS EXISTS
  The Second Brain AutoSave is a Claude Code "Stop" hook:
      ~/.claude/settings.json (Stop)
        -> .claude/hooks/session-end-flush.py  (run_git_auto_commit)
          -> .claude/scripts/git/auto_commit.py  (git add -A; commit "[AutoSave] <ts>"; push)
  It commits AND pushes whatever is on disk after every Claude response. Without a gate,
  a transient / mid-edit broken state becomes a permanent commit on main (and origin/main).
  This gate is invoked by auto_commit.py via the "pre_commit_check" key in a project's
  .gitaccount and decides whether it is safe to commit the current working tree.

CONTRACT (exit code is the only thing auto_commit.py looks at)
  exit 0      -> safe to commit; AutoSave proceeds.
  exit non-0  -> NOT safe; AutoSave skips this tick, leaving changes uncommitted in the
                 working tree to be retried on the next Stop. Nothing is lost.

WHAT IT GATES ON (for the project app dir given by --dir)
  1. Fast skip - if no build-relevant file under <dir>/src (or a build config such as
     package.json / tsconfig*.json / vite|vitest.config.*) changed, the commit is allowed
     without running anything, so doc/asset-only autosaves stay instant.
  2. Typecheck - `pnpm -C <dir> exec tsc --noEmit` must exit 0.
  3. Tests - `pnpm -C <dir> exec vitest run` must introduce NO NEW failures versus a
     recorded baseline. The baseline tolerates tests that were already failing when the
     gate was installed and RATCHETS: whenever the current failure set is a strict subset
     of the baseline, the baseline is rewritten to the smaller current set, so a once-
     failing test that gets fixed becomes protected against future regressions too.

Usage:
  python pre_commit_gate.py --dir D:/Projects/LEBOv2/lebo
  python pre_commit_gate.py --dir D:/Projects/LEBOv2/lebo --baseline <path> --verbose

Exit codes: 0 allow | 2 typecheck failed | 3 no test results | 4 new test failure(s).
"""
import argparse
import json
import os
import re
import subprocess
import sys
import tempfile
from pathlib import Path

TSC_TIMEOUT = 45      # seconds; `tsc --noEmit` measured ~6s on LEBOv2
VITEST_TIMEOUT = 150  # seconds; `vitest run` measured ~28s warm (cold runs are slower)


def log(msg: str) -> None:
    sys.stderr.write(f"[pre-commit-gate] {msg}\n")


def run_shell(cmd: str, timeout: int) -> subprocess.CompletedProcess:
    # shell=True so cmd.exe resolves pnpm/pnpm.cmd via PATH (same env as the Stop hook).
    return subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=timeout)


def git_repo_root(start: Path) -> Path:
    try:
        r = subprocess.run(
            ["git", "-C", str(start), "rev-parse", "--show-toplevel"],
            capture_output=True, text=True, timeout=30,
        )
        if r.returncode == 0 and r.stdout.strip():
            return Path(r.stdout.strip())
    except Exception:
        pass
    return start


def changed_paths(repo_root: Path) -> list[str]:
    """Repo-relative (posix) paths of all changed/untracked files."""
    try:
        r = subprocess.run(
            ["git", "-C", str(repo_root), "status", "--porcelain"],
            capture_output=True, text=True, timeout=30,
        )
    except Exception:
        return []
    paths = []
    for line in r.stdout.splitlines():
        if not line.strip():
            continue
        p = line[3:]  # strip the 2-char status + space
        if " -> " in p:  # rename: "old -> new"
            p = p.split(" -> ", 1)[1]
        paths.append(p.strip().strip('"').replace("\\", "/"))
    return paths


def should_gate(changed: list[str], app_rel: str) -> bool:
    """True if any changed path is TypeScript source or a build config under the app dir."""
    app_rel = app_rel.strip("/")
    prefix = (app_rel + "/") if app_rel and app_rel != "." else ""
    src_prefix = prefix + "src/"
    config_re = re.compile(
        r"^" + re.escape(prefix)
        + r"(package\.json|tsconfig.*\.json|vite\.config\.[cm]?[jt]s|vitest\.config\.[cm]?[jt]s)$"
    )
    for p in changed:
        if p.startswith(src_prefix) or config_re.match(p):
            return True
    return False


def typecheck(app_dir: Path) -> tuple[bool, str]:
    try:
        r = run_shell(f'pnpm -C "{app_dir.as_posix()}" exec tsc --noEmit', TSC_TIMEOUT)
    except subprocess.TimeoutExpired:
        return False, f"tsc timed out after {TSC_TIMEOUT}s"
    if r.returncode == 0:
        return True, "ok"
    detail = (r.stdout + r.stderr).strip()
    return False, detail[-1500:] if detail else f"exit code {r.returncode}"


def vitest_failures(app_dir: Path) -> tuple[set[str] | None, str]:
    """Run vitest; return (set of failing test ids, summary). None => results unavailable."""
    fd, out_path = tempfile.mkstemp(suffix=".json", prefix="autosave-vitest-")
    os.close(fd)
    out = Path(out_path)
    try:
        try:
            r = run_shell(
                f'pnpm -C "{app_dir.as_posix()}" exec vitest run '
                f'--reporter=json --outputFile="{out.as_posix()}"',
                VITEST_TIMEOUT,
            )
        except subprocess.TimeoutExpired:
            return None, f"vitest timed out after {VITEST_TIMEOUT}s"
        try:
            data = json.loads(out.read_text(encoding="utf-8"))
        except Exception as e:
            tail = (r.stderr or r.stdout or "")[-800:]
            return None, f"could not parse vitest json ({e}); rc={r.returncode}; tail: {tail}"
        fails: set[str] = set()
        for f in data.get("testResults", []):
            name = f.get("name", "")
            try:
                rel = os.path.relpath(name, str(app_dir)).replace("\\", "/")
            except Exception:
                rel = name.replace("\\", "/")
            for a in f.get("assertionResults", []):
                if a.get("status") == "failed":
                    fails.add(f"{rel} :: {a.get('fullName') or a.get('title') or '?'}")
        return fails, f"{data.get('numFailedTests')} failed / {data.get('numTotalTests')} total"
    finally:
        try:
            out.unlink()
        except OSError:
            pass


def load_baseline(path: Path) -> set[str] | None:
    if not path.exists():
        return None
    try:
        return set(json.loads(path.read_text(encoding="utf-8")).get("failing", []))
    except Exception:
        return None


def save_baseline(path: Path, fails: set[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps({"failing": sorted(fails), "count": len(fails)}, indent=2),
        encoding="utf-8",
    )


def main() -> int:
    ap = argparse.ArgumentParser(description="AutoSave build/test safety gate")
    ap.add_argument("--dir", required=True, help="App dir with package.json (e.g. D:/Projects/LEBOv2/lebo)")
    ap.add_argument("--baseline", default=None, help="Baseline JSON path (default: alongside this script)")
    ap.add_argument("--verbose", "-v", action="store_true")
    args = ap.parse_args()

    app_dir = Path(args.dir).resolve()
    if not (app_dir / "package.json").exists():
        log(f"no package.json under {app_dir}; allowing commit (nothing to gate)")
        return 0

    repo_root = git_repo_root(app_dir)
    app_rel = os.path.relpath(app_dir, repo_root).replace("\\", "/")
    baseline_path = (
        Path(args.baseline) if args.baseline
        else Path(__file__).parent / ".autosave-baselines" / f"{repo_root.name}.json"
    )

    # 1. Fast skip when no build-relevant file changed.
    if not should_gate(changed_paths(repo_root), app_rel):
        if args.verbose:
            log("no build-relevant changes; commit allowed without checks")
        return 0

    # 2. Typecheck must pass.
    ok, detail = typecheck(app_dir)
    if not ok:
        log("BLOCK: typecheck failed (tsc --noEmit):")
        log(detail)
        return 2
    if args.verbose:
        log("typecheck passed")

    # 3. Tests: no NEW failures versus baseline.
    current, summary = vitest_failures(app_dir)
    if current is None:
        log(f"BLOCK: could not obtain test results - {summary}")
        return 3

    baseline = load_baseline(baseline_path)
    if baseline is None:
        save_baseline(baseline_path, current)
        log(f"baseline initialised at {baseline_path} with {len(current)} known-failing "
            f"test(s); commit allowed ({summary})")
        return 0

    new_failures = current - baseline
    if new_failures:
        log(f"BLOCK: {len(new_failures)} NEW test failure(s) not in baseline ({summary}):")
        for t in sorted(new_failures):
            log(f"  NEW FAIL: {t}")
        return 4

    # No new failures. Ratchet the baseline down if previously-failing tests now pass.
    if current < baseline:
        fixed = len(baseline - current)
        save_baseline(baseline_path, current)
        log(f"commit allowed; ratcheted baseline down by {fixed} now-passing test(s) ({summary})")
    elif args.verbose:
        log(f"commit allowed; no new failures ({summary})")
    return 0


if __name__ == "__main__":
    sys.exit(main())
