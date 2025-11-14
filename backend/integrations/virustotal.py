"""
VirusTotal API Integration
Threat intelligence for URLs, IPs, files, and hashes
"""
import aiohttp
import logging
from typing import Dict, Any, Optional
from flask import current_app

logger = logging.getLogger(__name__)


class VirusTotalClient:
    """VirusTotal API client"""

    BASE_URL = "https://www.virustotal.com/api/v3"

    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or current_app.config.get('VIRUSTOTAL_API_KEY')
        if not self.api_key:
            logger.warning("VirusTotal API key not configured")

        self.headers = {
            'x-apikey': self.api_key
        }

    async def check_url(self, url: str) -> Dict[str, Any]:
        """
        Check URL reputation

        Args:
            url: URL to check

        Returns:
            VirusTotal analysis results
        """
        if not self.api_key:
            return {'error': 'API key not configured', 'verdict': 'unknown'}

        try:
            async with aiohttp.ClientSession() as session:
                # Submit URL for analysis
                data = aiohttp.FormData()
                data.add_field('url', url)

                async with session.post(
                    f"{self.BASE_URL}/urls",
                    headers=self.headers,
                    data=data
                ) as response:
                    if response.status == 200:
                        result = await response.json()
                        analysis_id = result['data']['id']

                        # Get analysis results
                        async with session.get(
                            f"{self.BASE_URL}/analyses/{analysis_id}",
                            headers=self.headers
                        ) as analysis_response:
                            if analysis_response.status == 200:
                                analysis_data = await analysis_response.json()
                                return self._parse_url_analysis(analysis_data)

            return {'error': 'Analysis failed', 'verdict': 'unknown'}

        except Exception as e:
            logger.error(f"VirusTotal URL check failed: {e}")
            return {'error': str(e), 'verdict': 'unknown'}

    async def check_ip(self, ip: str) -> Dict[str, Any]:
        """
        Check IP reputation

        Args:
            ip: IP address to check

        Returns:
            IP reputation data
        """
        if not self.api_key:
            return {'error': 'API key not configured', 'verdict': 'unknown'}

        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    f"{self.BASE_URL}/ip_addresses/{ip}",
                    headers=self.headers
                ) as response:
                    if response.status == 200:
                        result = await response.json()
                        return self._parse_ip_analysis(result)
                    else:
                        return {'error': f'HTTP {response.status}', 'verdict': 'unknown'}

        except Exception as e:
            logger.error(f"VirusTotal IP check failed: {e}")
            return {'error': str(e), 'verdict': 'unknown'}

    async def check_file_hash(self, file_hash: str) -> Dict[str, Any]:
        """
        Check file hash reputation

        Args:
            file_hash: File hash (MD5, SHA1, or SHA256)

        Returns:
            File analysis results
        """
        if not self.api_key:
            return {'error': 'API key not configured', 'verdict': 'unknown'}

        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    f"{self.BASE_URL}/files/{file_hash}",
                    headers=self.headers
                ) as response:
                    if response.status == 200:
                        result = await response.json()
                        return self._parse_file_analysis(result)
                    else:
                        return {'error': f'HTTP {response.status}', 'verdict': 'unknown'}

        except Exception as e:
            logger.error(f"VirusTotal file hash check failed: {e}")
            return {'error': str(e), 'verdict': 'unknown'}

    def _parse_url_analysis(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Parse URL analysis results"""
        try:
            stats = data['data']['attributes']['stats']
            malicious = stats.get('malicious', 0)
            suspicious = stats.get('suspicious', 0)
            harmless = stats.get('harmless', 0)
            undetected = stats.get('undetected', 0)

            total = malicious + suspicious + harmless + undetected

            if malicious > 0:
                verdict = 'malicious'
            elif suspicious > 3:
                verdict = 'suspicious'
            else:
                verdict = 'clean'

            return {
                'verdict': verdict,
                'malicious': malicious,
                'suspicious': suspicious,
                'harmless': harmless,
                'undetected': undetected,
                'total_scans': total,
                'detection_rate': f"{malicious}/{total}" if total > 0 else "0/0"
            }
        except Exception as e:
            logger.error(f"Failed to parse VT URL analysis: {e}")
            return {'error': str(e), 'verdict': 'unknown'}

    def _parse_ip_analysis(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Parse IP analysis results"""
        try:
            stats = data['data']['attributes']['last_analysis_stats']
            malicious = stats.get('malicious', 0)
            suspicious = stats.get('suspicious', 0)

            if malicious > 0:
                verdict = 'malicious'
            elif suspicious > 0:
                verdict = 'suspicious'
            else:
                verdict = 'clean'

            return {
                'verdict': verdict,
                'malicious': malicious,
                'suspicious': suspicious,
                'reputation': data['data']['attributes'].get('reputation', 0),
                'country': data['data']['attributes'].get('country', 'Unknown')
            }
        except Exception as e:
            logger.error(f"Failed to parse VT IP analysis: {e}")
            return {'error': str(e), 'verdict': 'unknown'}

    def _parse_file_analysis(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Parse file analysis results"""
        try:
            stats = data['data']['attributes']['last_analysis_stats']
            malicious = stats.get('malicious', 0)
            suspicious = stats.get('suspicious', 0)
            harmless = stats.get('harmless', 0)
            undetected = stats.get('undetected', 0)

            total = malicious + suspicious + harmless + undetected

            if malicious > 0:
                verdict = 'malicious'
            elif suspicious > 3:
                verdict = 'suspicious'
            else:
                verdict = 'clean'

            return {
                'verdict': verdict,
                'malicious': malicious,
                'suspicious': suspicious,
                'harmless': harmless,
                'undetected': undetected,
                'total_scans': total,
                'detection_rate': f"{malicious}/{total}" if total > 0 else "0/0",
                'file_type': data['data']['attributes'].get('type_description', 'Unknown'),
                'file_size': data['data']['attributes'].get('size', 0)
            }
        except Exception as e:
            logger.error(f"Failed to parse VT file analysis: {e}")
            return {'error': str(e), 'verdict': 'unknown'}
