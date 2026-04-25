# Session Manager — File Map

Quick reference for what each file does and when to touch it.

## Core server

| File | What it does | Edit when… |
|------|-------------|-----------|
| `server.py` | FastAPI app. All endpoints, bearer auth, Tailscale binding, process spawn/kill, ghost detection. Entry point: `python server.py` | Adding endpoints, changing spawn behavior, fixing auth logic |
| `config.json` | Project registry (id, name, path), port, hostname, hashed auth token. Read on every request — no restart needed for project changes | Adding/renaming projects, changing port, rotating token hash |
| `web/index.html` | Single-file mobile UI. Dark theme, project cards, token screen, 5 s poll. Vanilla JS — no build step | Changing the UI, adding card fields, tweaking styles |

## Setup & service

| File | What it does | Edit when… |
|------|-------------|-----------|
| `setup.ps1` | First-run script. Checks pwsh, claude ≥ 2.1.52, Tailscale, guides Remote Control `/config` step, generates auth token. No elevation needed. | Changing the onboarding flow or version check |
| `install-service.ps1` | Registers `ClaudeSessionManager` Windows service via NSSM. Prompts for user credentials so desktop windows are visible. Run as Admin. | Changing service name, log paths, restart delay |
| `uninstall-service.ps1` | Stops and removes the service. Falls back to `sc.exe` if NSSM not found. Run as Admin. | Rarely — only to reinstall clean |

## Docs

| File | What it does |
|------|-------------|
| `logs/` | `service-stdout.log` and `service-stderr.log` written by NSSM. First place to look when something breaks. |
| `../docs/session-manager-research.md` | Pre-build research notes: Windows process tree killing, NSSM setup, Tailscale IP detection. Background reading. |
| `../docs/session-manager-testing.md` | 10-step end-to-end phone test checklist. Run after any significant change. |
| `../.claude/skills/session-manager/SKILL.md` | Full reference for Claude: endpoints, expected responses, add-project guide, troubleshooting. |

## Common tasks

**Add a project:**
```jsonc
// config.json → projects array
{ "id": "my-proj", "name": "My Project", "path": "D:/path/to/project" }
```
Restart the server or service. Trust dialog is handled automatically.

**Rotate auth token:**
```powershell
pwsh D:\second-brain-starter\session_manager\setup.ps1
# Choose y at the token prompt
```

**Tail live logs:**
```powershell
Get-Content D:\second-brain-starter\session_manager\logs\service-stdout.log -Wait -Tail 30
```

**Manual run (bypass service):**
```powershell
D:\second-brain-starter\.venv\Scripts\python.exe D:\second-brain-starter\session_manager\server.py
```
