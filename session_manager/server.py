"""
Claude Code Session Manager — FastAPI server.

Binds to the Tailscale interface only. All /api/* routes require Bearer auth.
Multiple projects can run simultaneously as separate Remote Control sessions.
"""

import hashlib
import json
import secrets
import subprocess
import sys
import time
from pathlib import Path
from typing import Optional

import psutil
import uvicorn
from fastapi import Depends, FastAPI, HTTPException, Request
from fastapi.responses import FileResponse, JSONResponse
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

CONFIG_PATH = Path(__file__).parent / "config.json"
WEB_DIR = Path(__file__).parent / "web"

app = FastAPI(docs_url=None, redoc_url=None, openapi_url=None)
security = HTTPBearer(auto_error=False)

# { project_id: {"pid": int, "started_at": float} }
sessions: dict[str, dict] = {}

_start_time = time.time()
_tailscale_ip: str = ""


# ── Config ────────────────────────────────────────────────────────────────────

def load_config() -> dict:
    # utf-8-sig strips the BOM that Windows tools (PowerShell, Notepad) may write
    with open(CONFIG_PATH, encoding="utf-8-sig") as f:
        return json.load(f)


def save_config(config: dict) -> None:
    with open(CONFIG_PATH, "w", encoding="utf-8") as f:
        json.dump(config, f, indent=2)


# ── Auth ──────────────────────────────────────────────────────────────────────

def _hash(token: str) -> str:
    return hashlib.sha256(token.encode()).hexdigest()


def require_auth(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security),
) -> None:
    if credentials is None:
        raise HTTPException(status_code=401, detail="Bearer token required")
    config = load_config()
    if _hash(credentials.credentials) != config.get("auth_token_hash", ""):
        raise HTTPException(status_code=401, detail="Invalid token")


def require_tailscale(request: Request) -> None:
    host = request.client.host if request.client else ""
    # Tailscale assigns addresses in 100.64.0.0/10
    if not (host.startswith("100.") or host in ("127.0.0.1", "::1")):
        raise HTTPException(status_code=403, detail="Access denied: Tailscale only")


# ── Process helpers ───────────────────────────────────────────────────────────

_PWSH_CANDIDATES = [
    "pwsh",
    r"C:\Program Files\PowerShell\7\pwsh.exe",
    r"C:\Program Files\PowerShell\7-preview\pwsh.exe",
]

_TAILSCALE_CANDIDATES = [
    "tailscale",
    r"C:\Program Files\Tailscale\tailscale.exe",
    r"C:\Program Files (x86)\Tailscale\tailscale.exe",
]


def _find_pwsh() -> str:
    for candidate in _PWSH_CANDIDATES:
        try:
            r = subprocess.run([candidate, "-Version"], capture_output=True, timeout=3)
            if r.returncode == 0:
                return candidate
        except (FileNotFoundError, OSError):
            continue
    raise RuntimeError(
        "PowerShell 7 (pwsh) not found. "
        "Install from https://aka.ms/powershell and re-run setup.ps1"
    )


def _find_tailscale() -> str:
    for candidate in _TAILSCALE_CANDIDATES:
        try:
            r = subprocess.run([candidate, "version"], capture_output=True, timeout=3)
            if r.returncode == 0:
                return candidate
        except (FileNotFoundError, OSError):
            continue
    raise RuntimeError(
        "tailscale CLI not found. Add it to PATH or install from https://tailscale.com/download"
    )


def _get_tailscale_ip() -> str:
    cli = _find_tailscale()
    result = subprocess.run([cli, "ip", "-4"], capture_output=True, text=True, timeout=5)
    if result.returncode != 0:
        raise RuntimeError(f"tailscale ip -4 failed: {result.stderr.strip()}")
    ip = result.stdout.strip()
    if not ip:
        raise RuntimeError("Tailscale not connected or has no IPv4 address")
    return ip


def _is_alive(project_id: str) -> bool:
    entry = sessions.get(project_id)
    if not entry:
        return False
    try:
        proc = psutil.Process(entry["pid"])
        return proc.status() not in (psutil.STATUS_ZOMBIE, psutil.STATUS_DEAD)
    except psutil.NoSuchProcess:
        return False


