Write-Host "Starting DODO Local Agent on port 8001..." -ForegroundColor Green

# Check if port 8001 is occupied and free it
$connections = Get-NetTCPConnection -LocalPort 8001 -ErrorAction SilentlyContinue
if ($connections) {
    Write-Host "Port 8001 is currently occupied. Freeing port 8001..." -ForegroundColor Yellow
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

& $pythonCmd -m uvicorn local_agent.main:app --host 127.0.0.1 --port 8001
