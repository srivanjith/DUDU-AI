Write-Host "Starting DODO Backend on port 8000..." -ForegroundColor Green

# Check if port 8000 is occupied and free it
$connections = Get-NetTCPConnection -LocalPort 8000 -ErrorAction SilentlyContinue
if ($connections) {
    Write-Host "Port 8000 is currently occupied. Freeing port 8000..." -ForegroundColor Yellow
    foreach ($conn in $connections) {
        try {
            Stop-Process -Id $conn.OwningProcess -Force -ErrorAction SilentlyContinue
        } catch {}
    }
    Start-Sleep -Milliseconds 500
}

$env:PYTHONPATH = "D:\DODO"
Set-Location "D:\DODO"

$pythonCmd = "python"
if (Test-Path ".\.venv\Scripts\python.exe") {
    $pythonCmd = ".\.venv\Scripts\python.exe"
}

& $pythonCmd -m uvicorn backend.main:app --host 127.0.0.1 --port 8000 --reload
