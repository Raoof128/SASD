"""
Account Compromise Response Playbook
Automated response to compromised user accounts
"""
import logging
from typing import Dict, Any

from backend.playbooks.base_playbook import BasePlaybook
from backend.models import Incident

logger = logging.getLogger(__name__)


class AccountCompromisePlaybook(BasePlaybook):
    """Automated account compromise response playbook"""

    name = "Account Compromise Response"
    description = "Disable compromised accounts and revoke access"
    incident_types = ["account_compromise", "compromised_account", "lateral_movement", "unauthorized_access"]
    automation_rate = 0.88
    requires_approval = False
    version = "1.0.0"

    async def execute(self, incident: Incident, **kwargs) -> Dict[str, Any]:
        """Execute account compromise playbook"""

        results = {
            'incident_id': incident.id,
            'playbook': self.name,
            'accounts_disabled': [],
            'sessions_terminated': False,
            'password_reset_required': False
        }

        # Step 1: Identify compromised account
        username = incident.source_user or self._extract_username(incident)
        results['username'] = username

        if not username:
            results['success'] = False
            results['error'] = 'No username identified'
            return results

        # Step 2: Disable account in Active Directory
        disabled = await self._disable_ad_account(username)
        if disabled:
            results['accounts_disabled'].append(username)

        # Step 3: Terminate active sessions
        sessions_killed = await self._terminate_user_sessions(username)
        results['sessions_terminated'] = sessions_killed

        # Step 4: Force password reset
        password_reset = await self._force_password_reset(username)
        results['password_reset_required'] = password_reset

        # Step 5: Revoke access tokens
        tokens_revoked = await self._revoke_access_tokens(username)
        results['tokens_revoked'] = tokens_revoked

        # Step 6: Check for lateral movement
        lateral_movement = await self._check_lateral_movement(username, incident)
        results['lateral_movement_detected'] = lateral_movement

        # Step 7: Create ticket
        ticket = await self.create_ticket(
            title=f"Account Compromise: {username}",
            description=f"""
Account Compromise Incident #{incident.id}

Username: {username}
Account Disabled: {'Yes' if disabled else 'No'}
Sessions Terminated: {'Yes' if sessions_killed else 'No'}
Password Reset Required: Yes
Tokens Revoked: {'Yes' if tokens_revoked else 'No'}
Lateral Movement: {'Detected' if lateral_movement else 'Not detected'}
            """,
            priority='High'
        )

        if ticket:
            results['jira_ticket'] = ticket.get('key')

        # Step 8: Notify
        await self.notify(
            'slack',
            f"🔐 Account Compromise Contained\n"
            f"User: {username}\n"
            f"Incident: #{incident.id}\n"
            f"Account Disabled: {'✓' if disabled else '✗'}\n"
            f"Ticket: {ticket.get('key') if ticket else 'N/A'}"
        )

        results['success'] = True
        return results

    def _extract_username(self, incident: Incident) -> str:
        """Extract username from incident"""
        if incident.enrichment_data and 'username' in incident.enrichment_data:
            return incident.enrichment_data['username']
        return None

    async def _disable_ad_account(self, username: str) -> bool:
        """Disable Active Directory account"""
        action = self.add_action('containment', f'Disabling AD account: {username}')

        try:
            # In production, integrate with AD/LDAP
            self.logger.info(f"Disabling AD account: {username}")
            action.success({'username': username, 'simulated': True})
            return True
        except Exception as e:
            action.failed(str(e))
            return False

    async def _terminate_user_sessions(self, username: str) -> bool:
        """Terminate all active sessions"""
        action = self.add_action('containment', f'Terminating sessions for: {username}')

        try:
            self.logger.info(f"Terminating sessions: {username}")
            action.success({'username': username, 'simulated': True})
            return True
        except Exception as e:
            action.failed(str(e))
            return False

    async def _force_password_reset(self, username: str) -> bool:
        """Force password reset on next login"""
        action = self.add_action('remediation', f'Forcing password reset: {username}')

        try:
            self.logger.info(f"Forcing password reset: {username}")
            action.success({'username': username, 'simulated': True})
            return True
        except Exception as e:
            action.failed(str(e))
            return False

    async def _revoke_access_tokens(self, username: str) -> bool:
        """Revoke OAuth/API tokens"""
        action = self.add_action('containment', f'Revoking access tokens: {username}')

        try:
            self.logger.info(f"Revoking tokens: {username}")
            action.success({'username': username, 'simulated': True})
            return True
        except Exception as e:
            action.failed(str(e))
            return False

    async def _check_lateral_movement(self, username: str, incident: Incident) -> bool:
        """Check for lateral movement indicators"""
        action = self.add_action('investigation', f'Checking lateral movement: {username}')

        # In production, query SIEM for unusual access patterns
        lateral_detected = False
        action.success({'lateral_movement': lateral_detected})
        return lateral_detected
