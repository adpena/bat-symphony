# scripts/daemon.ps1 - Start/stop/status for BatSymphony daemon
param([string]$Action = "start")

$RepoRoot = Split-Path -Parent (Split-Path -Parent $PSCommandPath)
$StateDir = "$RepoRoot\state"
$PidFile = "$StateDir\daemon.pid"
$LogFile = "$StateDir\logs\daemon.log"
$ErrFile = "$StateDir\logs\daemon.log.err"

# Find uv
$UvPath = "$env:USERPROFILE\.local\bin\uv.exe"
if (-not (Test-Path $UvPath)) {
    $UvPath = (Get-Command uv -ErrorAction SilentlyContinue).Source
    if (-not $UvPath) {
        Write-Host "[FAIL] uv not found"
        exit 1
    }
}

switch ($Action) {
    "start" {
        if (Test-Path $PidFile) {
            $dpid = [int](Get-Content $PidFile -Raw).Trim()
            if (Get-Process -Id $dpid -ErrorAction SilentlyContinue) {
                Write-Host "Daemon already running (PID $dpid)"
                exit 0
            }
            Remove-Item $PidFile -Force
        }
        New-Item -ItemType Directory -Force -Path "$StateDir\logs" | Out-Null

        # Load .env if present
        $envFile = "$RepoRoot\.env"
        if (Test-Path $envFile) {
            Get-Content $envFile | ForEach-Object {
                if ($_ -match '^\s*([A-Za-z_][A-Za-z0-9_]*)\s*=\s*(.*)$' -and $_ -notmatch '^\s*#') {
                    [Environment]::SetEnvironmentVariable($Matches[1], $Matches[2], "Process")
                }
            }
        }

        $proc = Start-Process -FilePath $UvPath `
            -ArgumentList "run", "python", "-m", "bat_symphony" `
            -WorkingDirectory $RepoRoot `
            -RedirectStandardOutput $LogFile `
            -RedirectStandardError $ErrFile `
            -PassThru -WindowStyle Hidden

        Start-Sleep -Seconds 2
        if ($proc.HasExited) {
            Write-Host "[FAIL] Daemon exited immediately. Check $ErrFile"
            if (Test-Path $ErrFile) { Get-Content $ErrFile -Tail 10 }
            exit 1
        }

        $proc.Id | Out-File -FilePath $PidFile -NoNewline -Encoding ascii
        Write-Host "Daemon started (PID $($proc.Id))"
        Write-Host "Logs: $LogFile"
    }
    "stop" {
        if (Test-Path $PidFile) {
            $dpid = [int](Get-Content $PidFile -Raw).Trim()
            $proc = Get-Process -Id $dpid -ErrorAction SilentlyContinue
            if ($proc) {
                # Stop the process tree
                Stop-Process -Id $dpid -Force -ErrorAction SilentlyContinue
                Start-Sleep -Seconds 1
            }
            Remove-Item $PidFile -Force
            Write-Host "Daemon stopped"
        } else {
            # Try to find and kill orphaned daemon
            $procs = Get-Process -Name python -ErrorAction SilentlyContinue |
                Where-Object { $_.CommandLine -like "*bat_symphony*" }
            if ($procs) {
                $procs | Stop-Process -Force
                Write-Host "Killed orphaned daemon process(es)"
            } else {
                Write-Host "No daemon running"
            }
        }
    }
    "restart" {
        & $PSCommandPath -Action stop
        Start-Sleep -Seconds 2
        & $PSCommandPath -Action start
    }
    "status" {
        if (Test-Path $PidFile) {
            $dpid = [int](Get-Content $PidFile -Raw).Trim()
            if (Get-Process -Id $dpid -ErrorAction SilentlyContinue) {
                Write-Host "Daemon running (PID $dpid)"
                try {
                    $resp = Invoke-RestMethod -Uri "http://localhost:8787/health" -TimeoutSec 5
                    $resp | ConvertTo-Json -Depth 3
                } catch {
                    Write-Host "HTTP health check failed (process running but not responding)"
                }
            } else {
                Write-Host "Daemon not running (stale PID file)"
                Remove-Item $PidFile -Force
            }
        } else {
            Write-Host "No daemon running"
        }
    }
    "logs" {
        if (Test-Path $LogFile) {
            Get-Content $LogFile -Tail 50
        } else {
            Write-Host "No log file found"
        }
    }
    default {
        Write-Host "Usage: daemon.ps1 {start|stop|restart|status|logs}"
    }
}
