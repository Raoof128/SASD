"""
Incident Management Routes
CRUD operations for security incidents
"""
from datetime import datetime
from flask import Blueprint, request, jsonify
from sqlalchemy import desc, or_

from backend.models import Incident, IncidentStatus, IncidentSeverity, db
from backend.auth import login_required, create_audit_log, get_current_user, PermissionChecker

incidents_bp = Blueprint('incidents', __name__)


@incidents_bp.route('', methods=['GET'])
@login_required
def list_incidents():
    """List all incidents with filtering and pagination"""
    user = get_current_user()

    # Pagination
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 20, type=int)

    # Filters
    status = request.args.get('status')
    severity = request.args.get('severity')
    incident_type = request.args.get('type')
    assigned_to = request.args.get('assigned_to', type=int)
    search = request.args.get('search')

    # Build query
    query = Incident.query

    # Apply filters
    if status:
        query = query.filter(Incident.status == IncidentStatus[status.upper()])
    if severity:
        query = query.filter(Incident.severity == IncidentSeverity[severity.upper()])
    if incident_type:
        query = query.filter(Incident.incident_type == incident_type)
    if assigned_to:
        query = query.filter(Incident.assigned_to == assigned_to)
    if search:
        query = query.filter(
            or_(
                Incident.title.ilike(f'%{search}%'),
                Incident.description.ilike(f'%{search}%'),
                Incident.alert_id.ilike(f'%{search}%')
            )
        )

    # Order by creation date (newest first)
    query = query.order_by(desc(Incident.created_at))

    # Paginate
    pagination = query.paginate(page=page, per_page=per_page, error_out=False)

    return jsonify({
        'incidents': [incident.to_dict() for incident in pagination.items],
        'total': pagination.total,
        'pages': pagination.pages,
        'current_page': page,
        'per_page': per_page
    }), 200


@incidents_bp.route('/<int:incident_id>', methods=['GET'])
@login_required
def get_incident(incident_id):
    """Get incident details"""
    incident = Incident.query.get_or_404(incident_id)
    user = get_current_user()

    if not PermissionChecker.can_view_incident(user, incident):
        return jsonify({'error': 'Insufficient permissions'}), 403

    return jsonify(incident.to_dict()), 200


@incidents_bp.route('', methods=['POST'])
@login_required
def create_incident():
    """Create new incident (typically from SIEM webhook)"""
    data = request.get_json()

    required_fields = ['alert_id', 'title', 'severity', 'incident_type']
    if not all(field in data for field in required_fields):
        return jsonify({'error': 'Missing required fields'}), 400

    # Check for duplicate alert_id
    if Incident.query.filter_by(alert_id=data['alert_id']).first():
        return jsonify({'error': 'Incident with this alert_id already exists'}), 409

    incident = Incident(
        alert_id=data['alert_id'],
        title=data['title'],
        description=data.get('description', ''),
        severity=IncidentSeverity[data['severity'].upper()],
        incident_type=data['incident_type'],
        status=IncidentStatus.NEW,
        source_ip=data.get('source_ip'),
        destination_ip=data.get('destination_ip'),
        source_user=data.get('source_user'),
        affected_assets=data.get('affected_assets', []),
        enrichment_data=data.get('enrichment_data', {}),
        indicators_of_compromise=data.get('iocs', [])
    )

    db.session.add(incident)
    db.session.commit()

    create_audit_log(
        action='create',
        resource_type='incident',
        resource_id=incident.id,
        details={'alert_id': incident.alert_id, 'severity': incident.severity.value}
    )

    return jsonify({
        'message': 'Incident created successfully',
        'incident': incident.to_dict()
    }), 201


@incidents_bp.route('/<int:incident_id>', methods=['PUT'])
@login_required
def update_incident(incident_id):
    """Update incident"""
    incident = Incident.query.get_or_404(incident_id)
    user = get_current_user()

    if not PermissionChecker.can_modify_incident(user, incident):
        return jsonify({'error': 'Insufficient permissions'}), 403

    data = request.get_json()
    old_values = incident.to_dict()

    # Update fields
    if 'title' in data:
        incident.title = data['title']
    if 'description' in data:
        incident.description = data['description']
    if 'status' in data:
        incident.status = IncidentStatus[data['status'].upper()]
        if incident.status == IncidentStatus.CLOSED:
            incident.closed_at = datetime.utcnow()
            if incident.created_at:
                incident.resolution_time_seconds = int(
                    (incident.closed_at - incident.created_at).total_seconds()
                )
    if 'severity' in data:
        incident.severity = IncidentSeverity[data['severity'].upper()]
    if 'assigned_to' in data:
        incident.assigned_to = data['assigned_to']
    if 'enrichment_data' in data:
        incident.enrichment_data = data['enrichment_data']
    if 'iocs' in data:
        incident.indicators_of_compromise = data['iocs']

    incident.updated_at = datetime.utcnow()
    db.session.commit()

    create_audit_log(
        action='update',
        resource_type='incident',
        resource_id=incident.id,
        old_values=old_values,
        new_values=incident.to_dict()
    )

    return jsonify({
        'message': 'Incident updated successfully',
        'incident': incident.to_dict()
    }), 200


