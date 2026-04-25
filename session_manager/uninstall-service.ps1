#Requires -RunAsAdministrator
#Requires -Version 5.1
<#
.SYNOPSIS
    Stop and remove the ClaudeSessionManager Windows service.
    Does not delete any files.
#>

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

$ServiceName = "ClaudeSessionManager"

function Write-Step($n, $msg) { Write-Host "`n[$n] $msg" -ForegroundColor Cyan }
function Write-Ok($msg)       { Write-Host "    OK  $msg" -ForegroundColor Green }

# ── Locate NSSM ───────────────────────────────────────────────────────────

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
    Write-Host "    NSSM not found — attempting sc.exe fallback" -ForegroundColor Yellow
    $svc = Get-Service -Name $ServiceName -ErrorAction SilentlyContinue
    if ($svc) {
        Stop-Service -Name $ServiceName -Force -ErrorAction SilentlyContinue
        sc.exe delete $ServiceName
        Write-Ok "Service removed via sc.exe"
    } else {
        Write-Host "    Service '$ServiceName' not found — nothing to remove." -ForegroundColor DarkGray
    }
    exit 0
}
Write-Ok "NSSM: $nssm"

# ── Stop and remove ───────────────────────────────────────────────────────

Write-Step 2 "Stopping $ServiceName"
$svc = Get-Service -Name $ServiceName -ErrorAction SilentlyContinue
if (-not $svc) {
    Write-Host "    Service '$ServiceName' not found — nothing to remove." -ForegroundColor DarkGray
    exit 0
}
& $nssm stop $ServiceName confirm 2>&1 | Out-Null
Write-Ok "Stopped"

Write-Step 3 "Removing $ServiceName"
& $nssm remove $ServiceName confirm
Write-Ok "Removed"

Write-Host ""
Write-Host "  Done. Log files kept at session_manager\logs\" -ForegroundColor Green
Write-Host "  Re-install any time with install-service.ps1" -ForegroundColor DarkGray
Write-Host ""
