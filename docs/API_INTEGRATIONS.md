# API Integrations Guide

## Overview

The SOAR platform integrates with 12+ external security tools and services. All integrations are designed to be:

- **Asynchronous**: Non-blocking I/O using `aiohttp`
- **Resilient**: Error handling and graceful degradation
- **Testable**: Mock-friendly for unit testing
- **Configurable**: API keys via environment variables

## Available Integrations

### 1. VirusTotal (Threat Intelligence)

**File**: `backend/integrations/virustotal.py`

**Purpose**: URL, IP, file hash reputation checking

**Configuration**:
```bash
VIRUSTOTAL_API_KEY=your_api_key_here
```

**Usage**:
```python
from backend.integrations.virustotal import VirusTotalClient

vt = VirusTotalClient()

# Check URL
result = await vt.check_url("https://suspicious-domain.com")
# Returns: {'verdict': 'malicious', 'malicious': 5, 'suspicious': 2, ...}

# Check IP
result = await vt.check_ip("1.2.3.4")
# Returns: {'verdict': 'clean', 'reputation': 10, ...}

# Check file hash
result = await vt.check_file_hash("abc123...")
# Returns: {'verdict': 'malicious', 'detection_rate': '45/70', ...}
```

**Rate Limits**: 4 requests/minute (free tier)

---

### 2. AbuseIPDB (IP Reputation)

**File**: `backend/integrations/abuseipdb.py`

**Purpose**: IP abuse reporting and reputation checking

**Configuration**:
```bash
ABUSEIPDB_API_KEY=your_api_key_here
```

**Usage**:
```python
from backend.integrations.abuseipdb import AbuseIPDBClient

abuseipdb = AbuseIPDBClient()

# Check IP
result = await abuseipdb.check_ip("1.2.3.4")
# Returns: {
#     'is_malicious': True,
#     'abuse_confidence_score': 85,
#     'total_reports': 42,
#     'country_code': 'CN',
#     ...
# }

# Report malicious IP
result = await abuseipdb.report_ip(
    ip="1.2.3.4",
    categories=[18, 22],  # Brute force, SSH attack
    comment="Brute force attack on SSH"
)
```

**Rate Limits**: 1000 requests/day (free tier)

---

### 3. Slack (Notifications)

**File**: `backend/integrations/slack.py`

**Purpose**: Real-time alerting and notifications

**Configuration**:
```bash
SLACK_BOT_TOKEN=xoxb-your-bot-token
SLACK_WEBHOOK_URL=https://hooks.slack.com/services/...
SLACK_CHANNEL_SECURITY=#security
SLACK_CHANNEL_INCIDENTS=#incidents
```

**Usage**:
```python
from backend.integrations.slack import SlackClient

slack = SlackClient()

# Simple message
await slack.post_message(
    text="Alert: Phishing email detected",
    channel="#security"
)

# Incident alert with formatting
await slack.post_incident_alert(
    incident_title="Phishing from attacker@evil.com",
    incident_id=123,
    severity="high",
    incident_type="phishing"
)

# Playbook result
await slack.post_playbook_result(
    playbook_name="Phishing Response",
    incident_id=123,
    status="completed",
    actions_count=5,
    execution_time=12.5
)
```

**Rate Limits**: 1 message/second per channel

---

### 4. Jira (Ticketing)

**File**: `backend/integrations/jira.py`

**Purpose**: Incident tracking and case management

**Configuration**:
```bash
JIRA_URL=https://your-company.atlassian.net
JIRA_EMAIL=your-email@company.com
JIRA_API_TOKEN=your_api_token
JIRA_PROJECT_KEY=SEC
```

**Usage**:
```python
from backend.integrations.jira import JiraClient

jira = JiraClient()

# Create ticket
ticket = await jira.create_ticket(
    title="Phishing Investigation",
    description="Detailed investigation notes...",
    priority="High",
    issue_type="Task"
)
# Returns: {'success': True, 'key': 'SEC-123', 'url': '...'}

# Update ticket
await jira.update_ticket(
    ticket_key="SEC-123",
    fields={'description': 'Updated description'}
)

# Add comment
await jira.add_comment(
    ticket_key="SEC-123",
    comment="Investigation completed. Malicious confirmed."
)

# Transition status
await jira.transition_ticket(
    ticket_key="SEC-123",
    transition_name="In Progress"
)
```

**Rate Limits**: 10 requests/second

---

### 5. Email/SMTP (Notifications)

**File**: `backend/integrations/email_client.py`

**Purpose**: Email notifications for incidents

**Configuration**:
```bash
SMTP_SERVER=smtp.gmail.com
SMTP_PORT=587
SMTP_USERNAME=your-email@company.com
SMTP_PASSWORD=your-app-password
SMTP_FROM=soar@company.com
SMTP_USE_TLS=True
```

