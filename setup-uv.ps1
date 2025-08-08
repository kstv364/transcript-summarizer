# Transcript Summarizer - uv Setup Script
# Author: kstv364
# Description: Fast setup script using uv package manager for Windows

param(
    [switch]$SkipUvInstall,
    [switch]$SkipDocker,
    [string]$PythonVersion = "3.11"
)

# Enable strict mode
Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

Write-Host "🚀 Transcript Summarizer - uv Setup for Windows" -ForegroundColor Cyan
Write-Host "Author: kstv364" -ForegroundColor Gray
Write-Host ""

# Function to check if command exists
function Test-CommandExists {
    param($Command)
    $oldPreference = $ErrorActionPreference
    $ErrorActionPreference = 'stop'
    try {
        if (Get-Command $Command) { return $true }
    } catch { return $false }
    finally { $ErrorActionPreference = $oldPreference }
}

# Function to install uv
function Install-Uv {
    Write-Host "📦 Installing uv package manager..." -ForegroundColor Yellow
    
    try {
        # Method 1: PowerShell script (recommended)
        Write-Host "   Using PowerShell installer..." -ForegroundColor Gray
        Invoke-RestMethod https://astral.sh/uv/install.ps1 | Invoke-Expression
        
        # Refresh PATH
        $env:PATH = [System.Environment]::GetEnvironmentVariable("PATH", "Machine") + ";" + [System.Environment]::GetEnvironmentVariable("PATH", "User")
        
        Write-Host "   ✅ uv installed successfully!" -ForegroundColor Green
    } catch {
        Write-Host "   ❌ PowerShell install failed, trying pip..." -ForegroundColor Red
        try {
            pip install uv
            Write-Host "   ✅ uv installed via pip!" -ForegroundColor Green
        } catch {
            Write-Host "   ❌ Failed to install uv. Please install manually." -ForegroundColor Red
            Write-Host "   Visit: https://github.com/astral-sh/uv#installation" -ForegroundColor Blue
            exit 1
        }
    }
}

# Function to setup Python environment
function Setup-PythonEnvironment {
    Write-Host "� Setting up Python environment with uv..." -ForegroundColor Yellow
    
    # Create virtual environment
    Write-Host "   Creating virtual environment..." -ForegroundColor Gray
    uv venv venv --python $PythonVersion
    
    # Activate virtual environment
    Write-Host "   Activating virtual environment..." -ForegroundColor Gray
    & ".\venv\Scripts\Activate.ps1"
    
    # Install project dependencies
    Write-Host "   Installing project dependencies..." -ForegroundColor Gray
    uv pip install -e ".[dev]"
    
    Write-Host "   ✅ Python environment ready!" -ForegroundColor Green
}

# Function to setup Docker
function Setup-Docker {
    Write-Host "🐳 Setting up Docker services..." -ForegroundColor Yellow
    
    if (-not (Test-CommandExists "docker")) {
        Write-Host "   ⚠️ Docker not found. Please install Docker Desktop." -ForegroundColor Yellow
        Write-Host "   Download: https://www.docker.com/products/docker-desktop" -ForegroundColor Blue
        return
    }
    
    Write-Host "   Building Docker images..." -ForegroundColor Gray
    docker-compose build
    
    Write-Host "   Starting required services..." -ForegroundColor Gray
    docker-compose up redis chromadb -d
    
    Write-Host "   ✅ Docker services started!" -ForegroundColor Green
}

# Function to verify installation
function Test-Installation {
    Write-Host "🔍 Verifying installation..." -ForegroundColor Yellow
    
    # Test uv
    if (Test-CommandExists "uv") {
        $uvVersion = uv --version
        Write-Host "   ✅ uv: $uvVersion" -ForegroundColor Green
    } else {
        Write-Host "   ❌ uv not found" -ForegroundColor Red
    }
    
    # Test Python
    try {
        & ".\venv\Scripts\python.exe" -c "import transcript_summarizer; print('✅ Package imported successfully')"
    } catch {
        Write-Host "   ❌ Package import failed" -ForegroundColor Red
    }
    
    # Test Docker
    if (-not $SkipDocker -and (Test-CommandExists "docker")) {
        try {
            $redisStatus = docker-compose ps redis --format "table {{.State}}" | Select-String "running"
            $chromaStatus = docker-compose ps chromadb --format "table {{.State}}" | Select-String "running"
            
            if ($redisStatus) { Write-Host "   ✅ Redis service running" -ForegroundColor Green }
            else { Write-Host "   ⚠️ Redis service not running" -ForegroundColor Yellow }
            
            if ($chromaStatus) { Write-Host "   ✅ ChromaDB service running" -ForegroundColor Green }
            else { Write-Host "   ⚠️ ChromaDB service not running" -ForegroundColor Yellow }
        } catch {
            Write-Host "   ⚠️ Could not check Docker services" -ForegroundColor Yellow
        }
    }
}

