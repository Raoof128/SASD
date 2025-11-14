"""
AbuseIPDB API Integration
IP reputation and abuse reporting
"""
import aiohttp
import logging
from typing import Dict, Any, Optional
from flask import current_app

logger = logging.getLogger(__name__)


class AbuseIPDBClient:
    """AbuseIPDB API client"""

    BASE_URL = "https://api.abuseipdb.com/api/v2"

    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or current_app.config.get('ABUSEIPDB_API_KEY')
        if not self.api_key:
            logger.warning("AbuseIPDB API key not configured")

        self.headers = {
            'Key': self.api_key,
            'Accept': 'application/json'
        }

    async def check_ip(self, ip: str, max_age_days: int = 90) -> Dict[str, Any]:
        """
        Check IP reputation

        Args:
            ip: IP address to check
            max_age_days: Maximum age of reports to include

        Returns:
            IP reputation data
        """
        if not self.api_key:
            return {'error': 'API key not configured', 'is_malicious': False}

        try:
            params = {
                'ipAddress': ip,
                'maxAgeInDays': max_age_days,
                'verbose': ''
            }

            async with aiohttp.ClientSession() as session:
                async with session.get(
                    f"{self.BASE_URL}/check",
                    headers=self.headers,
                    params=params
                ) as response:
                    if response.status == 200:
                        result = await response.json()
                        return self._parse_check_response(result)
                    else:
                        error_text = await response.text()
                        logger.error(f"AbuseIPDB check failed: HTTP {response.status} - {error_text}")
                        return {'error': f'HTTP {response.status}', 'is_malicious': False}

        except Exception as e:
            logger.error(f"AbuseIPDB check failed: {e}")
            return {'error': str(e), 'is_malicious': False}

    async def report_ip(
        self,
        ip: str,
        categories: list,
        comment: str
    ) -> Dict[str, Any]:
        """
        Report malicious IP

        Args:
            ip: IP address to report
            categories: List of abuse category IDs
            comment: Description of malicious activity

        Returns:
            Report submission result
        """
        if not self.api_key:
            return {'error': 'API key not configured', 'success': False}

        try:
            data = {
                'ip': ip,
                'categories': ','.join(map(str, categories)),
                'comment': comment
            }

            async with aiohttp.ClientSession() as session:
                async with session.post(
                    f"{self.BASE_URL}/report",
                    headers=self.headers,
                    data=data
                ) as response:
                    if response.status == 200:
                        result = await response.json()
                        return {'success': True, 'data': result}
                    else:
                        return {'error': f'HTTP {response.status}', 'success': False}

        except Exception as e:
            logger.error(f"AbuseIPDB report failed: {e}")
            return {'error': str(e), 'success': False}

    def _parse_check_response(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Parse check response"""
        try:
            ip_data = data['data']

            abuse_confidence_score = ip_data.get('abuseConfidenceScore', 0)
            is_malicious = abuse_confidence_score > 50

            return {
                'ip': ip_data.get('ipAddress'),
                'is_malicious': is_malicious,
                'abuse_confidence_score': abuse_confidence_score,
                'is_public': ip_data.get('isPublic', True),
                'usage_type': ip_data.get('usageType', 'Unknown'),
                'isp': ip_data.get('isp', 'Unknown'),
                'domain': ip_data.get('domain', 'Unknown'),
                'country_code': ip_data.get('countryCode', 'Unknown'),
                'total_reports': ip_data.get('totalReports', 0),
                'num_distinct_users': ip_data.get('numDistinctUsers', 0),
                'last_reported_at': ip_data.get('lastReportedAt'),
                'verdict': 'malicious' if is_malicious else 'clean'
            }

        except Exception as e:
            logger.error(f"Failed to parse AbuseIPDB response: {e}")
            return {'error': str(e), 'is_malicious': False}
