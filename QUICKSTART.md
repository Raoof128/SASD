# SOAR Platform - Quick Start Guide

## Prerequisites

- **Docker & Docker Compose** (recommended) OR
- **Python 3.10+**, PostgreSQL, Redis

## Option 1: Docker (Recommended)

### 1. Clone Repository

```bash
git clone <repository-url>
cd soar-platform
```

### 2. Configure Environment

```bash
cp .env.example .env
# Edit .env with your API keys (optional for testing)
```

### 3. Start Platform

```bash
make docker-up
```

Or manually:

```bash
docker-compose up -d
docker-compose exec web python scripts/init_db.py
```

### 4. Access Dashboard

Open browser to: **http://localhost:5000**

**Default Login:**
- Username: `admin`
- Password: `changeme`

⚠️ **Change password immediately after first login!**

### 5. Stop Platform

```bash
make docker-down
```

---

## Option 2: Local Development

### 1. Install Dependencies

```bash
# Install PostgreSQL and Redis (Ubuntu/Debian)
sudo apt-get install postgresql redis-server

# Create virtual environment
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install Python packages
pip install -r requirements.txt
```

### 2. Configure Database

```bash
# Create PostgreSQL database
sudo -u postgres psql
CREATE DATABASE soar_db;
CREATE USER soar_user WITH PASSWORD 'soar_password';
GRANT ALL PRIVILEGES ON DATABASE soar_db TO soar_user;
\q
```

### 3. Configure Environment

```bash
cp .env.example .env
# Edit DATABASE_URL and other settings
```

### 4. Initialize Database

```bash
python scripts/init_db.py
```

### 5. Start Services

**Terminal 1 - Flask App:**
```bash
python run.py
```

**Terminal 2 - Celery Worker:**
```bash
celery -A backend.celery_app.celery_app worker --loglevel=info
```

**Terminal 3 - Redis:**
```bash
redis-server
```

### 6. Access Dashboard

Open browser to: **http://localhost:5000**

---

## Quick Commands

### Using Makefile

```bash
make help          # Show all available commands
make install       # Install dependencies
make init          # Initialize database
make run           # Run Flask app
make test          # Run tests
make docker-up     # Start with Docker
make docker-down   # Stop Docker containers
```

### Manual Commands

```bash
# Run application
python run.py

# Initialize database
python scripts/init_db.py

# Run tests
pytest tests/ -v

# Run with coverage
pytest tests/ --cov=backend --cov-report=html

# Start Celery worker
celery -A backend.celery_app.celery_app worker --loglevel=info

# Format code
black backend/
```

---

## Testing the Platform

### 1. Create Test Incident

```bash
curl -X POST http://localhost:5000/api/v1/incidents \
  -H "Content-Type: application/json" \
  -d '{
    "alert_id": "TEST-001",
    "title": "Test Phishing Email",
    "description": "Suspicious email from attacker@evil.com with URL: https://malicious-site.com",
    "severity": "high",
    "incident_type": "phishing",
    "source_ip": "1.2.3.4",
    "source_user": "victim@company.com"
  }'
```

### 2. View Incidents

Open: http://localhost:5000/api/v1/incidents

### 3. Execute Playbook

```bash
curl -X POST http://localhost:5000/api/v1/playbooks/1/execute \
  -H "Content-Type: application/json" \
  -d '{
    "incident_id": 1
  }'
```

### 4. View Dashboard

Open: http://localhost:5000/

---

## API Endpoints

### Authentication
- `POST /api/v1/auth/login` - Login
- `POST /api/v1/auth/logout` - Logout
- `GET /api/v1/auth/me` - Get current user

### Incidents
- `GET /api/v1/incidents` - List incidents
- `POST /api/v1/incidents` - Create incident
- `GET /api/v1/incidents/{id}` - Get incident details
- `PUT /api/v1/incidents/{id}` - Update incident
- `DELETE /api/v1/incidents/{id}` - Delete incident

### Playbooks
- `GET /api/v1/playbooks` - List playbooks
- `POST /api/v1/playbooks/{id}/execute` - Execute playbook
- `GET /api/v1/playbooks/executions` - List executions
- `GET /api/v1/playbooks/executions/{id}` - Get execution details

### Dashboard
- `GET /api/v1/dashboard/overview` - Dashboard metrics
- `GET /api/v1/dashboard/incidents/trend` - Incident trend data
- `GET /api/v1/dashboard/incidents/by-severity` - Severity breakdown
- `GET /api/v1/dashboard/playbooks/performance` - Playbook performance

### System
- `GET /health` - Health check
- `GET /api/v1/status` - API status

---

## Troubleshooting

### Database Connection Error

```bash
# Check PostgreSQL is running
sudo systemctl status postgresql

# Check Redis is running
sudo systemctl status redis

# Verify database exists
sudo -u postgres psql -l | grep soar_db
```

### Port Already in Use

```bash
# Find process using port 5000
lsof -i :5000

# Kill process
kill -9 <PID>

# Or use different port
export APP_PORT=5001
python run.py
```

### Celery Worker Not Starting

```bash
# Check Redis connection
redis-cli ping

# Check Celery broker URL in .env
echo $CELERY_BROKER_URL

# Run with verbose logging
celery -A backend.celery_app.celery_app worker --loglevel=debug
```

### Docker Issues

```bash
# View logs
docker-compose logs -f

# Restart containers
docker-compose restart

# Clean rebuild
docker-compose down -v
docker-compose build --no-cache
docker-compose up -d
```

---

## Next Steps

1. **Configure API Keys** - Add VirusTotal, AbuseIPDB keys in `.env`
2. **Change Passwords** - Update default user passwords
3. **Configure Slack** - Add Slack webhook for notifications
4. **Configure Jira** - Add Jira credentials for ticketing
5. **Review Documentation** - Read `docs/ARCHITECTURE.md`
6. **Run Tests** - Execute `make test` to verify setup
7. **Deploy to Production** - See `docs/DEPLOYMENT.md`

---

## Support

- **Documentation**: See `docs/` directory
- **Issues**: Open GitHub issue
- **API Docs**: See `docs/API_INTEGRATIONS.md`
