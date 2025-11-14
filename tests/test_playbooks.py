"""
Playbook Test Suite
Unit tests for security playbooks with mocked integrations
"""
import pytest
import asyncio
from unittest.mock import AsyncMock, MagicMock, patch

from backend.models import Incident, IncidentSeverity, IncidentStatus
from backend.playbooks.phishing_response import PhishingResponsePlaybook
from backend.playbooks.malware_containment import MalwareContainmentPlaybook
from backend.playbooks.account_compromise import AccountCompromisePlaybook


@pytest.fixture
def phishing_incident():
    """Create a mock phishing incident"""
    incident = MagicMock(spec=Incident)
    incident.id = 1
    incident.alert_id = "ALERT-12345"
    incident.title = "Phishing email from attacker@evil.com"
    incident.description = "Suspicious email with URL: https://malicious-site.com"
    incident.severity = IncidentSeverity.HIGH
    incident.status = IncidentStatus.NEW
    incident.source_ip = "1.2.3.4"
    incident.source_user = "victim@company.com"
    incident.enrichment_data = {'sender': 'attacker@evil.com'}
    incident.indicators_of_compromise = [
        {'type': 'url', 'value': 'https://malicious-site.com'},
        {'type': 'email', 'value': 'attacker@evil.com'}
    ]
    incident.affected_assets = []
    incident.created_at = None
    return incident


@pytest.fixture
def malware_incident():
    """Create a mock malware incident"""
    incident = MagicMock(spec=Incident)
    incident.id = 2
    incident.alert_id = "ALERT-67890"
    incident.title = "Malware detected on workstation"
    incident.description = "Ransomware detected"
    incident.severity = IncidentSeverity.CRITICAL
    incident.status = IncidentStatus.NEW
    incident.source_ip = "192.168.1.100"
    incident.affected_assets = ["192.168.1.100", "WORKSTATION-01"]
    incident.indicators_of_compromise = [
        {'type': 'md5', 'value': 'abc123def456'}
    ]
    incident.enrichment_data = {}
    incident.created_at = None
    return incident


@pytest.mark.asyncio
class TestPhishingResponsePlaybook:
    """Test phishing response playbook"""

    async def test_execute_malicious_url(self, phishing_incident):
        """Test phishing playbook with malicious URL"""
        playbook = PhishingResponsePlaybook()

        # Mock VirusTotal response (malicious)
        with patch('backend.integrations.virustotal.VirusTotalClient.check_url') as mock_vt:
            mock_vt.return_value = {
                'verdict': 'malicious',
                'malicious': 10,
                'suspicious': 2,
                'total_scans': 70
            }

            # Mock AbuseIPDB response
            with patch('backend.integrations.abuseipdb.AbuseIPDBClient.check_ip') as mock_abuse:
                mock_abuse.return_value = {
                    'is_malicious': True,
                    'abuse_confidence_score': 85,
                    'verdict': 'malicious'
                }

                # Mock Jira ticket creation
                with patch.object(playbook, 'create_ticket') as mock_jira:
                    mock_jira.return_value = {
                        'success': True,
                        'key': 'SEC-123',
                        'url': 'https://jira.com/browse/SEC-123'
                    }

                    # Mock Slack notification
                    with patch.object(playbook, 'notify') as mock_slack:
                        mock_slack.return_value = True

                        # Execute playbook
                        result = await playbook.execute(phishing_incident)

                        # Assertions
                        assert result['success'] == True
                        assert result['verdict'] == 'malicious'
                        assert result['containment_actions'] > 0
                        assert 'jira_ticket' in result
                        assert len(result['actions']) > 0

                        # Verify integrations were called
                        mock_vt.assert_called()
                        mock_abuse.assert_called()
                        mock_jira.assert_called()
                        mock_slack.assert_called()

    async def test_execute_clean_url(self, phishing_incident):
        """Test phishing playbook with clean URL"""
        playbook = PhishingResponsePlaybook()

        # Mock VirusTotal response (clean)
        with patch('backend.integrations.virustotal.VirusTotalClient.check_url') as mock_vt:
            mock_vt.return_value = {
                'verdict': 'clean',
                'malicious': 0,
                'suspicious': 0,
                'total_scans': 70
            }

            # Mock AbuseIPDB response (clean IP)
            with patch('backend.integrations.abuseipdb.AbuseIPDBClient.check_ip') as mock_abuse:
                mock_abuse.return_value = {
                    'is_malicious': False,
                    'abuse_confidence_score': 0,
                    'verdict': 'clean'
                }

                # Mock ticket creation
                with patch.object(playbook, 'create_ticket') as mock_jira:
                    mock_jira.return_value = {'success': True, 'key': 'SEC-124'}

                    with patch.object(playbook, 'notify') as mock_slack:
                        mock_slack.return_value = True

                        result = await playbook.execute(phishing_incident)

                        # Should be suspicious, not malicious
                        assert result['verdict'] == 'suspicious'
                        # No containment actions for clean emails
                        assert result['containment_actions'] == 0


