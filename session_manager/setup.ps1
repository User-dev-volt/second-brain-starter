#Requires -Version 5.1
<#
.SYNOPSIS
    First-run setup for Claude Code Session Manager.
    Run this once before install-service.ps1.
    Does NOT require elevation.
#>

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

$Root      = Split-Path $PSScriptRoot -Parent   # repo root
$ConfigPath = Join-Path $PSScriptRoot "config.json"
$Python    = Join-Path $Root ".venv\Scripts\python.exe"

function Write-Step($n, $msg) { Write-Host "`n[$n] $msg" -ForegroundColor Cyan }
function Write-Ok($msg)       { Write-Host "    OK  $msg" -ForegroundColor Green }
function Write-Warn($msg)     { Write-Host "    WARN $msg" -ForegroundColor Yellow }
function Write-Fail($msg)     { Write-Host "    FAIL $msg" -ForegroundColor Red; exit 1 }
function Pause-ForUser($msg)  {
    Write-Host "`n    $msg" -ForegroundColor White
    Write-Host "    Press ENTER when done..." -ForegroundColor DarkGray -NoNewline
    Read-Host | Out-Null
}

# ── 1. Python venv ─────────────────────────────────────────────────────────

Write-Step 1 "Checking Python venv"
if (-not (Test-Path $Python)) {
    Write-Fail "Python venv not found at $Python`n    Run: python -m venv .venv && .venv\Scripts\pip install -r requirements.txt"
}
Write-Ok $Python

# ── 2. Dependencies ────────────────────────────────────────────────────────

Write-Step 2 "Checking Python dependencies"
$missing = @()
foreach ($pkg in @("fastapi", "uvicorn", "psutil")) {
    $check = & $Python -c "import $pkg" 2>&1
    if ($LASTEXITCODE -ne 0) { $missing += $pkg }
}
if ($missing.Count -gt 0) {
    Write-Warn "Missing packages: $($missing -join ', '). Installing..."
    & $Python -m pip install fastapi "uvicorn[standard]" psutil --quiet
    Write-Ok "Installed"
} else {
    Write-Ok "All dependencies present"
}

# ── 3. PowerShell 7 (pwsh) ─────────────────────────────────────────────────

Write-Step 3 "Checking PowerShell 7 (pwsh)"
$pwshCandidates = @(
    "pwsh",
    "C:\Program Files\PowerShell\7\pwsh.exe"
)
$pwshPath = $null
foreach ($c in $pwshCandidates) {
    try {
        $v = & $c -Version 2>&1
        if ($LASTEXITCODE -eq 0) { $pwshPath = $c; break }
    } catch {}
}
if (-not $pwshPath) {
    Write-Host ""
    Write-Host "    PowerShell 7 is required to spawn Claude Code sessions." -ForegroundColor Red
    Write-Host "    Install it from: https://aka.ms/powershell" -ForegroundColor Yellow
    Write-Host "    After installing, re-run this script." -ForegroundColor Yellow
    exit 1
}
Write-Ok "Found: $pwshPath"

# ── 4. Claude Code version ─────────────────────────────────────────────────

Write-Step 4 "Checking Claude Code installation"
try {
    $rawVersion = (& claude --version 2>&1) | Select-Object -First 1
} catch {
    Write-Fail "claude command not found. Install Claude Code first: https://claude.ai/code"
}

# Parse version number from output like "Claude Code v2.1.52" or "2.1.52"
$vMatch = [regex]::Match($rawVersion, '(\d+)\.(\d+)\.(\d+)')
if (-not $vMatch.Success) {
    Write-Warn "Could not parse version from: $rawVersion"
} else {
    $major = [int]$vMatch.Groups[1].Value
    $minor = [int]$vMatch.Groups[2].Value
    $patch = [int]$vMatch.Groups[3].Value

    $required = @(2, 1, 52)
    $actual   = @($major, $minor, $patch)
    $ok = $false
    for ($i = 0; $i -lt 3; $i++) {
        if ($actual[$i] -gt $required[$i]) { $ok = $true; break }
        if ($actual[$i] -lt $required[$i]) { $ok = $false; break }
        $ok = $true
    }

    if (-not $ok) {
        Write-Fail "Claude Code $major.$minor.$patch is too old. Requires >= 2.1.52.`n    Run: claude update"
    }
    Write-Ok "Claude Code $major.$minor.$patch"
}

