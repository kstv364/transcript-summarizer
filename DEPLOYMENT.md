# Deployment Guide

This document provides detailed instructions for deploying the Transcript Summarizer application in various environments.

## Table of Contents

1. [Local Development](#local-development)
2. [Docker Deployment](#docker-deployment)
3. [Kubernetes Deployment](#kubernetes-deployment)
4. [Cloud Provider Deployment](#cloud-provider-deployment)
5. [Production Considerations](#production-considerations)
6. [Monitoring and Observability](#monitoring-and-observability)
7. [Cost Optimization](#cost-optimization)

## Local Development

### Prerequisites

- Python 3.9+
- Docker and Docker Compose
- Ollama
- Redis (optional, can use Docker)
- ChromaDB (optional, can use Docker)

### Setup

1. **Clone the repository**:
   ```bash
   git clone <repository-url>
   cd transcript-summarizer
   ```

2. **Install dependencies**:
   ```bash
   pip install -e ".[dev]"
   ```

3. **Start services**:
   ```bash
   # Option 1: Use Docker Compose for services
   docker-compose up redis chromadb -d
   
   # Option 2: Install services locally
   # Redis: https://redis.io/download
   # ChromaDB: pip install chromadb
   ```

4. **Start Ollama and pull model**:
   ```bash
   ollama serve
   ollama pull llama3
   ```

5. **Start the application**:
   ```bash
   # Terminal 1: Start Celery worker
   celery -A transcript_summarizer.worker worker --loglevel=info
   
   # Terminal 2: Start FastAPI server
   uvicorn transcript_summarizer.api:app --reload
   ```

## Docker Deployment

### Development Environment

```bash
# Start all services
docker-compose up -d

# View logs
docker-compose logs -f

# Stop services
docker-compose down
```

### Production Environment

```bash
# Use production compose file
docker-compose -f docker-compose.prod.yml up -d

# Scale workers
docker-compose -f docker-compose.prod.yml up -d --scale worker=4

# Update services
docker-compose -f docker-compose.prod.yml pull
docker-compose -f docker-compose.prod.yml up -d
```

## Kubernetes Deployment

### Prerequisites

- Kubernetes cluster (1.20+)
- kubectl configured
- Nginx Ingress Controller
- Persistent storage

### Basic Deployment

1. **Apply manifests**:
   ```bash
   kubectl apply -f k8s/
   ```

2. **Check deployment status**:
   ```bash
   kubectl get pods -n transcript-summarizer
   kubectl get services -n transcript-summarizer
   ```

3. **Access the application**:
   ```bash
   # Port forward for testing
   kubectl port-forward svc/transcript-summarizer-api 8000:8000 -n transcript-summarizer
   
   # Or configure ingress with your domain
   ```

### Production Deployment

1. **Update image references**:
   ```bash
   # In k8s/api.yaml and k8s/worker.yaml
   sed -i 's|transcript-summarizer:latest|your-registry/transcript-summarizer:v1.0.0|g' k8s/api.yaml
   sed -i 's|transcript-summarizer-worker:latest|your-registry/transcript-summarizer-worker:v1.0.0|g' k8s/worker.yaml
   ```

2. **Configure resource limits**:
   ```yaml
   resources:
     requests:
       memory: "256Mi"
       cpu: "250m"
     limits:
       memory: "512Mi"
       cpu: "500m"
   ```

3. **Set up monitoring**:
   ```bash
   # Install Prometheus and Grafana
   helm repo add prometheus-community https://prometheus-community.github.io/helm-charts
   helm install prometheus prometheus-community/kube-prometheus-stack
   ```

## Cloud Provider Deployment

### Google Cloud Platform (GKE)

1. **Create GKE cluster**:
   ```bash
   gcloud container clusters create transcript-summarizer \
     --zone=us-central1-a \
     --machine-type=e2-standard-2 \
     --num-nodes=3 \
     --enable-autoscaling \
     --min-nodes=1 \
     --max-nodes=10
   ```

2. **Configure kubectl**:
   ```bash
   gcloud container clusters get-credentials transcript-summarizer --zone=us-central1-a
   ```

3. **Deploy application**:
   ```bash
   kubectl apply -f k8s/
   ```

### Amazon Web Services (EKS)

1. **Create EKS cluster**:
   ```bash
   eksctl create cluster \
     --name transcript-summarizer \
     --region us-west-2 \
     --nodegroup-name standard-workers \
     --node-type t3.medium \
     --nodes 3 \
     --nodes-min 1 \
     --nodes-max 10
   ```

2. **Deploy application**:
   ```bash
   kubectl apply -f k8s/
   ```

### Azure Kubernetes Service (AKS)

1. **Create AKS cluster**:
   ```bash
   az aks create \
     --resource-group transcript-summarizer-rg \
     --name transcript-summarizer \
     --node-count 3 \
     --enable-addons monitoring \
     --generate-ssh-keys
   ```

2. **Configure kubectl**:
   ```bash
   az aks get-credentials --resource-group transcript-summarizer-rg --name transcript-summarizer
   ```

## Production Considerations

### Security

1. **Network security**:
   - Use TLS/SSL certificates
   - Configure firewall rules
   - Implement network policies

2. **Authentication and authorization**:
   - Add API key authentication
   - Implement rate limiting
   - Use OAuth2/JWT tokens

3. **Secrets management**:
   ```bash
   # Create secrets in Kubernetes
   kubectl create secret generic app-secrets \
     --from-literal=redis-password=your-password \
     --from-literal=chroma-token=your-token
   ```

### High Availability

1. **Multi-zone deployment**:
   ```yaml
   affinity:
     podAntiAffinity:
       preferredDuringSchedulingIgnoredDuringExecution:
       - weight: 100
         podAffinityTerm:
           labelSelector:
             matchExpressions:
             - key: app
               operator: In
               values:
               - transcript-summarizer-api
           topologyKey: kubernetes.io/zone
   ```

2. **Database backup and recovery**:
   ```bash
   # Backup ChromaDB data
   kubectl exec -it chromadb-pod -- tar czf /backup/chroma-backup.tar.gz /chroma/chroma
   
   # Backup Redis data
   kubectl exec -it redis-pod -- redis-cli BGSAVE
   ```

### Performance Optimization

1. **Resource tuning**:
   - Monitor CPU and memory usage
   - Adjust worker concurrency
   - Optimize chunk sizes

2. **Caching**:
   - Implement response caching
   - Use CDN for static assets
   - Cache frequently accessed summaries

## Monitoring and Observability

### Metrics

1. **Prometheus metrics**:
   - API request rates and latencies
   - Summarization task metrics
   - Resource utilization

2. **Custom dashboards**:
   ```yaml
   # Grafana dashboard configuration
   apiVersion: v1
   kind: ConfigMap
   metadata:
     name: transcript-summarizer-dashboard
   data:
     dashboard.json: |
       {
         "dashboard": {
           "title": "Transcript Summarizer",
           "panels": [
             {
               "title": "Request Rate",
               "type": "graph",
               "targets": [
                 {
                   "expr": "rate(http_requests_total[5m])"
                 }
               ]
             }
           ]
         }
       }
   ```

### Logging

1. **Centralized logging**:
   ```bash
   # Deploy ELK stack or use cloud logging
   helm repo add elastic https://helm.elastic.co
   helm install elasticsearch elastic/elasticsearch
   helm install kibana elastic/kibana
   helm install logstash elastic/logstash
   ```

2. **Log aggregation**:
   ```yaml
   # Fluent Bit configuration
   apiVersion: v1
   kind: ConfigMap
   metadata:
     name: fluent-bit-config
   data:
     fluent-bit.conf: |
       [INPUT]
           Name tail
           Path /var/log/containers/*transcript-summarizer*.log
           Parser docker
           Tag kube.*
   ```

### Alerting

1. **Alert rules**:
   ```yaml
   groups:
   - name: transcript-summarizer
     rules:
     - alert: HighErrorRate
       expr: rate(http_requests_total{status=~"5.."}[5m]) > 0.1
       for: 5m
       labels:
         severity: warning
       annotations:
         summary: High error rate detected
   ```

## Cost Optimization

### Resource Optimization

1. **Right-sizing**:
   - Use resource requests and limits
   - Monitor actual usage
   - Implement vertical pod autoscaling

2. **Autoscaling**:
   ```yaml
   apiVersion: autoscaling/v2
   kind: HorizontalPodAutoscaler
   metadata:
     name: transcript-summarizer-hpa
   spec:
     scaleTargetRef:
       apiVersion: apps/v1
       kind: Deployment
       name: transcript-summarizer-api
     minReplicas: 1
     maxReplicas: 10
     metrics:
     - type: Resource
       resource:
         name: cpu
         target:
           type: Utilization
           averageUtilization: 70
   ```

### Infrastructure Cost Reduction

1. **Use spot instances**:
   ```yaml
   # Node pool with spot instances
   nodeSelector:
     cloud.google.com/gke-preemptible: "true"
   tolerations:
   - key: cloud.google.com/gke-preemptible
     operator: Equal
     value: "true"
     effect: NoSchedule
   ```

2. **Schedule-based scaling**:
   ```bash
   # Use CronJobs to scale down during off-hours
   kubectl create cronjob scale-down \
     --schedule="0 18 * * *" \
     --image=bitnami/kubectl \
     -- kubectl scale deployment transcript-summarizer-api --replicas=1
   ```

### Model Optimization

1. **Use smaller models for simple tasks**:
   - llama3:8b for general summarization
   - llama3:3b for brief summaries
   - Custom fine-tuned models

2. **Implement model caching**:
   - Cache Ollama models on persistent volumes
   - Use model quantization
   - Implement model warm-up strategies

## Troubleshooting

### Common Issues

1. **Ollama connection issues**:
   ```bash
   # Check Ollama status
   kubectl logs deployment/ollama -n transcript-summarizer
   
   # Test connection
   kubectl exec -it api-pod -- curl http://ollama:11434/api/tags
   ```

2. **ChromaDB issues**:
   ```bash
   # Check ChromaDB health
   kubectl exec -it chromadb-pod -- curl http://localhost:8000/api/v1/heartbeat
   
   # Check persistent volume
   kubectl get pv,pvc -n transcript-summarizer
   ```

3. **Worker issues**:
   ```bash
   # Check Celery workers
   kubectl logs deployment/transcript-summarizer-worker -n transcript-summarizer
   
   # Check Redis connection
   kubectl exec -it redis-pod -- redis-cli ping
   ```

### Performance Issues

1. **Slow summarization**:
   - Check Ollama model loading time
   - Monitor worker resource usage
   - Optimize chunk sizes

2. **High memory usage**:
   - Monitor ChromaDB memory usage
   - Check for memory leaks in workers
   - Implement garbage collection

This deployment guide provides comprehensive instructions for deploying the Transcript Summarizer application in various environments, from local development to production cloud deployments.
