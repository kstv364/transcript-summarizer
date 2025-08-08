# Windows Development Setup Guide

This guide will help you set up Python and the complete development environment for the Transcript Summarizer project on Windows.

## 📋 Prerequisites

Before starting, ensure you have:
- Windows 10 or Windows 11
- Administrator access to install software
- At least 8GB RAM (16GB recommended)
- 10GB free disk space

## 🐍 Step 1: Install Python

### Option A: Install Python from Official Website (Recommended)

1. **Download Python 3.11**:
   - Go to https://www.python.org/downloads/
   - Click "Download Python 3.11.x" (latest 3.11 version)
   - Choose the "Windows installer (64-bit)" for most modern systems

2. **Run the Installer**:
   - **IMPORTANT**: Check "Add Python to PATH" at the bottom of the installer
   - Click "Install Now"
   - Wait for installation to complete
   - Click "Close" when finished

3. **Verify Installation**:
   ```powershell
   # Open PowerShell and run:
   python --version
   # Should show: Python 3.11.x
   
   uv --version
   # Should show uv version
   
   pip --version
   # Should show pip version
   ```

### Option B: Install using Microsoft Store (Alternative)

1. Open Microsoft Store
2. Search for "Python 3.11"
3. Install "Python 3.11" by Python Software Foundation
4. Verify installation as above

### Option C: Install using Chocolatey (For Advanced Users)

1. **Install Chocolatey** (if not already installed):
   ```powershell
   # Run PowerShell as Administrator
   Set-ExecutionPolicy Bypass -Scope Process -Force; [System.Net.ServicePointManager]::SecurityProtocol = [System.Net.ServicePointManager]::SecurityProtocol -bor 3072; iex ((New-Object System.Net.WebClient).DownloadString('https://community.chocolatey.org/install.ps1'))
   ```

2. **Install uv Package Manager**:
   ```powershell
   choco install uv -y
   refreshenv
   ```

3. **Install Python**:
   ```powershell
   choco install python311 -y
   refreshenv
   ```

## 🔧 Step 2: Install Git

1. **Download Git**:
   - Go to https://git-scm.com/download/win
   - Download the 64-bit installer

2. **Install Git**:
   - Run the installer with default settings
   - Make sure "Git from the command line and also from 3rd-party software" is selected

3. **Verify Installation**:
   ```powershell
   git --version
   # Should show git version
   ```

## 🐳 Step 3: Install Docker Desktop

1. **Download Docker Desktop**:
   - Go to https://www.docker.com/products/docker-desktop/
   - Download Docker Desktop for Windows

2. **Install Docker Desktop**:
   - Run the installer
   - Enable WSL 2 integration when prompted
   - Restart your computer when installation completes

3. **Start Docker Desktop**:
   - Launch Docker Desktop from Start menu
   - Wait for it to start (may take a few minutes first time)

4. **Verify Installation**:
   ```powershell
   docker --version
   docker-compose --version
   ```

## 🦙 Step 4: Install Ollama

1. **Download Ollama**:
   - Go to https://ollama.ai/download
   - Download Ollama for Windows

2. **Install Ollama**:
   - Run the installer
   - Follow the installation wizard

3. **Pull the Llama3 Model**:
   ```powershell
   # Open a new PowerShell window
   ollama pull llama3
   # This will download ~4.7GB model
   ```

4. **Verify Ollama is Working**:
   ```powershell
   ollama list
   # Should show llama3 model
   
   # Test the model
   ollama run llama3 "Hello, how are you?"
   # Should respond with AI-generated text
   ```

## 📁 Step 5: Clone and Setup the Project

1. **Clone the Repository**:
   ```powershell
   # Navigate to your workspace
   cd C:\Workspace\Personal
   
   # If you haven't already cloned it:
   git clone https://github.com/kstv364/transcript-summarizer.git
   cd transcript-summarizer
   ```

2. **Create Virtual Environment with uv**:
   ```powershell
   # Create virtual environment using uv (much faster than venv)
   uv venv venv
   
   # Activate virtual environment
   .\venv\Scripts\Activate.ps1
   
   # If you get execution policy error, run:
   Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
   # Then try activating again
   ```

3. **Install Project Dependencies with uv**:
   ```powershell
   # Make sure virtual environment is activated (you should see (venv) in prompt)
   
   # Install the project in development mode using uv (much faster than pip)
   uv pip install -e ".[dev]"
   ```

## 🚀 Step 6: Start the Development Environment

