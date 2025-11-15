# SOAR Platform - Example Scripts

This directory contains example scripts demonstrating how to use the SOAR platform programmatically.

## Prerequisites

1. **SOAR Platform Running**
   ```bash
   # Using Docker
   docker-compose up -d

   # OR using Make
   make docker-up
   ```

2. **Python Dependencies**
   ```bash
   pip install requests
   ```

3. **API Credentials**
   - Default username: `admin`
   - Default password: `changeme`
   - Update credentials in scripts if changed

## Available Examples

### 1. Create Incidents (`create_incident.py`)

Demonstrates how to create security incidents programmatically.

**Usage:**
```bash
python examples/create_incident.py
```

**Features:**
- Authentication with JWT tokens
- Creating different incident types (phishing, malware, brute force)
- Monitoring incident status
- Automatic playbook triggering

**Example Output:**
```
Creating phishing incident...
✓ Incident created: ID=1, Status=new
Creating malware detection incident...
✓ Incident created: ID=2, Status=investigating
```

### 2. Execute Playbooks (`execute_playbook.py`)

Shows how to execute security playbooks manually.

**Usage:**
```bash
python examples/execute_playbook.py
```

**Features:**
- List available playbooks
- Execute playbooks for specific incidents
- Monitor playbook execution status
- View execution results

**Example Output:**
```
Available playbooks:
[1] Phishing Response
    Description: Automated phishing investigation and response
    Enabled: True

Executing playbook: Phishing Response
✓ Execution started: ID=123
Status: running
Status: completed
```

### 3. Test API Integrations (`api_integrations.py`)

Tests external API integrations (VirusTotal, AbuseIPDB, Slack).

**Usage:**
```bash
python examples/api_integrations.py
```

**Features:**
- Test VirusTotal URL and file hash scanning
- Test AbuseIPDB IP reputation checks
- Test Slack notifications
- Verify API key configuration

**Requirements:**
- API keys configured in `.env` file
- See `.env.example` for required variables

**Example Output:**
```
Testing VirusTotal Integration
✓ URL scan successful
Malicious: 0
Suspicious: 0

Testing Slack Integration
✓ Slack notification sent

Configuration Status:
VirusTotal: ✓ Configured
AbuseIPDB: ✓ Configured
Slack: ✓ Configured
```

### 4. Dashboard Metrics (`dashboard_metrics.py`)

Retrieves and displays dashboard statistics and metrics.

**Usage:**
```bash
python examples/dashboard_metrics.py
```

**Features:**
- Fetch dashboard statistics
- Get recent incidents
- View platform metrics
- Generate reports

**Example Output:**
```
Dashboard Statistics
Total Incidents:        25
Open Incidents:         5
Resolved Incidents:     20
Automation Rate:        85.0%
Mean Time to Resolve:   3.2 minutes

Recent Incidents:
[1] Suspicious phishing email detected
    Severity: HIGH
    Status: resolved
    Created: 2024-11-14T10:30:00Z
```

## Configuration

### API Base URL

By default, examples connect to `http://localhost:5000/api/v1`

To change:
```python
BASE_URL = "http://your-server:5000/api/v1"
```

### Authentication

Update credentials in each script:
```python
USERNAME = "your-username"
PASSWORD = "your-password"
```

### API Keys (for `api_integrations.py`)

Configure in `.env` file:
```bash
VIRUSTOTAL_API_KEY=your_key_here
ABUSEIPDB_API_KEY=your_key_here
SLACK_WEBHOOK_URL=your_webhook_url_here
```

## Error Handling

All examples include error handling:

```python
try:
    main()
except requests.exceptions.RequestException as e:
    print(f"❌ Error: {e}")
    print("Make sure the SOAR platform is running")
    exit(1)
```

## Common Issues

### Connection Refused
```
❌ Error: Connection refused
```

**Solution:** Ensure SOAR platform is running:
```bash
docker-compose up -d
# OR
make run
```

### Authentication Failed
```
❌ Error: 401 Unauthorized
```

**Solution:** Check credentials:
1. Verify username/password in script
2. Ensure user exists in database
3. Check default credentials: `admin/changeme`

### API Key Not Configured
```
❌ VirusTotal API key not configured
```

**Solution:** Add API keys to `.env`:
```bash
cp .env.example .env
# Edit .env and add your API keys
```

## Advanced Usage

### Custom Incident Data

Modify incident creation:
```python
custom_incident = {
    "title": "Custom security event",
    "description": "Detailed description",
    "severity": "critical",  # low, medium, high, critical
    "incident_type": "custom_type",
    "source_ip": "192.168.1.100",
    "metadata": {
        "custom_field": "custom_value",
        "indicators": ["IOC1", "IOC2"]
    }
}

incident = create_incident(token, custom_incident)
```

### Filtering Incidents

Get incidents by criteria:
```python
# Get high severity incidents
response = requests.get(
    f"{BASE_URL}/incidents?severity=high&status=open",
    headers={"Authorization": f"Bearer {token}"}
)
```

### Bulk Operations

Create multiple incidents:
```python
incidents_data = [
    {...},  # Incident 1
    {...},  # Incident 2
    {...},  # Incident 3
]

for data in incidents_data:
    incident = create_incident(token, data)
    print(f"Created: {incident['id']}")
```

## Integration with CI/CD

Use examples in automated workflows:

```yaml
# .github/workflows/test-integration.yml
- name: Test SOAR Integration
  run: |
    docker-compose up -d
    sleep 10  # Wait for services
    python examples/create_incident.py
    python examples/dashboard_metrics.py
```

## Contributing

To add new examples:

1. Create a new Python file in `examples/`
2. Follow the existing code structure
3. Include error handling
4. Add documentation to this README
5. Submit a pull request

## Support

For questions or issues:
- Check existing GitHub issues
- Review main documentation in `docs/`
- Create a new issue with the `question` label

## License

These examples are part of the SOAR Platform and are licensed under the MIT License.
