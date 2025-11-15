# SOAR Platform Monitoring

This directory contains monitoring configurations for the SOAR platform using Prometheus and Grafana.

## Overview

The monitoring stack includes:
- **Prometheus**: Metrics collection and alerting
- **Grafana**: Metrics visualization and dashboards
- **Alertmanager**: Alert routing and notification
- **Node Exporter**: System-level metrics

## Quick Start

### Using Docker Compose

1. **Start monitoring stack:**
   ```bash
   docker-compose -f docker-compose.monitoring.yml up -d
   ```

2. **Access dashboards:**
   - Grafana: http://localhost:3000 (admin/admin)
   - Prometheus: http://localhost:9090
   - Alertmanager: http://localhost:9093

### Manual Setup

1. **Install Prometheus:**
   ```bash
   # Download and extract
   wget https://github.com/prometheus/prometheus/releases/download/v2.45.0/prometheus-2.45.0.linux-amd64.tar.gz
   tar xvfz prometheus-2.45.0.linux-amd64.tar.gz
   cd prometheus-2.45.0.linux-amd64

   # Copy configuration
   cp monitoring/prometheus/prometheus.yml .
   cp monitoring/prometheus/alerts.yml .

   # Start Prometheus
   ./prometheus --config.file=prometheus.yml
   ```

2. **Install Grafana:**
   ```bash
   # Ubuntu/Debian
   sudo apt-get install -y grafana

   # Start Grafana
   sudo systemctl start grafana-server
   sudo systemctl enable grafana-server
   ```

## Configuration

### Prometheus

#### Main Configuration (`prometheus/prometheus.yml`)

Defines scrape targets and intervals:
- **SOAR API**: Metrics endpoint on port 5000
- **PostgreSQL**: Database metrics
- **Redis**: Cache metrics
- **Celery**: Worker metrics
- **Node Exporter**: System metrics

#### Alert Rules (`prometheus/alerts.yml`)

Defines alerting rules:

**SOAR Platform Alerts:**
- High number of open incidents (>50)
- Critical incidents stalled (>5)
- Low automation rate (<70%)
- High MTTR (>10 minutes)
- Playbook execution failures

**Infrastructure Alerts:**
- API endpoint down
- Database connection issues
- Redis cache unavailable
- Celery workers not responding
- High CPU/memory usage
- Low disk space

**Performance Alerts:**
- High API response time (>2s p95)
- High error rate (>5%)

### Grafana

#### Datasources (`grafana/provisioning/datasources.yml`)

Pre-configured datasources:
- **Prometheus**: Default datasource for metrics
- **PostgreSQL**: Direct database queries

#### Dashboards

**SOAR Overview Dashboard** (`grafana/dashboards/soar-overview.json`):
- Total incidents counter
- Open incidents gauge
- Automation rate gauge
- MTTR display
- Incidents by severity pie chart
- Incidents by status pie chart
- Incident creation rate graph
- Playbook execution success rate
- API response time (p95)
- System health table

## Metrics

### Application Metrics

The SOAR platform exposes the following metrics at `/metrics`:

#### Incident Metrics
```
# Total incidents created
soar_incidents_total

# Open incidents
soar_incidents_open

# Incidents by severity
soar_incidents_by_severity{severity="critical|high|medium|low"}

# Incidents by status
soar_incidents_by_status{status="new|investigating|contained|resolved|closed"}

# Critical open incidents
soar_incidents_critical_open
```

#### Playbook Metrics
```
# Total playbook executions
soar_playbook_executions_total

# Successful playbook executions
soar_playbook_executions_success_total

# Failed playbook executions
soar_playbook_executions_failed_total

# Playbook execution duration
soar_playbook_execution_duration_seconds
```

#### Performance Metrics
```
# Automation rate percentage
soar_automation_rate

# Mean time to resolve (minutes)
soar_mttr_minutes

# API request duration
http_request_duration_seconds

# HTTP requests total
http_requests_total{method="GET|POST|PUT|DELETE", status="200|400|500"}
```

### System Metrics

Collected by Node Exporter:

```
# CPU usage
node_cpu_seconds_total

# Memory usage
node_memory_MemTotal_bytes
node_memory_MemAvailable_bytes

# Disk usage
node_filesystem_avail_bytes
node_filesystem_size_bytes

# Network traffic
node_network_receive_bytes_total
node_network_transmit_bytes_total
```

## Alerting

### Alert Routing

Configure Alertmanager for alert routing (`alertmanager.yml`):

```yaml
route:
  receiver: 'slack'
  group_by: ['alertname', 'severity']
  group_wait: 30s
  group_interval: 5m
  repeat_interval: 4h

receivers:
  - name: 'slack'
    slack_configs:
      - api_url: 'YOUR_SLACK_WEBHOOK_URL'
        channel: '#security-alerts'
        title: 'SOAR Platform Alert'
```