1. **Start Required Services**:
   ```powershell
   # Start Docker services (Redis and ChromaDB)
   docker-compose up redis chromadb -d
   
   # Verify services are running
   docker-compose ps
   ```

2. **Start Ollama Service** (if not already running):
   ```powershell
   # Ollama should auto-start, but if needed:
   ollama serve
   ```

3. **Start the Application**:
   
   **Terminal 1 - Start Celery Worker**:
   ```powershell
   # Make sure virtual environment is activated
   .\venv\Scripts\Activate.ps1
   
   # Start Celery worker
   celery -A transcript_summarizer.worker worker --loglevel=info --pool=solo
   ```
   
   **Terminal 2 - Start FastAPI Server**:
   ```powershell
   # Open new PowerShell window
   cd C:\Workspace\Personal\transcript-summarizer
   .\venv\Scripts\Activate.ps1
   
   # Start the API server
   uvicorn transcript_summarizer.api:app --reload --host 0.0.0.0 --port 8000
   ```

## ✅ Step 7: Verify Everything Works

1. **Test the API**:
   ```powershell
   # In a new PowerShell window
   cd C:\Workspace\Personal\transcript-summarizer
   .\venv\Scripts\Activate.ps1
   
   # Run the example
   python examples/api_example.py
   ```

2. **Open in Browser**:
   - Go to http://localhost:8000/docs for API documentation
   - Go to http://localhost:8000/health for health check

3. **Test CLI Tool**:
   ```powershell
   # Test the CLI
   transcript-summarizer health
   
   # Test CLI summarization
   echo "This is a test transcript about quarterly results." | transcript-summarizer summarize -
   ```

## 🛠️ Development Tools Setup

1. **Install VS Code** (if not already installed):
   - Download from https://code.visualstudio.com/
   - Install recommended extensions:
     - Python
     - Docker
     - YAML
     - GitLens

2. **Setup Pre-commit Hooks**:
   ```powershell
   # Install pre-commit hooks
   pre-commit install
   
   # Test pre-commit
   pre-commit run --all-files
   ```

3. **Run Tests**:
   ```powershell
   # Run the test suite
   pytest tests/ -v
   
   # Run with coverage
   pytest tests/ -v --cov=transcript_summarizer --cov-report=html
   ```

## 🐛 Troubleshooting

### Common Issues and Solutions

1. **"python is not recognized"**:
   - Restart PowerShell after Python installation
   - Check if Python is in PATH: `$env:PATH -split ';' | Select-String python`

2. **PowerShell Execution Policy Error**:
   ```powershell
   Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
   ```

3. **Docker not starting**:
   - Make sure Hyper-V is enabled in Windows Features
   - Restart Docker Desktop
   - Check if WSL 2 is properly installed

4. **Ollama model download fails**:
   - Check internet connection
   - Try: `ollama pull llama3:8b` for specific version
   - Free up disk space (models are large)

5. **Port already in use**:
   ```powershell
   # Find process using port 8000
   netstat -ano | findstr :8000
   
   # Kill process (replace PID with actual process ID)
   taskkill /PID <PID> /F
   ```

6. **Celery worker issues on Windows**:
   - Use `--pool=solo` flag for Celery on Windows
   - Make sure Redis is running: `docker-compose ps`

## 📝 Daily Development Workflow

Once everything is set up, your daily workflow will be:

1. **Start Development Environment**:
   ```powershell
   cd C:\Workspace\Personal\transcript-summarizer
   
   # Start services
   docker-compose up redis chromadb -d
   
   # Activate virtual environment
   .\venv\Scripts\Activate.ps1
   
   # Start worker (Terminal 1)
   celery -A transcript_summarizer.worker worker --loglevel=info --pool=solo
   
   # Start API (Terminal 2)
   uvicorn transcript_summarizer.api:app --reload
   ```

2. **Make Changes and Test**:
   ```powershell
   # Run tests
   pytest tests/
   
   # Check code quality
   black src/ tests/
   flake8 src/ tests/
   ```

3. **Stop Services When Done**:
   ```powershell
   # Stop Docker services
   docker-compose down
   
   # Deactivate virtual environment
   deactivate
   ```

## 🎉 Success!

You now have a complete development environment set up for the Transcript Summarizer project! The application will be available at:

- **API Documentation**: http://localhost:8000/docs
- **Health Check**: http://localhost:8000/health
- **Example Usage**: Run `python examples/api_example.py`

Happy coding! 🚀
