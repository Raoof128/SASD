"""
Dashboard Routes
API endpoints for metrics, statistics, and dashboard data
"""
from datetime import datetime, timedelta
from flask import Blueprint, request, jsonify
from sqlalchemy import func, and_

from backend.models import (
    Incident, IncidentStatus, IncidentSeverity,
    Playbook, PlaybookExecution, PlaybookExecutionStatus,
    Metric, AuditLog, db
)
from backend.auth import login_required, PermissionChecker, get_current_user

dashboard_bp = Blueprint('dashboard', __name__)


@dashboard_bp.route('/overview', methods=['GET'])
@login_required
def get_overview():
    """Get dashboard overview statistics"""
    # Time range filter (default: last 30 days)
    days = request.args.get('days', 30, type=int)
    start_date = datetime.utcnow() - timedelta(days=days)

    # Incident counts
    total_incidents = Incident.query.filter(
        Incident.created_at >= start_date
    ).count()

    new_incidents = Incident.query.filter(
        and_(
            Incident.status == IncidentStatus.NEW,
            Incident.created_at >= start_date
        )
    ).count()

    closed_incidents = Incident.query.filter(
        and_(
            Incident.status == IncidentStatus.CLOSED,
            Incident.created_at >= start_date
        )
    ).count()

    # Severity breakdown
    critical_incidents = Incident.query.filter(
        and_(
            Incident.severity == IncidentSeverity.CRITICAL,
            Incident.created_at >= start_date
        )
    ).count()

    high_incidents = Incident.query.filter(
        and_(
            Incident.severity == IncidentSeverity.HIGH,
            Incident.created_at >= start_date
        )
    ).count()

    # Playbook executions
    total_executions = PlaybookExecution.query.filter(
        PlaybookExecution.started_at >= start_date
    ).count()

    successful_executions = PlaybookExecution.query.filter(
        and_(
            PlaybookExecution.status == PlaybookExecutionStatus.COMPLETED,
            PlaybookExecution.started_at >= start_date
        )
    ).count()

    # MTTR (Mean Time To Response)
    avg_response_time = db.session.query(
        func.avg(Incident.response_time_seconds)
    ).filter(
        and_(
            Incident.response_time_seconds.isnot(None),
            Incident.created_at >= start_date
        )
    ).scalar()

    # MTTR (Mean Time To Resolution)
    avg_resolution_time = db.session.query(
        func.avg(Incident.resolution_time_seconds)
    ).filter(
        and_(
            Incident.resolution_time_seconds.isnot(None),
            Incident.created_at >= start_date
        )
    ).scalar()

    # Automation rate
    automation_rate = (successful_executions / total_incidents * 100) if total_incidents > 0 else 0

    # Cost savings calculation (assuming $100/hour analyst rate)
    analyst_hourly_rate = 100
    manual_avg_time_minutes = 45  # Manual handling time
    automated_avg_time_minutes = avg_response_time / 60 if avg_response_time else 5

    time_saved_minutes = successful_executions * (manual_avg_time_minutes - automated_avg_time_minutes)
    cost_savings = (time_saved_minutes / 60) * analyst_hourly_rate

    return jsonify({
        'time_range_days': days,
        'incidents': {
            'total': total_incidents,
            'new': new_incidents,
            'closed': closed_incidents,
            'critical': critical_incidents,
            'high': high_incidents,
            'closure_rate': (closed_incidents / total_incidents * 100) if total_incidents > 0 else 0
        },
        'playbooks': {
            'total_executions': total_executions,
            'successful_executions': successful_executions,
            'success_rate': (successful_executions / total_executions * 100) if total_executions > 0 else 0
        },
        'performance': {
            'avg_response_time_seconds': float(avg_response_time) if avg_response_time else None,
            'avg_response_time_minutes': float(avg_response_time / 60) if avg_response_time else None,
            'avg_resolution_time_seconds': float(avg_resolution_time) if avg_resolution_time else None,
            'avg_resolution_time_minutes': float(avg_resolution_time / 60) if avg_resolution_time else None,
            'automation_rate': automation_rate
        },
        'roi': {
            'time_saved_hours': time_saved_minutes / 60,
            'cost_savings_usd': cost_savings,
            'incidents_automated': successful_executions
        }
    }), 200


@dashboard_bp.route('/incidents/trend', methods=['GET'])
@login_required
def get_incident_trend():
    """Get incident trend data over time"""
    days = request.args.get('days', 30, type=int)
    start_date = datetime.utcnow() - timedelta(days=days)

    # Group by date
    trend_data = db.session.query(
        func.date(Incident.created_at).label('date'),
        func.count(Incident.id).label('count')
    ).filter(
        Incident.created_at >= start_date
    ).group_by(
        func.date(Incident.created_at)
    ).order_by('date').all()

    return jsonify({
        'trend': [
            {
                'date': date.isoformat() if date else None,
                'count': count
            }
            for date, count in trend_data
        ]
    }), 200