### Alert Notification Channels

Supported channels:
- **Slack**: Webhook integration
- **Email**: SMTP configuration
- **PagerDuty**: Incident management
- **Webhook**: Custom HTTP endpoints

### Alert Severity Levels

- **Critical**: Immediate action required (page on-call)
- **Warning**: Investigate soon (notify team)
- **Info**: Informational only

## Queries

### Useful Prometheus Queries

#### Incident Analysis
```promql
# Incident creation rate (last 1 hour)
rate(soar_incidents_total[1h])

# Percentage of critical incidents
(soar_incidents_by_severity{severity="critical"} / soar_incidents_total) * 100

# Average MTTR over time
avg_over_time(soar_mttr_minutes[24h])
```

#### Performance Analysis
```promql
# API latency p95, p99
histogram_quantile(0.95, rate(http_request_duration_seconds_bucket[5m]))
histogram_quantile(0.99, rate(http_request_duration_seconds_bucket[5m]))

# Error rate
rate(http_requests_total{status=~"5.."}[5m]) / rate(http_requests_total[5m])

# Requests per second
rate(http_requests_total[1m])
```

#### Playbook Analysis
```promql
# Playbook success rate
rate(soar_playbook_executions_success_total[5m]) / rate(soar_playbook_executions_total[5m]) * 100

# Average playbook execution time
avg(soar_playbook_execution_duration_seconds)
```

## Dashboards

### Creating Custom Dashboards

1. **Access Grafana**: http://localhost:3000
2. **Click** "+ Create" → "Dashboard"
3. **Add panels** with desired visualizations
4. **Configure queries** using Prometheus datasource
5. **Save** dashboard

### Exporting Dashboards

```bash
# Export dashboard JSON
curl -u admin:admin http://localhost:3000/api/dashboards/uid/DASHBOARD_UID
```

### Importing Dashboards

1. **Navigate** to Dashboards → Import
2. **Upload** JSON file or paste JSON
3. **Select** Prometheus datasource
4. **Click** Import

## Best Practices

### Retention

Configure Prometheus retention:
```yaml
# prometheus.yml
storage:
  tsdb:
    retention.time: 15d
    retention.size: 50GB
```

### Scrape Intervals

- **Critical metrics**: 10-15s
- **Standard metrics**: 30s
- **Infrastructure metrics**: 30-60s

### Alert Tuning

- Use `for` clause to avoid flapping alerts
- Set appropriate thresholds based on baseline
- Group related alerts
- Avoid alert fatigue with proper severity levels

### Performance

- Use recording rules for expensive queries
- Limit cardinality of labels
- Use federation for multi-cluster setups
- Archive old data to long-term storage

## Troubleshooting

### Prometheus Not Scraping

Check targets status:
```bash
# View targets
http://localhost:9090/targets

# Check Prometheus logs
docker logs prometheus
```

### Grafana Not Showing Data

1. **Verify datasource**: Configuration → Data Sources
2. **Test connection**: Click "Test" button
3. **Check queries**: Use Prometheus UI to verify queries
4. **Review time range**: Ensure data exists for selected range

### High Memory Usage

Reduce retention or cardinality:
```yaml
# Reduce retention
--storage.tsdb.retention.time=7d

# Limit series
--storage.tsdb.max-series=1000000
```

## Security

### Authentication

Configure Grafana authentication:
```ini
# grafana.ini
[auth]
disable_login_form = false

[auth.basic]
enabled = true

[auth.anonymous]
enabled = false
```

### TLS/SSL

Enable HTTPS for Grafana:
```ini
[server]
protocol = https
cert_file = /path/to/cert.pem
cert_key = /path/to/key.pem
```

### Network Security

- Use firewall rules to restrict access
- Enable authentication on Prometheus
- Use reverse proxy for additional security

## Integration

### CI/CD Integration

Monitor deployment metrics:
```promql
# Track deployments
increase(soar_deployments_total[1h])

# Post-deployment error rate
rate(http_requests_total{status=~"5.."}[5m] offset 10m)
```

### SIEM Integration

Export metrics to SIEM:
- Use Prometheus remote write
- Configure webhook receivers
- Stream to Elasticsearch

## Resources

- [Prometheus Documentation](https://prometheus.io/docs/)
- [Grafana Documentation](https://grafana.com/docs/)
- [PromQL Guide](https://prometheus.io/docs/prometheus/latest/querying/basics/)
- [Grafana Dashboards](https://grafana.com/grafana/dashboards/)

## Support

For monitoring issues:
- Check Prometheus/Grafana logs
- Review configuration files
- Consult main project documentation
- Create GitHub issue with `monitoring` label
