# Configuration Guide

This guide covers all configuration options for the Transcript Summarizer application.

## Table of Contents

- [Environment Variables](#environment-variables)
- [Ollama Configuration](#ollama-configuration)
- [ChromaDB Configuration](#chromadb-configuration)
- [Redis Configuration](#redis-configuration)
- [Celery Configuration](#celery-configuration)
- [Gradio Frontend Configuration](#gradio-frontend-configuration)
- [Docker Configuration](#docker-configuration)
- [Kubernetes Configuration](#kubernetes-configuration)
- [Development Configuration](#development-configuration)
- [Production Configuration](#production-configuration)

## Environment Variables

### Core Application Settings

| Variable | Default | Description |
|----------|---------|-------------|
| `LOG_LEVEL` | `INFO` | Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL) |
| `API_HOST` | `0.0.0.0` | API server host |
| `API_PORT` | `8000` | API server port |
| `FRONTEND_HOST` | `0.0.0.0` | Gradio frontend host |
| `FRONTEND_PORT` | `7860` | Gradio frontend port |
| `API_BASE_URL` | `http://localhost:8000` | Base URL for API (used by frontend) |

### Ollama Configuration

| Variable | Default | Description |
|----------|---------|-------------|
| `OLLAMA_BASE_URL` | `http://localhost:11434` | Ollama server URL |
| `OLLAMA_MODEL` | `llama3` | Default model for summarization |
| `OLLAMA_TIMEOUT` | `300` | Request timeout in seconds |
| `OLLAMA_MAX_RETRIES` | `3` | Maximum retry attempts |

### ChromaDB Configuration

| Variable | Default | Description |
|----------|---------|-------------|
| `CHROMA_HOST` | `localhost` | ChromaDB host |
| `CHROMA_PORT` | `8000` | ChromaDB port |
| `CHROMA_COLLECTION_NAME` | `transcripts` | Default collection name |
| `CHROMA_PERSIST_DIRECTORY` | `/data/chroma` | Data persistence directory |

### Redis Configuration

| Variable | Default | Description |
|----------|---------|-------------|
| `REDIS_URL` | `redis://localhost:6379/0` | Redis connection URL |
| `REDIS_MAX_CONNECTIONS` | `20` | Maximum connection pool size |
| `REDIS_SOCKET_KEEPALIVE` | `true` | Enable socket keepalive |
| `REDIS_HEALTH_CHECK_INTERVAL` | `30` | Health check interval in seconds |

### Celery Configuration

| Variable | Default | Description |
|----------|---------|-------------|
| `CELERY_BROKER_URL` | `redis://localhost:6379/0` | Message broker URL |
| `CELERY_RESULT_BACKEND` | `redis://localhost:6379/0` | Result backend URL |
| `CELERY_TASK_SERIALIZER` | `json` | Task serialization format |
| `CELERY_RESULT_SERIALIZER` | `json` | Result serialization format |
| `CELERY_ACCEPT_CONTENT` | `["json"]` | Accepted content types |
| `CELERY_TIMEZONE` | `UTC` | Timezone for scheduled tasks |
| `CELERY_ENABLE_UTC` | `true` | Enable UTC timezone |
| `CELERY_TASK_TRACK_STARTED` | `true` | Track task start time |
| `CELERY_TASK_TIME_LIMIT` | `1800` | Task time limit in seconds (30 minutes) |
| `CELERY_TASK_SOFT_TIME_LIMIT` | `1500` | Soft time limit in seconds (25 minutes) |
| `CELERY_WORKER_PREFETCH_MULTIPLIER` | `1` | Number of tasks to prefetch |
| `CELERY_WORKER_MAX_TASKS_PER_CHILD` | `1000` | Max tasks per worker process |

---

## Ollama Configuration

### Supported Models

The application supports various Ollama models. Configure via `OLLAMA_MODEL`:

```bash
# Recommended models for summarization
OLLAMA_MODEL=llama3          # Fast, good quality
OLLAMA_MODEL=llama3:8b       # Specific version
OLLAMA_MODEL=mistral         # Alternative option
OLLAMA_MODEL=codellama       # For code-heavy transcripts
OLLAMA_MODEL=gemma           # Google's model
```

### Model Download

Pull models before use:

```bash
# Download specific models
docker-compose exec ollama ollama pull llama3
docker-compose exec ollama ollama pull mistral
docker-compose exec ollama ollama pull gemma
```

### Custom Prompts

Customize summarization prompts in `src/transcript_summarizer/services/llm_service.py`:

```python
SUMMARIZATION_PROMPT = """
You are an expert at creating concise, informative summaries of transcripts.

Please summarize the following transcript, focusing on:
- Key points and main topics discussed
- Important decisions or conclusions
- Action items or next steps
- Any significant insights or quotes

Transcript:
{transcript}

Summary:
"""
```

---

## ChromaDB Configuration

### Persistence

ChromaDB data is persisted to ensure embeddings survive container restarts:

```yaml
# docker-compose.yml
services:
  chromadb:
    volumes:
      - ./data/chroma:/chroma/chroma
    environment:
      - CHROMA_DB_IMPL=duckdb+parquet
      - CHROMA_PERSIST_DIRECTORY=/chroma/chroma
```

### Collection Management

Configure collections via environment variables:

```bash
CHROMA_COLLECTION_NAME=transcripts
CHROMA_EMBEDDING_FUNCTION=default  # or custom
```

### Performance Tuning

For large datasets:

```bash
# Increase memory limits
CHROMA_MEMORY_LIMIT=2G
CHROMA_BATCH_SIZE=100
CHROMA_MAX_CONCURRENT_REQUESTS=10
```

---

## Redis Configuration

### Development Setup

```bash
# Basic Redis configuration
REDIS_URL=redis://localhost:6379/0
REDIS_MAX_CONNECTIONS=10
```

### Production Setup

```bash
# Production Redis with authentication
REDIS_URL=redis://:password@redis-host:6379/0
REDIS_MAX_CONNECTIONS=50
REDIS_SOCKET_KEEPALIVE=true
REDIS_SOCKET_KEEPALIVE_OPTIONS={
  "TCP_KEEPIDLE": 1,
  "TCP_KEEPINTVL": 3,
  "TCP_KEEPCNT": 5
}
```

### Redis Sentinel

For high availability:

```bash
REDIS_SENTINEL_HOSTS=sentinel1:26379,sentinel2:26379,sentinel3:26379
REDIS_SENTINEL_SERVICE_NAME=mymaster
REDIS_PASSWORD=your-password
```

---

## Celery Configuration

### Worker Configuration

Adjust worker settings based on your resources:

```bash
# CPU-intensive tasks
CELERY_WORKER_CONCURRENCY=4  # Number of CPU cores
CELERY_WORKER_PREFETCH_MULTIPLIER=1

# Memory-intensive tasks
CELERY_WORKER_MAX_MEMORY_PER_CHILD=200000  # 200MB in KB
CELERY_WORKER_MAX_TASKS_PER_CHILD=100
```

### Task Routing

Configure task routing for different queues:

```python
# In celery_config.py
CELERY_ROUTES = {
    'transcript_summarizer.tasks.summarize_transcript': {'queue': 'summarization'},
    'transcript_summarizer.tasks.process_vtt_file': {'queue': 'file_processing'},
}
```

### Monitoring

Enable Celery monitoring:

```bash
CELERY_SEND_EVENTS=true
CELERY_TASK_SEND_SENT_EVENT=true
```

---

## Gradio Frontend Configuration

### Basic Settings

```bash
FRONTEND_HOST=0.0.0.0
FRONTEND_PORT=7860
API_BASE_URL=http://localhost:8000
```

### Theme and UI

Customize the frontend appearance in `src/transcript_summarizer/frontend/gradio_ui.py`:

```python
def create_interface(self):
    with gr.Blocks(
        title="Transcript Summarizer",
        theme=gr.themes.Soft(),  # or gr.themes.Monochrome(), gr.themes.Glass()
        css="""
        .gradio-container {
            max-width: 1200px !important;
        }
        """
    ) as interface:
        # ... interface definition
```

### File Upload Limits

Configure file upload limits:

```python
# In gradio_ui.py
file_input = gr.File(
    label="Upload VTT or Text File",
    file_types=[".vtt", ".txt", ".srt"],
    file_count="single",
    max_size="10MB"  # Adjust as needed
)
```

---

## Docker Configuration

### Development Compose

For development with hot reloading:

```yaml
# docker-compose.dev.yml
services:
  api:
    build:
      context: .
      target: development
    volumes:
      - .:/app
    environment:
      - UVICORN_RELOAD=true
    command: uvicorn src.transcript_summarizer.main:app --host 0.0.0.0 --port 8000 --reload

  frontend:
    build:
      context: .
      dockerfile: Dockerfile.frontend
      target: development
    volumes:
      - .:/app
    environment:
      - GRADIO_SERVER_PORT=7860
      - API_BASE_URL=http://api:8000
```

### Production Compose

```yaml
# docker-compose.prod.yml
services:
  api:
    build:
      context: .
      target: production
    restart: unless-stopped
    environment:
      - LOG_LEVEL=WARNING
      - WORKERS=4
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/health"]
      interval: 30s
      timeout: 10s
      retries: 3
```

### Resource Limits

```yaml
services:
  api:
    deploy:
      resources:
        limits:
          memory: 2G
          cpus: '1.0'
        reservations:
          memory: 1G
          cpus: '0.5'

  ollama:
    deploy:
      resources:
        limits:
          memory: 8G
          cpus: '4.0'
        reservations:
          memory: 4G
          cpus: '2.0'
```

---

## Kubernetes Configuration

### Resource Requests and Limits

```yaml
# k8s/api.yaml
spec:
  containers:
  - name: api
    resources:
      requests:
        memory: "512Mi"
        cpu: "250m"
      limits:
        memory: "2Gi"
        cpu: "1000m"
```

### ConfigMap

```yaml
# k8s/configmap.yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: app-config
data:
  LOG_LEVEL: "INFO"
  OLLAMA_BASE_URL: "http://ollama:11434"
  OLLAMA_MODEL: "llama3"
  CHROMA_HOST: "chromadb"
  CHROMA_PORT: "8000"
  REDIS_URL: "redis://redis:6379/0"
  CELERY_WORKER_CONCURRENCY: "2"
  CELERY_TASK_TIME_LIMIT: "1800"
```

### Secrets

```yaml
# k8s/secrets.yaml
apiVersion: v1
kind: Secret
metadata:
  name: app-secrets
type: Opaque
stringData:
  REDIS_PASSWORD: "your-redis-password"
  OLLAMA_API_KEY: "your-ollama-api-key"  # if using hosted Ollama
```

### Persistent Volumes

```yaml
# k8s/persistent-volumes.yaml
apiVersion: v1
kind: PersistentVolumeClaim
metadata:
  name: chroma-pvc
spec:
  accessModes:
    - ReadWriteOnce
  resources:
    requests:
      storage: 10Gi
  storageClassName: fast-ssd
```

---

## Development Configuration

### Local Development

Create `.env.dev`:

```bash
LOG_LEVEL=DEBUG
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_MODEL=llama3
CHROMA_HOST=localhost
CHROMA_PORT=8001
REDIS_URL=redis://localhost:6379/0
API_BASE_URL=http://localhost:8000
UVICORN_RELOAD=true
```

### Testing Configuration

Create `.env.test`:

```bash
LOG_LEVEL=DEBUG
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_MODEL=llama3:test
CHROMA_HOST=localhost
CHROMA_PORT=8002
REDIS_URL=redis://localhost:6379/1
CELERY_TASK_ALWAYS_EAGER=true
```

### IDE Configuration

#### VS Code

`.vscode/settings.json`:

```json
{
  "python.defaultInterpreterPath": ".venv/bin/python",
  "python.testing.pytestEnabled": true,
  "python.testing.pytestArgs": ["tests/"],
  "python.linting.enabled": true,
  "python.linting.ruffEnabled": true,
  "python.formatting.provider": "black"
}
```

---

## Production Configuration

### Environment Variables

```bash
# Production settings
LOG_LEVEL=WARNING
API_WORKERS=4
CELERY_WORKER_CONCURRENCY=8
CELERY_WORKER_MAX_TASKS_PER_CHILD=100

# Security
ALLOWED_HOSTS=your-domain.com,api.your-domain.com
CORS_ORIGINS=https://app.your-domain.com

# Performance
REDIS_MAX_CONNECTIONS=100
OLLAMA_TIMEOUT=600
CHROMA_BATCH_SIZE=1000
```

### SSL/TLS Configuration

```yaml
# Ingress with TLS
spec:
  tls:
  - hosts:
    - api.your-domain.com
    - app.your-domain.com
    secretName: transcript-summarizer-tls
```

### Monitoring and Logging

```bash
# Structured logging
LOG_FORMAT=json
LOG_OUTPUT=stdout

# Metrics
ENABLE_METRICS=true
METRICS_PORT=9090
PROMETHEUS_ENDPOINT=/metrics
```

### Backup Configuration

```bash
# Redis backup
REDIS_SAVE_INTERVAL=300  # 5 minutes
REDIS_BACKUP_RETENTION=7  # 7 days

# ChromaDB backup
CHROMA_BACKUP_INTERVAL=daily
CHROMA_BACKUP_RETENTION=30  # 30 days
```

---

## Configuration Validation

### Health Checks

The application includes health check endpoints:

- `/health` - Overall application health
- `/health/redis` - Redis connectivity
- `/health/chroma` - ChromaDB connectivity
- `/health/ollama` - Ollama connectivity

### Configuration Validation

Add validation in your startup code:

```python
# src/transcript_summarizer/config.py
from pydantic import BaseSettings, validator

class Settings(BaseSettings):
    log_level: str = "INFO"
    ollama_base_url: str = "http://localhost:11434"
    ollama_model: str = "llama3"
    
    @validator('log_level')
    def validate_log_level(cls, v):
        valid_levels = ['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL']
        if v.upper() not in valid_levels:
            raise ValueError(f'Invalid log level: {v}')
        return v.upper()
    
    @validator('ollama_base_url')
    def validate_ollama_url(cls, v):
        if not v.startswith(('http://', 'https://')):
            raise ValueError('Ollama URL must start with http:// or https://')
        return v
```

---

## Troubleshooting Configuration

### Common Issues

1. **Service Discovery**: Ensure service names match between Docker Compose and application configuration
2. **Port Conflicts**: Check for port conflicts when running multiple instances
3. **Memory Limits**: Adjust memory limits based on model size and workload
4. **Network Connectivity**: Verify network connectivity between services

### Debugging Tools

```bash
# Check service connectivity
docker-compose exec api ping ollama
docker-compose exec api nslookup redis

# View configuration
docker-compose exec api env | grep -E "(OLLAMA|REDIS|CHROMA)"

# Test endpoints
curl http://localhost:8000/health
curl http://localhost:8001/api/v1/heartbeat
```

This completes the comprehensive configuration guide for the Transcript Summarizer application.
