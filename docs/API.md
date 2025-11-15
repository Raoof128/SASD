# SOAR Platform API Documentation

Complete API reference for the SOAR Platform REST API.

## Base URL

```
http://localhost:5000/api/v1
```

## Authentication

All API requests require authentication using JWT tokens.

### Login

**Endpoint:** `POST /api/v1/auth/login`

**Request:**
```json
{
  "username": "admin",
  "password": "changeme"
}
```

**Response:**
```json
{
  "token": "eyJ0eXAiOiJKV1QiLCJhbGc...",
  "user": {
    "id": 1,
    "username": "admin",
    "role": "admin"
  }
}
```

### Using Tokens

Include the JWT token in the Authorization header:

```bash
curl -H "Authorization: Bearer YOUR_TOKEN" http://localhost:5000/api/v1/incidents
```

## Endpoints

### Incidents

#### List Incidents

**Endpoint:** `GET /api/v1/incidents`

**Query Parameters:**
- `status` (optional): Filter by status (new, investigating, contained, resolved, closed)
- `severity` (optional): Filter by severity (low, medium, high, critical)
- `limit` (optional): Number of results (default: 50, max: 100)
- `offset` (optional): Pagination offset (default: 0)
- `sort` (optional): Sort field with direction (e.g., `-created_at`, `severity`)

**Example:**
```bash
GET /api/v1/incidents?status=open&severity=high&limit=20
```

**Response:**
```json
{
  "incidents": [
    {
      "id": 1,
      "alert_id": "INC-2024-001",
      "title": "Suspicious phishing email detected",
      "description": "User reported suspicious email",
      "severity": "high",
      "status": "investigating",
      "incident_type": "phishing",
      "source_ip": "192.168.1.100",
      "source_email": "attacker@malicious.com",
      "affected_systems": ["DESKTOP-001"],
      "metadata": {},
      "created_at": "2024-11-14T10:30:00Z",
      "updated_at": "2024-11-14T10:35:00Z",
      "resolved_at": null
    }
  ],
  "total": 1,
  "limit": 20,
  "offset": 0
}
```

#### Get Incident

**Endpoint:** `GET /api/v1/incidents/{id}`

**Response:**
```json
{
  "id": 1,
  "alert_id": "INC-2024-001",
  "title": "Suspicious phishing email detected",
  "severity": "high",
  "status": "investigating",
  "playbook_executions": [
    {
      "id": 1,
      "playbook_name": "Phishing Response",
      "status": "completed",
      "started_at": "2024-11-14T10:30:05Z",
      "completed_at": "2024-11-14T10:32:00Z"
    }
  ]
}
```

#### Create Incident

**Endpoint:** `POST /api/v1/incidents`

**Request:**
```json
{
  "title": "Suspicious activity detected",
  "description": "Multiple failed login attempts",
  "severity": "high",
  "incident_type": "brute_force",
  "source_ip": "203.0.113.45",
  "affected_systems": ["WEB-SERVER-01"],
  "metadata": {
    "failed_attempts": 50,
    "target_user": "admin"
  }
}
```

**Response:**
```json
{
  "id": 2,
  "alert_id": "INC-2024-002",
  "status": "new",
  "created_at": "2024-11-14T11:00:00Z"
}
```

#### Update Incident

**Endpoint:** `PUT /api/v1/incidents/{id}`

**Request:**
```json
{
  "status": "resolved",
  "notes": "False positive - legitimate admin activity"
}
```

**Response:**
```json
{
  "id": 2,
  "status": "resolved",
  "updated_at": "2024-11-14T11:05:00Z"
}
```

#### Delete Incident

**Endpoint:** `DELETE /api/v1/incidents/{id}`

**Response:**
```json
{
  "message": "Incident deleted successfully"
}
```

### Playbooks

#### List Playbooks

**Endpoint:** `GET /api/v1/playbooks`

**Response:**
```json
{
  "playbooks": [
    {
      "id": 1,
      "name": "Phishing Response",
      "description": "Automated phishing investigation and response",
      "enabled": true,
      "trigger_conditions": {
        "incident_type": "phishing",
        "severity": ["high", "critical"]
      },
      "automation_rate": 95.0,
      "avg_execution_time": 120
    }
  ]
}
```

#### Get Playbook

**Endpoint:** `GET /api/v1/playbooks/{id}`

**Response:**
```json
{
  "id": 1,
  "name": "Phishing Response",
  "description": "Automated phishing investigation and response",
  "enabled": true,
  "actions": [
    "Extract email details",
    "Check URL reputation",
    "Analyze attachments",
    "Quarantine if malicious",
    "Notify security team"
  ],
  "executions": [
    {
      "id": 1,
      "incident_id": 1,
      "status": "completed",
      "started_at": "2024-11-14T10:30:05Z"
    }
  ]
}
```

