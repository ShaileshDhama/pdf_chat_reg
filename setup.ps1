# Check if Redis is installed via winget
$redisInstalled = winget list --name "Redis"
if ($LASTEXITCODE -ne 0) {
    Write-Host "Installing Redis..."
    winget install -e --id Memurai.Memurai-Developer
} else {
    Write-Host "Redis is already installed"
}

# Create Python virtual environment
Write-Host "Creating Python virtual environment..."
python -m venv backend\venv
. backend\venv\Scripts\Activate.ps1

# Install Python dependencies
Write-Host "Installing Python dependencies..."
pip install -r backend\requirements.txt

# Install Node.js dependencies
Write-Host "Installing Node.js dependencies..."
Set-Location frontend
npm install
Set-Location ..

# Create necessary directories
Write-Host "Creating necessary directories..."
New-Item -Path "backend\uploads" -ItemType Directory -Force

Write-Host "Setup complete! You can now:"
Write-Host "1. Start Redis (it should start automatically as a Windows service)"
Write-Host "2. Start the backend: Set-Location backend && uvicorn app.main:app --reload"
Write-Host "3. Start the frontend: Set-Location frontend && npm start"
