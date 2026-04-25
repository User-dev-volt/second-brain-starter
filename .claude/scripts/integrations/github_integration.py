"""
github_integration.py — GitHub awareness for Alec's repos.

Auth: PAT token in GITHUB_PAT environment variable.
State: .claude/data/state/github-state.json (last-checked timestamp per repo)

Operations:
  authenticate()                        — Return authenticated Github client
  get_recent_activity(client, days=7)   — Commits across all repos
  get_open_issues(client, repo_name)    — Open issues + PRs for a repo
  format_context(activity)             — Markdown summary for vault injection

Install: pip install PyGithub
"""

import os
import json
import sys
from datetime import datetime, timezone, timedelta
from pathlib import Path

STATE_FILE = Path(__file__).parent.parent.parent / "data" / "state" / "github-state.json"


def authenticate(token_env: str = "GITHUB_PAT"):
    """Return an authenticated Github client.

    Args:
        token_env: Name of the environment variable holding the PAT.
                   Defaults to GITHUB_PAT. Use GITHUB_PAT_CHIMERA for the
                   Project Chimera account.
    """
    try:
        from github import Github, Auth
    except ImportError:
        print("PyGithub not installed. Run: pip install PyGithub", file=sys.stderr)
        sys.exit(1)

    token = os.environ.get(token_env)
    if not token:
        print(f"{token_env} environment variable not set.", file=sys.stderr)
        sys.exit(1)

    return Github(auth=Auth.Token(token))


def _load_state() -> dict:
    STATE_FILE.parent.mkdir(parents=True, exist_ok=True)
    if STATE_FILE.exists():
        return json.loads(STATE_FILE.read_text(encoding="utf-8"))
    return {}


def _save_state(state: dict):
    STATE_FILE.parent.mkdir(parents=True, exist_ok=True)
    STATE_FILE.write_text(json.dumps(state, indent=2), encoding="utf-8")


def get_recent_activity(client, days: int = 7) -> list[dict]:
    """Get commits across all repos in the last N days."""
    state = _load_state()
    since = datetime.now(timezone.utc) - timedelta(days=days)

    # Use last-checked if more recent than `days` ago
    last_checked_str = state.get("last_activity_check")
    if last_checked_str:
        last_checked = datetime.fromisoformat(last_checked_str)
        if last_checked > since:
            since = last_checked

    user = client.get_user()
    activity = []

    for repo in user.get_repos(sort="updated"):
        try:
            commits = list(repo.get_commits(since=since))
            if commits:
                activity.append({
                    "repo": repo.name,
                    "commits": len(commits),
                    "last_commit": commits[0].commit.message.splitlines()[0][:100],
                    "last_commit_date": commits[0].commit.author.date.isoformat(),
                    "url": repo.html_url,
                })
        except Exception:
            pass  # Repos with no commits or access issues

    activity.sort(key=lambda x: x["last_commit_date"], reverse=True)

    # Save updated state
    state["last_activity_check"] = datetime.now(timezone.utc).isoformat()
    _save_state(state)

    return activity


def get_open_issues(client, repo_name: str) -> list[dict]:
    """Get open issues and PRs for a specific repo."""
    user = client.get_user()
    repo = client.get_repo(f"{user.login}/{repo_name}")
    issues = []
    for i in repo.get_issues(state="open"):
        issues.append({
            "title": i.title,
            "number": i.number,
            "labels": [label.name for label in i.labels],
            "is_pr": i.pull_request is not None,
            "url": i.html_url,
            "created_at": i.created_at.isoformat(),
        })
    return issues


def format_context(activity: list[dict]) -> str:
    """Return a markdown summary of recent GitHub activity for vault injection."""
    if not activity:
        return "_No GitHub activity in the requested window._\n"

    lines = ["## Recent GitHub Activity\n"]
    for a in activity:
        lines.append(f"- **{a['repo']}** — {a['commits']} commit(s)")
        lines.append(f"  - Last: _{a['last_commit']}_")
        lines.append(f"  - {a['last_commit_date'][:10]}")
    return "\n".join(lines) + "\n"


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="GitHub integration")
    sub = parser.add_subparsers(dest="cmd")

    p_act = sub.add_parser("activity", help="Recent commits across all repos")
    p_act.add_argument("--days", type=int, default=7)
    p_act.add_argument("--json", action="store_true", dest="as_json")

    p_iss = sub.add_parser("issues", help="Open issues for a repo")
    p_iss.add_argument("--repo", required=True)
    p_iss.add_argument("--json", action="store_true", dest="as_json")

    args = parser.parse_args()
    client = authenticate()

    if args.cmd == "activity":
        data = get_recent_activity(client, args.days)
        if args.as_json:
            print(json.dumps(data, indent=2))
        else:
            print(format_context(data))

    elif args.cmd == "issues":
        data = get_open_issues(client, args.repo)
        if args.as_json:
            print(json.dumps(data, indent=2))
        else:
            for i in data:
                kind = "PR" if i["is_pr"] else "Issue"
                labels = ", ".join(i["labels"]) or "no labels"
                print(f"  [{kind} #{i['number']}] {i['title']} ({labels})")

    else:
        parser.print_help()