@dashboard_bp.route('/incidents/by-severity', methods=['GET'])
@login_required
def get_incidents_by_severity():
    """Get incident distribution by severity"""
    days = request.args.get('days', 30, type=int)
    start_date = datetime.utcnow() - timedelta(days=days)

    severity_data = db.session.query(
        Incident.severity,
        func.count(Incident.id).label('count')
    ).filter(
        Incident.created_at >= start_date
    ).group_by(Incident.severity).all()

    return jsonify({
        'data': [
            {
                'severity': severity.value if severity else 'unknown',
                'count': count
            }
            for severity, count in severity_data
        ]
    }), 200


@dashboard_bp.route('/incidents/by-type', methods=['GET'])
@login_required
def get_incidents_by_type():
    """Get incident distribution by type"""
    days = request.args.get('days', 30, type=int)
    start_date = datetime.utcnow() - timedelta(days=days)

    type_data = db.session.query(
        Incident.incident_type,
        func.count(Incident.id).label('count')
    ).filter(
        Incident.created_at >= start_date
    ).group_by(Incident.incident_type).all()

    return jsonify({
        'data': [
            {
                'type': incident_type,
                'count': count
            }
            for incident_type, count in type_data
        ]
    }), 200


@dashboard_bp.route('/playbooks/performance', methods=['GET'])
@login_required
def get_playbook_performance():
    """Get playbook performance metrics"""
    playbook_stats = db.session.query(
        Playbook.name,
        Playbook.incident_type,
        func.count(PlaybookExecution.id).label('total_executions'),
        func.sum(
            func.cast(PlaybookExecution.status == PlaybookExecutionStatus.COMPLETED, db.Integer)
        ).label('successful'),
        func.avg(PlaybookExecution.execution_time_seconds).label('avg_time')
    ).join(
        PlaybookExecution
    ).group_by(
        Playbook.id, Playbook.name, Playbook.incident_type
    ).all()

    return jsonify({
        'playbooks': [
            {
                'name': name,
                'incident_type': incident_type,
                'total_executions': total,
                'successful_executions': successful or 0,
                'success_rate': (successful / total * 100) if total > 0 and successful else 0,
                'avg_execution_time_seconds': float(avg_time) if avg_time else None
            }
            for name, incident_type, total, successful, avg_time in playbook_stats
        ]
    }), 200


@dashboard_bp.route('/activity/recent', methods=['GET'])
@login_required
def get_recent_activity():
    """Get recent system activity"""
    user = get_current_user()

    limit = request.args.get('limit', 50, type=int)

    if PermissionChecker.can_view_audit_logs(user):
        # Show all audit logs for authorized users
        activities = AuditLog.query.order_by(
            AuditLog.timestamp.desc()
        ).limit(limit).all()
    else:
        # Show only user's own activities
        activities = AuditLog.query.filter_by(
            user_id=user.id
        ).order_by(
            AuditLog.timestamp.desc()
        ).limit(limit).all()

    return jsonify({
        'activities': [activity.to_dict() for activity in activities]
    }), 200


@dashboard_bp.route('/metrics/record', methods=['POST'])
@login_required
def record_metric():
    """Record a custom metric"""
    data = request.get_json()

    required_fields = ['metric_name', 'metric_value']
    if not all(field in data for field in required_fields):
        return jsonify({'error': 'Missing required fields'}), 400

    metric = Metric(
        metric_name=data['metric_name'],
        metric_value=data['metric_value'],
        metric_type=data.get('metric_type', 'gauge'),
        tags=data.get('tags', {}),
        timestamp=datetime.utcnow()
    )

    db.session.add(metric)
    db.session.commit()

    return jsonify({
        'message': 'Metric recorded successfully',
        'metric': metric.to_dict()
    }), 201


@dashboard_bp.route('/metrics/query', methods=['GET'])
@login_required
def query_metrics():
    """Query metrics"""
    metric_name = request.args.get('name')
    hours = request.args.get('hours', 24, type=int)

    if not metric_name:
        return jsonify({'error': 'metric_name required'}), 400

    start_time = datetime.utcnow() - timedelta(hours=hours)

    metrics = Metric.query.filter(
        and_(
            Metric.metric_name == metric_name,
            Metric.timestamp >= start_time
        )
    ).order_by(Metric.timestamp).all()

    return jsonify({
        'metrics': [metric.to_dict() for metric in metrics]
    }), 200


@dashboard_bp.route('/health', methods=['GET'])
def health_check():
    """Comprehensive health check"""
    health_status = {
        'status': 'healthy',
        'timestamp': datetime.utcnow().isoformat(),
        'components': {}
    }

    # Database health
    try:
        db.session.execute('SELECT 1')
        health_status['components']['database'] = 'healthy'
    except Exception as e:
        health_status['status'] = 'unhealthy'
        health_status['components']['database'] = f'unhealthy: {str(e)}'

    # Check active playbooks
    try:
        active_playbooks = Playbook.query.filter_by(is_active=True).count()
        health_status['components']['playbooks'] = f'healthy ({active_playbooks} active)'
    except Exception as e:
        health_status['components']['playbooks'] = f'error: {str(e)}'

    return jsonify(health_status), 200 if health_status['status'] == 'healthy' else 503