def _kill(project_id: str) -> bool:
    """Kill session tree. Returns True once confirmed dead."""
    entry = sessions.pop(project_id, None)
    if not entry:
        return True
    pid = entry["pid"]
    subprocess.run(
        ["taskkill", "/PID", str(pid), "/T", "/F"],
        capture_output=True, timeout=10,
    )
    # Give the OS up to 3s to reap the tree
    for _ in range(6):
        if not psutil.pid_exists(pid):
            return True
        time.sleep(0.5)
    return not psutil.pid_exists(pid)


def _preseed_trust(path: str) -> None:
    """Create .claude/settings.json in the project dir if absent.
    Claude Code skips the interactive folder-trust prompt when this file exists."""
    settings = Path(path) / ".claude" / "settings.json"
    if not settings.exists():
        settings.parent.mkdir(parents=True, exist_ok=True)
        settings.write_text("{}\n", encoding="utf-8")


def _spawn(project_id: str, path: str) -> int:
    """Spawn pwsh → claude in path. Returns PID."""
    pwsh = _find_pwsh()

    CREATE_NEW_CONSOLE = 0x00000010
    CREATE_NEW_PROCESS_GROUP = 0x00000200

    # Pre-create .claude/settings.json so Claude Code skips the folder trust dialog.
    # This is equivalent to the user having already accepted trust for that directory.
    _preseed_trust(path)

    proc = subprocess.Popen(
        [pwsh, "-NoExit", "-Command", f"Set-Location '{path}'; claude --dangerously-skip-permissions"],
        creationflags=CREATE_NEW_CONSOLE | CREATE_NEW_PROCESS_GROUP,
        close_fds=True,
    )
    sessions[project_id] = {"pid": proc.pid, "started_at": time.time()}
    return proc.pid


def _send_esc(project_id: str) -> bool:
    """Send ESC keystroke to the terminal window owned by this session's PID."""
    entry = sessions.get(project_id)
    if not entry or not _is_alive(project_id):
        return False
    pid = entry["pid"]
    pwsh = _find_pwsh()
    # WScript.Shell.AppActivate focuses the window by PID, then SendKeys injects ESC.
    script = (
        f"$ws = New-Object -ComObject WScript.Shell; "
        f"if ($ws.AppActivate({pid})) {{ Start-Sleep -Milliseconds 150; "
        f"$ws.SendKeys('{{ESC}}'); exit 0 }} else {{ exit 1 }}"
    )
    result = subprocess.run(
        [pwsh, "-Command", script], capture_output=True, timeout=5
    )
    return result.returncode == 0


def _running_sessions() -> list[str]:
    """Return project_ids of all currently running sessions."""
    running = []
    for pid in list(sessions.keys()):
        if _is_alive(pid):
            running.append(pid)
        else:
            sessions.pop(pid, None)
    return running


# ── Routes ────────────────────────────────────────────────────────────────────

@app.get("/")
async def serve_ui(request: Request):
    require_tailscale(request)
    index = WEB_DIR / "index.html"
    if not index.exists():
        return JSONResponse({"detail": "UI not yet built (step 4)"}, status_code=503)
    return FileResponse(index)


@app.get("/api/health")
async def health(request: Request, _=Depends(require_auth)):
    require_tailscale(request)
    config = load_config()
    return {
        "status": "ok",
        "hostname": config.get("hostname", ""),
        "tailscale_ip": _tailscale_ip,
        "uptime_seconds": int(time.time() - _start_time),
        "active_sessions": _running_sessions(),
    }


@app.get("/api/projects")
async def list_projects(request: Request, _=Depends(require_auth)):
    require_tailscale(request)
    config = load_config()
    result = []
    for proj in config["projects"]:
        pid_entry = sessions.get(proj["id"])
        alive = _is_alive(proj["id"])
        if pid_entry and not alive:
            sessions.pop(proj["id"], None)
            pid_entry = None
        result.append({
            "id": proj["id"],
            "name": proj["name"],
            "path": proj["path"],
            "status": "running" if alive else "idle",
            "pid": pid_entry["pid"] if alive else None,
            "started_at": pid_entry["started_at"] if alive else None,
        })
    return result