@pytest.mark.asyncio
class TestMalwareContainmentPlaybook:
    """Test malware containment playbook"""

    async def test_execute_malware_containment(self, malware_incident):
        """Test malware containment playbook"""
        playbook = MalwareContainmentPlaybook()

        # Mock VirusTotal file hash check
        with patch('backend.integrations.virustotal.VirusTotalClient.check_file_hash') as mock_vt:
            mock_vt.return_value = {
                'verdict': 'malicious',
                'malicious': 45,
                'total_scans': 70,
                'detection_rate': '45/70'
            }

            # Mock ticket creation
            with patch.object(playbook, 'create_ticket') as mock_jira:
                mock_jira.return_value = {'success': True, 'key': 'SEC-125'}

                with patch.object(playbook, 'notify') as mock_slack:
                    mock_slack.return_value = True

                    result = await playbook.execute(malware_incident)

                    # Assertions
                    assert result['success'] == True
                    assert len(result['isolated_hosts']) > 0
                    assert result['forensic_data_collected'] == True
                    assert 'hash_reputation' in result

    async def test_extract_file_hash(self, malware_incident):
        """Test file hash extraction"""
        playbook = MalwareContainmentPlaybook()

        file_hash = playbook._extract_file_hash(malware_incident)

        assert file_hash == 'abc123def456'


@pytest.mark.asyncio
class TestAccountCompromisePlaybook:
    """Test account compromise playbook"""

    async def test_execute_account_compromise(self):
        """Test account compromise response"""
        incident = MagicMock(spec=Incident)
        incident.id = 3
        incident.source_user = "compromised.user"
        incident.severity = IncidentSeverity.HIGH
        incident.enrichment_data = {}
        incident.affected_assets = []

        playbook = AccountCompromisePlaybook()

        # Mock ticket creation
        with patch.object(playbook, 'create_ticket') as mock_jira:
            mock_jira.return_value = {'success': True, 'key': 'SEC-126'}

            with patch.object(playbook, 'notify') as mock_slack:
                mock_slack.return_value = True

                result = await playbook.execute(incident)

                # Assertions
                assert result['success'] == True
                assert result['username'] == 'compromised.user'
                assert len(result['accounts_disabled']) > 0
                assert result['sessions_terminated'] == True
                assert result['password_reset_required'] == True


def test_playbook_metadata():
    """Test playbook metadata"""
    playbook = PhishingResponsePlaybook()

    metadata = playbook.get_metadata()

    assert metadata['name'] == 'Phishing Investigation & Containment'
    assert metadata['automation_rate'] == 0.95
    assert metadata['requires_approval'] == False
    assert 'phishing' in metadata['incident_types']


@pytest.mark.asyncio
async def test_playbook_action_tracking():
    """Test playbook action tracking"""
    playbook = PhishingResponsePlaybook()

    # Add actions
    action1 = playbook.add_action('test_action', 'Testing action tracking')
    action1.success({'result': 'success'})

    action2 = playbook.add_action('test_action2', 'Another test')
    action2.failed('Test error')

    # Get summary
    summary = playbook.get_execution_summary()

    assert summary['total_actions'] == 2
    assert summary['successful_actions'] == 1
    assert summary['failed_actions'] == 1
    assert summary['success_rate'] == 50.0


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