#### Execute Playbook

**Endpoint:** `POST /api/v1/playbooks/{id}/execute`

**Request:**
```json
{
  "incident_id": 1,
  "parameters": {
    "auto_quarantine": true,
    "notify_channels": ["slack", "email"]
  }
}
```

**Response:**
```json
{
  "execution_id": 1,
  "status": "running",
  "started_at": "2024-11-14T10:30:05Z"
}
```

#### Get Execution Status

**Endpoint:** `GET /api/v1/playbooks/executions/{execution_id}`

**Response:**
```json
{
  "id": 1,
  "playbook_id": 1,
  "incident_id": 1,
  "status": "completed",
  "result": {
    "verdict": "malicious",
    "actions_taken": [
      "Quarantined 5 emails",
      "Blocked sender domain",
      "Created Jira ticket SOAR-123",
      "Notified security team via Slack"
    ],
    "indicators": {
      "malicious_urls": 2,
      "malicious_attachments": 1
    }
  },
  "started_at": "2024-11-14T10:30:05Z",
  "completed_at": "2024-11-14T10:32:00Z",
  "execution_time": 115
}
```

### Dashboard

#### Get Statistics

**Endpoint:** `GET /api/v1/dashboard/stats`

**Response:**
```json
{
  "total_incidents": 150,
  "open_incidents": 12,
  "resolved_incidents": 138,
  "critical_incidents": 3,
  "high_priority_incidents": 8,
  "total_executions": 420,
  "successful_executions": 398,
  "failed_executions": 22,
  "automation_rate": 85.5,
  "mttr": 3.2,
  "active_playbooks": 8
}
```

#### Get Metrics

**Endpoint:** `GET /api/v1/dashboard/metrics`

**Query Parameters:**
- `timeframe` (optional): 1h, 24h, 7d, 30d (default: 24h)

**Response:**
```json
{
  "timeframe": "24h",
  "incident_trends": [
    {"date": "2024-11-13", "count": 15},
    {"date": "2024-11-14", "count": 18}
  ],
  "severity_distribution": {
    "low": 5,
    "medium": 8,
    "high": 4,
    "critical": 1
  },
  "top_incident_types": [
    {"type": "phishing", "count": 10},
    {"type": "malware", "count": 5},
    {"type": "brute_force", "count": 3}
  ],
  "playbook_performance": [
    {
      "playbook": "Phishing Response",
      "executions": 50,
      "success_rate": 96.0,
      "avg_time": 120
    }
  ]
}
```

### API Integrations

#### Test Integration

**Endpoint:** `POST /api/v1/integrations/{integration_name}/test`

**Example:**
```bash
POST /api/v1/integrations/virustotal/test
```

**Response:**
```json
{
  "integration": "virustotal",
  "status": "success",
  "message": "Integration test successful",
  "response_time": 245
}
```

#### Check URL (VirusTotal)

**Endpoint:** `POST /api/v1/integrations/virustotal/check-url`

**Request:**
```json
{
  "url": "http://suspicious-site.com"
}
```

**Response:**
```json
{
  "url": "http://suspicious-site.com",
  "malicious": 15,
  "suspicious": 3,
  "clean": 65,
  "verdict": "malicious"
}
```

#### Check IP (AbuseIPDB)

**Endpoint:** `POST /api/v1/integrations/abuseipdb/check-ip`

**Request:**
```json
{
  "ip": "203.0.113.45"
}
```

**Response:**
```json
{
  "ip": "203.0.113.45",
  "abuseConfidenceScore": 85,
  "totalReports": 25,
  "verdict": "malicious"
}
```

### Health & Status

#### Health Check

**Endpoint:** `GET /health`

**Response:**
```json
{
  "status": "healthy",
  "timestamp": "2024-11-14T12:00:00Z",
  "services": {
    "database": "healthy",
    "redis": "healthy",
    "celery": "healthy"
  }
}
```

#### API Status

**Endpoint:** `GET /api/v1/status`

**Response:**
```json
{
  "version": "1.0.0",
  "uptime": 86400,
  "active_connections": 15
}
```

## Error Responses

### Error Format

All errors follow this format:

```json
{
  "error": "Error message",
  "code": "ERROR_CODE",
  "details": {}
}
```

### HTTP Status Codes

- `200 OK`: Success
- `201 Created`: Resource created successfully
- `400 Bad Request`: Invalid request parameters
- `401 Unauthorized`: Authentication required
- `403 Forbidden`: Insufficient permissions
- `404 Not Found`: Resource not found
- `409 Conflict`: Resource already exists
- `422 Unprocessable Entity`: Validation error
- `429 Too Many Requests`: Rate limit exceeded
- `500 Internal Server Error`: Server error

