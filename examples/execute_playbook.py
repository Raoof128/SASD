#!/usr/bin/env python3
"""
Example: Execute Security Playbooks

This script demonstrates how to:
1. List available playbooks
2. Execute playbooks manually
3. Monitor playbook execution
4. View execution results
"""

import requests
import json
import time
from typing import Dict, Any, List

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


def list_playbooks(token: str) -> List[Dict[str, Any]]:
    """List all available playbooks."""
    headers = {"Authorization": f"Bearer {token}"}
    response = requests.get(f"{BASE_URL}/playbooks", headers=headers)
    response.raise_for_status()
    return response.json()


def execute_playbook(token: str, playbook_id: int, incident_id: int) -> Dict[str, Any]:
    """Execute a playbook for an incident."""
    headers = {"Authorization": f"Bearer {token}"}
    response = requests.post(
        f"{BASE_URL}/playbooks/{playbook_id}/execute",
        json={"incident_id": incident_id},
        headers=headers
    )
    response.raise_for_status()
    return response.json()


def get_execution_status(token: str, execution_id: int) -> Dict[str, Any]:
    """Get playbook execution status."""
    headers = {"Authorization": f"Bearer {token}"}
    response = requests.get(
        f"{BASE_URL}/playbooks/executions/{execution_id}",
        headers=headers
    )
    response.raise_for_status()
    return response.json()


def create_test_incident(token: str) -> Dict[str, Any]:
    """Create a test incident for playbook execution."""
    headers = {"Authorization": f"Bearer {token}"}
    incident_data = {
        "title": "Test incident for playbook execution",
        "description": "Automated test incident",
        "severity": "medium",
        "incident_type": "phishing",
        "source_email": "test@example.com",
        "metadata": {
            "urls": ["http://example.com/test"],
            "sender": "test@example.com"
        }
    }
    response = requests.post(
        f"{BASE_URL}/incidents",
        json=incident_data,
        headers=headers
    )
    response.raise_for_status()
    return response.json()


def main():
    """Main execution."""
    print("=" * 60)
    print("SOAR Platform - Playbook Execution Example")
    print("=" * 60)

    # Authenticate
    print("\n1. Authenticating...")
    token = get_auth_token()
    print("   ✓ Authentication successful")

    # List available playbooks
    print("\n2. Available playbooks:")
    playbooks = list_playbooks(token)
    for pb in playbooks:
        print(f"   [{pb['id']}] {pb['name']}")
        print(f"       Description: {pb.get('description', 'N/A')}")
        print(f"       Enabled: {pb.get('enabled', True)}")
        print()

    # Create test incident
    print("3. Creating test incident...")
    incident = create_test_incident(token)
    print(f"   ✓ Incident created: ID={incident['id']}")

    # Execute first playbook
    if playbooks:
        playbook = playbooks[0]
        print(f"\n4. Executing playbook: {playbook['name']}")
        execution = execute_playbook(token, playbook['id'], incident['id'])
        print(f"   ✓ Execution started: ID={execution.get('execution_id', 'N/A')}")

        # Monitor execution
        if 'execution_id' in execution:
            print(f"\n5. Monitoring execution...")
            for i in range(10):
                time.sleep(2)
                status = get_execution_status(token, execution['execution_id'])
                print(f"   Status: {status.get('status', 'unknown')} (check {i+1}/10)")

                if status.get('status') in ['completed', 'failed']:
                    print(f"\n   Execution finished!")
                    print(f"   Result: {json.dumps(status.get('result', {}), indent=2)}")
                    break
    else:
        print("\n   ℹ No playbooks available")

    print("\n" + "=" * 60)
    print("Example completed successfully!")
    print("=" * 60)


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
        exit(1)
