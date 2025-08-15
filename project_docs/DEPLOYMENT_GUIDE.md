# XRPL MCP Server - Production Deployment Guide

## 🚀 Production Deployment Overview

This guide covers deploying the XRPL MCP Server to production environments with proper security, monitoring, and scaling considerations.

## 📋 Pre-Deployment Checklist

### Environment Requirements
- [ ] **Python 3.10+** installed on target servers
- [ ] **Poetry** for dependency management
- [ ] **Google API Key** with sufficient quota for Gemini API
- [ ] **Network Access** to XRPL networks (testnet/mainnet)
- [ ] **System Resources**: 2GB+ RAM, 2+ CPU cores recommended
- [ ] **Storage**: 10GB+ for logs, dependencies, and future data

### Security Requirements
- [ ] **API Authentication** implemented
- [ ] **Rate Limiting** configured
- [ ] **HTTPS/WSS** certificates obtained
- [ ] **Firewall Rules** configured
- [ ] **Environment Variables** secured
- [ ] **Log Access** restricted

### Monitoring Requirements
- [ ] **Health Check** endpoints configured
- [ ] **Logging** infrastructure ready
- [ ] **Metrics Collection** system available
- [ ] **Alerting** rules configured
- [ ] **Backup Strategy** implemented

## 🏗️ Deployment Architectures

### 1. Single Server Deployment (Small Scale)

```
[Load Balancer/Nginx] → [Server Instance]
                         ├── MCP Server (Port 8000)
                         ├── Agent Client (Port 8080)
                         └── Monitoring (Port 9090)
```

**Suitable For:**
- Small teams (< 50 users)
- Development/staging environments
- Proof of concept deployments

**Resource Requirements:**
- **RAM**: 2-4GB
- **CPU**: 2-4 cores
- **Storage**: 50GB
- **Network**: 10Mbps+

### 2. Microservices Deployment (Medium Scale)

```
[Load Balancer] → [MCP Server Cluster] → [XRPL Network]
                ↗ [Agent Client Cluster]
                ↗ [Redis Cache]
                ↗ [Database]
                ↗ [Monitoring Stack]
```

**Components:**
- **MCP Server Instances**: 2-3 replicas
- **Agent Client Instances**: 2-5 replicas  
- **Redis**: For session/cache storage
- **PostgreSQL**: For conversation history
- **Prometheus/Grafana**: For monitoring

**Suitable For:**
- Medium organizations (50-500 users)
- Production environments
- High availability requirements

### 3. Enterprise Deployment (Large Scale)

```
[CDN] → [API Gateway] → [Service Mesh]
                         ├── MCP Server Farm (Auto-scaling)
                         ├── Agent Client Farm (Auto-scaling)
                         ├── Cache Cluster (Redis/MemcacheD)
                         ├── Database Cluster (Primary/Replica)
                         ├── Message Queue (RabbitMQ/Kafka)
                         └── Observability Stack
```

**Features:**
- Auto-scaling based on demand
- Multi-region deployment
- Advanced monitoring and analytics
- Disaster recovery capabilities

## 🐳 Docker Deployment

### Docker Configuration

**Dockerfile for MCP Server:**
```dockerfile
FROM python:3.11-slim

WORKDIR /app

# Install Poetry
RUN pip install poetry

# Copy dependency files
COPY pyproject.toml poetry.lock ./

# Install dependencies
RUN poetry config virtualenvs.create false \
    && poetry install --no-dev --no-interaction --no-ansi

# Copy application code
COPY . .

# Expose port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=60s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# Run server
CMD ["poetry", "run", "python", "-m", "xrpl.server.main"]
```

**Dockerfile for Agent Client:**
```dockerfile
FROM python:3.11-slim

WORKDIR /app

RUN pip install poetry

COPY pyproject.toml poetry.lock ./
RUN poetry config virtualenvs.create false \
    && poetry install --no-dev

COPY . .

EXPOSE 8080

HEALTHCHECK --interval=30s --timeout=10s --start-period=60s --retries=3 \
    CMD curl -f http://localhost:8080/ || exit 1

CMD ["poetry", "run", "python", "client/client.py"]
```

### Docker Compose Configuration

