#Requires -RunAsAdministrator
#Requires -Version 5.1
<#
.SYNOPSIS
    Install ClaudeSessionManager as a Windows service via NSSM.
    Must be run as Administrator. Run setup.ps1 first.
#>

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

$ServiceName = "ClaudeSessionManager"
$Root        = Split-Path $PSScriptRoot -Parent
$Python      = Join-Path $Root ".venv\Scripts\python.exe"
$ServerScript = Join-Path $PSScriptRoot "server.py"
$LogDir      = Join-Path $PSScriptRoot "logs"

function Write-Step($n, $msg) { Write-Host "`n[$n] $msg" -ForegroundColor Cyan }
function Write-Ok($msg)       { Write-Host "    OK  $msg" -ForegroundColor Green }
function Write-Fail($msg)     { Write-Host "    FAIL $msg" -ForegroundColor Red; exit 1 }

# ── 1. Locate NSSM ────────────────────────────────────────────────────────

Write-Step 1 "Locating NSSM"
$nssmCandidates = @("nssm", "C:\tools\nssm.exe", "C:\Windows\System32\nssm.exe")
$nssm = $null
foreach ($c in $nssmCandidates) {
    try {
        $null = & $c version 2>&1
        if ($LASTEXITCODE -eq 0) { $nssm = $c; break }
    } catch {}
}
if (-not $nssm) {
    Write-Host @"

    NSSM not found. Install it:
      1. Download nssm.exe from https://nssm.cc/download
      2. Place nssm.exe in C:\tools\ (or anywhere on PATH)
      3. Re-run this script.

"@ -ForegroundColor Yellow
    exit 1
}
Write-Ok "NSSM: $nssm"

# ── 2. Prereqs ────────────────────────────────────────────────────────────

Write-Step 2 "Checking prereqs"
if (-not (Test-Path $Python))      { Write-Fail "Python venv missing: $Python — run setup.ps1 first" }
if (-not (Test-Path $ServerScript)) { Write-Fail "server.py not found: $ServerScript" }
New-Item -ItemType Directory -Path $LogDir -Force | Out-Null
Write-Ok "Python: $Python"
Write-Ok "Server: $ServerScript"
Write-Ok "Logs:   $LogDir"

# ── 3. Check config has a token ───────────────────────────────────────────

Write-Step 3 "Checking config.json"
$configPath = Join-Path $PSScriptRoot "config.json"
$config = Get-Content $configPath -Raw | ConvertFrom-Json
if (-not $config.auth_token_hash) {
    Write-Fail "auth_token_hash is empty in config.json — run setup.ps1 first"
}
Write-Ok "Token hash present"

# ── 4. Remove existing service if present ────────────────────────────────

Write-Step 4 "Removing any existing $ServiceName service"
$existing = Get-Service -Name $ServiceName -ErrorAction SilentlyContinue
if ($existing) {
    & $nssm stop $ServiceName confirm 2>&1 | Out-Null
    & $nssm remove $ServiceName confirm
    Write-Ok "Removed old service"
} else {
    Write-Ok "No existing service found"
}

# ── 5. Get user account for service ──────────────────────────────────────

Write-Step 5 "Service account"
Write-Host @"

    The service must run as YOUR user account (not LocalSystem) so that
    Claude Code windows appear on your desktop.

    Enter your Windows username and password below.
    These are stored securely by the Windows Service Control Manager.

"@ -ForegroundColor White

$currentUser = "$env:COMPUTERNAME\$env:USERNAME"
Write-Host "    Current user: $currentUser" -ForegroundColor DarkGray
$svcUser = Read-Host "    Service account username (ENTER to use '$currentUser')"
if (-not $svcUser.Trim()) { $svcUser = $currentUser }
$svcPassSecure = Read-Host "    Password for $svcUser" -AsSecureString
$svcPass = [Runtime.InteropServices.Marshal]::PtrToStringAuto(
    [Runtime.InteropServices.Marshal]::SecureStringToBSTR($svcPassSecure)
)

# ── 6. Install service ────────────────────────────────────────────────────

Write-Step 6 "Installing $ServiceName"

& $nssm install $ServiceName $Python
& $nssm set $ServiceName AppParameters      "`"$ServerScript`""
& $nssm set $ServiceName AppDirectory       $PSScriptRoot
& $nssm set $ServiceName AppStdout          (Join-Path $LogDir "service-stdout.log")
& $nssm set $ServiceName AppStderr          (Join-Path $LogDir "service-stderr.log")
& $nssm set $ServiceName AppRotateFiles     1
& $nssm set $ServiceName AppRotateOnline    1
& $nssm set $ServiceName AppRotateBytes     10485760   # 10 MB
& $nssm set $ServiceName AppRestartDelay    5000
& $nssm set $ServiceName Start              SERVICE_AUTO_START
& $nssm set $ServiceName DisplayName        "Claude Session Manager"
& $nssm set $ServiceName Description        "Manages Claude Code sessions via mobile web UI"
& $nssm set $ServiceName ObjectName         $svcUser $svcPass

# Wipe the plain-text password from memory immediately
$svcPass = $null
[System.GC]::Collect()

Write-Ok "Service registered"

# ── 7. Start service ──────────────────────────────────────────────────────

Write-Step 7 "Starting service"
& $nssm start $ServiceName
Start-Sleep -Seconds 3
$svc = Get-Service -Name $ServiceName
Write-Ok "Service status: $($svc.Status)"

# ── 8. Verify port is open ────────────────────────────────────────────────

Write-Step 8 "Verifying port $($config.port)"
$port = $config.port
$listening = netstat -ano | Select-String ":$port\s"
if ($listening) {
    Write-Ok "Port $port is listening"
} else {
    Write-Host "    Port $port not yet open — check logs at $LogDir" -ForegroundColor Yellow
}

# ── Done ──────────────────────────────────────────────────────────────────

Write-Host ""
Write-Host "  Service installed and running!" -ForegroundColor Green
Write-Host ""
Write-Host "  Useful commands:"
Write-Host "    Get-Service $ServiceName"                              -ForegroundColor DarkGray
Write-Host "    Restart-Service $ServiceName"                         -ForegroundColor DarkGray
Write-Host "    Get-Content '$LogDir\service-stdout.log' -Tail 20"   -ForegroundColor DarkGray
Write-Host ""
Write-Host "  Bookmark on your phone:" -ForegroundColor White
Write-Host "    http://$($config.hostname):$($config.port)" -ForegroundColor Cyan
Write-Host ""
