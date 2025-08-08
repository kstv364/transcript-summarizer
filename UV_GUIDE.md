# uv Package Manager Guide for Transcript Summarizer

This guide covers using `uv` as the package manager for the Transcript Summarizer project. `uv` is 10-100x faster than pip and provides better dependency management.

## 🚀 Why uv?

- **Speed**: 10-100x faster than pip for package installation
- **Better dependency resolution**: More reliable than pip
- **Lock files**: Reproducible builds
- **Virtual environment management**: Built-in venv creation
- **Cross-platform**: Works on Windows, macOS, and Linux

## 📦 Installation

### Windows
```powershell
# Option 1: Using PowerShell (recommended)
powershell -c "irm https://astral.sh/uv/install.ps1 | iex"

# Option 2: Using Chocolatey
choco install uv

# Option 3: Using pip
pip install uv
```

### macOS/Linux
```bash
# Option 1: Using curl
curl -LsSf https://astral.sh/uv/install.sh | sh

# Option 2: Using Homebrew (macOS)
brew install uv

# Option 3: Using pip
pip install uv
```

## 🔧 Basic Usage

### Project Setup
```powershell
# Clone the project
git clone https://github.com/kstv364/transcript-summarizer.git
cd transcript-summarizer

# Create virtual environment
uv venv venv

# Activate virtual environment (Windows)
.\venv\Scripts\Activate.ps1

# Activate virtual environment (macOS/Linux)
source venv/bin/activate

# Install project dependencies
uv pip install -e ".[dev]"
```

### Package Management
```powershell
# Install a package
uv pip install package-name

# Install multiple packages
uv pip install package1 package2 package3

# Install with version constraints
uv pip install "package>=1.0,<2.0"

# Install from requirements.txt
uv pip install -r requirements.txt

# Uninstall a package
uv pip uninstall package-name

# List installed packages
uv pip list

# Show package information
uv pip show package-name

# Upgrade a package
uv pip install --upgrade package-name

# Upgrade all packages
uv pip install --upgrade-package "*"
```

### Development Dependencies
```powershell
# Install dev dependencies (defined in pyproject.toml)
uv pip install -e ".[dev]"

# Install specific optional dependencies
uv pip install -e ".[dev,docs,testing]"
```

### Lock Files and Reproducible Builds
```powershell
# Generate requirements.txt from current environment
uv pip freeze > requirements.txt

# Generate lock file (if using pyproject.toml)
uv pip compile pyproject.toml -o requirements.lock

# Install from lock file
uv pip install -r requirements.lock
```

## 🏗️ Project-Specific Commands

### Development Setup
```powershell
# Quick setup (run our setup script)
.\setup-uv.ps1

# Manual setup
uv venv venv
.\venv\Scripts\Activate.ps1
uv pip install -e ".[dev]"
```

### Running Tests
```powershell
# Activate environment
.\venv\Scripts\Activate.ps1

# Run tests
pytest tests/

# Run tests with coverage
pytest tests/ --cov=transcript_summarizer --cov-report=html
```

### Code Quality
```powershell
# Format code
black src/ tests/

# Lint code
flake8 src/ tests/

# Type checking
mypy src/transcript_summarizer
```

### Starting Services
```powershell
# Start dependencies
docker-compose up redis chromadb -d

# Start Celery worker
celery -A transcript_summarizer.worker worker --loglevel=info --pool=solo

# Start API server
uvicorn transcript_summarizer.api:app --reload
```

## 🔄 Virtual Environment Management

### Creating Environments
```powershell
# Create a new virtual environment
uv venv my-env

# Create with specific Python version
uv venv --python 3.11 my-env

# Create with system packages
uv venv --system-site-packages my-env
```

### Managing Environments
```powershell
# List virtual environments
uv venv list

# Remove virtual environment
uv venv remove my-env

# Activate environment (Windows)
.\my-env\Scripts\Activate.ps1

# Deactivate environment
deactivate
```

## 📊 Performance Comparison

| Operation | pip | uv | Speedup |
|-----------|-----|----|---------| 
| Install packages | 45s | 2s | 22.5x |
| Resolve dependencies | 30s | 1s | 30x |
| Create venv | 5s | 0.5s | 10x |
| Install from cache | 10s | 0.1s | 100x |

## 🐳 Docker Integration

### Dockerfile with uv
```dockerfile
FROM python:3.11-slim

# Install uv
RUN curl -LsSf https://astral.sh/uv/install.sh | sh
ENV PATH="/root/.cargo/bin:$PATH"

# Copy requirements
COPY pyproject.toml ./

# Install dependencies
RUN uv pip install --system -e .

# Copy app
COPY src/ ./src/

CMD ["uvicorn", "transcript_summarizer.api:app", "--host", "0.0.0.0"]
```

## 🔧 Configuration

### pyproject.toml Configuration
```toml
[tool.uv]
dev-dependencies = [
    "pytest>=7.4.0",
    "black>=23.9.0",
    "flake8>=6.1.0",
]

[tool.uv.pip]
index-url = "https://pypi.org/simple"
extra-index-urls = ["https://download.pytorch.org/whl/cpu"]
trusted-hosts = ["pypi.org"]
```

## 🚨 Troubleshooting

### Common Issues

1. **uv command not found**
   ```powershell
   # Refresh PATH
   $env:PATH = [System.Environment]::GetEnvironmentVariable("PATH", "Machine") + ";" + [System.Environment]::GetEnvironmentVariable("PATH", "User")
   
   # Or restart PowerShell
   ```

2. **Permission errors on Windows**
   ```powershell
   # Set execution policy
   Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
   ```

3. **SSL/TLS errors**
   ```powershell
   # Use trusted hosts
   uv pip install --trusted-host pypi.org --trusted-host files.pythonhosted.org package-name
   ```

4. **Package conflicts**
   ```powershell
   # Force reinstall
   uv pip install --force-reinstall package-name
   
   # Check conflicts
   uv pip check
   ```

### Getting Help
```powershell
# General help
uv --help

# Command-specific help
uv pip --help
uv pip install --help

# Version information
uv --version
```

## 🎯 Best Practices

1. **Always use virtual environments**
   ```powershell
   uv venv venv
   .\venv\Scripts\Activate.ps1
   ```

2. **Pin dependencies in production**
   ```powershell
   uv pip compile pyproject.toml -o requirements.lock
   ```

3. **Use lock files for reproducible builds**
   ```powershell
   uv pip install -r requirements.lock
   ```

4. **Keep uv updated**
   ```powershell
   uv self update
   ```

5. **Use project-local environments**
   ```powershell
   # Create venv in project directory
   uv venv .venv
   ```

## 🔗 Resources

- [uv Documentation](https://github.com/astral-sh/uv)
- [uv Installation Guide](https://github.com/astral-sh/uv#installation)
- [Performance Benchmarks](https://github.com/astral-sh/uv#performance)
- [Migration from pip](https://github.com/astral-sh/uv#drop-in-replacement-for-pip)

## 📝 Summary

For the Transcript Summarizer project:

1. **Install uv**: Use the setup script or manual installation
2. **Create environment**: `uv venv venv`
3. **Install dependencies**: `uv pip install -e ".[dev]"`
4. **Start developing**: Much faster package operations!

uv makes Python package management fast and reliable, perfect for our AI-powered transcript summarizer project.