```yaml
version: '3.8'

services:
  mcp-server:
    build:
      context: .
      dockerfile: Dockerfile.mcp
    ports:
      - "8000:8000"
    environment:
      - LOG_LEVEL=INFO
      - XRPL_NETWORK=${XRPL_NETWORK:-https://s.altnet.rippletest.net:51234/}
    volumes:
      - ./logs:/app/logs
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/health"]
      interval: 30s
      timeout: 10s
      retries: 3
    restart: unless-stopped

  agent-client:
    build:
      context: .
      dockerfile: Dockerfile.agent
    ports:
      - "8080:8080"
    environment:
      - GOOGLE_API_KEY=${GOOGLE_API_KEY}
      - MCP_SERVER_URL=http://mcp-server:8000/sse
    volumes:
      - ./logs:/app/logs
    depends_on:
      - mcp-server
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8080/"]
      interval: 30s
      timeout: 10s
      retries: 3
    restart: unless-stopped

  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"
    volumes:
      - redis-data:/data
    restart: unless-stopped

  nginx:
    image: nginx:alpine
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./nginx.conf:/etc/nginx/nginx.conf
      - ./ssl:/etc/nginx/ssl
    depends_on:
      - mcp-server
      - agent-client
    restart: unless-stopped

  prometheus:
    image: prom/prometheus:latest
    ports:
      - "9090:9090"
    volumes:
      - ./prometheus.yml:/etc/prometheus/prometheus.yml
      - prometheus-data:/prometheus
    restart: unless-stopped

  grafana:
    image: grafana/grafana:latest
    ports:
      - "3000:3000"
    environment:
      - GF_SECURITY_ADMIN_PASSWORD=${GRAFANA_PASSWORD}
    volumes:
      - grafana-data:/var/lib/grafana
    restart: unless-stopped

volumes:
  redis-data:
  prometheus-data:
  grafana-data:
```

### Deployment Commands

```bash
# Build and start services
docker-compose up -d

# Scale agent clients
docker-compose up -d --scale agent-client=3

# View logs
docker-compose logs -f

# Update services
docker-compose pull
docker-compose up -d

# Backup data
docker run --rm -v redis-data:/data -v $(pwd):/backup alpine tar czf /backup/redis-backup.tar.gz /data
```

## ☸️ Kubernetes Deployment

### Kubernetes Manifests

**MCP Server Deployment:**
```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: xrpl-mcp-server
  labels:
    app: xrpl-mcp-server
spec:
  replicas: 3
  selector:
    matchLabels:
      app: xrpl-mcp-server
  template:
    metadata:
      labels:
        app: xrpl-mcp-server
    spec:
      containers:
      - name: mcp-server
        image: xrpl-mcp-server:latest
        ports:
        - containerPort: 8000
        env:
        - name: LOG_LEVEL
          value: "INFO"
        - name: XRPL_NETWORK
          valueFrom:
            configMapKeyRef:
              name: xrpl-config
              key: network-url
        resources:
          requests:
            memory: "512Mi"
            cpu: "250m"
          limits:
            memory: "1Gi"
            cpu: "500m"
        livenessProbe:
          httpGet:
            path: /health
            port: 8000
          initialDelaySeconds: 60
          periodSeconds: 30
        readinessProbe:
          httpGet:
            path: /health
            port: 8000
          initialDelaySeconds: 30
          periodSeconds: 10
---
apiVersion: v1
kind: Service
metadata:
  name: xrpl-mcp-server-service
spec:
  selector:
    app: xrpl-mcp-server
  ports:
  - protocol: TCP
    port: 8000
    targetPort: 8000
  type: ClusterIP
```

**Agent Client Deployment:**
```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: xrpl-agent-client
spec:
  replicas: 5
  selector:
    matchLabels:
      app: xrpl-agent-client
  template:
    metadata:
      labels:
        app: xrpl-agent-client
    spec:
      containers:
      - name: agent-client
        image: xrpl-agent-client:latest
        ports:
        - containerPort: 8080
        env:
        - name: GOOGLE_API_KEY
          valueFrom:
            secretKeyRef:
              name: api-keys
              key: google-api-key
        - name: MCP_SERVER_URL
          value: "http://xrpl-mcp-server-service:8000/sse"
        resources:
          requests:
            memory: "1Gi"
            cpu: "500m"
          limits:
            memory: "2Gi"
            cpu: "1"
---
apiVersion: v1
kind: Service
metadata:
  name: xrpl-agent-client-service
spec:
  selector:
    app: xrpl-agent-client
  ports:
  - protocol: TCP
    port: 8080
    targetPort: 8080
  type: LoadBalancer
```

### Horizontal Pod Autoscaler

```yaml
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: agent-client-hpa
spec:
  scaleTargetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: xrpl-agent-client
  minReplicas: 2
  maxReplicas: 20
  metrics:
  - type: Resource
    resource:
      name: cpu
      target:
        type: Utilization
        averageUtilization: 70
  - type: Resource
    resource:
      name: memory
      target:
        type: Utilization
        averageUtilization: 80
```

## 🔒 Security Configuration

### Environment Variables Security

