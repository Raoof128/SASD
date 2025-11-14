# SOAR Platform Deployment Guide

## Quick Start (Docker Compose)

### Prerequisites

- Docker 20.10+
- Docker Compose 2.0+
- 4GB RAM minimum
- 10GB disk space

### Step 1: Clone Repository

```bash
git clone <repository-url>
cd soar-platform
```

### Step 2: Configure Environment

```bash
cp .env.example .env
vim .env  # Edit with your API keys and configuration
```

**Critical settings to configure**:
```bash
SECRET_KEY=<generate-strong-random-key>
VIRUSTOTAL_API_KEY=<your-key>
ABUSEIPDB_API_KEY=<your-key>
SLACK_WEBHOOK_URL=<your-webhook>
JIRA_URL=<your-jira-url>
JIRA_API_TOKEN=<your-token>
```

### Step 3: Start Services

```bash
docker-compose up -d
```

This will start:
- PostgreSQL database
- Redis cache
- Flask web application (port 5000)
- Celery workers for async tasks

### Step 4: Initialize Database

```bash
docker-compose exec web flask db upgrade
```

### Step 5: Access Dashboard

Open browser to: `http://localhost:5000`

**Default credentials**:
- Username: `admin`
- Password: `changeme`

**IMPORTANT**: Change default password immediately!

## Production Deployment

### Architecture

```
Internet
    │
    ▼
[Load Balancer]
    │
    ├─> [Web App Instance 1]
    ├─> [Web App Instance 2]
    └─> [Web App Instance N]
         │
         ├─> [PostgreSQL (Primary)]
         │    └─> [PostgreSQL (Replica)]
         │
         ├─> [Redis Cluster]
         │
         └─> [Celery Workers]
```

### Kubernetes Deployment

#### Prerequisites

- Kubernetes cluster (1.24+)
- kubectl configured
- Helm 3.0+

#### Step 1: Create Namespace

```bash
kubectl create namespace soar-platform
```

#### Step 2: Create Secrets

```bash
kubectl create secret generic soar-secrets \
  --from-literal=secret-key=<strong-random-key> \
  --from-literal=database-password=<db-password> \
  --from-literal=virustotal-api-key=<key> \
  --from-literal=abuseipdb-api-key=<key> \
  --from-literal=slack-webhook=<webhook> \
  --from-literal=jira-api-token=<token> \
  -n soar-platform
```

#### Step 3: Create ConfigMap

```bash
kubectl create configmap soar-config \
  --from-literal=database-host=postgres-service \
  --from-literal=redis-host=redis-service \
  --from-literal=jira-url=https://your-company.atlassian.net \
  -n soar-platform
```

#### Step 4: Deploy PostgreSQL

```yaml
# postgres-deployment.yaml
apiVersion: apps/v1
kind: StatefulSet
metadata:
  name: postgres
  namespace: soar-platform
spec:
  serviceName: postgres-service
  replicas: 1
  selector:
    matchLabels:
      app: postgres
  template:
    metadata:
      labels:
        app: postgres
    spec:
      containers:
      - name: postgres
        image: postgres:15-alpine
        env:
        - name: POSTGRES_DB
          value: soar_db
        - name: POSTGRES_USER
          value: soar_user
        - name: POSTGRES_PASSWORD
          valueFrom:
            secretKeyRef:
              name: soar-secrets
              key: database-password
        ports:
        - containerPort: 5432
        volumeMounts:
        - name: postgres-storage
          mountPath: /var/lib/postgresql/data
  volumeClaimTemplates:
  - metadata:
      name: postgres-storage
    spec:
      accessModes: ["ReadWriteOnce"]
      resources:
        requests:
          storage: 20Gi
```

```bash
kubectl apply -f postgres-deployment.yaml
```

#### Step 5: Deploy Redis

```yaml
# redis-deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: redis
  namespace: soar-platform
spec:
  replicas: 1
  selector:
    matchLabels:
      app: redis
  template:
    metadata:
      labels:
        app: redis
    spec:
      containers:
      - name: redis
        image: redis:7-alpine
        ports:
        - containerPort: 6379
```

```bash
kubectl apply -f redis-deployment.yaml
```

#### Step 6: Deploy Web Application

```yaml
# web-deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: soar-web
  namespace: soar-platform
spec:
  replicas: 3
  selector:
    matchLabels:
      app: soar-web
  template:
    metadata:
      labels:
        app: soar-web
    spec:
      containers:
      - name: web
        image: soar-platform:latest
        ports:
        - containerPort: 5000
        env:
        - name: SECRET_KEY
          valueFrom:
            secretKeyRef:
              name: soar-secrets
              key: secret-key
        - name: DATABASE_URL
          value: postgresql://soar_user:$(DATABASE_PASSWORD)@postgres-service:5432/soar_db
        - name: REDIS_URL
          value: redis://redis-service:6379/0
        - name: VIRUSTOTAL_API_KEY
          valueFrom:
            secretKeyRef:
              name: soar-secrets
              key: virustotal-api-key
        livenessProbe:
          httpGet:
            path: /health
            port: 5000
          initialDelaySeconds: 30
          periodSeconds: 10
        readinessProbe:
          httpGet:
            path: /health
            port: 5000
          initialDelaySeconds: 5
          periodSeconds: 5
        resources:
          requests:
            memory: "256Mi"
            cpu: "250m"
          limits:
            memory: "512Mi"
            cpu: "500m"
```

```bash
kubectl apply -f web-deployment.yaml
```

