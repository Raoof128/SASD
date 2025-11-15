#!/usr/bin/env python3
"""
Example: Retrieve Dashboard Metrics

This script demonstrates how to:
1. Fetch dashboard statistics
2. Get recent incidents
3. Retrieve playbook execution metrics
4. Generate reports
"""

import requests
import json
from typing import Dict, Any
from datetime import datetime, timedelta

# Configuration
BASE_URL = "http://localhost:5000/api/v1"
USERNAME = "admin"
PASSWORD = "changeme"


def get_auth_token() -> str:
    """Authenticate and get JWT token."""
    response = requests.post(
        f"{BASE_URL}/auth/login",
        json={"username": USERNAME, "password": PASSWORD}
    )
    response.raise_for_status()
    return response.json()['token']


def get_dashboard_stats(token: str) -> Dict[str, Any]:
    """Get dashboard statistics."""
    headers = {"Authorization": f"Bearer {token}"}
    response = requests.get(f"{BASE_URL}/dashboard/stats", headers=headers)
    response.raise_for_status()
    return response.json()


def get_recent_incidents(token: str, limit: int = 10) -> list:
    """Get recent incidents."""
    headers = {"Authorization": f"Bearer {token}"}
    response = requests.get(
        f"{BASE_URL}/incidents?limit={limit}&sort=-created_at",
        headers=headers
    )
    response.raise_for_status()
    return response.json().get('incidents', [])


def get_metrics(token: str, timeframe: str = "24h") -> Dict[str, Any]:
    """Get platform metrics."""
    headers = {"Authorization": f"Bearer {token}"}
    response = requests.get(
        f"{BASE_URL}/dashboard/metrics?timeframe={timeframe}",
        headers=headers
    )
    response.raise_for_status()
    return response.json()


def print_stats_table(stats: Dict[str, Any]):
    """Print statistics in a formatted table."""
    print("\n" + "=" * 60)
    print("Dashboard Statistics")
    print("=" * 60)
    print(f"Total Incidents:        {stats.get('total_incidents', 0)}")
    print(f"Open Incidents:         {stats.get('open_incidents', 0)}")
    print(f"Resolved Incidents:     {stats.get('resolved_incidents', 0)}")
    print(f"Critical Incidents:     {stats.get('critical_incidents', 0)}")
    print(f"High Priority:          {stats.get('high_priority_incidents', 0)}")
    print(f"Playbook Executions:    {stats.get('total_executions', 0)}")
    print(f"Successful Executions:  {stats.get('successful_executions', 0)}")
    print(f"Failed Executions:      {stats.get('failed_executions', 0)}")

    if stats.get('automation_rate'):
        print(f"Automation Rate:        {stats['automation_rate']:.1f}%")
    if stats.get('mttr'):
        print(f"Mean Time to Resolve:   {stats['mttr']:.1f} minutes")


def print_recent_incidents(incidents: list):
    """Print recent incidents."""
    print("\n" + "=" * 60)
    print("Recent Incidents")
    print("=" * 60)

    if not incidents:
        print("No incidents found")
        return

    for inc in incidents[:5]:
        print(f"\n[{inc.get('id')}] {inc.get('title')}")
        print(f"    Severity: {inc.get('severity', 'N/A').upper()}")
        print(f"    Status: {inc.get('status', 'N/A')}")
        print(f"    Created: {inc.get('created_at', 'N/A')}")
        if inc.get('source_ip'):
            print(f"    Source IP: {inc.get('source_ip')}")


def print_metrics(metrics: Dict[str, Any]):
    """Print platform metrics."""
    print("\n" + "=" * 60)
    print("Platform Metrics")
    print("=" * 60)

    if 'incident_trends' in metrics:
        print("\nIncident Trends:")
        for trend in metrics['incident_trends']:
            print(f"  {trend['date']}: {trend['count']} incidents")

    if 'severity_distribution' in metrics:
        print("\nSeverity Distribution:")
        for severity, count in metrics['severity_distribution'].items():
            print(f"  {severity.capitalize()}: {count}")

    if 'top_incident_types' in metrics:
        print("\nTop Incident Types:")
        for incident_type in metrics['top_incident_types']:
            print(f"  {incident_type['type']}: {incident_type['count']}")


def main():
    """Main execution."""
    print("=" * 60)
    print("SOAR Platform - Dashboard Metrics Example")
    print("=" * 60)

    # Authenticate
    print("\n1. Authenticating...")
    token = get_auth_token()
    print("   ✓ Authentication successful")

    # Get statistics
    print("\n2. Fetching dashboard statistics...")
    stats = get_dashboard_stats(token)
    print_stats_table(stats)

    # Get recent incidents
    print("\n3. Fetching recent incidents...")
    incidents = get_recent_incidents(token, limit=10)
    print_recent_incidents(incidents)

    # Get metrics
    print("\n4. Fetching platform metrics...")
    metrics = get_metrics(token, timeframe="7d")
    print_metrics(metrics)

    # Summary
    print("\n" + "=" * 60)
    print("Metrics Retrieved Successfully!")
    print("=" * 60)
    print(f"\nTotal Incidents: {stats.get('total_incidents', 0)}")
    print(f"Automation Rate: {stats.get('automation_rate', 0):.1f}%")
    print(f"\nView full dashboard at: http://localhost:5000/dashboard")


if __name__ == "__main__":
    try:
        main()
    except requests.exceptions.RequestException as e:
        print(f"\n❌ Error: {e}")
        print("\nMake sure the SOAR platform is running:")
        print("  docker-compose up -d")
        exit(1)
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        exit(1)
