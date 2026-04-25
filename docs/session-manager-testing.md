# End-to-End Phone Test Checklist

Run these checks in order the first time you set up the service,
and after any significant change (new project, token rotation, OS update).

## Prerequisites

- [ ] `setup.ps1` completed without errors
- [ ] `install-service.ps1` ran as Administrator and reported "Port 8765 is listening"
- [ ] Phone is connected to your Tailscale network
- [ ] Claude mobile app is installed and signed in to Claude Pro

---

## 1. Server reachability

**From the desktop** (PowerShell):
```powershell
Invoke-RestMethod http://100.121.27.81:8765/api/health `
  -Headers @{ Authorization = "Bearer <your-token>" }
```
Expected: JSON with `"status": "ok"` and `"hostname": "voltreezy"`.

**From the phone browser**:
- Open `http://voltreezy:8765`
- Expected: token entry screen loads with dark background
- If it times out: check Tailscale is connected on both devices

---

## 2. Token auth

- [ ] Open `http://voltreezy:8765` on phone
- [ ] Enter a **wrong** token → red "Invalid token. Try again." message appears
- [ ] Enter the **correct** token → project cards load
- [ ] Close the browser tab, reopen → token entry screen shown again (sessionStorage cleared — expected)
- [ ] Re-enter token → cards load without re-fetching from server with wrong token

---

## 3. Project list

- [ ] All three projects (Chimera, AD/SB Tracker, Second Brain) show as cards
- [ ] Each card shows a gray dot and "Idle" status
- [ ] Each card has a single **Start** button
- [ ] Path text is visible (truncated on small screens is OK)

---

## 4. Start a session

- [ ] Tap **Start** on the Second Brain card
- [ ] Card dot turns yellow ("transitioning") immediately
- [ ] A new PowerShell 7 window opens on the `voltreezy` desktop running `claude`
- [ ] After ~3 seconds the toast appears: "Session starting — switch to the Claude app → Code tab."
- [ ] After the next 5-second poll the card shows green dot + uptime ("started Xs ago")
- [ ] **Start** button is replaced by **Restart** + **Stop**

---

## 5. One-session enforcement

- [ ] With Second Brain running, tap **Start** on Chimera
- [ ] Expected: toast shows the 409 error message about one session at a time
- [ ] Second Brain card still shows running; Chimera card still shows idle

---

## 6. Remote Control handoff

- [ ] With a session running, open the Claude mobile app
- [ ] Tap the **Code** tab (bottom nav)
- [ ] Expected: Claude Code connects to the running session on `voltreezy`
- [ ] Send a test message: "What directory am I in?"
- [ ] Expected: Claude responds with the project path

---

## 7. Restart

- [ ] Tap **Restart** on the running project
- [ ] Card enters yellow transitioning state
- [ ] Old `pwsh` window on desktop closes; new one opens after ~2 seconds
- [ ] Card returns to green running state with uptime reset to "0s ago"
- [ ] Remote Control reconnects in the Claude app (may need to re-tap Code tab)

---

## 8. Stop

- [ ] Tap **Stop** on the running project
- [ ] `pwsh` window on desktop closes
- [ ] Card returns to gray idle with **Start** button
- [ ] `GET /api/projects` confirms `"status": "idle"` for that project

---

## 9. Ghost detection

Simulate a dead session (run this on the desktop):
```powershell
# Get the PID of the running claude session from the UI or /api/projects
taskkill /PID <pid> /T /F
```
- [ ] Within 5–10 seconds (next poll) the card auto-flips to idle
- [ ] No manual refresh required

---

## 10. Service persistence

- [ ] Reboot `voltreezy`
- [ ] After login, wait ~30 seconds
- [ ] Check: `Get-Service ClaudeSessionManager` shows `Running`
- [ ] Open `http://voltreezy:8765` on phone → cards load without any manual start

---

## Known limitations (by design)

| Limitation | Why |
|-----------|-----|
| One session at a time | Remote Control is single-session per machine |
| 10-min network timeout | Built into Remote Control — restart to reconnect |
| `--dangerously-skip-permissions` not passed | Incompatible with Remote Control |
| Token re-entry on tab close | `sessionStorage` is intentionally ephemeral |
| Windows only | Uses `CREATE_NEW_CONSOLE`, `taskkill`, and `pwsh` |