#### Step 7: Deploy Celery Workers

```yaml
# celery-deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: celery-worker
  namespace: soar-platform
spec:
  replicas: 2
  selector:
    matchLabels:
      app: celery-worker
  template:
    metadata:
      labels:
        app: celery-worker
    spec:
      containers:
      - name: worker
        image: soar-platform:latest
        command: ["celery", "-A", "backend.orchestrator.celery", "worker", "--loglevel=info"]
        env:
        # Same env vars as web deployment
```

```bash
kubectl apply -f celery-deployment.yaml
```

#### Step 8: Create Ingress

```yaml
# ingress.yaml
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: soar-ingress
  namespace: soar-platform
  annotations:
    cert-manager.io/cluster-issuer: letsencrypt-prod
spec:
  tls:
  - hosts:
    - soar.your-company.com
    secretName: soar-tls
  rules:
  - host: soar.your-company.com
    http:
      paths:
      - path: /
        pathType: Prefix
        backend:
          service:
            name: soar-web-service
            port:
              number: 80
```

```bash
kubectl apply -f ingress.yaml
```

## Security Hardening

### 1. Change Default Credentials

```bash
# Access container
docker-compose exec web python

# Change admin password
from backend.models import User, db
from backend.app import create_app

app = create_app()
with app.app_context():
    admin = User.query.filter_by(username='admin').first()
    admin.set_password('your-strong-password')
    db.session.commit()
```

### 2. Enable HTTPS

Update `docker-compose.yml` to use nginx reverse proxy:

```yaml
nginx:
  image: nginx:alpine
  ports:
    - "443:443"
  volumes:
    - ./nginx.conf:/etc/nginx/nginx.conf
    - ./ssl:/etc/nginx/ssl
  depends_on:
    - web
```

### 3. Restrict Network Access

Configure firewall rules:
```bash
# Allow only specific IPs to access admin endpoints
ufw allow from 10.0.0.0/8 to any port 5000
```

### 4. Enable Audit Logging

Ensure all audit logs are written to secure location:
```bash
LOG_LEVEL=INFO
LOG_FORMAT=json
```

### 5. Rotate API Keys

Implement key rotation policy:
- VirusTotal: Monthly
- Slack webhooks: Quarterly
- Jira tokens: Quarterly

## Monitoring & Alerting

### Prometheus Metrics

Expose metrics endpoint:
```python
# Already implemented in backend/routes/dashboard.py
GET /api/v1/dashboard/health
```

Configure Prometheus scraping:
```yaml
# prometheus.yml
scrape_configs:
  - job_name: 'soar-platform'
    static_configs:
      - targets: ['web:5000']
```

### Grafana Dashboard

Import dashboard from `monitoring/grafana-dashboard.json`

Key metrics:
- Incident response time (MTTR)
- Playbook success rate
- API integration health
- Database query performance

### Log Aggregation

Ship logs to ELK stack:

```yaml
# filebeat.yml
filebeat.inputs:
  - type: container
    paths:
      - '/var/lib/docker/containers/*/*.log'
```

## Backup & Recovery

### Database Backups

Daily backups:
```bash
# Automated backup script
#!/bin/bash
BACKUP_DIR=/backups
DATE=$(date +%Y%m%d_%H%M%S)

docker-compose exec -T postgres pg_dump -U soar_user soar_db | \
  gzip > $BACKUP_DIR/soar_db_$DATE.sql.gz

# Retain last 30 days
find $BACKUP_DIR -name "soar_db_*.sql.gz" -mtime +30 -delete
```

Schedule with cron:
```bash
0 2 * * * /opt/soar/backup.sh
```

### Disaster Recovery

Restore from backup:
```bash
gunzip < backup.sql.gz | \
  docker-compose exec -T postgres psql -U soar_user soar_db
```

## Performance Tuning

### Database Optimization

```sql
-- Create indexes for frequently queried fields
CREATE INDEX idx_incidents_created_at ON incidents(created_at DESC);
CREATE INDEX idx_incidents_severity ON incidents(severity);
CREATE INDEX idx_incidents_status ON incidents(status);
CREATE INDEX idx_playbook_executions_incident_id ON playbook_executions(incident_id);
```

### Redis Configuration

```bash
# redis.conf
maxmemory 2gb
maxmemory-policy allkeys-lru
```

### Application Tuning

Update `docker-compose.yml`:
```yaml
web:
  environment:
    - WORKERS=4
    - THREADS=2
    - MAX_WORKERS=8
```

## Troubleshooting

### Issue: Cannot connect to database

```bash
# Check database logs
docker-compose logs postgres

# Verify connection
docker-compose exec web python -c "from backend.models import db; from backend.app import create_app; app = create_app(); app.app_context().push(); db.session.execute('SELECT 1')"
```

### Issue: Celery tasks not executing

```bash
# Check Celery worker logs
docker-compose logs celery

# Verify Redis connection
docker-compose exec redis redis-cli ping
```

### Issue: API integrations failing

```bash
# Check integration status
curl http://localhost:5000/api/v1/dashboard/health
```

## Maintenance

### Update Application

```bash
# Pull latest changes
git pull origin main

# Rebuild containers
docker-compose down
docker-compose build
docker-compose up -d

# Run migrations
docker-compose exec web flask db upgrade
```

### Scale Workers

```bash
# Increase Celery workers
docker-compose up -d --scale celery=5
```

## Support

For issues or questions:
- GitHub Issues: <repository-url>/issues
- Documentation: <repository-url>/docs
- Security: security@company.com
