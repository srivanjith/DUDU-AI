Write-Host "Starting DODO Local Agent on port 8001..." -ForegroundColor Green
$env:PYTHONPATH = "D:\DODO"

$pythonCmd = "python"
if (Test-Path ".\.venv\Scripts\python.exe") {
    try {
        & ".\.venv\Scripts\python.exe" -V | Out-Null
        $pythonCmd = ".\.venv\Scripts\python.exe"
    } catch {
        $pythonCmd = "python"
    }
}

& $pythonCmd -m uvicorn local_agent.main:app --host 127.0.0.1 --port 8001
