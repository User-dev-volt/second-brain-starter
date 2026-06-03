"""
heartbeat.py — Proactive project health monitor for Alec's Second Brain.

Runs every 30 minutes during active hours (9 AM–10 PM EST). On each run:
  1. Gather data from GitHub, ComfyUI, and project snapshots
  2. Diff against last-seen state — skip if nothing changed
  3. Call Claude with the diff to identify stalls, new commits, completed generations
  4. Apply any snapshot updates (low-risk file writes)
  5. Show Windows Toast notifications for anything worth surfacing
  6. Save new state

Schedule via Windows Task Scheduler (see setup_scheduler.bat).

Cost: ~$0.05/run × 30 runs/day ≈ $1.50/day
"""

import sys
import json
import os
from datetime import datetime, timezone
from pathlib import Path

# Resolve sibling modules
SCRIPTS_DIR = Path(__file__).parent
sys.path.insert(0, str(SCRIPTS_DIR / "utils"))
sys.path.insert(0, str(SCRIPTS_DIR / "integrations"))

import vault_router
import snapshot as snap
from notifications import show_windows_toast

VAULT_ROOT = vault_router.VAULT_ROOT
PROJECTS_ROOT = vault_router.PROJECTS_ROOT


# ---------------------------------------------------------------------------
# Data gathering
# ---------------------------------------------------------------------------

def _get_github_activity() -> list:
    """Return recent commit activity across all accounts. Returns [] on failure."""
    try:
        from github_integration import authenticate, get_recent_activity
    except Exception as e:
        print(f"[heartbeat] GitHub import failed: {e}", file=sys.stderr)
        return []

    activity = []
    seen_repos = set()

    for token_env in ("GITHUB_PAT", "GITHUB_PAT_CHIMERA"):
        if not os.environ.get(token_env):
            continue
        try:
            client = authenticate(token_env=token_env)
            for item in get_recent_activity(client, days=1):
                if item["repo"] not in seen_repos:
                    seen_repos.add(item["repo"])
                    activity.append(item)
        except Exception as e:
            print(f"[heartbeat] GitHub fetch failed ({token_env}): {e}", file=sys.stderr)

    activity.sort(key=lambda x: x["last_commit_date"], reverse=True)
    return activity


def _get_comfyui_status() -> dict | None:
    """Return ComfyUI queue status dict, or None if unavailable."""
    try:
        from comfyui_integration import get_queue_status
        return get_queue_status()
    except Exception:
        return None


def _get_project_last_touched() -> dict:
    """
    Scan PROJECTS_ROOT (D:\\Projects) and return {slug: last_touched_iso} for each
    project that has a Snapshot.md with a **Last Touched:** field.
    """
    import re
    projects_dir = PROJECTS_ROOT
    result = {}
    if not projects_dir.exists():
        return result

    for project_dir in projects_dir.iterdir():
        if not project_dir.is_dir():
            continue
        snapshot = project_dir / "Snapshot.md"
        if not snapshot.exists():
            continue
        text = snapshot.read_text(encoding="utf-8")
        m = re.search(r"\*\*Last Touched:\*\*\s*(.*)", text)
        if m:
            raw = m.group(1).strip()
            # Parse "YYYY-MM-DD HH:MM" → ISO 8601
            try:
                dt = datetime.strptime(raw, "%Y-%m-%d %H:%M").replace(tzinfo=timezone.utc)
                result[project_dir.name] = dt.isoformat()
            except ValueError:
                result[project_dir.name] = raw
        else:
            result[project_dir.name] = None

    return result


def _load_soul_and_user() -> str:
    """Return SOUL.md + USER.md concatenated for Claude's system prompt."""
    parts = []
    for fname in ("SOUL.md", "USER.md"):
        path = VAULT_ROOT / "00_Meta" / fname
        if path.exists():
            parts.append(path.read_text(encoding="utf-8"))
    return "\n\n---\n\n".join(parts)


def _load_project_index() -> str:
    """Return the current project index markdown."""
    index = VAULT_ROOT / "00_Meta" / "projects-index.md"
    if index.exists():
        return index.read_text(encoding="utf-8")
    return "(No project index found)"


# ---------------------------------------------------------------------------
# HABITS checklist auto-detection
# ---------------------------------------------------------------------------

def _update_habits_checklist(github_activity: list, comfyui_status: dict | None):
    """
    Auto-detect and check off objective HABITS pillars:
    - Main Game: any commit to a game repo today
    - Asset Creation: any ComfyUI generation completed today
    Writes today's date to HABITS.md history section if needed.
    """
    import re

    habits_path = VAULT_ROOT / "00_Meta" / "HABITS.md"
    if not habits_path.exists():
        return

    today = datetime.now().strftime("%Y-%m-%d")
    content = habits_path.read_text(encoding="utf-8")

    GAME_REPOS = {"moviebuilder", "project_chimera", "video-gen", "poe2_optimizer_v6"}
    game_committed = any(
        r.get("repo", "").lower().replace("-", "_") in GAME_REPOS
        or "game" in r.get("repo", "").lower()
        for r in github_activity
    )

    asset_created = False
    if comfyui_status:
        history = comfyui_status.get("history", {})
        for entry in history.values():
            # ComfyUI history entry has a timestamp — check if today
            try:
                ts = entry.get("timestamp_ms", 0) / 1000
                entry_date = datetime.fromtimestamp(ts).strftime("%Y-%m-%d")
                if entry_date == today:
                    asset_created = True
                    break
            except Exception:
                pass

    # Check/uncheck pillars in today's section
    if game_committed:
        content = re.sub(
            r"- \[ \] \*\*Main Game\*\*",
            "- [x] **Main Game**",
            content,
        )
    if asset_created:
        content = re.sub(
            r"- \[ \] \*\*Asset Creation\*\*",
            "- [x] **Asset Creation**",
            content,
        )

    habits_path.write_text(content, encoding="utf-8")


