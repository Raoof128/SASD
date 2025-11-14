"""
Playbook Orchestrator
Handles playbook selection, execution, and coordination
"""
import asyncio
import logging
from typing import Dict, Any, Optional, List
from datetime import datetime

from celery import Celery
from flask import current_app

from backend.models import (
    Incident, Playbook, PlaybookExecution,
    PlaybookExecutionStatus, IncidentStatus, db
)
from backend.decision_engine import DecisionEngine

logger = logging.getLogger(__name__)

# Initialize Celery
celery = Celery('soar_tasks')


@celery.task(bind=True)
def execute_playbook_async(self, execution_id: int):
    """
    Execute playbook asynchronously using Celery

    Args:
        execution_id: PlaybookExecution ID
    """
    from backend.app import create_app
    app = create_app()

    with app.app_context():
        execution = PlaybookExecution.query.get(execution_id)
        if not execution:
            logger.error(f"Execution {execution_id} not found")
            return

        incident = Incident.query.get(execution.incident_id)
        playbook_record = Playbook.query.get(execution.playbook_id)

        if not incident or not playbook_record:
            logger.error(f"Incident or playbook not found for execution {execution_id}")
            execution.status = PlaybookExecutionStatus.FAILED
            execution.errors = [{'message': 'Incident or playbook not found'}]
            db.session.commit()
            return

        try:
            # Get playbook instance
            playbook_instance = get_playbook_instance(playbook_record.name)

            if not playbook_instance:
                raise ValueError(f"Playbook class not found: {playbook_record.name}")

            # Execute playbook
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)

            result = loop.run_until_complete(
                playbook_instance.execute_with_tracking(incident, execution)
            )

            loop.close()

            # Update playbook statistics
            playbook_record.total_executions += 1
            playbook_record.successful_executions += 1
            playbook_record.last_executed_at = datetime.utcnow()

            # Update average execution time
            if playbook_record.average_execution_time:
                playbook_record.average_execution_time = (
                    (playbook_record.average_execution_time * (playbook_record.total_executions - 1)
                     + execution.execution_time_seconds) / playbook_record.total_executions
                )
            else:
                playbook_record.average_execution_time = execution.execution_time_seconds

            # Update incident status
            if incident.status == IncidentStatus.NEW:
                incident.status = IncidentStatus.INVESTIGATING

            db.session.commit()

            logger.info(f"Playbook execution {execution_id} completed successfully")
            return result

        except Exception as e:
            logger.error(f"Playbook execution {execution_id} failed: {e}", exc_info=True)

            playbook_record.total_executions += 1
            playbook_record.failed_executions += 1
            playbook_record.last_executed_at = datetime.utcnow()

            db.session.commit()
            raise


def get_playbook_instance(playbook_name: str):
    """
    Get playbook instance by name

    Args:
        playbook_name: Name of the playbook

    Returns:
        Playbook instance or None
    """
    # Import all playbook classes
    from backend.playbooks.phishing_response import PhishingResponsePlaybook
    from backend.playbooks.malware_containment import MalwareContainmentPlaybook
    from backend.playbooks.account_compromise import AccountCompromisePlaybook
    from backend.playbooks.data_exfiltration import DataExfiltrationPlaybook
    from backend.playbooks.brute_force_defense import BruteForceDefensePlaybook
    from backend.playbooks.vulnerability_remediation import VulnerabilityRemediationPlaybook
    from backend.playbooks.powershell_analysis import PowerShellAnalysisPlaybook
    from backend.playbooks.dns_tunneling import DNSTunnelingPlaybook

    playbook_map = {
        'Phishing Investigation & Containment': PhishingResponsePlaybook,
        'Malware Detection & Containment': MalwareContainmentPlaybook,
        'Account Compromise Response': AccountCompromisePlaybook,
        'Data Exfiltration Detection': DataExfiltrationPlaybook,
        'Brute Force Defense': BruteForceDefensePlaybook,
        'Vulnerability Confirmation & Remediation': VulnerabilityRemediationPlaybook,
        'Suspicious PowerShell Execution': PowerShellAnalysisPlaybook,
        'DNS Tunneling Detection': DNSTunnelingPlaybook
    }

    playbook_class = playbook_map.get(playbook_name)
    return playbook_class() if playbook_class else None


