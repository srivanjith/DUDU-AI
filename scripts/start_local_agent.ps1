Write-Host "Starting DODO Local Agent on port 8001..." -ForegroundColor Green
$env:PYTHONPATH = "D:\DODO"
& ".\.venv\Scripts\python.exe" -m uvicorn local_agent.main:app --host 127.0.0.1 --port 8001 --reload