@app.post("/api/projects/{project_id}/start")
async def start_session(project_id: str, request: Request, _=Depends(require_auth)):
    require_tailscale(request)
    config = load_config()

    proj = next((p for p in config["projects"] if p["id"] == project_id), None)
    if not proj:
        raise HTTPException(status_code=404, detail=f"Project '{project_id}' not found")

    if _is_alive(project_id):
        raise HTTPException(
            status_code=409,
            detail="Session already running. Use /restart to cycle it.",
        )

    try:
        pid = _spawn(project_id, proj["path"])
    except RuntimeError as e:
        raise HTTPException(status_code=500, detail=str(e))

    return {"status": "started", "pid": pid, "project_id": project_id}


@app.post("/api/projects/{project_id}/restart")
async def restart_session(project_id: str, request: Request, _=Depends(require_auth)):
    require_tailscale(request)
    config = load_config()

    proj = next((p for p in config["projects"] if p["id"] == project_id), None)
    if not proj:
        raise HTTPException(status_code=404, detail=f"Project '{project_id}' not found")

    if _is_alive(project_id):
        _kill(project_id)

    time.sleep(2)

    try:
        pid = _spawn(project_id, proj["path"])
    except RuntimeError as e:
        raise HTTPException(status_code=500, detail=str(e))

    return {"status": "restarted", "pid": pid, "project_id": project_id}


@app.post("/api/projects/{project_id}/stop")
async def stop_session(project_id: str, request: Request, _=Depends(require_auth)):
    require_tailscale(request)
    config = load_config()

    proj = next((p for p in config["projects"] if p["id"] == project_id), None)
    if not proj:
        raise HTTPException(status_code=404, detail=f"Project '{project_id}' not found")

    if not sessions.get(project_id) and not _is_alive(project_id):
        return {"status": "already_idle", "project_id": project_id}

    dead = _kill(project_id)
    if not dead:
        raise HTTPException(
            status_code=500,
            detail="Failed to kill session — it may still be visible in Task Manager",
        )
    return {"status": "stopped", "project_id": project_id}


@app.post("/api/projects/{project_id}/esc")
async def send_esc(project_id: str, request: Request, _=Depends(require_auth)):
    require_tailscale(request)
    config = load_config()

    proj = next((p for p in config["projects"] if p["id"] == project_id), None)
    if not proj:
        raise HTTPException(status_code=404, detail=f"Project '{project_id}' not found")

    if not _is_alive(project_id):
        raise HTTPException(status_code=409, detail="No running session to send ESC to")

    sent = _send_esc(project_id)
    if not sent:
        raise HTTPException(
            status_code=500,
            detail="Could not focus the terminal window — it may be minimized or behind another app",
        )
    return {"status": "esc_sent", "project_id": project_id}


# ── Startup ───────────────────────────────────────────────────────────────────

def main():
    global _tailscale_ip

    config = load_config()

    # First-run token generation
    if not config.get("auth_token_hash"):
        token = secrets.token_urlsafe(32)
        config["auth_token_hash"] = _hash(token)
        save_config(config)
        print("\n" + "=" * 60)
        print("AUTH TOKEN (shown once — save it now):")
        print(f"  {token}")
        print("=" * 60 + "\n")

    # Detect Tailscale IP
    try:
        _tailscale_ip = _get_tailscale_ip()
    except Exception as e:
        print(f"ERROR: {e}", file=sys.stderr)
        sys.exit(1)

    port = config.get("port", 8765)
    hostname = config.get("hostname", _tailscale_ip)

    print(f"Tailscale IP : {_tailscale_ip}")
    print(f"Listening on : http://{_tailscale_ip}:{port}")
    print(f"Bookmark     : http://{hostname}:{port}")

    uvicorn.run(app, host=_tailscale_ip, port=port, log_level="info")


if __name__ == "__main__":
    main()
