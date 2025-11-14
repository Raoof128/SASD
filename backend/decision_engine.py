"""
Decision Engine
AI/rule-based incident classification and playbook selection
"""
import logging
from typing import Optional, Dict, Any, List
import re

from backend.models import Incident, IncidentSeverity

logger = logging.getLogger(__name__)


class DecisionEngine:
    """
    Decision engine for automatic incident classification and playbook selection

    Uses rule-based logic to analyze incidents and select appropriate playbooks.
    Can be extended with ML models for more sophisticated classification.
    """

    def __init__(self):
        self.logger = logging.getLogger(__name__)

    def select_playbook(self, incident: Incident) -> Optional[str]:
        """
        Select appropriate playbook for incident

        Args:
            incident: Incident to analyze

        Returns:
            Playbook name or None
        """
        # Use incident type as primary selector
        if incident.incident_type:
            playbook_mapping = {
                'phishing': 'Phishing Investigation & Containment',
                'phishing_email': 'Phishing Investigation & Containment',
                'suspicious_email': 'Phishing Investigation & Containment',
                'malware': 'Malware Detection & Containment',
                'malware_detection': 'Malware Detection & Containment',
                'ransomware': 'Malware Detection & Containment',
                'account_compromise': 'Account Compromise Response',
                'compromised_account': 'Account Compromise Response',
                'lateral_movement': 'Account Compromise Response',
                'data_exfiltration': 'Data Exfiltration Detection',
                'data_leak': 'Data Exfiltration Detection',
                'brute_force': 'Brute Force Defense',
                'brute_force_attack': 'Brute Force Defense',
                'failed_login': 'Brute Force Defense',
                'vulnerability': 'Vulnerability Confirmation & Remediation',
                'cve': 'Vulnerability Confirmation & Remediation',
                'powershell': 'Suspicious PowerShell Execution',
                'powershell_execution': 'Suspicious PowerShell Execution',
                'suspicious_script': 'Suspicious PowerShell Execution',
                'dns_tunneling': 'DNS Tunneling Detection',
                'suspicious_dns': 'DNS Tunneling Detection',
                'c2_communication': 'DNS Tunneling Detection'
            }

            # Normalize incident type
            incident_type_normalized = incident.incident_type.lower().strip()

            if incident_type_normalized in playbook_mapping:
                return playbook_mapping[incident_type_normalized]

        # Fallback: analyze incident details
        return self._analyze_incident_content(incident)

    def _analyze_incident_content(self, incident: Incident) -> Optional[str]:
        """
        Analyze incident content to determine playbook

        Args:
            incident: Incident to analyze

        Returns:
            Playbook name or None
        """
        title = (incident.title or '').lower()
        description = (incident.description or '').lower()
        combined_text = f"{title} {description}"

        # Phishing indicators
        phishing_keywords = ['phishing', 'phish', 'suspicious email', 'spam', 'fraudulent email']
        if any(keyword in combined_text for keyword in phishing_keywords):
            return 'Phishing Investigation & Containment'

        # Malware indicators
        malware_keywords = ['malware', 'virus', 'trojan', 'ransomware', 'malicious file']
        if any(keyword in combined_text for keyword in malware_keywords):
            return 'Malware Detection & Containment'

        # Account compromise indicators
        account_keywords = ['account compromise', 'compromised account', 'unauthorized access', 'lateral movement']
        if any(keyword in combined_text for keyword in account_keywords):
            return 'Account Compromise Response'

        # Data exfiltration indicators
        exfil_keywords = ['data exfiltration', 'data leak', 'unauthorized transfer', 'large file upload']
        if any(keyword in combined_text for keyword in exfil_keywords):
            return 'Data Exfiltration Detection'

        # Brute force indicators
        brute_keywords = ['brute force', 'failed login', 'password attack', 'multiple failed attempts']
        if any(keyword in combined_text for keyword in brute_keywords):
            return 'Brute Force Defense'

        # Vulnerability indicators
        vuln_keywords = ['vulnerability', 'cve-', 'exploit', 'unpatched']
        if any(keyword in combined_text for keyword in vuln_keywords):
            return 'Vulnerability Confirmation & Remediation'

        # PowerShell indicators
        ps_keywords = ['powershell', 'suspicious script', 'encoded command', 'invoke-']
        if any(keyword in combined_text for keyword in ps_keywords):
            return 'Suspicious PowerShell Execution'

        # DNS tunneling indicators
        dns_keywords = ['dns tunneling', 'suspicious dns', 'c2 communication', 'command and control']
        if any(keyword in combined_text for keyword in dns_keywords):
            return 'DNS Tunneling Detection'

        self.logger.warning(f"No playbook selected for incident {incident.id}")
        return None

    def classify_severity(self, incident: Incident) -> IncidentSeverity:
        """
        Classify incident severity

        Args:
            incident: Incident to classify

        Returns:
            IncidentSeverity enum value
        """
        # If severity is already set, validate it
        if incident.severity:
            return incident.severity

        # Classification logic based on incident characteristics
        score = 0

        # Check incident type criticality
        critical_types = ['ransomware', 'data_exfiltration', 'account_compromise']
        high_types = ['malware', 'brute_force', 'lateral_movement']

        if incident.incident_type:
            incident_type_lower = incident.incident_type.lower()
            if any(t in incident_type_lower for t in critical_types):
                score += 3
            elif any(t in incident_type_lower for t in high_types):
                score += 2

        # Check affected assets
        if incident.affected_assets:
            asset_count = len(incident.affected_assets) if isinstance(incident.affected_assets, list) else 0
            if asset_count > 10:
                score += 2
            elif asset_count > 5:
                score += 1

        # Check indicators of compromise
        if incident.indicators_of_compromise:
            ioc_count = len(incident.indicators_of_compromise) if isinstance(incident.indicators_of_compromise, list) else 0
            if ioc_count > 5:
                score += 1

        # Classify based on score
        if score >= 5:
            return IncidentSeverity.CRITICAL
        elif score >= 3:
            return IncidentSeverity.HIGH
        elif score >= 1:
            return IncidentSeverity.MEDIUM
        else:
            return IncidentSeverity.LOW

    def extract_iocs(self, incident: Incident) -> List[Dict[str, str]]:
        """
        Extract Indicators of Compromise from incident

        Args:
            incident: Incident to analyze

        Returns:
            List of IOC dictionaries
        """
        iocs = []
        text = f"{incident.title} {incident.description}"

        # IP addresses
        ip_pattern = r'\b(?:\d{1,3}\.){3}\d{1,3}\b'
        ips = re.findall(ip_pattern, text)
        for ip in ips:
            iocs.append({'type': 'ip', 'value': ip})

        # Email addresses
        email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
        emails = re.findall(email_pattern, text)
        for email in emails:
            iocs.append({'type': 'email', 'value': email})

        # URLs
        url_pattern = r'https?://[^\s<>"{}|\\^`\[\]]+'
        urls = re.findall(url_pattern, text)
        for url in urls:
            iocs.append({'type': 'url', 'value': url})

        # File hashes (MD5, SHA1, SHA256)
        md5_pattern = r'\b[a-fA-F0-9]{32}\b'
        sha1_pattern = r'\b[a-fA-F0-9]{40}\b'
        sha256_pattern = r'\b[a-fA-F0-9]{64}\b'

        md5_hashes = re.findall(md5_pattern, text)
        for hash_val in md5_hashes:
            iocs.append({'type': 'md5', 'value': hash_val})

        sha1_hashes = re.findall(sha1_pattern, text)
        for hash_val in sha1_hashes:
            iocs.append({'type': 'sha1', 'value': hash_val})

        sha256_hashes = re.findall(sha256_pattern, text)
        for hash_val in sha256_hashes:
            iocs.append({'type': 'sha256', 'value': hash_val})

        # Domain names
        domain_pattern = r'\b(?:[a-zA-Z0-9](?:[a-zA-Z0-9-]{0,61}[a-zA-Z0-9])?\.)+[a-zA-Z]{2,}\b'
        domains = re.findall(domain_pattern, text)
        for domain in domains:
            # Filter out common false positives
            if domain not in ['example.com', 'localhost.local']:
                iocs.append({'type': 'domain', 'value': domain})

        return iocs

    def recommend_actions(self, incident: Incident) -> List[str]:
        """
        Recommend manual actions for incident

        Args:
            incident: Incident to analyze

        Returns:
            List of recommended actions
        """
        recommendations = []

        incident_type = (incident.incident_type or '').lower()

        # Type-specific recommendations
        if 'phishing' in incident_type:
            recommendations.extend([
                'Review email headers for spoofing indicators',
                'Check for similar emails in other mailboxes',
                'Update email filtering rules',
                'Conduct user awareness training'
            ])

        elif 'malware' in incident_type:
            recommendations.extend([
                'Perform full system scan on affected hosts',
                'Review recent file modifications',
                'Check for persistence mechanisms',
                'Update antivirus signatures'
            ])

        elif 'account' in incident_type:
            recommendations.extend([
                'Review account activity logs',
                'Check for unauthorized privilege escalation',
                'Audit access to sensitive resources',
                'Enable MFA if not already enabled'
            ])

        # Severity-specific recommendations
        if incident.severity in [IncidentSeverity.CRITICAL, IncidentSeverity.HIGH]:
            recommendations.extend([
                'Escalate to incident response team',
                'Consider engaging external forensics',
                'Prepare executive communication',
                'Document all actions for post-incident review'
            ])

        return recommendations
