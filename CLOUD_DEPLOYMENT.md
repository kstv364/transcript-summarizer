# Cloud Deployment Guide

This guide covers deploying the Transcript Summarizer to AWS EKS or DigitalOcean Kubernetes (DOKS) clusters.

## Prerequisites

- GitHub repository with the application code
- Container registry access (GitHub Container Registry)
- Cloud platform account (AWS or DigitalOcean)
- kubectl installed locally
- Cloud CLI tools (AWS CLI or doctl)

## 🚀 AWS EKS Deployment

### 1. Create EKS Cluster

```bash
# Install eksctl
curl --silent --location "https://github.com/weaveworks/eksctl/releases/latest/download/eksctl_$(uname -s)_amd64.tar.gz" | tar xz -C /tmp
sudo mv /tmp/eksctl /usr/local/bin

# Create EKS cluster
eksctl create cluster \
  --name transcript-summarizer \
  --region us-east-1 \
  --nodegroup-name standard-workers \
  --node-type t3.medium \
  --nodes 3 \
  --nodes-min 1 \
  --nodes-max 4 \
  --managed
```

### 2. Configure GitHub Secrets

Add these secrets to your GitHub repository:

- `AWS_ACCESS_KEY_ID`: Your AWS access key
- `AWS_SECRET_ACCESS_KEY`: Your AWS secret key

### 3. Configure GitHub Variables

Add these repository variables:

- `DEPLOY_PLATFORM`: Set to `aws`
- `EKS_CLUSTER_NAME`: Your EKS cluster name (e.g., `transcript-summarizer`)

### 4. Install Ingress Controller

```bash
# Install AWS Load Balancer Controller
kubectl apply -k "github.com/aws/eks-charts/stable/aws-load-balancer-controller//crds?ref=master"

# Create service account
eksctl create iamserviceaccount \
  --cluster=transcript-summarizer \
  --namespace=kube-system \
  --name=aws-load-balancer-controller \
  --role-name AmazonEKSLoadBalancerControllerRole \
  --attach-policy-arn=arn:aws:iam::aws:policy/ElasticLoadBalancingFullAccess \
  --approve

# Install controller
helm repo add eks https://aws.github.io/eks-charts
helm repo update
helm install aws-load-balancer-controller eks/aws-load-balancer-controller \
  -n kube-system \
  --set clusterName=transcript-summarizer \
  --set serviceAccount.create=false \
  --set serviceAccount.name=aws-load-balancer-controller
```

### 5. Configure DNS (Optional)

```bash
# Install external-dns for automatic DNS management
helm repo add external-dns https://kubernetes-sigs.github.io/external-dns/
helm install external-dns external-dns/external-dns \
  --set provider=aws \
  --set aws.zoneType=public \
  --set txtOwnerId=transcript-summarizer \
  --set domainFilters[0]=your-domain.com
```

### 6. Deploy Application

Push to main branch - GitHub Actions will automatically deploy to AWS.

---

## 🌊 DigitalOcean Kubernetes Deployment

### 1. Create DOKS Cluster

```bash
# Install doctl
curl -sL https://github.com/digitalocean/doctl/releases/download/v1.95.0/doctl-1.95.0-linux-amd64.tar.gz | tar -xzv
sudo mv doctl /usr/local/bin

# Authenticate
doctl auth init

# Create cluster
doctl kubernetes cluster create transcript-summarizer \
  --region nyc3 \
  --version 1.28.2-do.0 \
  --count 3 \
  --size s-2vcpu-2gb \
  --auto-upgrade=true \
  --surge-upgrade=true
```

### 2. Configure GitHub Secrets

Add this secret to your GitHub repository:

- `DIGITALOCEAN_ACCESS_TOKEN`: Your DigitalOcean API token

### 3. Configure GitHub Variables

Add these repository variables:

- `DEPLOY_PLATFORM`: Set to `digitalocean`
- `DO_CLUSTER_NAME`: Your DOKS cluster name (e.g., `transcript-summarizer`)

### 4. Install Ingress Controller

```bash
# Install NGINX Ingress Controller
kubectl apply -f https://raw.githubusercontent.com/kubernetes/ingress-nginx/controller-v1.8.1/deploy/static/provider/do/deploy.yaml

# Wait for load balancer
kubectl wait --namespace ingress-nginx \
  --for=condition=ready pod \
  --selector=app.kubernetes.io/component=controller \
  --timeout=300s
```

### 5. Configure DNS

```bash
# Get load balancer IP
kubectl get svc -n ingress-nginx ingress-nginx-controller

# Create DNS records pointing to the load balancer IP:
# api.transcript-summarizer.your-domain.com
# app.transcript-summarizer.your-domain.com
```

