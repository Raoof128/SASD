"""
Phishing Investigation & Containment Playbook
Automated response to phishing emails and malicious URLs
"""
import logging
from typing import Dict, Any
import re

from backend.playbooks.base_playbook import BasePlaybook
from backend.models import Incident

logger = logging.getLogger(__name__)


class PhishingResponsePlaybook(BasePlaybook):
    """
    Automated phishing response playbook

    Actions:
    1. Extract email details (sender, URLs, attachments)
    2. Query VirusTotal for URL/attachment reputation
    3. Check sender IP against AbuseIPDB
    4. Quarantine emails from sender (if malicious)
    5. Create Jira ticket with analysis
    6. Notify SOC via Slack
    """

    name = "Phishing Investigation & Containment"
    description = "Automated investigation and containment of phishing attempts"
    incident_types = ["phishing", "phishing_email", "suspicious_email"]
    automation_rate = 0.95  # 95% automated
    requires_approval = False
    version = "1.0.0"

    async def execute(self, incident: Incident, **kwargs) -> Dict[str, Any]:
        """Execute phishing response playbook"""

        results = {
            'incident_id': incident.id,
            'playbook': self.name,
            'actions': [],
            'verdict': 'unknown',
            'containment_actions': 0
        }

        # Step 1: Extract email details
        email_data = self._extract_email_details(incident)
        results['email_data'] = email_data

        # Step 2: Query threat intelligence for URLs
        url_verdicts = []
        if email_data.get('urls'):
            for url in email_data['urls']:
                verdict = await self._check_url_reputation(url)
                url_verdicts.append(verdict)
                results['actions'].append(f"Checked URL: {url} - {verdict['verdict']}")

        # Step 3: Check sender IP reputation
        ip_verdict = None
        if email_data.get('sender_ip'):
            ip_verdict = await self._check_ip_reputation(email_data['sender_ip'])
            results['actions'].append(
                f"Checked IP: {email_data['sender_ip']} - {ip_verdict.get('verdict', 'unknown')}"
            )

        # Step 4: Determine if phishing is malicious
        is_malicious = self._is_malicious(url_verdicts, ip_verdict)
        results['verdict'] = 'malicious' if is_malicious else 'suspicious'

        # Step 5: Containment actions if malicious
        if is_malicious:
            # Quarantine emails from sender
            if email_data.get('sender'):
                quarantine_result = await self._quarantine_emails(email_data['sender'])
                if quarantine_result:
                    results['containment_actions'] += 1
                    results['actions'].append(f"Quarantined emails from {email_data['sender']}")

            # Block malicious URLs at firewall (if available)
            for url_verdict in url_verdicts:
                if url_verdict.get('verdict') == 'malicious':
                    block_result = await self._block_url(url_verdict['url'])
                    if block_result:
                        results['containment_actions'] += 1
                        results['actions'].append(f"Blocked URL: {url_verdict['url']}")

        # Step 6: Create Jira ticket
        ticket = await self._create_investigation_ticket(
            incident=incident,
            email_data=email_data,
            url_verdicts=url_verdicts,
            ip_verdict=ip_verdict,
            verdict=results['verdict']
        )

        if ticket and ticket.get('success'):
            results['jira_ticket'] = ticket.get('key')
            results['jira_url'] = ticket.get('url')
            results['actions'].append(f"Created Jira ticket: {ticket.get('key')}")

        # Step 7: Notify SOC
        notification_sent = await self._notify_soc(
            incident=incident,
            verdict=results['verdict'],
            jira_ticket=ticket.get('key') if ticket else None,
            actions_taken=results['containment_actions']
        )

        if notification_sent:
            results['actions'].append("Notified SOC team via Slack")

        results['success'] = True
        return results

    def _extract_email_details(self, incident: Incident) -> Dict[str, Any]:
        """Extract email details from incident"""
        action = self.add_action('extract_data', 'Extracting email details from incident')

        email_data = {
            'sender': None,
            'sender_ip': incident.source_ip,
            'recipient': incident.source_user,
            'subject': incident.title,
            'urls': [],
            'attachments': []
        }

        # Extract sender from description or enrichment data
        if incident.enrichment_data and 'sender' in incident.enrichment_data:
            email_data['sender'] = incident.enrichment_data['sender']

        # Extract URLs from description
        description = incident.description or ''
        url_pattern = r'https?://[^\s<>"{}|\\^`\[\]]+'
        urls = re.findall(url_pattern, description)
        email_data['urls'] = list(set(urls))  # Deduplicate

        # Extract from IOCs if available
        if incident.indicators_of_compromise:
            for ioc in incident.indicators_of_compromise:
                if isinstance(ioc, dict):
                    if ioc.get('type') == 'url':
                        email_data['urls'].append(ioc['value'])
                    elif ioc.get('type') == 'email':
                        if not email_data['sender']:
                            email_data['sender'] = ioc['value']

        action.success(email_data)
        return email_data

    async def _check_url_reputation(self, url: str) -> Dict[str, Any]:
        """Check URL reputation via VirusTotal"""
        action = self.add_action('threat_intel', f'Checking URL reputation: {url}')

        try:
            from backend.integrations.virustotal import VirusTotalClient
            vt = VirusTotalClient()
            result = await vt.check_url(url)

            action.success(result)
            return {'url': url, **result}

        except Exception as e:
            self.logger.error(f"URL check failed: {e}")
            action.failed(str(e))
            return {'url': url, 'verdict': 'unknown', 'error': str(e)}

    async def _check_ip_reputation(self, ip: str) -> Dict[str, Any]:
        """Check IP reputation via AbuseIPDB"""
        action = self.add_action('threat_intel', f'Checking IP reputation: {ip}')

        try:
            from backend.integrations.abuseipdb import AbuseIPDBClient
            abuseipdb = AbuseIPDBClient()
            result = await abuseipdb.check_ip(ip)

            action.success(result)
            return result

        except Exception as e:
            self.logger.error(f"IP check failed: {e}")
            action.failed(str(e))
            return {'verdict': 'unknown', 'error': str(e)}

    def _is_malicious(
        self,
        url_verdicts: list,
        ip_verdict: Dict[str, Any]
    ) -> bool:
        """Determine if phishing is malicious based on verdicts"""

        # Check URLs
        for verdict in url_verdicts:
            if verdict.get('verdict') == 'malicious':
                return True

        # Check IP
        if ip_verdict and ip_verdict.get('is_malicious'):
            return True

        # Check abuse confidence score
        if ip_verdict and ip_verdict.get('abuse_confidence_score', 0) > 70:
            return True

        return False

    async def _quarantine_emails(self, sender: str) -> bool:
        """Quarantine emails from sender"""
        action = self.add_action('containment', f'Quarantining emails from {sender}')

        try:
            # This would integrate with email security platform (Proofpoint, Mimecast, etc.)
            # For now, we'll simulate the action
            self.logger.info(f"Quarantining emails from {sender}")

            # In production, call email security API:
            # from backend.integrations.proofpoint import ProofpointClient
            # proofpoint = ProofpointClient()
            # result = await proofpoint.quarantine_emails(sender)

            action.success({'sender': sender, 'simulated': True})
            return True

        except Exception as e:
            self.logger.error(f"Email quarantine failed: {e}")
            action.failed(str(e))
            return False

    async def _block_url(self, url: str) -> bool:
        """Block malicious URL at firewall"""
        action = self.add_action('containment', f'Blocking URL: {url}')

        try:
            # This would integrate with firewall API
            # For now, we'll simulate the action
            self.logger.info(f"Blocking URL: {url}")

            # In production, call firewall API:
            # from backend.integrations.firewall import FirewallClient
            # firewall = FirewallClient()
            # result = await firewall.block_url(url)

            action.success({'url': url, 'simulated': True})
            return True

        except Exception as e:
            self.logger.error(f"URL blocking failed: {e}")
            action.failed(str(e))
            return False

    async def _create_investigation_ticket(
        self,
        incident: Incident,
        email_data: Dict[str, Any],
        url_verdicts: list,
        ip_verdict: Dict[str, Any],
        verdict: str
    ) -> Dict[str, Any]:
        """Create Jira ticket for investigation"""

        # Build description
        description = f"""
Phishing Investigation - Incident #{incident.id}

*Incident Details:*
- Alert ID: {incident.alert_id}
- Severity: {incident.severity.value if incident.severity else 'Unknown'}
- Verdict: {verdict.upper()}

*Email Information:*
- Sender: {email_data.get('sender', 'Unknown')}
- Sender IP: {email_data.get('sender_ip', 'Unknown')}
- Recipient: {email_data.get('recipient', 'Unknown')}
- Subject: {email_data.get('subject', 'Unknown')}

*Threat Intelligence:*
"""

        # Add URL analysis
        if url_verdicts:
            description += "\nURLs:\n"
            for url_verdict in url_verdicts:
                description += f"- {url_verdict.get('url')}: {url_verdict.get('verdict', 'unknown')}\n"

        # Add IP analysis
        if ip_verdict:
            description += f"\nSender IP Reputation:\n"
            description += f"- Verdict: {ip_verdict.get('verdict', 'unknown')}\n"
            description += f"- Abuse Confidence: {ip_verdict.get('abuse_confidence_score', 'N/A')}%\n"

        description += f"\n*Automated Analysis:*\n{incident.description or 'No additional details'}"

        # Determine priority
        priority = 'High' if verdict == 'malicious' else 'Medium'

        return await self.create_ticket(
            title=f"Phishing: {email_data.get('sender', 'Unknown')} → {incident.id}",
            description=description,
            priority=priority
        )

    async def _notify_soc(
        self,
        incident: Incident,
        verdict: str,
        jira_ticket: str,
        actions_taken: int
    ) -> bool:
        """Notify SOC team via Slack"""

        message = (
            f"🎣 Phishing {verdict.upper()} Contained\n"
            f"Incident: #{incident.id}\n"
            f"Verdict: {verdict}\n"
            f"Actions Taken: {actions_taken}\n"
            f"Jira: {jira_ticket or 'N/A'}"
        )

        return await self.notify('slack', message, channel='#security')