@incidents_bp.route('/<int:incident_id>', methods=['DELETE'])
@login_required
def delete_incident(incident_id):
    """Delete incident"""
    incident = Incident.query.get_or_404(incident_id)
    user = get_current_user()

    if not PermissionChecker.can_modify_incident(user, incident):
        return jsonify({'error': 'Insufficient permissions'}), 403

    alert_id = incident.alert_id
    db.session.delete(incident)
    db.session.commit()

    create_audit_log(
        action='delete',
        resource_type='incident',
        resource_id=incident_id,
        details={'alert_id': alert_id}
    )

    return jsonify({'message': 'Incident deleted successfully'}), 200


@incidents_bp.route('/<int:incident_id>/assign', methods=['POST'])
@login_required
def assign_incident(incident_id):
    """Assign incident to user"""
    incident = Incident.query.get_or_404(incident_id)
    data = request.get_json()

    if 'user_id' not in data:
        return jsonify({'error': 'user_id required'}), 400

    from backend.models import User
    user = User.query.get(data['user_id'])
    if not user:
        return jsonify({'error': 'User not found'}), 404

    old_assigned_to = incident.assigned_to
    incident.assigned_to = data['user_id']
    incident.updated_at = datetime.utcnow()

    db.session.commit()

    create_audit_log(
        action='assign',
        resource_type='incident',
        resource_id=incident.id,
        details={
            'old_assigned_to': old_assigned_to,
            'new_assigned_to': data['user_id']
        }
    )

    return jsonify({
        'message': 'Incident assigned successfully',
        'incident': incident.to_dict()
    }), 200


@incidents_bp.route('/<int:incident_id>/enrich', methods=['POST'])
@login_required
def enrich_incident(incident_id):
    """Manually trigger enrichment for incident"""
    incident = Incident.query.get_or_404(incident_id)

    # Import orchestrator for enrichment
    from backend.orchestrator import enrich_incident_data

    try:
        enrichment_data = enrich_incident_data(incident)
        incident.enrichment_data = enrichment_data
        incident.updated_at = datetime.utcnow()

        db.session.commit()

        create_audit_log(
            action='enrich',
            resource_type='incident',
            resource_id=incident.id,
            details={'enrichment_sources': list(enrichment_data.keys())}
        )

        return jsonify({
            'message': 'Incident enriched successfully',
            'enrichment_data': enrichment_data
        }), 200

    except Exception as e:
        return jsonify({
            'error': 'Enrichment failed',
            'message': str(e)
        }), 500


@incidents_bp.route('/stats', methods=['GET'])
@login_required
def get_incident_stats():
    """Get incident statistics"""
    from sqlalchemy import func

    # Status breakdown
    status_stats = db.session.query(
        Incident.status,
        func.count(Incident.id)
    ).group_by(Incident.status).all()

    # Severity breakdown
    severity_stats = db.session.query(
        Incident.severity,
        func.count(Incident.id)
    ).group_by(Incident.severity).all()

    # Type breakdown
    type_stats = db.session.query(
        Incident.incident_type,
        func.count(Incident.id)
    ).group_by(Incident.incident_type).all()

    # Average response time
    avg_response_time = db.session.query(
        func.avg(Incident.response_time_seconds)
    ).scalar()

    # Average resolution time
    avg_resolution_time = db.session.query(
        func.avg(Incident.resolution_time_seconds)
    ).filter(Incident.resolution_time_seconds.isnot(None)).scalar()

    return jsonify({
        'by_status': {status.value: count for status, count in status_stats},
        'by_severity': {severity.value: count for severity, count in severity_stats},
        'by_type': {itype: count for itype, count in type_stats},
        'average_response_time_seconds': float(avg_response_time) if avg_response_time else None,
        'average_resolution_time_seconds': float(avg_resolution_time) if avg_resolution_time else None,
        'total_incidents': Incident.query.count()
    }), 200
