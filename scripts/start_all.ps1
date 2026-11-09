# DODO One-Click Local Launcher
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "   🦅 Launching DODO Local Platform    " -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan

# 1. Start Backend in new window
Start-Process powershell -ArgumentList "-NoExit", "-Command", "cd D:\DODO; powershell -ExecutionPolicy Bypass -File .\scripts\start_backend.ps1"

# 2. Start Local Agent in new window
Start-Process powershell -ArgumentList "-NoExit", "-Command", "cd D:\DODO; powershell -ExecutionPolicy Bypass -File .\scripts\start_local_agent.ps1"

# 3. Start Frontend in new window
Start-Process powershell -ArgumentList "-NoExit", "-Command", "cd D:\DODO; powershell -ExecutionPolicy Bypass -File .\scripts\start_frontend.ps1"

Write-Host "`nAll DODO services started!" -ForegroundColor Green
Write-Host "Frontend:    http://localhost:3000" -ForegroundColor White
Write-Host "Backend API: http://localhost:8000" -ForegroundColor White
Write-Host "Local Agent: http://localhost:8001" -ForegroundColor White
Write-Host "Swagger Docs: http://localhost:8000/docs" -ForegroundColor White

