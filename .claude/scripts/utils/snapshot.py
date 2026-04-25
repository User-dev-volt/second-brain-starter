"""
snapshot.py — State persistence and diffing for the heartbeat.

Stores the last-seen snapshot of GitHub activity, project timestamps, and
ComfyUI status in .claude/data/state/heartbeat-state.json.

Usage:
    from snapshot import load_state, save_state, diff_snapshot

    old = load_state()
    new = { "github": [...], "projects": {...}, "comfyui_running": None }
    delta = diff_snapshot(old, new)
    if delta:
        save_state(new)
"""

import json
from pathlib import Path
from datetime import datetime, timezone

STATE_FILE = Path(__file__).parent.parent.parent / "data" / "state" / "heartbeat-state.json"


def load_state() -> dict:
    """Load the last heartbeat state. Returns empty dict if no state exists."""
    STATE_FILE.parent.mkdir(parents=True, exist_ok=True)
    if STATE_FILE.exists():
        try:
            return json.loads(STATE_FILE.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            return {}
    return {}


def save_state(state: dict) -> None:
    """Persist the current snapshot to disk, adding a timestamp."""
    STATE_FILE.parent.mkdir(parents=True, exist_ok=True)
    state["_saved_at"] = datetime.now(timezone.utc).isoformat()
    STATE_FILE.write_text(json.dumps(state, indent=2, default=str), encoding="utf-8")


def diff_snapshot(old: dict, new: dict) -> dict:
    """
    Compare old and new snapshots. Returns a dict describing what changed.

    Keys in the returned dict:
      "new_commits"     — list of repos with commits not in old state
      "stalling"        — list of project names untouched for 7+ days
      "comfyui_changed" — True if ComfyUI running status changed
      "project_updates" — dict of {project: new_last_touched} for changed projects

    Returns an empty dict if nothing changed.
    """
    delta = {}

    # --- GitHub: new commit activity ---
    old_repos = {item["repo"]: item for item in old.get("github", [])}
    new_repos = {item["repo"]: item for item in new.get("github", [])}

    new_commits = []
    for repo, info in new_repos.items():
        if repo not in old_repos:
            new_commits.append(info)
        elif info.get("last_commit_date") != old_repos[repo].get("last_commit_date"):
            new_commits.append(info)

    if new_commits:
        delta["new_commits"] = new_commits

    # --- Projects: detect stalling (7+ days without a touch) ---
    stalling = []
    project_updates = {}
    now = datetime.now(timezone.utc)
    old_projects = old.get("projects", {})
    new_projects = new.get("projects", {})

    for project, last_touched_str in new_projects.items():
        if last_touched_str:
            try:
                last_touched = datetime.fromisoformat(last_touched_str)
                # Make timezone-aware if naive
                if last_touched.tzinfo is None:
                    last_touched = last_touched.replace(tzinfo=timezone.utc)
                days_idle = (now - last_touched).days
                if days_idle >= 7:
                    stalling.append({"project": project, "days_idle": days_idle})
            except (ValueError, TypeError):
                pass

        # Track changed timestamps
        if last_touched_str != old_projects.get(project):
            project_updates[project] = last_touched_str

    if stalling:
        delta["stalling"] = stalling
    if project_updates:
        delta["project_updates"] = project_updates

    # --- ComfyUI: running status changed ---
    old_running = old.get("comfyui_running")
    new_running = new.get("comfyui_running")
    if old_running != new_running:
        delta["comfyui_changed"] = True
        delta["comfyui_running"] = new_running
        delta["comfyui_was"] = old_running

    return delta
