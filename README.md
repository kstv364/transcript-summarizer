# Transcript Summarizer

A scalable, production-ready transcript summarizer application built with Python, Ollama APIs, and LangChain. Designed to handle long transcripts that exceed the context window of smaller models like Llama3 8B.

## Features

- **🎯 Web Interface**: Modern Gradio-based web frontend for easy interaction
- **📁 VTT Support**: Upload WebVTT subtitle files or paste transcript text directly
- **⚡ Scalable Architecture**: Handles transcripts of any length using chunking and map-reduce strategies
- **🦙 Ollama Integration**: Uses local Ollama models for cost-effective summarization
- **🗃️ Vector Storage**: ChromaDB for efficient document retrieval and similarity search
- **🚀 Async Processing**: FastAPI-based REST API with async support
- **⚙️ Background Tasks**: Celery integration for long-running summarization tasks
- **🐳 Containerized**: Docker and Kubernetes ready with frontend included
- **📊 Production Ready**: Logging, monitoring, and health checks
- **🔄 CI/CD**: GitHub Actions for automated testing and deployment to AWS/DigitalOcean

## Architecture

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Gradio        │    │   FastAPI       │    │   Celery        │
│   Frontend      │────│   Web Server    │────│   Workers       │
└─────────────────┘    └─────────────────┘    └─────────────────┘
         │                       │                       │
         │                       │                       │
    ┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
    │   ChromaDB      │    │   Redis         │    │   Ollama        │
    │   Vector Store  │    │   Task Queue    │    │   LLM API       │
    └─────────────────┘    └─────────────────┘    └─────────────────┘
```

### Components

- **🎯 Gradio Frontend** (Port 7860): User-friendly web interface for uploading VTT files and managing summarizations
- **🚀 FastAPI Server** (Port 8000): REST API with endpoints for transcript processing and status tracking
- **⚙️ Celery Workers**: Background processing for AI-powered summarization tasks
- **🗃️ ChromaDB**: Vector database for semantic search and document storage
- **📊 Redis**: Task queue and caching layer
- **🦙 Ollama**: Local LLM inference server

## Quick Start

### Automated Setup (Recommended)

For the fastest setup experience, use our automated scripts:

**Windows (PowerShell):**
```powershell
# Quick setup with uv (super fast package manager)
.\setup-uv.ps1

# Or standard setup
.\setup-windows.ps1
```

**macOS/Linux:**
```bash
# Using uv (recommended)
./setup.sh --use-uv

# Or standard setup
./setup.sh
```

### Package Manager Choice

We recommend using **uv** for 10-100x faster package operations:
- 📚 **[Complete uv Guide](UV_GUIDE.md)** - Everything you need to know about uv
- 🪟 **[Windows Setup Guide](WINDOWS_SETUP.md)** - Comprehensive Windows setup

### Manual Setup

1. **Install dependencies**:
   ```bash
   # Using uv (recommended - much faster)
   uv pip install -e ".[dev]"
   
   # Or using pip
   pip install -e ".[dev]"
   ```

2. **Start Ollama** (if not already running):
   ```bash
   # Install Ollama: https://ollama.ai/
   ollama pull llama3
   ```

3. **Start services**:
   ```bash
   # Start Redis (required for Celery)
   docker run -d -p 6379:6379 redis:alpine
   
   # Start ChromaDB
   docker run -d -p 8000:8000 chromadb/chroma:latest
   ```

4. **Run the application**:
   
   **Option A: Full Stack with Frontend (Recommended)**
   ```bash
   # Start all services including Gradio frontend
   docker-compose up -d
   
   # Access the web interface at: http://localhost:7860
   # API documentation at: http://localhost:8000/docs
   ```
   
   **Option B: API + Workers Only**
   ```bash
   # Start Celery worker
   celery -A transcript_summarizer.worker worker --loglevel=info
   
   # Start FastAPI server
   uvicorn transcript_summarizer.api:app --reload
   
   # Launch Gradio frontend (separate terminal)
   transcript-summarizer frontend
   ```

### Docker Compose

Start the complete application stack including the Gradio frontend:

```bash
# Start all services
docker-compose up -d

# Access the application
# Web Interface: http://localhost:7860
# API Docs: http://localhost:8000/docs
# Monitoring: http://localhost:5555 (Flower)
```

### Kubernetes

Deploy to AWS EKS or DigitalOcean Kubernetes:

```bash
# Configure your cluster context first
# For AWS EKS:
aws eks update-kubeconfig --region us-east-1 --name your-cluster-name

# For DigitalOcean:
doctl kubernetes cluster kubeconfig save your-cluster-name

# Deploy the application
kubectl apply -f k8s/
```

## Usage

### Web Interface (Recommended)

1. **Launch the Gradio Frontend**:
   ```bash
   # Using Docker Compose
   docker-compose up frontend
   
   # Or using CLI
   transcript-summarizer frontend
   ```

2. **Access the Web Interface**: Open http://localhost:7860 in your browser

3. **Upload or Paste Content**:
   - Upload a VTT subtitle file (.vtt)
   - Upload a text file (.txt)
   - Or paste transcript text directly

4. **Choose Summary Type**:
   - **Concise**: Brief overview with key points
   - **Detailed**: Comprehensive summary with context
   - **Bullet Points**: Structured list format

5. **Get Results**: View your summary in real-time with processing status

### API Endpoints

- `POST /summarize`: Submit a transcript for summarization
- `POST /summarize/upload`: Upload VTT or text files for summarization
- `GET /status/{task_id}`: Check summarization status
- `GET /summary/{task_id}`: Retrieve completed summary
- `GET /health`: Health check endpoint
- `GET /metrics`: Prometheus metrics

### Example Usage

```python
import requests

# Submit transcript
response = requests.post(
    "http://localhost:8000/summarize",
    json={"text": "Your long transcript here..."}
)
task_id = response.json()["task_id"]

# Check status
status = requests.get(f"http://localhost:8000/status/{task_id}")

# Get summary
summary = requests.get(f"http://localhost:8000/summary/{task_id}")
```

## Configuration

Environment variables:

- `OLLAMA_BASE_URL`: Ollama API URL (default: http://localhost:11434)
- `OLLAMA_MODEL`: Model name (default: llama3)
- `REDIS_URL`: Redis connection URL
- `CHROMA_HOST`: ChromaDB host
- `CHUNK_SIZE`: Text chunk size (default: 4000)
- `CHUNK_OVERLAP`: Chunk overlap (default: 200)

## Development

### Setup

```bash
# Install development dependencies
uv pip install -e ".[dev]"

# Install pre-commit hooks
pre-commit install
```

### Testing

```bash
pytest
```

### Code Quality

```bash
black src/ tests/
flake8 src/ tests/
mypy src/
```

## Deployment

### Cost Optimization

- Uses local Ollama models (no API costs)
- Efficient vector storage with ChromaDB
- Redis for lightweight task queuing
- Horizontal scaling with Kubernetes
- Resource limits and requests configured

### Production Considerations

- Health checks and readiness probes
- Prometheus metrics for monitoring
- Structured logging with structlog
- Graceful shutdown handling
- Error handling and retry logic

## License

MIT License - see LICENSE file for details.
