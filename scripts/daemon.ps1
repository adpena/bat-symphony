# scripts/daemon.ps1 - Start/stop/status for BatSymphony daemon
param([string]$Action = "start")

$RepoRoot = Split-Path -Parent (Split-Path -Parent $PSCommandPath)
$PidFile = "$RepoRoot\state\daemon.pid"
$LogFile = "$RepoRoot\state\logs\daemon.log"
$UvPath = "$env:USERPROFILE\.local\bin\uv.exe"

switch ($Action) {
    "start" {
        if (Test-Path $PidFile) {
            $pid = Get-Content $PidFile
            if (Get-Process -Id $pid -ErrorAction SilentlyContinue) {
                Write-Host "Daemon already running (PID $pid)"
                exit 0
            }
        }
        New-Item -ItemType Directory -Force -Path "$RepoRoot\state\logs" | Out-Null
        $proc = Start-Process -FilePath $UvPath -ArgumentList "run", "python", "-m", "bat_symphony" -WorkingDirectory $RepoRoot -RedirectStandardOutput $LogFile -RedirectStandardError "$LogFile.err" -PassThru -NoNewWindow
        $proc.Id | Out-File -FilePath $PidFile -NoNewline
        Write-Host "Daemon started (PID $($proc.Id))"
    }
    "stop" {
        if (Test-Path $PidFile) {
            $pid = Get-Content $PidFile
            Stop-Process -Id $pid -ErrorAction SilentlyContinue
            Remove-Item $PidFile
            Write-Host "Daemon stopped"
        } else {
            Write-Host "No daemon running"
        }
    }
    "status" {
        if (Test-Path $PidFile) {
            $pid = Get-Content $PidFile
            if (Get-Process -Id $pid -ErrorAction SilentlyContinue) {
                Write-Host "Daemon running (PID $pid)"
                try {
                    $resp = Invoke-RestMethod -Uri "http://localhost:8787/health" -TimeoutSec 5
                    $resp | ConvertTo-Json
                } catch {
                    Write-Host "HTTP health check failed"
                }
            } else {
                Write-Host "Daemon not running (stale PID file)"
                Remove-Item $PidFile
            }
        } else {
            Write-Host "No daemon running"
        }
    }
}
