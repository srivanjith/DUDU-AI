Write-Host "Starting DODO Backend on port 8000..." -ForegroundColor Green
$env:PYTHONPATH = "D:\DODO"
& ".\.venv\Scripts\python.exe" -m uvicorn backend.main:app --host 0.0.0.0 --port 8000 --reload

