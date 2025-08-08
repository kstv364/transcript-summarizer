# Transcript Summarizer

A scalable, production-ready transcript summarizer application built with Python, Ollama APIs, and LangChain. Designed to handle long transcripts that exceed the context window of smaller models like Llama3 8B.

## Features

- **Scalable Architecture**: Handles transcripts of any length using chunking and map-reduce strategies
- **Ollama Integration**: Uses local Ollama models for cost-effective summarization
- **Vector Storage**: ChromaDB for efficient document retrieval and similarity search
- **Async Processing**: FastAPI-based REST API with async support
- **Background Tasks**: Celery integration for long-running summarization tasks
- **Containerized**: Docker and Kubernetes ready
- **Production Ready**: Logging, monitoring, and health checks
- **CI/CD**: GitHub Actions for automated testing and deployment

## Architecture

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   FastAPI       │    │   Celery        │    │   ChromaDB      │
│   Web Server    │────│   Workers       │────│   Vector Store  │
└─────────────────┘    └─────────────────┘    └─────────────────┘
         │                       │                       │
         │                       │                       │
    ┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
    │   Redis         │    │   Ollama        │    │   Prometheus    │
    │   Task Queue    │    │   LLM API       │    │   Metrics       │
    └─────────────────┘    └─────────────────┘    └─────────────────┘
```

## Quick Start

### Local Development

1. **Install dependencies**:
   ```bash
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
   ```bash
   # Start Celery worker
   celery -A transcript_summarizer.worker worker --loglevel=info
   
   # Start FastAPI server
   uvicorn transcript_summarizer.api:app --reload
   ```

### Docker Compose

```bash
docker-compose up -d
```

### Kubernetes

```bash
kubectl apply -f k8s/
```

## Usage

### API Endpoints

- `POST /summarize`: Submit a transcript for summarization
- `GET /status/{task_id}`: Check summarization status
- `GET /summary/{task_id}`: Retrieve completed summary
- `GET /health`: Health check endpoint
- `GET /metrics`: Prometheus metrics

### Example

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
pip install -e ".[dev]"

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
