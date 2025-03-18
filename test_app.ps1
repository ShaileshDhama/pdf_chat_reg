# Test script for PDF Chat Application

Write-Host "Testing PDF Chat Application..." -ForegroundColor Green

# Test Redis Connection
Write-Host "`nTesting Redis connection..." -ForegroundColor Yellow
try {
    redis-cli ping
    if ($LASTEXITCODE -eq 0) {
        Write-Host "Redis connection successful!" -ForegroundColor Green
    } else {
        Write-Host "Redis connection failed!" -ForegroundColor Red
        Write-Host "Please make sure Redis is running." -ForegroundColor Red
        exit 1
    }
} catch {
    Write-Host "Redis-cli not found. Please make sure Redis is installed." -ForegroundColor Red
    exit 1
}

# Test Backend Health
Write-Host "`nTesting Backend health..." -ForegroundColor Yellow
try {
    $response = Invoke-RestMethod -Uri "http://localhost:8000/api/v1/health" -Method Get
    if ($response.status -eq "healthy") {
        Write-Host "Backend is healthy!" -ForegroundColor Green
    } else {
        Write-Host "Backend health check failed!" -ForegroundColor Red
        exit 1
    }
} catch {
    Write-Host "Backend is not running or encountered an error!" -ForegroundColor Red
    Write-Host "Please start the backend server: cd backend && uvicorn app.main:app --reload" -ForegroundColor Yellow
    exit 1
}

# Test Frontend Development Server
Write-Host "`nTesting Frontend development server..." -ForegroundColor Yellow
try {
    $response = Invoke-RestMethod -Uri "http://localhost:3000" -Method Get -ErrorAction SilentlyContinue
    Write-Host "Frontend server is running!" -ForegroundColor Green
} catch {
    Write-Host "Frontend server is not running!" -ForegroundColor Red
    Write-Host "Please start the frontend server: cd frontend && npm start" -ForegroundColor Yellow
    exit 1
}

# Create test directories if they don't exist
Write-Host "`nChecking required directories..." -ForegroundColor Yellow
$directories = @(
    "backend\uploads",
    "backend\app\core",
    "backend\app\api\endpoints"
)

foreach ($dir in $directories) {
    if (-not (Test-Path $dir)) {
        New-Item -ItemType Directory -Path $dir -Force
        Write-Host "Created directory: $dir" -ForegroundColor Green
    } else {
        Write-Host "Directory exists: $dir" -ForegroundColor Green
    }
}

Write-Host "`nAll tests completed!" -ForegroundColor Green
Write-Host "`nNext steps:"
Write-Host "1. Start Redis server (if not running)" -ForegroundColor Yellow
Write-Host "2. Start backend: cd backend && uvicorn app.main:app --reload" -ForegroundColor Yellow
Write-Host "3. Start frontend: cd frontend && npm start" -ForegroundColor Yellow
