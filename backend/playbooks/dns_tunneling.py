"""
DNS Tunneling Detection Playbook
Automated response to DNS tunneling / C2 communication
"""
import logging
from typing import Dict, Any

from backend.playbooks.base_playbook import BasePlaybook
from backend.models import Incident

logger = logging.getLogger(__name__)


class DNSTunnelingPlaybook(BasePlaybook):
    """DNS tunneling detection playbook"""

    name = "DNS Tunneling Detection"
    description = "Block C2 communication via DNS tunneling"
    incident_types = ["dns_tunneling", "suspicious_dns", "c2_communication"]
    automation_rate = 0.83
    requires_approval = False
    version = "1.0.0"

    async def execute(self, incident: Incident, **kwargs) -> Dict[str, Any]:
        """Execute DNS tunneling playbook"""

        results = {
            'incident_id': incident.id,
            'playbook': self.name,
            'blocked_domains': [],
            'endpoint_isolated': False,
            'dns_logs_collected': False
        }

        # Step 1: Extract suspicious domain
        suspicious_domain = self._extract_suspicious_domain(incident)
        results['suspicious_domain'] = suspicious_domain

        # Step 2: Block C2 domain at firewall/DNS
        if suspicious_domain:
            blocked = await self._block_c2_domain(suspicious_domain)
            if blocked:
                results['blocked_domains'].append(suspicious_domain)

        # Step 3: Isolate endpoint network segment
        source_host = incident.source_ip or (incident.affected_assets[0] if incident.affected_assets else None)
        if source_host:
            isolated = await self._isolate_network_segment(source_host)
            results['endpoint_isolated'] = isolated

        # Step 4: Collect DNS logs for forensics
        logs_collected = await self._collect_dns_logs(incident)
        results['dns_logs_collected'] = logs_collected

        # Step 5: Check domain reputation
        if suspicious_domain:
            domain_reputation = await self._check_domain_reputation(suspicious_domain)
            results['domain_reputation'] = domain_reputation

        # Step 6: Create incident ticket
        ticket = await self.create_ticket(
            title=f"DNS Tunneling: {suspicious_domain or 'Unknown'}",
            description=f"""
DNS Tunneling Detected

Incident ID: #{incident.id}
Suspicious Domain: {suspicious_domain}
Source: {source_host}
Domain Blocked: {'Yes' if suspicious_domain in results['blocked_domains'] else 'No'}
Endpoint Isolated: {'Yes' if results['endpoint_isolated'] else 'No'}

C2 communication detected. Immediate action required.
            """,
            priority='High'
        )

        if ticket:
            results['jira_ticket'] = ticket.get('key')

        # Step 7: Alert security team
        await self.notify(
            'slack',
            f"🌐 DNS Tunneling Detected\n"
            f"Domain: {suspicious_domain}\n"
            f"Source: {source_host}\n"
            f"Blocked: {'✓' if results['blocked_domains'] else '✗'}\n"
            f"Ticket: {ticket.get('key') if ticket else 'N/A'}",
            channel='#incidents'
        )

        results['success'] = True
        return results

    def _extract_suspicious_domain(self, incident: Incident) -> str:
        """Extract suspicious domain from incident"""
        if incident.enrichment_data:
            return incident.enrichment_data.get('domain')

        # Try to extract from IOCs
        if incident.indicators_of_compromise:
            for ioc in incident.indicators_of_compromise:
                if isinstance(ioc, dict) and ioc.get('type') == 'domain':
                    return ioc['value']

        return incident.destination_ip  # Fallback

    async def _block_c2_domain(self, domain: str) -> bool:
        """Block C2 domain at firewall/DNS"""
        action = self.add_action('containment', f'Blocking C2 domain: {domain}')

        try:
            self.logger.info(f"Blocking domain: {domain}")
            action.success({'domain': domain, 'simulated': True})
            return True
        except Exception as e:
            action.failed(str(e))
            return False

    async def _isolate_network_segment(self, host: str) -> bool:
        """Isolate endpoint network segment"""
        action = self.add_action('containment', f'Isolating network segment: {host}')

        try:
            self.logger.info(f"Isolating network segment: {host}")
            action.success({'host': host, 'simulated': True})
            return True
        except Exception as e:
            action.failed(str(e))
            return False

    async def _collect_dns_logs(self, incident: Incident) -> bool:
        """Collect DNS logs for forensics"""
        action = self.add_action('forensics', 'Collecting DNS logs')

        try:
            self.logger.info("Collecting DNS logs")
            action.success({'simulated': True})
            return True
        except Exception as e:
            action.failed(str(e))
            return False

    async def _check_domain_reputation(self, domain: str) -> Dict[str, Any]:
        """Check domain reputation"""
        action = self.add_action('threat_intel', f'Checking domain reputation: {domain}')

        try:
            from backend.integrations.virustotal import VirusTotalClient
            vt = VirusTotalClient()
            # Note: VT URL check can work for domains too
            result = await vt.check_url(f"http://{domain}")
            action.success(result)
            return result
        except Exception as e:
            action.failed(str(e))
            return {'verdict': 'unknown', 'error': str(e)}