# ── 5. Remote Control — manual step ───────────────────────────────────────

Write-Step 5 "Enable Remote Control (manual step required)"
Write-Host @"

    Remote Control cannot be enabled from the command line — it must be
    set inside a running Claude Code session.

    Steps:
      1. Open a terminal and run:  claude
      2. Once inside Claude Code, type:  /config
      3. Find the setting:  "Enable Remote Control for all sessions"
      4. Set it to:  true (or "on")
      5. Close that Claude Code session and return here.

    This setting is stored globally and applies to every future session,
    including the ones this service will spawn.

"@ -ForegroundColor White
Pause-ForUser "Complete the /config step above, then press ENTER to continue."

# ── 6. Tailscale check ─────────────────────────────────────────────────────

Write-Step 6 "Checking Tailscale"
$tsCandidates = @(
    "tailscale",
    "C:\Program Files\Tailscale\tailscale.exe"
)
$tsPath = $null
foreach ($c in $tsCandidates) {
    try {
        $v = & $c version 2>&1
        if ($LASTEXITCODE -eq 0) { $tsPath = $c; break }
    } catch {}
}
if (-not $tsPath) {
    Write-Fail "Tailscale not found. Install from https://tailscale.com/download"
}
$tsIP = (& $tsPath ip -4 2>&1).Trim()
if (-not $tsIP) {
    Write-Fail "Tailscale is installed but not connected. Connect to your tailnet first."
}
Write-Ok "Tailscale IP: $tsIP"

# ── 7. Auth token ──────────────────────────────────────────────────────────

Write-Step 7 "Generating auth token"

$config = Get-Content $ConfigPath -Raw | ConvertFrom-Json
$skipToken = $false

if ($config.auth_token_hash) {
    Write-Warn "A token is already stored in config.json."
    $reset = Read-Host "    Generate a new token? This invalidates the old one. (y/N)"
    if ($reset.Trim().ToLower() -ne "y") {
        Write-Host "    Keeping existing token." -ForegroundColor DarkGray
        $skipToken = $true
    }
}

if (-not $skipToken) {
    # Use Python's secrets module for a cryptographically strong token
    $genScript = @"
import secrets, hashlib, json, pathlib
token = secrets.token_urlsafe(32)
h = hashlib.sha256(token.encode()).hexdigest()
p = pathlib.Path(r'$($ConfigPath.Replace("\","\\"))')
d = json.loads(p.read_text(encoding='utf-8-sig'))
d['auth_token_hash'] = h
p.write_text(json.dumps(d, indent=2), encoding='utf-8')
print(token)
"@
    $token = (& $Python -c $genScript).Trim()

    Write-Host ""
    Write-Host "    ╔══════════════════════════════════════════════════════════╗" -ForegroundColor Yellow
    Write-Host "    ║  AUTH TOKEN — shown once, never stored in plain text    ║" -ForegroundColor Yellow
    Write-Host "    ║                                                          ║" -ForegroundColor Yellow
    Write-Host "    ║  $token  ║" -ForegroundColor Yellow
    Write-Host "    ║                                                          ║" -ForegroundColor Yellow
    Write-Host "    ║  Save this now. You will enter it in the mobile UI.     ║" -ForegroundColor Yellow
    Write-Host "    ╚══════════════════════════════════════════════════════════╝" -ForegroundColor Yellow
    Write-Host ""
    Pause-ForUser "Copy the token above, then press ENTER."
}

# ── 8. Summary ─────────────────────────────────────────────────────────────

$hostname = $config.hostname
$port     = $config.port

Write-Host ""
Write-Host "  Setup complete!" -ForegroundColor Green
Write-Host ""
Write-Host "  Next step: run install-service.ps1 as Administrator to start on boot."
Write-Host "  Or for a manual test run:"
Write-Host "      $Python $(Join-Path $PSScriptRoot 'server.py')" -ForegroundColor Cyan
Write-Host ""
Write-Host "  Bookmark on your phone:" -ForegroundColor White
Write-Host "      http://${hostname}:${port}" -ForegroundColor Cyan
Write-Host ""