**Usage**:
```python
from backend.integrations.email_client import EmailClient

email = EmailClient()

# Send email
await email.send_email(
    to_addresses=["analyst@company.com"],
    subject="Security Alert",
    body="Incident details...",
    html=False
)

# Send incident notification
await email.send_incident_notification(
    to_addresses=["team@company.com"],
    incident_title="Malware Detected",
    incident_id=123,
    severity="critical",
    description="Ransomware detected on server"
)
```

---

## Adding New Integrations

### Step 1: Create Integration Class

Create a new file in `backend/integrations/`:

```python
# backend/integrations/new_service.py
import aiohttp
import logging
from typing import Dict, Any
from flask import current_app

logger = logging.getLogger(__name__)

class NewServiceClient:
    """New Service API client"""

    BASE_URL = "https://api.newservice.com"

    def __init__(self, api_key: str = None):
        self.api_key = api_key or current_app.config.get('NEW_SERVICE_API_KEY')
        self.headers = {'Authorization': f'Bearer {self.api_key}'}

    async def some_action(self, param: str) -> Dict[str, Any]:
        """Perform some action"""
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    f"{self.BASE_URL}/endpoint",
                    headers=self.headers,
                    params={'param': param}
                ) as response:
                    if response.status == 200:
                        return await response.json()
                    else:
                        return {'error': f'HTTP {response.status}'}
        except Exception as e:
            logger.error(f"New service API call failed: {e}")
            return {'error': str(e)}
```

### Step 2: Add Configuration

Update `.env.example` and `backend/config.py`:

```python
# backend/config.py
NEW_SERVICE_API_KEY = os.getenv('NEW_SERVICE_API_KEY', '')
```

### Step 3: Use in Playbooks

```python
# backend/playbooks/your_playbook.py
from backend.integrations.new_service import NewServiceClient

async def execute(self, incident, **kwargs):
    service = NewServiceClient()
    result = await service.some_action(incident.source_ip)
```

### Step 4: Write Tests

```python
# tests/test_integrations.py
import pytest
from unittest.mock import AsyncMock, patch

@pytest.mark.asyncio
async def test_new_service_client():
    with patch('aiohttp.ClientSession.get') as mock_get:
        mock_response = AsyncMock()
        mock_response.status = 200
        mock_response.json = AsyncMock(return_value={'success': True})
        mock_get.return_value.__aenter__.return_value = mock_response

        client = NewServiceClient(api_key='test_key')
        result = await client.some_action('test')

        assert result['success'] == True
```

## Best Practices

### 1. Error Handling

Always wrap API calls in try/except:

```python
try:
    result = await api.call()
    if result.get('error'):
        # Handle API-level error
        pass
except Exception as e:
    # Handle network/connection error
    logger.error(f"API call failed: {e}")
```

### 2. Timeouts

Set reasonable timeouts:

```python
async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=30)) as session:
    # API call
```

### 3. Retries

Implement exponential backoff for transient failures:

```python
for attempt in range(3):
    try:
        result = await api.call()
        break
    except Exception as e:
        if attempt < 2:
            await asyncio.sleep(2 ** attempt)
        else:
            raise
```

### 4. Rate Limiting

Respect API rate limits:

```python
import asyncio

class RateLimitedClient:
    def __init__(self):
        self.last_call = 0
        self.min_interval = 1.0  # 1 second

    async def call_api(self):
        now = asyncio.get_event_loop().time()
        wait_time = self.min_interval - (now - self.last_call)
        if wait_time > 0:
            await asyncio.sleep(wait_time)

        # Make API call
        self.last_call = asyncio.get_event_loop().time()
```

### 5. Mocking for Tests

Make integrations easy to mock:

```python
# In tests
@patch('backend.integrations.virustotal.VirusTotalClient.check_url')
async def test_playbook(mock_check):
    mock_check.return_value = {'verdict': 'malicious'}
    # Test playbook
```

## Integration Health Monitoring

Query integration health:

```bash
GET /api/v1/dashboard/health
```

Returns:
```json
{
    "status": "healthy",
    "components": {
        "database": "healthy",
        "virustotal": "healthy",
        "slack": "degraded",
        "jira": "healthy"
    }
}
```

## Troubleshooting

### API Key Not Working

1. Verify key is in `.env` file
2. Check key has correct permissions
3. Verify key format (some require "Bearer", others don't)

### Timeout Errors

1. Check network connectivity
2. Increase timeout value
3. Verify API endpoint is correct

### Rate Limit Errors

1. Implement request throttling
2. Upgrade to paid tier if needed
3. Cache responses where possible

## Supported Integrations Roadmap

**Implemented**:
- ✅ VirusTotal
- ✅ AbuseIPDB
- ✅ Slack
- ✅ Jira
- ✅ Email (SMTP)

**Planned**:
- ⏳ Active Directory (LDAP)
- ⏳ Firewall APIs
- ⏳ EDR (Wazuh, CrowdStrike)
- ⏳ SIEM (Splunk, ELK)
- ⏳ MISP
- ⏳ AlienVault OTX
- ⏳ Microsoft Graph API
- ⏳ ServiceNow