```bash
# Use Kubernetes secrets or Docker secrets
kubectl create secret generic api-keys \
    --from-literal=google-api-key=${GOOGLE_API_KEY}

# For Docker Swarm
echo ${GOOGLE_API_KEY} | docker secret create google_api_key -
```

### API Authentication

**Add to client/client.py:**
```python
from fastapi import HTTPException, Depends, Header
import jwt

async def verify_api_key(x_api_key: str = Header()):
    if not x_api_key or x_api_key != os.getenv("API_KEY"):
        raise HTTPException(status_code=401, detail="Invalid API key")
    return x_api_key

async def verify_jwt_token(authorization: str = Header()):
    try:
        token = authorization.replace("Bearer ", "")
        payload = jwt.decode(token, os.getenv("JWT_SECRET"), algorithms=["HS256"])
        return payload
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Invalid token")

@app.websocket("/chat")
async def websocket_endpoint(
    websocket: WebSocket,
    api_key: str = Depends(verify_api_key)
):
    # WebSocket with API key authentication
```

### Rate Limiting

```python
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded

limiter = Limiter(key_func=get_remote_address)
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

@app.get("/")
@limiter.limit("100/minute")
async def root(request: Request):
    return {"message": "XRPL AI Agent API"}

@app.websocket("/chat")
@limiter.limit("10/minute")
async def websocket_endpoint(websocket: WebSocket, request: Request):
    # Rate limited WebSocket
```

### HTTPS/WSS Configuration

**Nginx Configuration:**
```nginx
server {
    listen 443 ssl http2;
    server_name your-domain.com;

    ssl_certificate /etc/nginx/ssl/cert.pem;
    ssl_certificate_key /etc/nginx/ssl/key.pem;

    # Security headers
    add_header X-Frame-Options DENY;
    add_header X-Content-Type-Options nosniff;
    add_header X-XSS-Protection "1; mode=block";
    add_header Strict-Transport-Security "max-age=31536000; includeSubDomains";

    # Agent Client API
    location / {
        proxy_pass http://agent-client:8080;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    # WebSocket support
    location /chat {
        proxy_pass http://agent-client:8080;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    # MCP Server (internal access only)
    location /mcp {
        proxy_pass http://mcp-server:8000;
        allow 10.0.0.0/8;
        allow 172.16.0.0/12;
        allow 192.168.0.0/16;
        deny all;
    }
}
```

## 📊 Monitoring and Observability

### Health Check Endpoints

**Add to both servers:**
```python
@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "version": "1.0.0",
        "uptime": time.time() - start_time
    }

@app.get("/ready")
async def readiness_check():
    # Check dependencies
    try:
        # Test XRPL connection
        await xrpl_client.request(ServerInfo())
        # Test tool availability
        tools_count = len(await client.get_tools())
        if tools_count < 150:
            raise Exception(f"Insufficient tools loaded: {tools_count}")
        
        return {"status": "ready", "tools_count": tools_count}
    except Exception as e:
        raise HTTPException(status_code=503, detail=f"Not ready: {e}")
```

### Metrics Collection

**Prometheus Metrics:**
```python
from prometheus_client import Counter, Histogram, Gauge, generate_latest

# Metrics
tool_requests_total = Counter('tool_requests_total', 'Total tool requests', ['tool_name', 'status'])
tool_request_duration = Histogram('tool_request_duration_seconds', 'Tool request duration')
active_connections = Gauge('websocket_connections_active', 'Active WebSocket connections')

@app.middleware("http")
async def metrics_middleware(request: Request, call_next):
    start_time = time.time()
    response = await call_next(request)
    request_time = time.time() - start_time
    
    tool_request_duration.observe(request_time)
    return response

@app.get("/metrics")
async def metrics():
    return Response(generate_latest(), media_type="text/plain")
```

### Logging Configuration

```python
import logging
import sys
from datetime import datetime

# Configure structured logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('/app/logs/application.log')
    ]
)

# Create logger
logger = logging.getLogger(__name__)

# Log important events
@mcp.tool()
async def create_transaction_payment(**kwargs):
    logger.info(f"Payment creation requested", extra={
        "tool": "create_transaction_payment",
        "account": kwargs.get("account"),
        "amount": kwargs.get("amount"),
        "timestamp": datetime.utcnow().isoformat()
    })
```

### Alerting Rules

