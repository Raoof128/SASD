"""
Suspicious PowerShell Execution Playbook
Automated analysis of suspicious PowerShell activity
"""
import logging
from typing import Dict, Any
import re

from backend.playbooks.base_playbook import BasePlaybook
from backend.models import Incident

logger = logging.getLogger(__name__)


class PowerShellAnalysisPlaybook(BasePlaybook):
    """PowerShell analysis playbook"""

    name = "Suspicious PowerShell Execution"
    description = "Analyze and contain suspicious PowerShell activity"
    incident_types = ["powershell", "powershell_execution", "suspicious_script"]
    automation_rate = 0.87
    requires_approval = False
    version = "1.0.0"

    async def execute(self, incident: Incident, **kwargs) -> Dict[str, Any]:
        """Execute PowerShell analysis playbook"""

        results = {
            'incident_id': incident.id,
            'playbook': self.name,
            'malicious_indicators': [],
            'process_terminated': False,
            'script_blocked': False
        }

        # Step 1: Extract PowerShell command
        ps_command = self._extract_powershell_command(incident)
        results['powershell_command'] = ps_command

        # Step 2: Analyze for malicious patterns
        malicious_indicators = self._analyze_ps_command(ps_command)
        results['malicious_indicators'] = malicious_indicators

        # Step 3: Determine if malicious
        is_malicious = len(malicious_indicators) > 0
        results['verdict'] = 'malicious' if is_malicious else 'suspicious'

        # Step 4: Terminate process if malicious
        if is_malicious and incident.affected_assets:
            for host in incident.affected_assets:
                terminated = await self._terminate_powershell_process(host)
                if terminated:
                    results['process_terminated'] = True

        # Step 5: Block script execution (if applicable)
        if is_malicious:
            blocked = await self._block_script_execution(ps_command)
            results['script_blocked'] = blocked

        # Step 6: Create investigation ticket
        ticket = await self.create_ticket(
            title=f"Suspicious PowerShell: {incident.title}",
            description=f"""
Suspicious PowerShell Execution

Incident ID: #{incident.id}
Verdict: {results['verdict']}
Malicious Indicators: {', '.join(malicious_indicators) if malicious_indicators else 'None'}

Command:
{ps_command or 'Not available'}

Process Terminated: {'Yes' if results['process_terminated'] else 'No'}
            """,
            priority='High' if is_malicious else 'Medium'
        )

        if ticket:
            results['jira_ticket'] = ticket.get('key')

        # Step 7: Notify
        await self.notify(
            'slack',
            f"💻 Suspicious PowerShell Detected\n"
            f"Verdict: {results['verdict']}\n"
            f"Indicators: {len(malicious_indicators)}\n"
            f"Terminated: {'✓' if results['process_terminated'] else '✗'}\n"
            f"Ticket: {ticket.get('key') if ticket else 'N/A'}"
        )

        results['success'] = True
        return results

    def _extract_powershell_command(self, incident: Incident) -> str:
        """Extract PowerShell command from incident"""
        if incident.enrichment_data:
            return incident.enrichment_data.get('command_line', '')
        return incident.description or ''

    def _analyze_ps_command(self, command: str) -> list:
        """Analyze PowerShell command for malicious patterns"""
        action = self.add_action('investigation', 'Analyzing PowerShell command for malicious patterns')

        malicious_patterns = {
            'encoded_command': r'-[eE]nc?o?d?e?d?C?o?m?m?a?n?d?',
            'download_cradle': r'(Invoke-WebRequest|iwr|wget|curl).*\|.*Invoke-Expression',
            'bypass_execution_policy': r'-[eE]xec(utionPolicy)?\s+[bB]ypass',
            'hidden_window': r'-[wW]indowStyle\s+[hH]idden',
            'base64_encoded': r'[A-Za-z0-9+/]{50,}={0,2}',
            'invoke_expression': r'(Invoke-Expression|iex)',
            'download_file': r'(DownloadFile|DownloadString)',
            'webclient': r'New-Object.*Net\.WebClient'
        }

        indicators = []
        command_lower = command.lower()

        for indicator_name, pattern in malicious_patterns.items():
            if re.search(pattern, command, re.IGNORECASE):
                indicators.append(indicator_name)

        action.success({'indicators': indicators})
        return indicators

    async def _terminate_powershell_process(self, host: str) -> bool:
        """Terminate PowerShell process"""
        action = self.add_action('containment', f'Terminating PowerShell process on: {host}')

        try:
            self.logger.info(f"Terminating PowerShell on {host}")
            action.success({'host': host, 'simulated': True})
            return True
        except Exception as e:
            action.failed(str(e))
            return False

    async def _block_script_execution(self, command: str) -> bool:
        """Block script execution"""
        action = self.add_action('containment', 'Blocking malicious script execution')

        try:
            self.logger.info("Blocking script execution")
            action.success({'simulated': True})
            return True
        except Exception as e:
            action.failed(str(e))
            return False
