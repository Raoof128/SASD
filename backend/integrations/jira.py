"""
Jira API Integration
Create and update tickets for incident tracking
"""
import aiohttp
import base64
import logging
from typing import Dict, Any, Optional
from flask import current_app

logger = logging.getLogger(__name__)


class JiraClient:
    """Jira API client"""

    def __init__(
        self,
        url: Optional[str] = None,
        email: Optional[str] = None,
        api_token: Optional[str] = None
    ):
        self.url = (url or current_app.config.get('JIRA_URL', '')).rstrip('/')
        self.email = email or current_app.config.get('JIRA_EMAIL')
        self.api_token = api_token or current_app.config.get('JIRA_API_TOKEN')
        self.project_key = current_app.config.get('JIRA_PROJECT_KEY', 'SEC')

        if not all([self.url, self.email, self.api_token]):
            logger.warning("Jira credentials not fully configured")

        # Create basic auth header
        auth_string = f"{self.email}:{self.api_token}"
        b64_auth = base64.b64encode(auth_string.encode()).decode()

        self.headers = {
            'Authorization': f'Basic {b64_auth}',
            'Content-Type': 'application/json',
            'Accept': 'application/json'
        }

    async def create_ticket(
        self,
        title: str,
        description: str,
        priority: str = 'Medium',
        issue_type: str = 'Task',
        **kwargs
    ) -> Dict[str, Any]:
        """
        Create Jira ticket

        Args:
            title: Ticket summary
            description: Ticket description
            priority: Priority (Low, Medium, High, Highest)
            issue_type: Issue type (Task, Bug, Story)
            **kwargs: Additional fields

        Returns:
            Created ticket data
        """
        if not all([self.url, self.email, self.api_token]):
            return {'error': 'Jira not configured', 'success': False}

        try:
            payload = {
                'fields': {
                    'project': {'key': self.project_key},
                    'summary': title,
                    'description': description,
                    'issuetype': {'name': issue_type},
                    'priority': {'name': priority}
                }
            }

            # Add custom fields
            if kwargs:
                payload['fields'].update(kwargs)

            async with aiohttp.ClientSession() as session:
                async with session.post(
                    f"{self.url}/rest/api/3/issue",
                    headers=self.headers,
                    json=payload
                ) as response:
                    if response.status in [200, 201]:
                        result = await response.json()
                        return {
                            'success': True,
                            'key': result['key'],
                            'id': result['id'],
                            'url': f"{self.url}/browse/{result['key']}"
                        }
                    else:
                        error_text = await response.text()
                        logger.error(f"Jira ticket creation failed: {error_text}")
                        return {'error': f'HTTP {response.status}', 'success': False}

        except Exception as e:
            logger.error(f"Jira ticket creation failed: {e}")
            return {'error': str(e), 'success': False}

    async def update_ticket(
        self,
        ticket_key: str,
        fields: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Update Jira ticket

        Args:
            ticket_key: Ticket key (e.g., SEC-123)
            fields: Fields to update

        Returns:
            Update result
        """
        if not all([self.url, self.email, self.api_token]):
            return {'error': 'Jira not configured', 'success': False}

        try:
            payload = {'fields': fields}

            async with aiohttp.ClientSession() as session:
                async with session.put(
                    f"{self.url}/rest/api/3/issue/{ticket_key}",
                    headers=self.headers,
                    json=payload
                ) as response:
                    if response.status == 204:
                        return {'success': True}
                    else:
                        error_text = await response.text()
                        logger.error(f"Jira ticket update failed: {error_text}")
                        return {'error': f'HTTP {response.status}', 'success': False}

        except Exception as e:
            logger.error(f"Jira ticket update failed: {e}")
            return {'error': str(e), 'success': False}

    async def add_comment(
        self,
        ticket_key: str,
        comment: str
    ) -> Dict[str, Any]:
        """
        Add comment to Jira ticket

        Args:
            ticket_key: Ticket key
            comment: Comment text

        Returns:
            Comment creation result
        """
        if not all([self.url, self.email, self.api_token]):
            return {'error': 'Jira not configured', 'success': False}

        try:
            payload = {
                'body': comment
            }

            async with aiohttp.ClientSession() as session:
                async with session.post(
                    f"{self.url}/rest/api/3/issue/{ticket_key}/comment",
                    headers=self.headers,
                    json=payload
                ) as response:
                    if response.status in [200, 201]:
                        result = await response.json()
                        return {'success': True, 'comment_id': result['id']}
                    else:
                        error_text = await response.text()
                        logger.error(f"Jira comment failed: {error_text}")
                        return {'error': f'HTTP {response.status}', 'success': False}

        except Exception as e:
            logger.error(f"Jira comment failed: {e}")
            return {'error': str(e), 'success': False}

    async def transition_ticket(
        self,
        ticket_key: str,
        transition_name: str
    ) -> Dict[str, Any]:
        """
        Transition ticket to new status

        Args:
            ticket_key: Ticket key
            transition_name: Transition name (e.g., "In Progress", "Done")

        Returns:
            Transition result
        """
        if not all([self.url, self.email, self.api_token]):
            return {'error': 'Jira not configured', 'success': False}

        try:
            # Get available transitions
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    f"{self.url}/rest/api/3/issue/{ticket_key}/transitions",
                    headers=self.headers
                ) as response:
                    if response.status == 200:
                        transitions = await response.json()

                        # Find transition ID
                        transition_id = None
                        for t in transitions.get('transitions', []):
                            if t['name'].lower() == transition_name.lower():
                                transition_id = t['id']
                                break

                        if not transition_id:
                            return {'error': f'Transition "{transition_name}" not found', 'success': False}

                        # Perform transition
                        async with session.post(
                            f"{self.url}/rest/api/3/issue/{ticket_key}/transitions",
                            headers=self.headers,
                            json={'transition': {'id': transition_id}}
                        ) as trans_response:
                            if trans_response.status == 204:
                                return {'success': True}
                            else:
                                return {'error': f'HTTP {trans_response.status}', 'success': False}

        except Exception as e:
            logger.error(f"Jira transition failed: {e}")
            return {'error': str(e), 'success': False}
