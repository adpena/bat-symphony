# scripts/doctor.ps1 - Health check for BatSymphony stack
$errors = 0

Write-Host "=== BatSymphony Doctor ==="

# Check uv
$uv = "$env:USERPROFILE\.local\bin\uv.exe"
if (Test-Path $uv) {
    $uvv = & $uv --version 2>&1
    Write-Host "[OK] uv: $uvv"
} else {
    Write-Host "[FAIL] uv not found at $uv"
    $errors++
}

# Check git
try {
    $gitv = git --version 2>&1
    Write-Host "[OK] git: $gitv"
} catch {
    Write-Host "[FAIL] git not found"
    $errors++
}

# Check gh
$gh = "$env:USERPROFILE\.local\bin\gh.exe"
if (Test-Path $gh) {
    $ghv = & $gh --version 2>&1 | Select-Object -First 1
    Write-Host "[OK] gh: $ghv"
} else {
    Write-Host "[FAIL] gh not found at $gh"
    $errors++
}

# Check Ollama
try {
    $resp = Invoke-RestMethod -Uri "http://localhost:11434/api/tags" -TimeoutSec 5
    $models = ($resp.models | ForEach-Object { $_.name }) -join ", "
    Write-Host "[OK] Ollama: $models"
} catch {
    Write-Host "[FAIL] Ollama not reachable at localhost:11434"
    $errors++
}

# Check daemon
try {
    $health = Invoke-RestMethod -Uri "http://localhost:8787/health" -TimeoutSec 5
    Write-Host "[OK] Daemon: status=$($health.status), uptime=$($health.uptime_s)s"
} catch {
    Write-Host "[WARN] Daemon not running (this is expected if not started)"
}

if ($errors -eq 0) {
    Write-Host "`n=== All checks passed ==="
} else {
    Write-Host "`n=== $errors check(s) failed ==="
}
exit $errors
