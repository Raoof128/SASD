#!/usr/bin/env python3
"""
Example: Create and Process Security Incidents

This script demonstrates how to:
1. Create security incidents programmatically
2. Trigger automated playbook execution
3. Monitor incident status
"""

import requests
import json
import time
from typing import Dict, Any

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


def create_incident(token: str, incident_data: Dict[str, Any]) -> Dict[str, Any]:
    """Create a new security incident."""
    headers = {"Authorization": f"Bearer {token}"}
    response = requests.post(
        f"{BASE_URL}/incidents",
        json=incident_data,
        headers=headers
    )
    response.raise_for_status()
    return response.json()


def get_incident_status(token: str, incident_id: int) -> Dict[str, Any]:
    """Get incident status."""
    headers = {"Authorization": f"Bearer {token}"}
    response = requests.get(
        f"{BASE_URL}/incidents/{incident_id}",
        headers=headers
    )
    response.raise_for_status()
    return response.json()


def main():
    """Main execution."""
    print("=" * 60)
    print("SOAR Platform - Incident Creation Example")
    print("=" * 60)

    # Authenticate
    print("\n1. Authenticating...")
    token = get_auth_token()
    print("   ✓ Authentication successful")

    # Example 1: Phishing Email Incident
    print("\n2. Creating phishing incident...")
    phishing_incident = {
        "title": "Suspicious phishing email detected",
        "description": "User reported suspicious email with attachment",
        "severity": "high",
        "incident_type": "phishing",
        "source_ip": "192.168.1.100",
        "source_email": "attacker@malicious.com",
        "metadata": {
            "subject": "Urgent: Account Verification Required",
            "sender": "attacker@malicious.com",
            "recipient": "user@company.com",
            "urls": ["http://malicious-site.com/phishing"],
            "attachments": ["invoice.pdf.exe"]
        }
    }

    incident1 = create_incident(token, phishing_incident)
    print(f"   ✓ Incident created: ID={incident1['id']}, Status={incident1['status']}")

    # Example 2: Malware Detection Incident
    print("\n3. Creating malware detection incident...")
    malware_incident = {
        "title": "Malware detected on endpoint",
        "description": "Antivirus detected suspicious file",
        "severity": "critical",
        "incident_type": "malware",
        "source_ip": "192.168.1.50",
        "affected_systems": ["DESKTOP-001"],
        "metadata": {
            "file_hash": "d41d8cd98f00b204e9800998ecf8427e",
            "file_name": "malware.exe",
            "file_path": "C:\\Users\\John\\Downloads\\malware.exe",
            "detection_time": "2024-11-14T10:30:00Z"
        }
    }

    incident2 = create_incident(token, malware_incident)
    print(f"   ✓ Incident created: ID={incident2['id']}, Status={incident2['status']}")

    # Example 3: Brute Force Attack
    print("\n4. Creating brute force incident...")
    bruteforce_incident = {
        "title": "Multiple failed login attempts detected",
        "description": "50+ failed login attempts from same IP",
        "severity": "high",
        "incident_type": "brute_force",
        "source_ip": "203.0.113.45",
        "metadata": {
            "target_user": "admin",
            "failed_attempts": 53,
            "time_window": "5 minutes",
            "attack_vector": "SSH"
        }
    }

    incident3 = create_incident(token, bruteforce_incident)
    print(f"   ✓ Incident created: ID={incident3['id']}, Status={incident3['status']}")

    # Monitor first incident
    print(f"\n5. Monitoring incident {incident1['id']} processing...")
    for i in range(5):
        time.sleep(2)
        status = get_incident_status(token, incident1['id'])
        print(f"   Status: {status['status']} (checked {i+1}/5)")

        if status['status'] in ['resolved', 'closed']:
            print(f"   ✓ Incident resolved!")
            break

    print("\n" + "=" * 60)
    print("Example completed successfully!")
    print("=" * 60)
    print("\nCreated Incidents:")
    print(f"  - Phishing: ID={incident1['id']}")
    print(f"  - Malware: ID={incident2['id']}")
    print(f"  - Brute Force: ID={incident3['id']}")
    print("\nView incidents at: http://localhost:5000/dashboard")


if __name__ == "__main__":
    try:
        main()
    except requests.exceptions.RequestException as e:
        print(f"\n❌ Error: {e}")
        print("\nMake sure the SOAR platform is running:")
        print("  docker-compose up -d")
        print("  OR")
        print("  make run")
        exit(1)