# ---------------------------------------------------------------------------
# Evening nudge (after 8 PM, warn on unchecked pillars)
# ---------------------------------------------------------------------------

def _check_evening_nudge() -> list[str]:
    """Return a list of unchecked pillar names if it's past 8 PM EST."""
    import re

    # EST = UTC-5, EDT = UTC-4 (we approximate as UTC-5)
    now_utc = datetime.now(timezone.utc)
    hour_est = (now_utc.hour - 5) % 24
    if hour_est < 20:  # Before 8 PM EST
        return []

    habits_path = VAULT_ROOT / "00_Meta" / "HABITS.md"
    if not habits_path.exists():
        return []

    content = habits_path.read_text(encoding="utf-8")
    unchecked = re.findall(r"- \[ \] \*\*(.+?)\*\*", content)
    return unchecked


# ---------------------------------------------------------------------------
# Claude analysis
# ---------------------------------------------------------------------------

def _call_claude_analysis(diff: dict, project_index: str, system: str) -> dict:
    """
    Pass the diff to Claude and get back notifications + snapshot_updates.
    Returns {"notifications": [...], "snapshot_updates": [...]} or empty on failure.
    """
    try:
        import anthropic
    except ImportError:
        print("[heartbeat] anthropic package not installed.", file=sys.stderr)
        return {}

    client = anthropic.Anthropic()

    prompt = f"""Review this project activity update for Alec's Second Brain and identify:
1. Any project that hasn't been touched in 7+ days (stalling) — flag it
2. Any new GitHub commits worth noting in a project snapshot
3. Any ComfyUI generation status changes worth surfacing

Activity diff:
{json.dumps(diff, indent=2)}

Current project index:
{project_index}

Respond ONLY with valid JSON in this exact format:
{{
  "notifications": [
    {{"title": "Short title", "body": "One-sentence body"}}
  ],
  "snapshot_updates": [
    {{"project": "slug", "fields": {{"Status": "Active", "Last Commit": "message"}}}}
  ]
}}

Keep notifications brief and actionable. Only include entries where there's something genuinely worth surfacing. Return empty arrays if nothing notable."""

    try:
        response = client.messages.create(
            model="claude-sonnet-4-6",
            max_tokens=512,
            system=system,
            messages=[{"role": "user", "content": prompt}],
        )
        text = response.content[0].text.strip()
        # Strip markdown code fences if present
        if text.startswith("```"):
            text = text.split("```")[1]
            if text.startswith("json"):
                text = text[4:]
        return json.loads(text)
    except Exception as e:
        print(f"[heartbeat] Claude call failed: {e}", file=sys.stderr)
        return {}


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def run_heartbeat():
    print(f"[heartbeat] {datetime.now().strftime('%Y-%m-%d %H:%M')} — running", file=sys.stderr)

    # 1. Gather data
    github_activity = _get_github_activity()
    project_last_touched = _get_project_last_touched()
    comfyui_status = _get_comfyui_status()
    comfyui_running = None
    if comfyui_status:
        comfyui_running = comfyui_status.get("queue_running", [None])[0]

    current_snapshot = {
        "github": github_activity,
        "projects": project_last_touched,
        "comfyui_running": comfyui_running,
    }

    # 2. Diff
    old_state = snap.load_state()
    diff = snap.diff_snapshot(old_state, current_snapshot)

    # 3. Auto-update HABITS checklist regardless of diff
    _update_habits_checklist(github_activity, comfyui_status)

    # 4. Evening nudge check
    unchecked = _check_evening_nudge()
    if unchecked:
        nudge_body = "Still unchecked: " + ", ".join(unchecked)
        show_windows_toast("Second Brain — Daily Habits", nudge_body, duration=8)

    # 5. If nothing changed, skip Claude call
    if not diff:
        print("[heartbeat] No changes detected — skipping Claude call.", file=sys.stderr)
        snap.save_state(current_snapshot)
        return

    # 6. Call Claude with diff
    system_prompt = _load_soul_and_user()
    project_index = _load_project_index()
    result = _call_claude_analysis(diff, project_index, system_prompt)

    # 7. Apply snapshot updates (low-risk file writes)
    if result.get("snapshot_updates"):
        try:
            sys.path.insert(0, str(SCRIPTS_DIR / "integrations"))
            from obsidian import update_project_snapshot
            for update in result["snapshot_updates"]:
                project = update.get("project")
                fields = update.get("fields", {})
                if project and fields:
                    update_project_snapshot(project, fields)
                    print(f"[heartbeat] Updated snapshot: {project}", file=sys.stderr)
        except Exception as e:
            print(f"[heartbeat] Snapshot update failed: {e}", file=sys.stderr)

    # 8. Show notifications
    for notif in result.get("notifications", []):
        show_windows_toast(notif.get("title", "Second Brain"), notif.get("body", ""), duration=7)

    # 9. Save new state
    snap.save_state(current_snapshot)
    print("[heartbeat] Done.", file=sys.stderr)


if __name__ == "__main__":
    run_heartbeat()
