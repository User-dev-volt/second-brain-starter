# Research Notes — Claude Code Session Manager

## 1. Spawning & killing process trees on Windows (pwsh → claude → MCP children)

### Spawning

Use `subprocess.Popen` with two creation flags:

```python
import subprocess

proc = subprocess.Popen(
    ["pwsh", "-NoExit", "-Command", f"Set-Location '{path}'; claude"],
    creationflags=subprocess.CREATE_NEW_CONSOLE | subprocess.CREATE_NEW_PROCESS_GROUP,
)
```

- `CREATE_NEW_CONSOLE` opens a visible PowerShell 7 window on the desktop (required by spec).
- `CREATE_NEW_PROCESS_GROUP` gives the tree its own Windows job/group ID, which makes tree-killing more predictable.
- Do **not** use `shell=True` — it spawns a hidden `cmd.exe` wrapper that can detach children when killed, producing orphans.

### Killing

`taskkill /PID <pid> /T /F` (as specified) terminates the entire tree rooted at `<pid>` forcefully.
Confirm death by checking `proc.poll() is not None` or catching `psutil.NoSuchProcess`.

`psutil` offers the most reliable cross-platform alternative if `taskkill` fails for any reason:

```python
import psutil, signal

def kill_tree(pid: int):
    try:
        parent = psutil.Process(pid)
        children = parent.children(recursive=True)
        for child in children:
            child.kill()
        parent.kill()
        psutil.wait_procs([parent] + children, timeout=5)
    except psutil.NoSuchProcess:
        pass
```

### Ghost detection

After a Restart or after the Remote Control 10-minute timeout, the tracked PID may no longer be alive.
Check with `psutil.pid_exists(pid)` or `proc.poll() is not None` on every `/api/projects` poll.
Mark status `dead` and surface a Restart button rather than reporting it as running.

### Key gotcha

`CREATE_NEW_CONSOLE` spawns in a **separate window station on the local desktop**. The parent Python
process (uvicorn running as NSSM service) cannot share a console with the child — that is intentional
and correct. The child window will be visible on the desktop but not attached to any pipe.

---

## 2. NSSM + FastAPI/uvicorn as a Windows service

### What NSSM does

NSSM wraps any executable (here: Python/uvicorn) as a proper Windows service without modifying the app.
It handles start-on-boot, restart-on-crash, stdout/stderr log capture.

### Install NSSM

Download `nssm.exe` from https://nssm.cc/download — single binary, no installer.
Place it somewhere on `PATH` (e.g. `C:\tools\nssm.exe`).

### Create the service (CLI — used in `install-service.ps1`)

```powershell
$python = "D:\second-brain-starter\.venv\Scripts\python.exe"
$appDir  = "D:\second-brain-starter\session_manager"
$logDir  = "D:\second-brain-starter\logs"

nssm install ClaudeSessionManager $python
nssm set ClaudeSessionManager AppParameters "-m uvicorn server:app --host <tailscale_ip> --port 8765"
nssm set ClaudeSessionManager AppDirectory  $appDir
nssm set ClaudeSessionManager AppStdout     "$logDir\service-stdout.log"
nssm set ClaudeSessionManager AppStderr     "$logDir\service-stderr.log"
nssm set ClaudeSessionManager AppRotateFiles 1
nssm set ClaudeSessionManager AppRestartDelay 5000   # ms, restart on crash
nssm set ClaudeSessionManager Start SERVICE_AUTO_START
nssm start ClaudeSessionManager
```

### Uninstall

```powershell
nssm stop ClaudeSessionManager
nssm remove ClaudeSessionManager confirm
```

### Important: service account & desktop access

By default NSSM runs as `LocalSystem`. Because the server spawns `CREATE_NEW_CONSOLE` windows that
need to be **visible on the interactive desktop**, the service must either:

- Run as the logged-in user account (set in NSSM → Log On tab), **or**
- Have "Allow service to interact with desktop" enabled (legacy, not reliable on Windows 10/11).

**Recommended:** set the service to run as your user account with stored credentials.

```powershell
nssm set ClaudeSessionManager ObjectName ".\Alec" "YourPassword"
```

Without this the `CREATE_NEW_CONSOLE` window spawns in Session 0 (invisible).

---

## 3. Detecting the Tailscale interface IP on Windows (Python)

### Preferred: CLI subprocess

Tailscale ships a CLI that works on v1.8+:

```python
import subprocess

def get_tailscale_ip() -> str:
    result = subprocess.run(
        ["tailscale", "ip", "-4"],
        capture_output=True, text=True, timeout=5
    )
    if result.returncode != 0:
        raise RuntimeError(f"tailscale ip -4 failed: {result.stderr.strip()}")
    ip = result.stdout.strip()
    if not ip:
        raise RuntimeError("Tailscale is not connected or has no IPv4 address")
    return ip
```

Call this once at server startup; store the result. Re-running on each request is unnecessary overhead.

### Alternative: tailscale status --json

```python
import subprocess, json

raw = subprocess.check_output(["tailscale", "status", "--json"], text=True)
data = json.loads(raw)
ip = data["Self"]["TailscaleIPs"][0]   # first IPv4
```

This gives more metadata (hostname, online status) but is heavier to parse.

### Binding uvicorn to the Tailscale IP

Pass the detected IP as `--host` when uvicorn starts. The server then only accepts connections
arriving on the Tailscale interface — no exposure on LAN or WAN. Requests from other interfaces
will be refused at the OS level (not even reaching FastAPI).

To double-check at the application layer, compare `request.client.host` against the known Tailscale
subnet (`100.64.0.0/10`) and reject anything outside it.

---

## Decision summary

| Question | Decision |
|---|---|
| How to spawn claude window | `Popen(["pwsh",…], creationflags=CREATE_NEW_CONSOLE\|CREATE_NEW_PROCESS_GROUP)` |
| How to kill tree | `taskkill /PID <pid> /T /F`, confirm with `proc.poll()` |
| Ghost detection | `psutil.pid_exists(pid)` on every status poll |
| Process tree library | `psutil` as fallback; `taskkill` as primary (already on all Windows) |
| Service wrapper | NSSM with service running as logged-in user account |
| Tailscale IP | `tailscale ip -4` via subprocess at startup |
| Bind address | Tailscale IP only — no `0.0.0.0` |
