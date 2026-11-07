Write-Host "Running DODO Platform Test Suites..." -ForegroundColor Cyan
$env:PYTHONPATH = "D:\DODO"
& ".\.venv\Scripts\pytest.exe" backend/tests/test_backend.py backend/tests/test_end_to_end_demo.py -v
