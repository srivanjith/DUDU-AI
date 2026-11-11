Write-Host "Starting DODO Next.js Frontend on port 3000..." -ForegroundColor Cyan

# Check if port 3000 is occupied and free it
$connections = Get-NetTCPConnection -LocalPort 3000 -ErrorAction SilentlyContinue
if ($connections) {
    Write-Host "Port 3000 is currently occupied. Freeing port 3000..." -ForegroundColor Yellow
    foreach ($conn in $connections) {
        try {
            Stop-Process -Id $conn.OwningProcess -Force -ErrorAction SilentlyContinue
        } catch {}
    }
    Start-Sleep -Milliseconds 500
}

Set-Location "D:\DODO\frontend"
npm run dev
