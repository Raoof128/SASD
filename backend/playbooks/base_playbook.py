"""
Base Playbook Class
Abstract base class for all security playbooks
"""
from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional
from datetime import datetime
import asyncio
import logging

from backend.models import Incident, PlaybookExecution, PlaybookExecutionStatus, db

logger = logging.getLogger(__name__)


class PlaybookAction:
    """Represents a single action taken by a playbook"""

    def __init__(self, action_type: str, description: str, **kwargs):
        self.action_type = action_type
        self.description = description
        self.timestamp = datetime.utcnow()
        self.status = 'pending'
        self.result = None
        self.error = None
        self.metadata = kwargs

    def success(self, result: Any = None):
        """Mark action as successful"""
        self.status = 'success'
        self.result = result

    def failed(self, error: str):
        """Mark action as failed"""
        self.status = 'failed'
        self.error = error

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            'action_type': self.action_type,
            'description': self.description,
            'timestamp': self.timestamp.isoformat(),
            'status': self.status,
            'result': self.result,
            'error': self.error,
            'metadata': self.metadata
        }


class BasePlaybook(ABC):
    """
    Abstract base class for security playbooks

    All playbooks must inherit from this class and implement the execute() method.
    """

    # Playbook metadata (override in subclasses)
    name: str = "Base Playbook"
    description: str = "Base playbook template"
    incident_types: List[str] = []
    automation_rate: float = 0.0  # 0.0 to 1.0
    requires_approval: bool = False
    version: str = "1.0.0"

    def __init__(self):
        self.actions: List[PlaybookAction] = []
        self.logger = logging.getLogger(f"playbook.{self.__class__.__name__}")
        self.start_time = None
        self.end_time = None

    @abstractmethod
    async def execute(self, incident: Incident, **kwargs) -> Dict[str, Any]:
        """
        Execute the playbook for the given incident

        Args:
            incident: The incident to process
            **kwargs: Additional parameters

        Returns:
            Dictionary containing execution results
        """
        pass

    def add_action(self, action_type: str, description: str, **kwargs) -> PlaybookAction:
        """Add an action to the playbook execution"""
        action = PlaybookAction(action_type, description, **kwargs)
        self.actions.append(action)
        self.logger.info(f"Action added: {description}")
        return action

    async def execute_with_tracking(
        self,
        incident: Incident,
        execution: PlaybookExecution,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Execute playbook with full tracking and error handling

        Args:
            incident: The incident to process
            execution: The execution record to update
            **kwargs: Additional parameters

        Returns:
            Dictionary containing execution results
        """
        self.start_time = datetime.utcnow()
        execution.status = PlaybookExecutionStatus.RUNNING
        db.session.commit()

        try:
            self.logger.info(f"Starting playbook: {self.name} for incident {incident.id}")

            # Execute the playbook
            result = await self.execute(incident, **kwargs)

            self.end_time = datetime.utcnow()
            execution_time = (self.end_time - self.start_time).total_seconds()

            # Update execution record
            execution.status = PlaybookExecutionStatus.COMPLETED
            execution.completed_at = self.end_time
            execution.execution_time_seconds = execution_time
            execution.actions_taken = [action.to_dict() for action in self.actions]
            execution.actions_count = len(self.actions)
            execution.result_data = result

            # Update incident response time if not set
            if not incident.response_time_seconds:
                incident.response_time_seconds = int(
                    (self.start_time - incident.created_at).total_seconds()
                )

            db.session.commit()

            self.logger.info(
                f"Playbook completed successfully in {execution_time:.2f}s "
                f"with {len(self.actions)} actions"
            )

            return result

        except Exception as e:
            self.logger.error(f"Playbook execution failed: {e}", exc_info=True)

            self.end_time = datetime.utcnow()
            execution_time = (self.end_time - self.start_time).total_seconds()

            # Update execution record with error
            execution.status = PlaybookExecutionStatus.FAILED
            execution.completed_at = self.end_time
            execution.execution_time_seconds = execution_time
            execution.actions_taken = [action.to_dict() for action in self.actions]
            execution.actions_count = len(self.actions)
            execution.errors = [{
                'message': str(e),
                'type': type(e).__name__,
                'timestamp': datetime.utcnow().isoformat()
            }]

            db.session.commit()

            raise

    async def enrich_threat_intelligence(self, incident: Incident) -> Dict[str, Any]:
        """
        Enrich incident with threat intelligence data

        Args:
            incident: The incident to enrich

        Returns:
            Dictionary containing enrichment data
        """
        enrichment_data = {}

        # Import integrations
        try:
            from backend.integrations.virustotal import VirusTotalClient
            from backend.integrations.abuseipdb import AbuseIPDBClient

            # Enrich IPs
            if incident.source_ip:
                action = self.add_action(
                    'threat_intel',
                    f'Checking IP reputation: {incident.source_ip}'
                )

                try:
                    # Check AbuseIPDB
                    abuseipdb = AbuseIPDBClient()
                    ip_data = await abuseipdb.check_ip(incident.source_ip)
                    enrichment_data['abuseipdb'] = ip_data
                    action.success(ip_data)
                except Exception as e:
                    self.logger.error(f"AbuseIPDB enrichment failed: {e}")
                    action.failed(str(e))

            # Additional enrichment can be added here

        except ImportError as e:
            self.logger.warning(f"Threat intelligence integrations not available: {e}")

        return enrichment_data

    async def notify(self, channel: str, message: str, **kwargs) -> bool:
        """
        Send notification to specified channel

        Args:
            channel: Notification channel (slack, email, etc.)
            message: Message to send
            **kwargs: Additional parameters

        Returns:
            True if notification sent successfully
        """
        action = self.add_action('notify', f'Sending notification to {channel}')

        try:
            if channel == 'slack':
                from backend.integrations.slack import SlackClient
                slack = SlackClient()
                result = await slack.post_message(message, **kwargs)
                action.success(result)
                return True

            elif channel == 'email':
                from backend.integrations.email_client import EmailClient
                email = EmailClient()
                result = await email.send_email(message, **kwargs)
                action.success(result)
                return True

            else:
                action.failed(f'Unknown notification channel: {channel}')
                return False

        except Exception as e:
            self.logger.error(f"Notification failed: {e}")
            action.failed(str(e))
            return False

    async def create_ticket(
        self,
        title: str,
        description: str,
        priority: str = 'Medium',
        **kwargs
    ) -> Optional[Dict[str, Any]]:
        """
        Create ticket in ticketing system

        Args:
            title: Ticket title
            description: Ticket description
            priority: Ticket priority
            **kwargs: Additional parameters

        Returns:
            Ticket data if successful
        """
        action = self.add_action('create_ticket', f'Creating ticket: {title}')

        try:
            from backend.integrations.jira import JiraClient
            jira = JiraClient()
            ticket = await jira.create_ticket(
                title=title,
                description=description,
                priority=priority,
                **kwargs
            )
            action.success(ticket)
            return ticket

        except Exception as e:
            self.logger.error(f"Ticket creation failed: {e}")
            action.failed(str(e))
            return None

    def get_execution_summary(self) -> Dict[str, Any]:
        """Get execution summary"""
        successful_actions = len([a for a in self.actions if a.status == 'success'])
        failed_actions = len([a for a in self.actions if a.status == 'failed'])

        execution_time = 0
        if self.start_time and self.end_time:
            execution_time = (self.end_time - self.start_time).total_seconds()

        return {
            'playbook_name': self.name,
            'total_actions': len(self.actions),
            'successful_actions': successful_actions,
            'failed_actions': failed_actions,
            'success_rate': (successful_actions / len(self.actions) * 100) if self.actions else 0,
            'execution_time_seconds': execution_time,
            'actions': [action.to_dict() for action in self.actions]
        }

    @classmethod
    def get_metadata(cls) -> Dict[str, Any]:
        """Get playbook metadata"""
        return {
            'name': cls.name,
            'description': cls.description,
            'incident_types': cls.incident_types,
            'automation_rate': cls.automation_rate,
            'requires_approval': cls.requires_approval,
            'version': cls.version
        }