**Prometheus Alerting Rules:**
```yaml
groups:
- name: xrpl-mcp-server
  rules:
  - alert: XRPLMCPServerDown
    expr: up{job="xrpl-mcp-server"} == 0
    for: 1m
    labels:
      severity: critical
    annotations:
      summary: "XRPL MCP Server is down"

  - alert: HighErrorRate
    expr: rate(tool_requests_total{status="error"}[5m]) > 0.1
    for: 5m
    labels:
      severity: warning
    annotations:
      summary: "High error rate detected"

  - alert: HighMemoryUsage
    expr: container_memory_usage_bytes / container_spec_memory_limit_bytes > 0.9
    for: 5m
    labels:
      severity: warning
    annotations:
      summary: "High memory usage detected"
```

## 🗃️ Database Integration

### PostgreSQL Setup for Conversation History

```python
# Add to requirements
# asyncpg==0.28.0
# sqlalchemy==2.0.0

from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import declarative_base, sessionmaker

Base = declarative_base()

class Conversation(Base):
    __tablename__ = "conversations"
    
    id = Column(Integer, primary_key=True)
    user_id = Column(String, index=True)
    session_id = Column(String, index=True)
    message = Column(Text)
    response = Column(Text)
    tool_calls = Column(JSON)
    created_at = Column(DateTime, default=datetime.utcnow)

# Database connection
engine = create_async_engine(os.getenv("DATABASE_URL"))
AsyncSessionLocal = sessionmaker(engine, class_=AsyncSession)

async def save_conversation(user_id: str, session_id: str, message: str, response: str, tool_calls: list):
    async with AsyncSessionLocal() as session:
        conversation = Conversation(
            user_id=user_id,
            session_id=session_id,
            message=message,
            response=response,
            tool_calls=tool_calls
        )
        session.add(conversation)
        await session.commit()
```

## 🔄 CI/CD Pipeline

### GitHub Actions Workflow

```yaml
name: Deploy XRPL MCP Server

on:
  push:
    branches: [main]
  pull_request:
    branches: [main]

jobs:
  test:
    runs-on: ubuntu-latest
    
    services:
      redis:
        image: redis
        options: >-
          --health-cmd "redis-cli ping"
          --health-interval 10s
          --health-timeout 5s
          --health-retries 5
    
    steps:
    - uses: actions/checkout@v3
    
    - name: Set up Python
      uses: actions/setup-python@v4
      with:
        python-version: '3.11'
    
    - name: Install Poetry
      uses: snok/install-poetry@v1
    
    - name: Install dependencies
      run: poetry install
    
    - name: Run tests
      run: |
        poetry run python test_mcp_tools.py
        poetry run python test_currency_agent.py
      env:
        GOOGLE_API_KEY: ${{ secrets.GOOGLE_API_KEY }}
    
    - name: Build Docker images
      run: |
        docker build -t xrpl-mcp-server:${{ github.sha }} -f Dockerfile.mcp .
        docker build -t xrpl-agent-client:${{ github.sha }} -f Dockerfile.agent .
    
  deploy:
    needs: test
    runs-on: ubuntu-latest
    if: github.ref == 'refs/heads/main'
    
    steps:
    - uses: actions/checkout@v3
    
    - name: Deploy to production
      run: |
        # Deploy to Kubernetes/Docker Swarm/etc.
        kubectl set image deployment/xrpl-mcp-server mcp-server=xrpl-mcp-server:${{ github.sha }}
        kubectl set image deployment/xrpl-agent-client agent-client=xrpl-agent-client:${{ github.sha }}
        kubectl rollout status deployment/xrpl-mcp-server
        kubectl rollout status deployment/xrpl-agent-client
```

## 🔧 Production Maintenance

### Backup Strategy

```bash
# Database backup
pg_dump $DATABASE_URL > backup-$(date +%Y%m%d).sql

# Redis backup  
redis-cli --rdb backup-$(date +%Y%m%d).rdb

# Configuration backup
tar -czf config-backup-$(date +%Y%m%d).tar.gz \
    .env nginx.conf docker-compose.yml k8s/
```

### Log Rotation

```bash
# Logrotate configuration
cat > /etc/logrotate.d/xrpl-mcp << EOF
/app/logs/*.log {
    daily
    rotate 30
    compress
    delaycompress
    missingok
    notifempty
    copytruncate
}
EOF
```

### Performance Tuning

```python
# Optimize for production
import asyncio

# Increase connection pool size
xrpl_client = AsyncJsonRpcClient(
    url="https://s1.ripple.com:51234/",
    pool_connections=20,
    pool_maxsize=50
)

# Configure async settings
asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())  # Windows
# or
asyncio.set_event_loop_policy(asyncio.UnixEventLoopPolicy())  # Unix

# Memory optimization
import gc
gc.set_threshold(700, 10, 10)  # Tune garbage collection
```

---

This deployment guide provides comprehensive instructions for taking the XRPL MCP Server from development to production with proper security, monitoring, and scaling considerations.

*Last Updated: August 15, 2025*