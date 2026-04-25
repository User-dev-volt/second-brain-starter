---
name: session-manager
description: Manage the Claude Code Session Manager service — check status, add projects, rotate the auth token, and troubleshoot sessions. Triggers on /session-manager, "session manager status", "add project to session manager", "session won't start", "session manager auth", or any question about the phone-to-desktop Claude Code control panel.
argument-hint: [status | add-project | rotate-token | logs | troubleshoot <issue>]
---

# Claude Code Session Manager

Phone-to-desktop control panel for Claude Code sessions over Tailscale.
Lets you start, restart, and stop `claude` sessions from the Claude mobile app
without walking to your desk.

## What it does and why

`/remote-control` lets your phone *drive* a running Claude Code session, but it
cannot start a new one, kill a stuck one, or switch projects remotely.
This service fills those gaps with a small FastAPI server on `voltreezy` that:

1. Serves a mobile-friendly web page at `http://voltreezy:8765`
2. Spawns `pwsh → claude` in the correct project folder when you tap **Start**
3. Kills the process tree when you tap **Stop** or **Restart**
4. Tracks PID liveness and surfaces dead sessions as restartable

One Remote Control session per machine is enforced — the UI and API both
reject a Start if another session is already running.

## File layout

```
session_manager/
  server.py          FastAPI app — all endpoints live here
  config.json        Projects list, port, hostname, hashed auth token
  setup.ps1          First-run: checks deps, guides /config step, generates token
  install-service.ps1   Register as Windows service via NSSM (run as Admin)
  uninstall-service.ps1 Remove service
  web/index.html     Mobile UI — served at GET /
  logs/              stdout/stderr from the Windows service
```

## Endpoints

All `/api/*` routes require `Authorization: Bearer <token>`.
The server only accepts connections from the Tailscale subnet (`100.x.x.x`).

| Method | Path | Description |
|--------|------|-------------|
| `GET`  | `/` | Mobile web UI (HTML) |
| `GET`  | `/api/health` | Uptime, hostname, Tailscale IP, active session |
| `GET`  | `/api/projects` | All projects with status, PID, started_at |
| `POST` | `/api/projects/{id}/start` | Spawn new session (409 if one already running) |
| `POST` | `/api/projects/{id}/restart` | Kill any running session, wait 2 s, spawn fresh |
| `POST` | `/api/projects/{id}/stop` | Kill session cleanly |

### Example responses

```jsonc
// GET /api/health
{
  "status": "ok",
  "hostname": "voltreezy",
  "tailscale_ip": "100.121.27.81",
  "uptime_seconds": 3721,
  "active_session": "second-brain"   // null if none running
}

// GET /api/projects — one entry per project
{
  "id": "second-brain",
  "name": "Second Brain",
  "path": "D:/second-brain-starter",
  "status": "running",   // "running" | "idle"
  "pid": 14832,
  "started_at": 1745234567.3
}

// POST /api/projects/{id}/start  →  200
{ "status": "started", "pid": 14832, "project_id": "second-brain" }

// POST /api/projects/{id}/start  →  409 (another session running)
{ "detail": "Session 'second-brain' is already running. Remote Control supports one session at a time — stop it first." }

// POST /api/projects/{id}/stop   →  200
{ "status": "stopped", "project_id": "second-brain" }

// POST /api/projects/{id}/stop   →  200 (was already idle)
{ "status": "already_idle", "project_id": "second-brain" }
```

## Adding a new project

1. Open `session_manager/config.json`.
2. Add an entry to the `projects` array:

```json
{
  "id":   "my-project",
  "name": "My Project",
  "path": "C:/Users/Alec/code/my-project"
}
```

- `id` — URL-safe slug, used in API paths. No spaces or special characters.
- `name` — Display name shown on the mobile card.
- `path` — Absolute Windows path to the project folder. Forward or back slashes both work.

3. Restart the service (or the manual process) to reload config:

```powershell
Restart-Service ClaudeSessionManager
# or, for a manual run: Ctrl-C and re-run server.py
```

No code changes needed — config is read on every request.

## Rotating the auth token

Re-run setup and choose **y** when asked to generate a new token:

```powershell
pwsh session_manager\setup.ps1
```

The old token is immediately invalidated. Update it in the mobile UI's token
entry screen (or clear `sessionStorage` in the browser to force re-entry).

## Checking logs

```powershell
# Live tail (service mode)
Get-Content session_manager\logs\service-stdout.log -Wait -Tail 30

# Last 20 lines of errors
Get-Content session_manager\logs\service-stderr.log -Tail 20

# Service status
Get-Service ClaudeSessionManager
```

## Troubleshooting

### Session won't start — "PowerShell 7 not found"

`pwsh` is not installed or not on PATH.
Install it: `winget install Microsoft.PowerShell`
Then restart the service. The server auto-discovers `pwsh` in
`C:\Program Files\PowerShell\7\pwsh.exe` even if it isn't on PATH.

### Session won't start — "Session X is already running"

One Remote Control session per machine. Either:
- Tap **Stop** on the running project first, then **Start** on the new one, or
- Tap **Restart** on the project you want — it kills whatever is running first.

### Auth fails — UI shows token entry screen after each page load

The token is stored in `sessionStorage`, which clears when the browser tab is
closed. This is intentional. Paste the token again, or use a bookmark with
the token pre-filled (not recommended on a shared phone).

If the token itself stopped working, check whether `setup.ps1` was re-run and
a new token was generated — the old one is immediately invalid.

### Process ghost — status shows "running" but session is dead

This happens after the Remote Control 10-minute network timeout kills the
underlying connection without cleanly exiting `claude`. The server detects
dead PIDs on every 5-second poll and marks them `idle` automatically.
If the card is still showing "running" after 10 seconds, tap **Restart** —
it will kill the ghost PID (or skip gracefully if it's already gone) and
spawn a fresh session.

### Tailscale disconnected — cannot reach `voltreezy:8765`

The server binds *only* to the Tailscale IP at startup. If Tailscale drops
and reconnects with a different IP, the server must be restarted:

```powershell
Restart-Service ClaudeSessionManager
```

If Tailscale is not connected at all, the server will refuse to start
(`tailscale ip -4` returns nothing) and the service will show `Stopped`.
Reconnect Tailscale, then: `Start-Service ClaudeSessionManager`.

### Service starts but port is not listening

1. Check the log: `Get-Content session_manager\logs\service-stderr.log -Tail 30`
2. Common causes:
   - Port 8765 already taken — change `port` in `config.json` and reinstall
   - Service running as `LocalSystem` — reinstall and set it to your user account
     so it can bind to the Tailscale interface and spawn visible windows
   - `auth_token_hash` is empty — re-run `setup.ps1` to generate a token
