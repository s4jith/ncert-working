# NCERT Doubt-Solver Startup Script

Write-Host "============================================" -ForegroundColor Cyan
Write-Host "  NCERT Doubt-Solver v2.0 - Starting..." -ForegroundColor Cyan
Write-Host "============================================" -ForegroundColor Cyan
Write-Host ""

$projectRoot = $PSScriptRoot

# Check if backend venv exists
$backendVenv = Join-Path $projectRoot "backend\venv"
if (-not (Test-Path $backendVenv)) {
    Write-Host "[1/4] Creating Python virtual environment..." -ForegroundColor Yellow
    python -m venv $backendVenv
}

# Install backend dependencies
Write-Host "[2/4] Installing backend dependencies..." -ForegroundColor Yellow
& "$backendVenv\Scripts\Activate.ps1"
pip install -r (Join-Path $projectRoot "backend\requirements.txt") --quiet 2>$null

# Install frontend dependencies
Write-Host "[3/4] Installing frontend dependencies..." -ForegroundColor Yellow
$frontendPath = Join-Path $projectRoot "frontend"
if (-not (Test-Path (Join-Path $frontendPath "node_modules"))) {
    Push-Location $frontendPath
    npm install
    Pop-Location
}

Write-Host "[4/4] Starting servers..." -ForegroundColor Yellow
Write-Host ""

# Start backend
Start-Process powershell -ArgumentList "-NoExit", "-Command", "cd '$projectRoot\backend'; & '$backendVenv\Scripts\Activate.ps1'; uvicorn app.main:app --reload --port 8000"

# Start frontend  
Start-Process powershell -ArgumentList "-NoExit", "-Command", "cd '$projectRoot\frontend'; npm run dev"

Write-Host ""
Write-Host "============================================" -ForegroundColor Green
Write-Host "  Servers Starting!" -ForegroundColor Green
Write-Host "============================================" -ForegroundColor Green
Write-Host ""
Write-Host "  Frontend: http://localhost:5173" -ForegroundColor White
Write-Host "  Backend:  http://localhost:8000" -ForegroundColor White
Write-Host "  API Docs: http://localhost:8000/docs" -ForegroundColor White
Write-Host ""
