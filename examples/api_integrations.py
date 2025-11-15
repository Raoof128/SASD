#!/usr/bin/env python3
"""
Example: Test API Integrations

This script demonstrates how to:
1. Test VirusTotal integration
2. Test AbuseIPDB integration
3. Test notification integrations (Slack, Email)
4. Verify API key configuration
"""

import asyncio
import os
import sys
from typing import Dict, Any

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backend.integrations.virustotal import VirusTotalClient
from backend.integrations.abuseipdb import AbuseIPDBClient
from backend.integrations.slack import SlackClient
from backend.config import get_config


async def test_virustotal():
    """Test VirusTotal integration."""
    print("\n" + "=" * 60)
    print("Testing VirusTotal Integration")
    print("=" * 60)

    config = get_config()

    if not config.VIRUSTOTAL_API_KEY:
        print("❌ VirusTotal API key not configured")
        print("   Set VIRUSTOTAL_API_KEY in .env file")
        return

    vt = VirusTotalClient(config.VIRUSTOTAL_API_KEY)

    # Test URL scanning
    print("\n1. Testing URL scan...")
    test_url = "http://example.com"
    try:
        result = await vt.check_url(test_url)
        print(f"   ✓ URL scan successful")
        print(f"   Malicious: {result.get('malicious', 0)}")
        print(f"   Suspicious: {result.get('suspicious', 0)}")
    except Exception as e:
        print(f"   ❌ Error: {e}")

    # Test file hash lookup
    print("\n2. Testing file hash lookup...")
    test_hash = "d41d8cd98f00b204e9800998ecf8427e"  # MD5 of empty file
    try:
        result = await vt.check_file_hash(test_hash)
        print(f"   ✓ Hash lookup successful")
        print(f"   Detected: {result.get('detected', False)}")
    except Exception as e:
        print(f"   ❌ Error: {e}")


async def test_abuseipdb():
    """Test AbuseIPDB integration."""
    print("\n" + "=" * 60)
    print("Testing AbuseIPDB Integration")
    print("=" * 60)

    config = get_config()

    if not config.ABUSEIPDB_API_KEY:
        print("❌ AbuseIPDB API key not configured")
        print("   Set ABUSEIPDB_API_KEY in .env file")
        return

    abuse = AbuseIPDBClient(config.ABUSEIPDB_API_KEY)

    # Test IP reputation check
    print("\n1. Testing IP reputation...")
    test_ip = "8.8.8.8"  # Google DNS (should be clean)
    try:
        result = await abuse.check_ip(test_ip)
        print(f"   ✓ IP check successful")
        print(f"   Abuse Score: {result.get('abuseConfidenceScore', 0)}%")
        print(f"   Total Reports: {result.get('totalReports', 0)}")
    except Exception as e:
        print(f"   ❌ Error: {e}")


async def test_slack():
    """Test Slack integration."""
    print("\n" + "=" * 60)
    print("Testing Slack Integration")
    print("=" * 60)

    config = get_config()

    if not config.SLACK_WEBHOOK_URL:
        print("❌ Slack webhook URL not configured")
        print("   Set SLACK_WEBHOOK_URL in .env file")
        return

    slack = SlackClient(config.SLACK_WEBHOOK_URL)

    # Test notification
    print("\n1. Sending test notification...")
    try:
        await slack.send_alert(
            title="SOAR Platform Test",
            message="This is a test notification from the SOAR platform",
            severity="info"
        )
        print(f"   ✓ Slack notification sent")
    except Exception as e:
        print(f"   ❌ Error: {e}")


async def main():
    """Main execution."""
    print("=" * 60)
    print("SOAR Platform - API Integration Testing")
    print("=" * 60)

    # Test all integrations
    await test_virustotal()
    await test_abuseipdb()
    await test_slack()

    print("\n" + "=" * 60)
    print("Integration testing completed!")
    print("=" * 60)
    print("\nConfiguration Status:")

    config = get_config()
    integrations = {
        "VirusTotal": bool(config.VIRUSTOTAL_API_KEY),
        "AbuseIPDB": bool(config.ABUSEIPDB_API_KEY),
        "Slack": bool(config.SLACK_WEBHOOK_URL),
        "Jira": bool(config.JIRA_URL and config.JIRA_USERNAME and config.JIRA_API_TOKEN),
        "Email": bool(config.SMTP_SERVER and config.SMTP_USERNAME and config.SMTP_PASSWORD),
    }

    for name, configured in integrations.items():
        status = "✓ Configured" if configured else "❌ Not configured"
        print(f"  {name}: {status}")

    print("\nTo configure integrations, update your .env file with API keys")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n\nTest interrupted by user")
    except Exception as e:
        print(f"\n❌ Error: {e}")
        exit(1)