### Example Errors

**401 Unauthorized:**
```json
{
  "error": "Authentication required",
  "code": "UNAUTHORIZED"
}
```

**403 Forbidden:**
```json
{
  "error": "Insufficient permissions",
  "code": "FORBIDDEN",
  "details": {
    "required_role": "admin",
    "user_role": "analyst"
  }
}
```

**422 Validation Error:**
```json
{
  "error": "Validation failed",
  "code": "VALIDATION_ERROR",
  "details": {
    "severity": ["Must be one of: low, medium, high, critical"],
    "title": ["Field is required"]
  }
}
```

## Rate Limiting

API requests are rate limited:
- **Anonymous**: 100 requests/hour
- **Authenticated**: 1000 requests/hour
- **Admin**: 5000 requests/hour

Rate limit headers:
```
X-RateLimit-Limit: 1000
X-RateLimit-Remaining: 999
X-RateLimit-Reset: 1699977600
```

## Pagination

List endpoints support pagination:

```bash
GET /api/v1/incidents?limit=20&offset=40
```

**Response includes:**
```json
{
  "incidents": [...],
  "total": 150,
  "limit": 20,
  "offset": 40,
  "has_more": true
}
```

## Filtering

Use query parameters for filtering:

```bash
# Single filter
GET /api/v1/incidents?status=open

# Multiple filters
GET /api/v1/incidents?status=open&severity=high&incident_type=phishing

# Date range
GET /api/v1/incidents?created_after=2024-11-01&created_before=2024-11-14
```

## Sorting

Use the `sort` parameter:

```bash
# Ascending
GET /api/v1/incidents?sort=severity

# Descending (prefix with -)
GET /api/v1/incidents?sort=-created_at

# Multiple fields
GET /api/v1/incidents?sort=-severity,created_at
```

## Field Selection

Select specific fields to reduce payload:

```bash
GET /api/v1/incidents?fields=id,title,severity,status
```

## Webhooks

Subscribe to events:

**Endpoint:** `POST /api/v1/webhooks`

**Request:**
```json
{
  "url": "https://your-server.com/webhook",
  "events": ["incident.created", "incident.resolved", "playbook.completed"],
  "secret": "your_webhook_secret"
}
```

**Webhook Payload:**
```json
{
  "event": "incident.created",
  "timestamp": "2024-11-14T12:00:00Z",
  "data": {
    "incident_id": 1,
    "severity": "high",
    "title": "Suspicious activity detected"
  }
}
```

## SDK Examples

### Python

```python
import requests

class SOARClient:
    def __init__(self, base_url, username, password):
        self.base_url = base_url
        self.token = self._login(username, password)

    def _login(self, username, password):
        response = requests.post(
            f"{self.base_url}/auth/login",
            json={"username": username, "password": password}
        )
        return response.json()['token']

    def create_incident(self, data):
        return requests.post(
            f"{self.base_url}/incidents",
            json=data,
            headers={"Authorization": f"Bearer {self.token}"}
        ).json()

# Usage
client = SOARClient("http://localhost:5000/api/v1", "admin", "changeme")
incident = client.create_incident({
    "title": "Test incident",
    "severity": "medium"
})
```

### cURL

```bash
# Login
TOKEN=$(curl -X POST http://localhost:5000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username":"admin","password":"changeme"}' \
  | jq -r '.token')

# Create incident
curl -X POST http://localhost:5000/api/v1/incidents \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "title": "Test incident",
    "severity": "high",
    "incident_type": "phishing"
  }'
```

### JavaScript

```javascript
class SOARClient {
  constructor(baseURL, username, password) {
    this.baseURL = baseURL;
    this.token = null;
    this.login(username, password);
  }

  async login(username, password) {
    const response = await fetch(`${this.baseURL}/auth/login`, {
      method: 'POST',
      headers: {'Content-Type': 'application/json'},
      body: JSON.stringify({username, password})
    });
    const data = await response.json();
    this.token = data.token;
  }

  async createIncident(incidentData) {
    const response = await fetch(`${this.baseURL}/incidents`, {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${this.token}`,
        'Content-Type': 'application/json'
      },
      body: JSON.stringify(incidentData)
    });
    return await response.json();
  }
}

// Usage
const client = new SOARClient('http://localhost:5000/api/v1', 'admin', 'changeme');
```

## Versioning

The API uses URL versioning. Current version: `v1`

Breaking changes will increment the version number.

## Support

For API issues or questions:
- Check example scripts in `examples/`
- Review main documentation
- Create GitHub issue with `api` label
