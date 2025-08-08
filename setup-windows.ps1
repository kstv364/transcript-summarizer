# Windows Setup Script for Transcript Summarizer
# Run this script in PowerShell as Administrator

Write-Host "🚀 Transcript Summarizer Windows Setup Script" -ForegroundColor Green
Write-Host "=============================================" -ForegroundColor Green

# Check if running as administrator
if (-NOT ([Security.Principal.WindowsPrincipal] [Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([Security.Principal.WindowsBuiltInRole] "Administrator")) {
    Write-Host "❌ This script needs to be run as Administrator!" -ForegroundColor Red
    Write-Host "Please right-click PowerShell and select 'Run as Administrator'" -ForegroundColor Yellow
    Read-Host "Press Enter to exit"
    exit 1
}

# Set execution policy
Write-Host "📋 Setting PowerShell execution policy..." -ForegroundColor Cyan
Set-ExecutionPolicy RemoteSigned -Force

# Install Chocolatey if not present
Write-Host "🍫 Checking for Chocolatey..." -ForegroundColor Cyan
if (!(Get-Command choco -ErrorAction SilentlyContinue)) {
    Write-Host "Installing Chocolatey..." -ForegroundColor Yellow
    Set-ExecutionPolicy Bypass -Scope Process -Force
    [System.Net.ServicePointManager]::SecurityProtocol = [System.Net.ServicePointManager]::SecurityProtocol -bor 3072
    iex ((New-Object System.Net.WebClient).DownloadString('https://community.chocolatey.org/install.ps1'))
    refreshenv
    Write-Host "✅ Chocolatey installed!" -ForegroundColor Green
} else {
    Write-Host "✅ Chocolatey already installed!" -ForegroundColor Green
}

# Install Python 3.11
Write-Host "🐍 Installing Python 3.11..." -ForegroundColor Cyan
choco install python311 -y
refreshenv

# Install uv package manager
Write-Host "⚡ Installing uv package manager..." -ForegroundColor Cyan
choco install uv -y
refreshenv

# Install Git
Write-Host "📥 Installing Git..." -ForegroundColor Cyan
choco install git -y

# Install Docker Desktop
Write-Host "🐳 Installing Docker Desktop..." -ForegroundColor Cyan
choco install docker-desktop -y

# Install VS Code
Write-Host "💻 Installing VS Code..." -ForegroundColor Cyan
choco install vscode -y

Write-Host "⏳ Refreshing environment variables..." -ForegroundColor Cyan
refreshenv

# Verify installations
Write-Host "🔍 Verifying installations..." -ForegroundColor Cyan

try {
    $pythonVersion = python --version
    Write-Host "✅ Python: $pythonVersion" -ForegroundColor Green
} catch {
    Write-Host "❌ Python installation failed" -ForegroundColor Red
}

try {
    $uvVersion = uv --version
    Write-Host "✅ uv: $uvVersion" -ForegroundColor Green
} catch {
    Write-Host "❌ uv installation failed" -ForegroundColor Red
}

try {
    $gitVersion = git --version
    Write-Host "✅ Git: $gitVersion" -ForegroundColor Green
} catch {
    Write-Host "❌ Git installation failed" -ForegroundColor Red
}

Write-Host "`n🎉 Base installations complete!" -ForegroundColor Green
Write-Host "📝 Next Steps:" -ForegroundColor Yellow
Write-Host "1. Restart your computer" -ForegroundColor White
Write-Host "2. Start Docker Desktop from the Start menu" -ForegroundColor White
Write-Host "3. Install Ollama from https://ollama.ai/download" -ForegroundColor White
Write-Host "4. Follow the WINDOWS_SETUP.md guide for project setup" -ForegroundColor White

Read-Host "`nPress Enter to exit"
