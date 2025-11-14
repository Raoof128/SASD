"""
Brute Force Defense Playbook
Automated response to brute force attacks
"""
import logging
from typing import Dict, Any

from backend.playbooks.base_playbook import BasePlaybook
from backend.models import Incident

logger = logging.getLogger(__name__)


class BruteForceDefensePlaybook(BasePlaybook):
    """Brute force attack defense playbook"""

    name = "Brute Force Defense"
    description = "Block brute force attacks and lock targeted accounts"
    incident_types = ["brute_force", "brute_force_attack", "failed_login", "password_attack"]
    automation_rate = 0.92
    requires_approval = False
    version = "1.0.0"

    async def execute(self, incident: Incident, **kwargs) -> Dict[str, Any]:
        """Execute brute force defense playbook"""

        results = {
            'incident_id': incident.id,
            'playbook': self.name,
            'attacker_ip_blocked': False,
            'target_account_locked': False,
            'failed_attempts': 0
        }

        # Step 1: Identify attacker IP
        attacker_ip = incident.source_ip
        results['attacker_ip'] = attacker_ip

        # Step 2: Identify target account
        target_account = incident.source_user or self._extract_target_account(incident)
        results['target_account'] = target_account

        # Step 3: Block attacker IP at firewall
        if attacker_ip:
            blocked = await self._block_attacker_ip(attacker_ip)
            results['attacker_ip_blocked'] = blocked

        # Step 4: Implement account lockout
        if target_account:
            locked = await self._lockout_account(target_account)
            results['target_account_locked'] = locked

        # Step 5: Notify user of suspicious activity
        if target_account:
            notified = await self._notify_user(target_account)
            results['user_notified'] = notified

        # Step 6: Check IP reputation
        if attacker_ip:
            ip_reputation = await self._check_attacker_reputation(attacker_ip)
            results['ip_reputation'] = ip_reputation

        # Step 7: Create ticket
        ticket = await self.create_ticket(
            title=f"Brute Force Attack: {attacker_ip or 'Unknown'} → {target_account or 'Multiple'}",
            description=f"""
Brute Force Attack Detected

Incident ID: #{incident.id}
Attacker IP: {attacker_ip}
Target Account: {target_account}
IP Blocked: {'Yes' if results['attacker_ip_blocked'] else 'No'}
Account Locked: {'Yes' if results['target_account_locked'] else 'No'}
            """,
            priority='Medium'
        )

        if ticket:
            results['jira_ticket'] = ticket.get('key')

        # Step 8: Notify SOC
        await self.notify(
            'slack',
            f"🔒 Brute Force Attack Blocked\n"
            f"Attacker: {attacker_ip}\n"
            f"Target: {target_account}\n"
            f"IP Blocked: {'✓' if results['attacker_ip_blocked'] else '✗'}\n"
            f"Ticket: {ticket.get('key') if ticket else 'N/A'}"
        )

        results['success'] = True
        return results

    def _extract_target_account(self, incident: Incident) -> str:
        """Extract target account from incident"""
        if incident.enrichment_data:
            return incident.enrichment_data.get('target_account')
        return None

    async def _block_attacker_ip(self, ip: str) -> bool:
        """Block attacker IP"""
        action = self.add_action('containment', f'Blocking attacker IP: {ip}')

        try:
            self.logger.info(f"Blocking IP: {ip}")
            action.success({'ip': ip, 'simulated': True})
            return True
        except Exception as e:
            action.failed(str(e))
            return False

    async def _lockout_account(self, account: str) -> bool:
        """Implement account lockout"""
        action = self.add_action('containment', f'Locking account: {account}')

        try:
            self.logger.info(f"Locking account: {account}")
            action.success({'account': account, 'simulated': True})
            return True
        except Exception as e:
            action.failed(str(e))
            return False

    async def _notify_user(self, account: str) -> bool:
        """Notify user of suspicious activity"""
        action = self.add_action('notification', f'Notifying user: {account}')

        try:
            self.logger.info(f"Notifying user: {account}")
            action.success({'account': account, 'simulated': True})
            return True
        except Exception as e:
            action.failed(str(e))
            return False

    async def _check_attacker_reputation(self, ip: str) -> Dict[str, Any]:
        """Check attacker IP reputation"""
        try:
            from backend.integrations.abuseipdb import AbuseIPDBClient
            abuseipdb = AbuseIPDBClient()
            return await abuseipdb.check_ip(ip)
        except Exception as e:
            return {'error': str(e)}
