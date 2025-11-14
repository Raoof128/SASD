"""
SOAR Platform Database Models
SQLAlchemy ORM models for incidents, playbooks, executions, integrations, and audit logs
"""
from datetime import datetime
from enum import Enum as PyEnum
from typing import Optional, Dict, Any
import json

from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import Column, Integer, String, Text, DateTime, Boolean, Float, ForeignKey, Enum, JSON
from sqlalchemy.orm import relationship
from sqlalchemy.ext.declarative import declarative_base
from werkzeug.security import generate_password_hash, check_password_hash

db = SQLAlchemy()


class IncidentStatus(PyEnum):
    """Incident status enumeration"""
    NEW = "new"
    INVESTIGATING = "investigating"
    CONTAINED = "contained"
    REMEDIATED = "remediated"
    CLOSED = "closed"
    FALSE_POSITIVE = "false_positive"


class IncidentSeverity(PyEnum):
    """Incident severity enumeration"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class PlaybookExecutionStatus(PyEnum):
    """Playbook execution status"""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    TIMEOUT = "timeout"
    CANCELLED = "cancelled"


class UserRole(PyEnum):
    """User roles for RBAC"""
    ANALYST = "analyst"
    INCIDENT_COMMANDER = "incident_commander"
    ADMIN = "admin"


class User(db.Model):
    """User model for authentication and RBAC"""
    __tablename__ = 'users'

    id = Column(Integer, primary_key=True)
    username = Column(String(80), unique=True, nullable=False, index=True)
    email = Column(String(120), unique=True, nullable=False, index=True)
    password_hash = Column(String(255), nullable=False)
    role = Column(Enum(UserRole), default=UserRole.ANALYST, nullable=False)
    full_name = Column(String(120))
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    last_login = Column(DateTime)

    # Relationships
    incidents_assigned = relationship('Incident', back_populates='assigned_user', foreign_keys='Incident.assigned_to')
    audit_logs = relationship('AuditLog', back_populates='user')

    def set_password(self, password: str) -> None:
        """Hash and set password"""
        self.password_hash = generate_password_hash(password)

    def check_password(self, password: str) -> bool:
        """Verify password against hash"""
        return check_password_hash(self.password_hash, password)

    def has_permission(self, required_role: UserRole) -> bool:
        """Check if user has required permission level"""
        role_hierarchy = {
            UserRole.ANALYST: 1,
            UserRole.INCIDENT_COMMANDER: 2,
            UserRole.ADMIN: 3
        }
        return role_hierarchy.get(self.role, 0) >= role_hierarchy.get(required_role, 0)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            'id': self.id,
            'username': self.username,
            'email': self.email,
            'role': self.role.value if self.role else None,
            'full_name': self.full_name,
            'is_active': self.is_active,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'last_login': self.last_login.isoformat() if self.last_login else None
        }


class Incident(db.Model):
    """Incident model for security events"""
    __tablename__ = 'incidents'

    id = Column(Integer, primary_key=True)
    alert_id = Column(String(255), unique=True, nullable=False, index=True)
    title = Column(String(255), nullable=False)
    description = Column(Text)
    status = Column(Enum(IncidentStatus), default=IncidentStatus.NEW, nullable=False, index=True)
    severity = Column(Enum(IncidentSeverity), default=IncidentSeverity.MEDIUM, nullable=False, index=True)
    incident_type = Column(String(100), index=True)  # phishing, malware, account_compromise, etc.

    # Source information
    source_ip = Column(String(45))
    destination_ip = Column(String(45))
    source_user = Column(String(255))
    affected_assets = Column(JSON)  # List of affected hosts/users

    # Enrichment data
    enrichment_data = Column(JSON)  # Data from threat intel APIs
    indicators_of_compromise = Column(JSON)  # IOCs extracted

    # Assignment and tracking
    assigned_to = Column(Integer, ForeignKey('users.id'))
    assigned_user = relationship('User', back_populates='incidents_assigned', foreign_keys=[assigned_to])

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    closed_at = Column(DateTime)

    # Metrics
    response_time_seconds = Column(Integer)  # Time from creation to first action
    resolution_time_seconds = Column(Integer)  # Time from creation to closure

    # Relationships
    playbook_executions = relationship('PlaybookExecution', back_populates='incident', cascade='all, delete-orphan')

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            'id': self.id,
            'alert_id': self.alert_id,
            'title': self.title,
            'description': self.description,
            'status': self.status.value if self.status else None,
            'severity': self.severity.value if self.severity else None,
            'incident_type': self.incident_type,
            'source_ip': self.source_ip,
            'destination_ip': self.destination_ip,
            'source_user': self.source_user,
            'affected_assets': self.affected_assets,
            'enrichment_data': self.enrichment_data,
            'indicators_of_compromise': self.indicators_of_compromise,
            'assigned_to': self.assigned_to,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
            'closed_at': self.closed_at.isoformat() if self.closed_at else None,
            'response_time_seconds': self.response_time_seconds,
            'resolution_time_seconds': self.resolution_time_seconds
        }


class Playbook(db.Model):
    """Playbook model for automated security responses"""
    __tablename__ = 'playbooks'

    id = Column(Integer, primary_key=True)
    name = Column(String(255), unique=True, nullable=False, index=True)
    description = Column(Text)
    incident_type = Column(String(100), nullable=False, index=True)
    trigger_rules = Column(JSON)  # Conditions for automatic triggering
    automation_rate = Column(Float, default=0.0)  # Percentage automated (0.0-1.0)

    # Playbook metadata
    version = Column(String(20), default='1.0.0')
    author = Column(String(100))
    is_active = Column(Boolean, default=True)
    requires_approval = Column(Boolean, default=False)  # High-risk actions need approval

    # Performance metrics
    total_executions = Column(Integer, default=0)
    successful_executions = Column(Integer, default=0)
    failed_executions = Column(Integer, default=0)
    average_execution_time = Column(Float)  # In seconds

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    last_executed_at = Column(DateTime)

    # Relationships
    executions = relationship('PlaybookExecution', back_populates='playbook')

    @property
    def success_rate(self) -> float:
        """Calculate success rate"""
        if self.total_executions == 0:
            return 0.0
        return (self.successful_executions / self.total_executions) * 100

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            'id': self.id,
            'name': self.name,
            'description': self.description,
            'incident_type': self.incident_type,
            'trigger_rules': self.trigger_rules,
            'automation_rate': self.automation_rate,
            'version': self.version,
            'author': self.author,
            'is_active': self.is_active,
            'requires_approval': self.requires_approval,
            'total_executions': self.total_executions,
            'successful_executions': self.successful_executions,
            'failed_executions': self.failed_executions,
            'success_rate': self.success_rate,
            'average_execution_time': self.average_execution_time,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
            'last_executed_at': self.last_executed_at.isoformat() if self.last_executed_at else None
        }


class PlaybookExecution(db.Model):
    """Playbook execution tracking"""
    __tablename__ = 'playbook_executions'

    id = Column(Integer, primary_key=True)
    playbook_id = Column(Integer, ForeignKey('playbooks.id'), nullable=False, index=True)
    incident_id = Column(Integer, ForeignKey('incidents.id'), nullable=False, index=True)

    status = Column(Enum(PlaybookExecutionStatus), default=PlaybookExecutionStatus.PENDING, nullable=False, index=True)

    # Execution details
    actions_taken = Column(JSON)  # List of actions performed
    actions_count = Column(Integer, default=0)
    errors = Column(JSON)  # List of errors encountered

    # Timestamps
    started_at = Column(DateTime, default=datetime.utcnow, index=True)
    completed_at = Column(DateTime)
    execution_time_seconds = Column(Float)

    # User interaction
    triggered_by = Column(String(100))  # 'automatic' or username
    approved_by = Column(String(100))

    # Results
    result_data = Column(JSON)  # Structured results from playbook

    # Relationships
    playbook = relationship('Playbook', back_populates='executions')
    incident = relationship('Incident', back_populates='playbook_executions')

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            'id': self.id,
            'playbook_id': self.playbook_id,
            'incident_id': self.incident_id,
            'status': self.status.value if self.status else None,
            'actions_taken': self.actions_taken,
            'actions_count': self.actions_count,
            'errors': self.errors,
            'started_at': self.started_at.isoformat() if self.started_at else None,
            'completed_at': self.completed_at.isoformat() if self.completed_at else None,
            'execution_time_seconds': self.execution_time_seconds,
            'triggered_by': self.triggered_by,
            'approved_by': self.approved_by,
            'result_data': self.result_data
        }


class APIIntegration(db.Model):
    """API integration configuration and tracking"""
    __tablename__ = 'api_integrations'

    id = Column(Integer, primary_key=True)
    service_name = Column(String(100), unique=True, nullable=False, index=True)
    service_type = Column(String(50))  # threat_intel, email, ticketing, etc.
    endpoint = Column(String(255))

    # Credentials (should be encrypted)
    api_key_encrypted = Column(Text)
    additional_config = Column(JSON)  # Service-specific configuration

    # Status tracking
    is_active = Column(Boolean, default=True)
    last_used = Column(DateTime)
    last_error = Column(Text)
    total_calls = Column(Integer, default=0)
    failed_calls = Column(Integer, default=0)

    # Rate limiting
    rate_limit_per_minute = Column(Integer)
    rate_limit_per_day = Column(Integer)

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    @property
    def success_rate(self) -> float:
        """Calculate API success rate"""
        if self.total_calls == 0:
            return 100.0
        return ((self.total_calls - self.failed_calls) / self.total_calls) * 100

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary (without sensitive data)"""
        return {
            'id': self.id,
            'service_name': self.service_name,
            'service_type': self.service_type,
            'endpoint': self.endpoint,
            'is_active': self.is_active,
            'last_used': self.last_used.isoformat() if self.last_used else None,
            'total_calls': self.total_calls,
            'failed_calls': self.failed_calls,
            'success_rate': self.success_rate,
            'rate_limit_per_minute': self.rate_limit_per_minute,
            'rate_limit_per_day': self.rate_limit_per_day,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }


class AuditLog(db.Model):
    """Audit logging for compliance and security"""
    __tablename__ = 'audit_logs'

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id'), index=True)

    # Action details
    action = Column(String(100), nullable=False, index=True)  # create, update, delete, execute, etc.
    resource_type = Column(String(50), nullable=False)  # incident, playbook, user, etc.
    resource_id = Column(Integer)

    # Request details
    ip_address = Column(String(45))
    user_agent = Column(String(255))

    # Change tracking
    details = Column(JSON)  # Additional context about the action
    old_values = Column(JSON)  # Previous state
    new_values = Column(JSON)  # New state

    # Timestamp
    timestamp = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)

    # Relationships
    user = relationship('User', back_populates='audit_logs')

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            'id': self.id,
            'user_id': self.user_id,
            'action': self.action,
            'resource_type': self.resource_type,
            'resource_id': self.resource_id,
            'ip_address': self.ip_address,
            'user_agent': self.user_agent,
            'details': self.details,
            'timestamp': self.timestamp.isoformat() if self.timestamp else None
        }


class Metric(db.Model):
    """System metrics for dashboard"""
    __tablename__ = 'metrics'

    id = Column(Integer, primary_key=True)
    metric_name = Column(String(100), nullable=False, index=True)
    metric_value = Column(Float, nullable=False)
    metric_type = Column(String(50))  # counter, gauge, histogram
    tags = Column(JSON)  # Additional metadata
    timestamp = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            'id': self.id,
            'metric_name': self.metric_name,
            'metric_value': self.metric_value,
            'metric_type': self.metric_type,
            'tags': self.tags,
            'timestamp': self.timestamp.isoformat() if self.timestamp else None
        }