### 6. Install cert-manager (SSL)

```bash
# Install cert-manager
kubectl apply -f https://github.com/cert-manager/cert-manager/releases/download/v1.13.0/cert-manager.yaml

# Wait for cert-manager
kubectl wait --for=condition=ready pod -l app=cert-manager -n cert-manager --timeout=300s

# Create cluster issuer
kubectl apply -f - <<EOF
apiVersion: cert-manager.io/v1
kind: ClusterIssuer
metadata:
  name: letsencrypt-prod
spec:
  acme:
    server: https://acme-v02.api.letsencrypt.org/directory
    email: your-email@domain.com
    privateKeySecretRef:
      name: letsencrypt-prod
    solvers:
    - http01:
        ingress:
          class: nginx
EOF
```

### 7. Deploy Application

Push to main branch - GitHub Actions will automatically deploy to DigitalOcean.

---

## 🔧 Configuration

### Environment Variables

Update `k8s/configmap.yaml` with your configuration:

```yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: app-config
  namespace: transcript-summarizer
data:
  OLLAMA_BASE_URL: "http://ollama:11434"
  OLLAMA_MODEL: "llama3"
  CHROMA_HOST: "chromadb"
  CHROMA_PORT: "8000"
  REDIS_URL: "redis://redis:6379/0"
  LOG_LEVEL: "INFO"
```

### Ingress Configuration

Update `k8s/ingress.yaml` with your domain:

```yaml
spec:
  tls:
  - hosts:
    - api.your-domain.com
    - app.your-domain.com
    secretName: transcript-summarizer-tls
  rules:
  - host: api.your-domain.com
    http:
      paths:
      - path: /
        pathType: Prefix
        backend:
          service:
            name: api
            port:
              number: 8000
  - host: app.your-domain.com
    http:
      paths:
      - path: /
        pathType: Prefix
        backend:
          service:
            name: frontend
            port:
              number: 7860
```

---

## 📊 Monitoring

### Health Checks

```bash
# Check pod status
kubectl get pods -n transcript-summarizer

# Check service endpoints
kubectl get endpoints -n transcript-summarizer

# View logs
kubectl logs -f deployment/api -n transcript-summarizer
kubectl logs -f deployment/frontend -n transcript-summarizer
```

### Application URLs

After deployment, access your application at:

- **Web Interface**: https://app.your-domain.com
- **API Documentation**: https://api.your-domain.com/docs
- **Health Check**: https://api.your-domain.com/health

---

## 🔒 Security

### RBAC

The application uses minimal RBAC permissions. Review `k8s/` manifests for security settings.

### Network Policies

Consider implementing network policies for additional security:

```bash
# Example network policy (customize as needed)
kubectl apply -f - <<EOF
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: transcript-summarizer-netpol
  namespace: transcript-summarizer
spec:
  podSelector: {}
  policyTypes:
  - Ingress
  - Egress
  ingress:
  - from:
    - namespaceSelector:
        matchLabels:
          name: ingress-nginx
  egress:
  - {}
EOF
```

---

## 🛠️ Troubleshooting

### Common Issues

1. **Pod Not Starting**:
   ```bash
   kubectl describe pod <pod-name> -n transcript-summarizer
   kubectl logs <pod-name> -n transcript-summarizer
   ```

2. **Ingress Not Working**:
   ```bash
   kubectl describe ingress -n transcript-summarizer
   kubectl get events -n transcript-summarizer
   ```

3. **Service Discovery Issues**:
   ```bash
   kubectl get endpoints -n transcript-summarizer
   kubectl exec -it <pod-name> -n transcript-summarizer -- nslookup redis
   ```

### Performance Tuning

1. **Adjust Resource Limits**: Update CPU/memory limits in deployment manifests
2. **Scale Workers**: Modify replica count in `k8s/worker.yaml`
3. **Enable HPA**: Configure Horizontal Pod Autoscaler for automatic scaling

---

## 📈 Scaling

### Horizontal Pod Autoscaler

```bash
# Create HPA for API
kubectl autoscale deployment api --cpu-percent=70 --min=2 --max=10 -n transcript-summarizer

# Create HPA for workers
kubectl autoscale deployment worker --cpu-percent=80 --min=2 --max=20 -n transcript-summarizer
```

### Vertical Scaling

Update resource requests/limits in the deployment manifests based on monitoring data.

---

## 💰 Cost Optimization

### AWS EKS
- Use Spot instances for worker nodes
- Enable cluster autoscaler
- Consider Fargate for serverless containers

### DigitalOcean DOKS
- Use appropriately sized droplets
- Enable auto-scaling
- Consider reserved instances for predictable workloads

---

This completes the deployment setup for both AWS EKS and DigitalOcean Kubernetes clusters.