def enrich_incident_data(incident: Incident) -> Dict[str, Any]:
    """
    Enrich incident with threat intelligence and context

    Args:
        incident: Incident to enrich

    Returns:
        Enrichment data dictionary
    """
    enrichment_data = {}

    try:
        from backend.integrations.virustotal import VirusTotalClient
        from backend.integrations.abuseipdb import AbuseIPDBClient

        # Enrich source IP
        if incident.source_ip:
            try:
                abuseipdb = AbuseIPDBClient()
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                ip_data = loop.run_until_complete(abuseipdb.check_ip(incident.source_ip))
                loop.close()

                enrichment_data['source_ip_reputation'] = ip_data
            except Exception as e:
                logger.error(f"IP enrichment failed: {e}")

        # Additional enrichment sources can be added here

    except Exception as e:
        logger.error(f"Incident enrichment failed: {e}")

    return enrichment_data


def auto_select_playbook(incident: Incident) -> Optional[Playbook]:
    """
    Automatically select appropriate playbook for incident

    Args:
        incident: Incident to analyze

    Returns:
        Selected Playbook or None
    """
    # Use decision engine to select playbook
    decision_engine = DecisionEngine()
    playbook_name = decision_engine.select_playbook(incident)

    if playbook_name:
        playbook = Playbook.query.filter_by(
            name=playbook_name,
            is_active=True
        ).first()
        return playbook

    return None


def trigger_auto_response(incident: Incident) -> Optional[PlaybookExecution]:
    """
    Trigger automatic response for incident

    Args:
        incident: Incident to respond to

    Returns:
        PlaybookExecution if triggered, None otherwise
    """
    # Select appropriate playbook
    playbook = auto_select_playbook(incident)

    if not playbook:
        logger.info(f"No playbook selected for incident {incident.id}")
        return None

    # Check if playbook requires approval
    if playbook.requires_approval:
        logger.info(f"Playbook {playbook.name} requires approval for incident {incident.id}")
        # Create pending execution for approval
        execution = PlaybookExecution(
            playbook_id=playbook.id,
            incident_id=incident.id,
            status=PlaybookExecutionStatus.PENDING,
            triggered_by='automatic',
            started_at=datetime.utcnow()
        )
        db.session.add(execution)
        db.session.commit()
        return execution

    # Execute playbook
    execution = PlaybookExecution(
        playbook_id=playbook.id,
        incident_id=incident.id,
        status=PlaybookExecutionStatus.PENDING,
        triggered_by='automatic',
        started_at=datetime.utcnow()
    )

    db.session.add(execution)
    db.session.commit()

    # Trigger async execution
    execute_playbook_async.delay(execution.id)

    logger.info(f"Auto-response triggered: {playbook.name} for incident {incident.id}")
    return execution


def initialize_default_playbooks(app):
    """Initialize default playbooks in database"""
    with app.app_context():
        # Import all playbook classes
        from backend.playbooks.phishing_response import PhishingResponsePlaybook
        from backend.playbooks.malware_containment import MalwareContainmentPlaybook
        from backend.playbooks.account_compromise import AccountCompromisePlaybook
        from backend.playbooks.data_exfiltration import DataExfiltrationPlaybook
        from backend.playbooks.brute_force_defense import BruteForceDefensePlaybook
        from backend.playbooks.vulnerability_remediation import VulnerabilityRemediationPlaybook
        from backend.playbooks.powershell_analysis import PowerShellAnalysisPlaybook
        from backend.playbooks.dns_tunneling import DNSTunnelingPlaybook

        playbook_classes = [
            PhishingResponsePlaybook,
            MalwareContainmentPlaybook,
            AccountCompromisePlaybook,
            DataExfiltrationPlaybook,
            BruteForceDefensePlaybook,
            VulnerabilityRemediationPlaybook,
            PowerShellAnalysisPlaybook,
            DNSTunnelingPlaybook
        ]

        for playbook_class in playbook_classes:
            metadata = playbook_class.get_metadata()

            # Check if playbook already exists
            existing = Playbook.query.filter_by(name=metadata['name']).first()

            if not existing:
                playbook = Playbook(
                    name=metadata['name'],
                    description=metadata['description'],
                    incident_type=','.join(metadata['incident_types']),
                    automation_rate=metadata['automation_rate'],
                    version=metadata['version'],
                    requires_approval=metadata['requires_approval'],
                    is_active=True
                )
                db.session.add(playbook)

        db.session.commit()
        app.logger.info("Default playbooks initialized")
