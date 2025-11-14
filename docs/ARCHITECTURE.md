# SOAR Platform Architecture

## System Overview

The SOAR Platform is built on a microservices-inspired architecture with the following components:

```
┌─────────────────────────────────────────────────────────────┐
│                     Web Dashboard (Flask)                    │
│              Bootstrap 5 + Chart.js + JavaScript             │
└────────────────────────┬────────────────────────────────────┘
                         │ HTTP/REST
┌────────────────────────┴────────────────────────────────────┐
│                    Flask API Backend                         │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐      │
│  │  Auth & RBAC │  │  Incidents   │  │  Playbooks   │      │
│  └──────────────┘  └──────────────┘  └──────────────┘      │
└────────────────────────┬────────────────────────────────────┘
                         │
         ┌───────────────┼───────────────┐
         │               │               │
    ┌────▼────┐     ┌────▼────┐    ┌────▼────┐
    │PostgreSQL│     │  Redis  │    │ Celery  │
    │         │     │  Cache  │    │ Workers │
    └─────────┘     └─────────┘    └────┬────┘
                                         │
                              ┌──────────┴──────────┐
                              │  Playbook Engine    │
                              │  - Base Playbook    │
                              │  - Orchestrator     │
                              │  - Decision Engine  │
                              └──────────┬──────────┘
                                         │
                        ┌────────────────┴────────────────┐
                        │    External Integrations        │
                        │  - VirusTotal                   │
                        │  - AbuseIPDB                    │
                        │  - Slack                        │
                        │  - Jira                         │
                        │  - Email/AD/Firewall/EDR        │
                        └─────────────────────────────────┘
```

## Component Details

### 1. Flask API Backend

**Location**: `backend/app.py`

- RESTful API endpoints for all SOAR operations
- JWT and session-based authentication
- Role-based access control (RBAC)
- Request validation and error handling

**Key Routes**:
- `/api/v1/auth/*` - Authentication and user management
- `/api/v1/incidents/*` - Incident CRUD operations
- `/api/v1/playbooks/*` - Playbook execution and management
- `/api/v1/dashboard/*` - Metrics and dashboard data

### 2. Database Layer (PostgreSQL)

**Location**: `backend/models.py`

**Tables**:
- `users` - User accounts with roles
- `incidents` - Security incidents
- `playbooks` - Playbook definitions
- `playbook_executions` - Execution tracking
- `api_integrations` - External API configurations
- `audit_logs` - Comprehensive audit trail
- `metrics` - Performance metrics

### 3. Orchestration Engine

**Location**: `backend/orchestrator.py`

Responsibilities:
- Async playbook execution via Celery
- Playbook selection and routing
- Execution tracking and metrics
- Error handling and rollback

### 4. Decision Engine

**Location**: `backend/decision_engine.py`

Features:
- Rule-based incident classification
- Automatic playbook selection
- IOC extraction
- Severity assessment
- Action recommendations

### 5. Playbook System

**Location**: `backend/playbooks/`

**Architecture**:
```python
BasePlaybook (Abstract)
    ├── PhishingResponsePlaybook
    ├── MalwareContainmentPlaybook
    ├── AccountCompromisePlaybook
    ├── DataExfiltrationPlaybook
    ├── BruteForceDefensePlaybook
    ├── VulnerabilityRemediationPlaybook
    ├── PowerShellAnalysisPlaybook
    └── DNSTunnelingPlaybook
```

Each playbook inherits from `BasePlaybook` and implements:
- `execute()` method for automated response
- Action tracking for audit trail
- Integration with threat intelligence
- Notification and ticketing

### 6. API Integrations

**Location**: `backend/integrations/`

All integrations follow a consistent pattern:
- Async/await for non-blocking I/O
- Error handling and retry logic
- Rate limiting awareness
- Mock-friendly for testing

## Data Flow

### Incident Response Flow

```
1. Alert Ingestion
   └─> SIEM webhook → /api/v1/incidents (POST)

2. Enrichment
   └─> Orchestrator queries threat intel APIs
   └─> VirusTotal, AbuseIPDB, etc.

3. Classification
   └─> Decision Engine analyzes incident
   └─> Selects appropriate playbook

4. Playbook Execution
   └─> Celery worker executes playbook async
   └─> Actions logged to database
   └─> External APIs called (containment, ticketing)

5. Notification
   └─> Slack/Email alerts sent
   └─> Jira ticket created
   └─> Dashboard updated

6. Metrics Collection
   └─> Response time calculated
   └─> Automation rate tracked
   └─> ROI computed
```

## Security Considerations

### Authentication & Authorization

- JWT tokens for API authentication
- Session-based auth for web UI
- Role hierarchy: Analyst < Incident Commander < Admin
- Password hashing with bcrypt
- CSRF protection

### API Key Management

- API keys encrypted at rest
- Environment variable configuration
- Separate keys per integration
- Rate limiting enforcement

### Audit Logging

- All actions logged with user, timestamp, IP
- Immutable audit trail
- Old/new values tracked for changes
- Queryable for compliance

## Scalability

### Horizontal Scaling

- Stateless Flask application (multiple instances)
- Celery workers scale independently
- Redis for session sharing
- PostgreSQL with connection pooling

### Performance Optimizations

- Database indexes on frequently queried fields
- Redis caching for session data
- Async API calls to external services
- Batch operations where possible

### High Availability

- Health check endpoints (`/health`)
- Graceful degradation if external APIs fail
- Database connection retry logic
- Celery task retry with exponential backoff

## Deployment Architecture

### Docker Compose (Development)

```
web (Flask) ──┬──> postgres (Database)
              ├──> redis (Cache/Broker)
              └──> celery (Workers)
```

### Kubernetes (Production)

```
Ingress
  └─> Service (web)
       └─> Deployment (web pods)
            ├─> ConfigMap (environment)
            └─> Secret (API keys)

StatefulSet (postgres)
  └─> PersistentVolume

Deployment (redis)
Deployment (celery workers)
```

## Monitoring & Observability

### Metrics

- Prometheus-compatible metrics endpoint
- Custom business metrics (MTTR, automation rate)
- Playbook execution times
- API integration health

### Logging

- Structured JSON logging
- Log levels: DEBUG, INFO, WARNING, ERROR
- Centralized log aggregation (compatible with ELK)

### Health Checks

- Database connectivity
- Redis availability
- External API status
- Playbook availability

## Future Enhancements

1. **Machine Learning**
   - ML-based incident classification
   - Anomaly detection
   - Predictive analytics

2. **Advanced Orchestration**
   - Playbook chaining
   - Conditional logic
   - User interaction workflows

3. **Additional Integrations**
   - MISP threat sharing
   - ServiceNow ticketing
   - Microsoft Sentinel
   - CrowdStrike EDR

4. **Enhanced UI**
   - React/Vue.js frontend
   - Real-time WebSocket updates
   - Interactive playbook editor

5. **Compliance**
   - SOC 2 controls
   - GDPR compliance
   - Customizable retention policies
