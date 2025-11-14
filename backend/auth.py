"""
SOAR Platform Authentication & RBAC
Handles user authentication, session management, and role-based access control
"""
from functools import wraps
from typing import Optional, Callable
from datetime import datetime

from flask import request, jsonify, g, current_app
from flask_login import LoginManager, current_user
import jwt

from backend.models import User, UserRole, db, AuditLog

login_manager = LoginManager()


@login_manager.user_loader
def load_user(user_id: int) -> Optional[User]:
    """Load user by ID for Flask-Login"""
    return User.query.get(int(user_id))


def generate_token(user: User) -> str:
    """Generate JWT token for API authentication"""
    import time
    payload = {
        'user_id': user.id,
        'username': user.username,
        'role': user.role.value if user.role else None,
        'exp': int(time.time()) + current_app.config.get('PERMANENT_SESSION_LIFETIME', 3600).total_seconds()
    }
    return jwt.encode(payload, current_app.config['SECRET_KEY'], algorithm='HS256')


def verify_token(token: str) -> Optional[dict]:
    """Verify and decode JWT token"""
    try:
        payload = jwt.decode(token, current_app.config['SECRET_KEY'], algorithms=['HS256'])
        return payload
    except jwt.ExpiredSignatureError:
        return None
    except jwt.InvalidTokenError:
        return None


def get_current_user() -> Optional[User]:
    """Get current authenticated user from token or session"""
    # Try Flask-Login first
    if current_user.is_authenticated:
        return current_user

    # Try JWT token from Authorization header
    auth_header = request.headers.get('Authorization')
    if auth_header and auth_header.startswith('Bearer '):
        token = auth_header.split(' ')[1]
        payload = verify_token(token)
        if payload:
            user = User.query.get(payload['user_id'])
            if user and user.is_active:
                return user

    return None


def login_required(f: Callable) -> Callable:
    """Decorator to require authentication"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        user = get_current_user()
        if not user:
            return jsonify({'error': 'Authentication required'}), 401

        g.current_user = user
        return f(*args, **kwargs)

    return decorated_function


def role_required(required_role: UserRole) -> Callable:
    """Decorator to require specific role"""
    def decorator(f: Callable) -> Callable:
        @wraps(f)
        def decorated_function(*args, **kwargs):
            user = get_current_user()
            if not user:
                return jsonify({'error': 'Authentication required'}), 401

            if not user.has_permission(required_role):
                return jsonify({
                    'error': 'Insufficient permissions',
                    'required_role': required_role.value,
                    'your_role': user.role.value if user.role else None
                }), 403

            g.current_user = user
            return f(*args, **kwargs)

        return decorated_function
    return decorator


def admin_required(f: Callable) -> Callable:
    """Decorator to require admin role"""
    return role_required(UserRole.ADMIN)(f)


def incident_commander_required(f: Callable) -> Callable:
    """Decorator to require incident commander or higher role"""
    return role_required(UserRole.INCIDENT_COMMANDER)(f)


def create_audit_log(
    action: str,
    resource_type: str,
    resource_id: Optional[int] = None,
    details: Optional[dict] = None,
    old_values: Optional[dict] = None,
    new_values: Optional[dict] = None
) -> AuditLog:
    """Create audit log entry"""
    user = get_current_user()

    audit_log = AuditLog(
        user_id=user.id if user else None,
        action=action,
        resource_type=resource_type,
        resource_id=resource_id,
        ip_address=request.remote_addr,
        user_agent=request.headers.get('User-Agent'),
        details=details,
        old_values=old_values,
        new_values=new_values,
        timestamp=datetime.utcnow()
    )

    db.session.add(audit_log)
    db.session.commit()

    return audit_log


def audit_action(action: str, resource_type: str):
    """Decorator to automatically log actions"""
    def decorator(f: Callable) -> Callable:
        @wraps(f)
        def decorated_function(*args, **kwargs):
            # Execute the function
            result = f(*args, **kwargs)

            # Create audit log
            resource_id = kwargs.get('id') or kwargs.get('incident_id') or kwargs.get('playbook_id')
            create_audit_log(
                action=action,
                resource_type=resource_type,
                resource_id=resource_id,
                details={'endpoint': request.endpoint, 'method': request.method}
            )

            return result

        return decorated_function
    return decorator


class PermissionChecker:
    """Helper class for checking permissions"""

    @staticmethod
    def can_view_incident(user: User, incident) -> bool:
        """Check if user can view incident"""
        if user.role == UserRole.ADMIN:
            return True
        if user.role == UserRole.INCIDENT_COMMANDER:
            return True
        if user.role == UserRole.ANALYST:
            # Analysts can view incidents assigned to them or unassigned
            return incident.assigned_to is None or incident.assigned_to == user.id
        return False

    @staticmethod
    def can_modify_incident(user: User, incident) -> bool:
        """Check if user can modify incident"""
        if user.role == UserRole.ADMIN:
            return True
        if user.role == UserRole.INCIDENT_COMMANDER:
            return True
        if user.role == UserRole.ANALYST:
            # Analysts can only modify incidents assigned to them
            return incident.assigned_to == user.id
        return False

    @staticmethod
    def can_execute_playbook(user: User, playbook) -> bool:
        """Check if user can execute playbook"""
        if user.role == UserRole.ADMIN:
            return True
        if user.role == UserRole.INCIDENT_COMMANDER:
            return True
        if user.role == UserRole.ANALYST:
            # Analysts can execute non-critical playbooks
            return not playbook.requires_approval
        return False

    @staticmethod
    def can_approve_playbook(user: User) -> bool:
        """Check if user can approve high-risk playbooks"""
        return user.role in [UserRole.INCIDENT_COMMANDER, UserRole.ADMIN]

    @staticmethod
    def can_manage_users(user: User) -> bool:
        """Check if user can manage other users"""
        return user.role == UserRole.ADMIN

    @staticmethod
    def can_manage_integrations(user: User) -> bool:
        """Check if user can manage API integrations"""
        return user.role == UserRole.ADMIN

    @staticmethod
    def can_view_audit_logs(user: User) -> bool:
        """Check if user can view audit logs"""
        return user.role in [UserRole.INCIDENT_COMMANDER, UserRole.ADMIN]


def init_default_users(app):
    """Initialize default users if none exist"""
    with app.app_context():
        # Check if any users exist
        if User.query.count() == 0:
            # Create default admin user
            admin = User(
                username='admin',
                email='admin@soar-platform.local',
                role=UserRole.ADMIN,
                full_name='System Administrator',
                is_active=True
            )
            admin.set_password('changeme')  # Must be changed on first login

            # Create default analyst user
            analyst = User(
                username='analyst',
                email='analyst@soar-platform.local',
                role=UserRole.ANALYST,
                full_name='SOC Analyst',
                is_active=True
            )
            analyst.set_password('changeme')

            # Create default incident commander
            commander = User(
                username='commander',
                email='commander@soar-platform.local',
                role=UserRole.INCIDENT_COMMANDER,
                full_name='Incident Commander',
                is_active=True
            )
            commander.set_password('changeme')

            db.session.add_all([admin, analyst, commander])
            db.session.commit()

            app.logger.info("Default users created: admin, analyst, commander (password: changeme)")
