# Start script for PDF Chat Application

Write-Host "Starting PDF Chat Application..." -ForegroundColor Green

# Check if Docker is running
$dockerStatus = docker info 2>&1
if ($LASTEXITCODE -ne 0) {
    Write-Host "Docker is not running. Please start Docker Desktop and try again." -ForegroundColor Red
    exit 1
}

# Start the application using Docker Compose
Write-Host "`nStarting application containers..." -ForegroundColor Yellow
docker-compose up --build -d

Write-Host "`nApplication is starting up!" -ForegroundColor Green
Write-Host "Frontend will be available at: http://localhost:3000" -ForegroundColor Cyan
Write-Host "Backend API will be available at: http://localhost:8000" -ForegroundColor Cyan
Write-Host "Redis will be available at: localhost:6379" -ForegroundColor Cyan

# Wait for services to be ready
Write-Host "`nWaiting for services to be ready..." -ForegroundColor Yellow

$maxAttempts = 30
$attempt = 0
$ready = $false

while (-not $ready -and $attempt -lt $maxAttempts) {
    $attempt++
    
    try {
        # Check if frontend is ready
        $frontendResponse = Invoke-WebRequest -Uri "http://localhost:3000" -Method Head -TimeoutSec 1
        
        # Check if backend is ready
        $backendResponse = Invoke-WebRequest -Uri "http://localhost:8000/api/v1/health" -Method Get -TimeoutSec 1
        
        if ($frontendResponse.StatusCode -eq 200 -and $backendResponse.StatusCode -eq 200) {
            $ready = $true
            Write-Host "`nAll services are ready!" -ForegroundColor Green
            break
        }
    }
    catch {
        Write-Host "Waiting for services to start... (Attempt $attempt of $maxAttempts)" -ForegroundColor Yellow
        Start-Sleep -Seconds 2
    }
}

if (-not $ready) {
    Write-Host "`nWarning: Not all services are responding. Please check the logs:" -ForegroundColor Yellow
    Write-Host "docker-compose logs" -ForegroundColor Cyan
}

Write-Host "`nUseful commands:" -ForegroundColor Green
Write-Host "- View logs: docker-compose logs -f" -ForegroundColor Cyan
Write-Host "- Stop application: docker-compose down" -ForegroundColor Cyan
Write-Host "- Restart application: docker-compose restart" -ForegroundColor Cyan