# Function to show next steps
function Show-NextSteps {
    Write-Host ""
    Write-Host "🎉 Setup Complete!" -ForegroundColor Green
    Write-Host ""
    Write-Host "Next steps:" -ForegroundColor Cyan
    Write-Host "1. Activate the virtual environment:" -ForegroundColor White
    Write-Host "   .\venv\Scripts\Activate.ps1" -ForegroundColor Gray
    Write-Host ""
    Write-Host "2. Start the API server:" -ForegroundColor White
    Write-Host "   uvicorn transcript_summarizer.api:app --reload" -ForegroundColor Gray
    Write-Host ""
    Write-Host "3. Start a Celery worker (new terminal):" -ForegroundColor White
    Write-Host "   celery -A transcript_summarizer.worker worker --loglevel=info --pool=solo" -ForegroundColor Gray
    Write-Host ""
    Write-Host "4. Access the API at http://localhost:8000" -ForegroundColor White
    Write-Host "   API docs: http://localhost:8000/docs" -ForegroundColor Gray
    Write-Host ""
    Write-Host "5. Run tests:" -ForegroundColor White
    Write-Host "   pytest tests/" -ForegroundColor Gray
    Write-Host ""
    Write-Host "📚 Documentation:" -ForegroundColor Cyan
    Write-Host "   - README.md - Project overview" -ForegroundColor Gray
    Write-Host "   - UV_GUIDE.md - uv package manager guide" -ForegroundColor Gray
    Write-Host "   - examples/ - Usage examples" -ForegroundColor Gray
    Write-Host ""
    Write-Host "� Useful uv commands:" -ForegroundColor Cyan
    Write-Host "   uv pip install package-name    # Install package" -ForegroundColor Gray
    Write-Host "   uv pip list                    # List packages" -ForegroundColor Gray
    Write-Host "   uv pip freeze > requirements.txt  # Export deps" -ForegroundColor Gray
    Write-Host ""
}

# Main execution
try {
    # Check prerequisites
    Write-Host "🔍 Checking prerequisites..." -ForegroundColor Yellow
    
    if (-not (Test-CommandExists "python")) {
        Write-Host "   ❌ Python not found. Please install Python $PythonVersion+" -ForegroundColor Red
        Write-Host "   Download: https://www.python.org/downloads/" -ForegroundColor Blue
        exit 1
    }
    
    $pythonVersion = python --version
    Write-Host "   ✅ $pythonVersion" -ForegroundColor Green
    
    # Install uv if needed
    if (-not $SkipUvInstall) {
        if (-not (Test-CommandExists "uv")) {
            Install-Uv
        } else {
            $uvVersion = uv --version
            Write-Host "   ✅ uv already installed: $uvVersion" -ForegroundColor Green
        }
    }
    
    # Setup Python environment
    Setup-PythonEnvironment
    
    # Setup Docker services
    if (-not $SkipDocker) {
        Setup-Docker
    }
    
    # Verify installation
    Test-Installation
    
    # Show next steps
    Show-NextSteps
    
} catch {
    Write-Host ""
    Write-Host "❌ Setup failed: $($_.Exception.Message)" -ForegroundColor Red
    Write-Host ""
    Write-Host "Troubleshooting:" -ForegroundColor Yellow
    Write-Host "1. Run as Administrator if you get permission errors" -ForegroundColor White
    Write-Host "2. Set execution policy: Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser" -ForegroundColor White
    Write-Host "3. Check internet connection for package downloads" -ForegroundColor White
    Write-Host "4. Manually install uv: https://github.com/astral-sh/uv#installation" -ForegroundColor White
    Write-Host ""
    exit 1
}
