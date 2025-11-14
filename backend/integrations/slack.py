"""
Slack API Integration
Send notifications and alerts to Slack channels
"""
import aiohttp
import logging
from typing import Dict, Any, Optional
from flask import current_app

logger = logging.getLogger(__name__)


class SlackClient:
    """Slack API client"""

    def __init__(self, bot_token: Optional[str] = None, webhook_url: Optional[str] = None):
        self.bot_token = bot_token or current_app.config.get('SLACK_BOT_TOKEN')
        self.webhook_url = webhook_url or current_app.config.get('SLACK_WEBHOOK_URL')

        if not self.bot_token and not self.webhook_url:
            logger.warning("Slack credentials not configured")

        self.headers = {
            'Authorization': f'Bearer {self.bot_token}',
            'Content-Type': 'application/json'
        }

    async def post_message(
        self,
        text: str,
        channel: Optional[str] = None,
        blocks: Optional[list] = None,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Post message to Slack channel

        Args:
            text: Message text
            channel: Channel to post to (defaults to configured channel)
            blocks: Rich formatting blocks
            **kwargs: Additional message parameters

        Returns:
            API response
        """
        if not channel:
            channel = current_app.config.get('SLACK_CHANNEL_SECURITY', '#security')

        # Use webhook if available (simpler)
        if self.webhook_url:
            return await self._post_webhook(text, channel, blocks)

        # Otherwise use Bot API
        if not self.bot_token:
            return {'error': 'Slack not configured', 'success': False}

        try:
            payload = {
                'channel': channel,
                'text': text,
                **kwargs
            }

            if blocks:
                payload['blocks'] = blocks

            async with aiohttp.ClientSession() as session:
                async with session.post(
                    'https://slack.com/api/chat.postMessage',
                    headers=self.headers,
                    json=payload
                ) as response:
                    result = await response.json()

                    if result.get('ok'):
                        return {'success': True, 'data': result}
                    else:
                        logger.error(f"Slack message failed: {result.get('error')}")
                        return {'error': result.get('error'), 'success': False}

        except Exception as e:
            logger.error(f"Slack post failed: {e}")
            return {'error': str(e), 'success': False}

    async def _post_webhook(
        self,
        text: str,
        channel: Optional[str] = None,
        blocks: Optional[list] = None
    ) -> Dict[str, Any]:
        """Post message using webhook"""
        try:
            payload = {'text': text}

            if channel:
                payload['channel'] = channel

            if blocks:
                payload['blocks'] = blocks

            async with aiohttp.ClientSession() as session:
                async with session.post(
                    self.webhook_url,
                    json=payload
                ) as response:
                    if response.status == 200:
                        return {'success': True}
                    else:
                        return {'error': f'HTTP {response.status}', 'success': False}

        except Exception as e:
            logger.error(f"Slack webhook failed: {e}")
            return {'error': str(e), 'success': False}

    async def post_incident_alert(
        self,
        incident_title: str,
        incident_id: int,
        severity: str,
        incident_type: str,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Post formatted incident alert

        Args:
            incident_title: Title of the incident
            incident_id: Incident ID
            severity: Incident severity
            incident_type: Type of incident
            **kwargs: Additional details

        Returns:
            API response
        """
        # Emoji mapping for severity
        severity_emoji = {
            'critical': ':rotating_light:',
            'high': ':warning:',
            'medium': ':large_orange_diamond:',
            'low': ':white_circle:'
        }

        emoji = severity_emoji.get(severity.lower(), ':bell:')

        blocks = [
            {
                "type": "header",
                "text": {
                    "type": "plain_text",
                    "text": f"{emoji} Security Incident #{incident_id}"
                }
            },
            {
                "type": "section",
                "fields": [
                    {
                        "type": "mrkdwn",
                        "text": f"*Title:*\n{incident_title}"
                    },
                    {
                        "type": "mrkdwn",
                        "text": f"*Severity:*\n{severity.upper()}"
                    },
                    {
                        "type": "mrkdwn",
                        "text": f"*Type:*\n{incident_type}"
                    },
                    {
                        "type": "mrkdwn",
                        "text": f"*Incident ID:*\n{incident_id}"
                    }
                ]
            }
        ]

        # Add additional fields if provided
        if kwargs:
            extra_fields = []
            for key, value in kwargs.items():
                extra_fields.append({
                    "type": "mrkdwn",
                    "text": f"*{key.replace('_', ' ').title()}:*\n{value}"
                })

            if extra_fields:
                blocks.append({
                    "type": "section",
                    "fields": extra_fields
                })

        text = f"{emoji} Security Incident: {incident_title} (Severity: {severity})"
        channel = current_app.config.get('SLACK_CHANNEL_INCIDENTS', '#incidents')

        return await self.post_message(text=text, channel=channel, blocks=blocks)

    async def post_playbook_result(
        self,
        playbook_name: str,
        incident_id: int,
        status: str,
        actions_count: int,
        execution_time: float
    ) -> Dict[str, Any]:
        """
        Post playbook execution result

        Args:
            playbook_name: Name of the playbook
            incident_id: Incident ID
            status: Execution status
            actions_count: Number of actions taken
            execution_time: Execution time in seconds

        Returns:
            API response
        """
        status_emoji = {
            'completed': ':white_check_mark:',
            'failed': ':x:',
            'cancelled': ':no_entry:'
        }

        emoji = status_emoji.get(status.lower(), ':gear:')

        text = (
            f"{emoji} Playbook Execution {status.title()}\n"
            f"Playbook: {playbook_name}\n"
            f"Incident: #{incident_id}\n"
            f"Actions Taken: {actions_count}\n"
            f"Execution Time: {execution_time:.2f}s"
        )

        channel = current_app.config.get('SLACK_CHANNEL_SECURITY', '#security')

        return await self.post_message(text=text, channel=channel)
