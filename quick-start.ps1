# Quick Start Script for Transcript Summarizer (Windows PowerShell)
# This script sets up the development environment and starts the application

$ErrorActionPreference = "Stop"

Write-Host "Transcript Summarizer Quick Start" -ForegroundColor Green
Write-Host "==================================" -ForegroundColor Green

# Check if Docker is running
try {
    docker info | Out-Null
    Write-Host "[OK] Docker is running" -ForegroundColor Green
} catch {
    Write-Host "[ERROR] Docker is not running. Please start Docker and try again." -ForegroundColor Red
    exit 1
}

# Check if Docker Compose is available
if (!(Get-Command docker-compose -ErrorAction SilentlyContinue)) {
    Write-Host "[ERROR] Docker Compose is not installed. Please install it and try again." -ForegroundColor Red
    exit 1
}

# Create necessary directories
Write-Host "Creating necessary directories..." -ForegroundColor Yellow
New-Item -ItemType Directory -Force -Path "data\chroma" | Out-Null
New-Item -ItemType Directory -Force -Path "data\redis" | Out-Null
New-Item -ItemType Directory -Force -Path "logs" | Out-Null

# Pull the latest images
Write-Host "Pulling Docker images..." -ForegroundColor Yellow
docker-compose pull

# Build the application images
Write-Host "Building application images..." -ForegroundColor Yellow
docker-compose build

# Start the services
Write-Host "Starting services..." -ForegroundColor Yellow
docker-compose up -d

# Wait for services to be ready
Write-Host "Waiting for services to start..." -ForegroundColor Yellow
Start-Sleep -Seconds 10

# Function to check if a service is healthy
function Test-ServiceHealth {
    param(
        [string]$ServiceName,
        [string]$Url,
        [int]$MaxAttempts = 30
    )
    
    for ($attempt = 1; $attempt -le $MaxAttempts; $attempt++) {
        try {
            $response = Invoke-WebRequest -Uri $Url -UseBasicParsing -TimeoutSec 5
            if ($response.StatusCode -eq 200) {
                Write-Host "[OK] $ServiceName is healthy" -ForegroundColor Green
                return $true
            }
        } catch {
            # Service not ready yet
        }
        
        Write-Host "Waiting for $ServiceName... (attempt $attempt/$MaxAttempts)" -ForegroundColor Yellow
        Start-Sleep -Seconds 2
    }
    
    Write-Host "[ERROR] $ServiceName failed to start" -ForegroundColor Red
    return $false
}

Write-Host "Checking service health..." -ForegroundColor Yellow

# Check API health
Test-ServiceHealth -ServiceName "API" -Url "http://localhost:8000/health"

# Check Redis
try {
    $redisResponse = docker-compose exec -T redis redis-cli ping
    if ($redisResponse -match "PONG") {
        Write-Host "[OK] Redis is healthy" -ForegroundColor Green
    } else {
        Write-Host "[ERROR] Redis is not responding" -ForegroundColor Red
    }
} catch {
    Write-Host "[ERROR] Redis is not responding" -ForegroundColor Red
}

# Check ChromaDB
Test-ServiceHealth -ServiceName "ChromaDB" -Url "http://localhost:8001/api/v1/heartbeat"

# Check Gradio Frontend
Test-ServiceHealth -ServiceName "Frontend" -Url "http://localhost:7860"

Write-Host ""
Write-Host "All services are running!" -ForegroundColor Green
Write-Host ""
Write-Host "Access the application:" -ForegroundColor Cyan
Write-Host "   • Web Interface: http://localhost:7860" -ForegroundColor White
Write-Host "   • API Documentation: http://localhost:8000/docs" -ForegroundColor White
Write-Host "   • API Health: http://localhost:8000/health" -ForegroundColor White
Write-Host "   • ChromaDB Admin: http://localhost:8001" -ForegroundColor White
Write-Host ""
Write-Host "Useful commands:" -ForegroundColor Cyan
Write-Host "   • View logs: docker-compose logs -f" -ForegroundColor White
Write-Host "   • Stop services: docker-compose down" -ForegroundColor White
Write-Host "   • Restart services: docker-compose restart" -ForegroundColor White
Write-Host "   • Update images: docker-compose pull; docker-compose up -d" -ForegroundColor White
Write-Host ""
Write-Host "For more information, see:" -ForegroundColor Cyan
Write-Host "   • README.md - General documentation" -ForegroundColor White
Write-Host "   • CLOUD_DEPLOYMENT.md - Cloud deployment guide" -ForegroundColor White
Write-Host ""
Write-Host "Happy summarizing!" -ForegroundColor Green
