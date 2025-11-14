"""
Playbook Management Routes
API endpoints for playbook execution and management
"""
from datetime import datetime
from flask import Blueprint, request, jsonify, current_app

from backend.models import (
    Playbook, PlaybookExecution, PlaybookExecutionStatus,
    Incident, db
)
from backend.auth import (
    login_required, incident_commander_required,
    create_audit_log, get_current_user, PermissionChecker
)

playbooks_bp = Blueprint('playbooks', __name__)


@playbooks_bp.route('', methods=['GET'])
@login_required
def list_playbooks():
    """List all playbooks"""
    playbooks = Playbook.query.filter_by(is_active=True).all()
    return jsonify([playbook.to_dict() for playbook in playbooks]), 200


@playbooks_bp.route('/<int:playbook_id>', methods=['GET'])
@login_required
def get_playbook(playbook_id):
    """Get playbook details"""
    playbook = Playbook.query.get_or_404(playbook_id)
    return jsonify(playbook.to_dict()), 200


@playbooks_bp.route('/<int:playbook_id>/execute', methods=['POST'])
@login_required
def execute_playbook(playbook_id):
    """Execute a playbook for an incident"""
    playbook = Playbook.query.get_or_404(playbook_id)
    user = get_current_user()

    # Check permissions
    if not PermissionChecker.can_execute_playbook(user, playbook):
        return jsonify({
            'error': 'Insufficient permissions',
            'requires_approval': playbook.requires_approval
        }), 403

    data = request.get_json()
    if not data or 'incident_id' not in data:
        return jsonify({'error': 'incident_id required'}), 400

    incident = Incident.query.get_or_404(data['incident_id'])

    # Create execution record
    execution = PlaybookExecution(
        playbook_id=playbook_id,
        incident_id=incident.id,
        status=PlaybookExecutionStatus.PENDING,
        triggered_by=user.username,
        started_at=datetime.utcnow()
    )

    db.session.add(execution)
    db.session.commit()

    # Execute playbook asynchronously
    from backend.orchestrator import execute_playbook_async

    try:
        # Start async execution
        task = execute_playbook_async.delay(execution.id)

        create_audit_log(
            action='execute_playbook',
            resource_type='playbook',
            resource_id=playbook.id,
            details={
                'incident_id': incident.id,
                'execution_id': execution.id,
                'task_id': task.id
            }
        )

        return jsonify({
            'message': 'Playbook execution started',
            'execution_id': execution.id,
            'task_id': task.id,
            'status': 'pending'
        }), 202

    except Exception as e:
        current_app.logger.error(f"Failed to execute playbook: {e}")
        execution.status = PlaybookExecutionStatus.FAILED
        execution.errors = [{'message': str(e)}]
        db.session.commit()

        return jsonify({
            'error': 'Playbook execution failed',
            'message': str(e)
        }), 500


@playbooks_bp.route('/executions/<int:execution_id>', methods=['GET'])
@login_required
def get_execution(execution_id):
    """Get playbook execution status"""
    execution = PlaybookExecution.query.get_or_404(execution_id)
    return jsonify(execution.to_dict()), 200


@playbooks_bp.route('/executions/<int:execution_id>/cancel', methods=['POST'])
@incident_commander_required
def cancel_execution(execution_id):
    """Cancel running playbook execution"""
    execution = PlaybookExecution.query.get_or_404(execution_id)

    if execution.status not in [PlaybookExecutionStatus.PENDING, PlaybookExecutionStatus.RUNNING]:
        return jsonify({'error': 'Cannot cancel completed execution'}), 400

    execution.status = PlaybookExecutionStatus.CANCELLED
    execution.completed_at = datetime.utcnow()
    if execution.started_at:
        execution.execution_time_seconds = (
            execution.completed_at - execution.started_at
        ).total_seconds()

    db.session.commit()

    create_audit_log(
        action='cancel_execution',
        resource_type='playbook_execution',
        resource_id=execution.id
    )

    return jsonify({
        'message': 'Playbook execution cancelled',
        'execution': execution.to_dict()
    }), 200


@playbooks_bp.route('/executions', methods=['GET'])
@login_required
def list_executions():
    """List playbook executions with filtering"""
    # Pagination
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 20, type=int)

    # Filters
    playbook_id = request.args.get('playbook_id', type=int)
    incident_id = request.args.get('incident_id', type=int)
    status = request.args.get('status')

    query = PlaybookExecution.query

    if playbook_id:
        query = query.filter_by(playbook_id=playbook_id)
    if incident_id:
        query = query.filter_by(incident_id=incident_id)
    if status:
        query = query.filter_by(status=PlaybookExecutionStatus[status.upper()])

    query = query.order_by(PlaybookExecution.started_at.desc())

    pagination = query.paginate(page=page, per_page=per_page, error_out=False)

    return jsonify({
        'executions': [execution.to_dict() for execution in pagination.items],
        'total': pagination.total,
        'pages': pagination.pages,
        'current_page': page,
        'per_page': per_page
    }), 200


@playbooks_bp.route('/stats', methods=['GET'])
@login_required
def get_playbook_stats():
    """Get playbook execution statistics"""
    from sqlalchemy import func

    # Execution status breakdown
    status_stats = db.session.query(
        PlaybookExecution.status,
        func.count(PlaybookExecution.id)
    ).group_by(PlaybookExecution.status).all()

    # Most executed playbooks
    top_playbooks = db.session.query(
        Playbook.name,
        func.count(PlaybookExecution.id).label('executions')
    ).join(PlaybookExecution).group_by(Playbook.name).order_by(
        func.count(PlaybookExecution.id).desc()
    ).limit(10).all()

    # Average execution time
    avg_execution_time = db.session.query(
        func.avg(PlaybookExecution.execution_time_seconds)
    ).filter(PlaybookExecution.execution_time_seconds.isnot(None)).scalar()

    # Success rate
    total = PlaybookExecution.query.count()
    successful = PlaybookExecution.query.filter_by(
        status=PlaybookExecutionStatus.COMPLETED
    ).count()
    success_rate = (successful / total * 100) if total > 0 else 0

    return jsonify({
        'by_status': {status.value: count for status, count in status_stats},
        'top_playbooks': [{'name': name, 'executions': count} for name, count in top_playbooks],
        'average_execution_time_seconds': float(avg_execution_time) if avg_execution_time else None,
        'total_executions': total,
        'successful_executions': successful,
        'success_rate': success_rate
    }), 200


@playbooks_bp.route('/<int:playbook_id>/approve', methods=['POST'])
@incident_commander_required
def approve_playbook_execution(playbook_id):
    """Approve high-risk playbook execution"""
    playbook = Playbook.query.get_or_404(playbook_id)

    if not playbook.requires_approval:
        return jsonify({'error': 'This playbook does not require approval'}), 400

    data = request.get_json()
    if not data or 'execution_id' not in data:
        return jsonify({'error': 'execution_id required'}), 400

    execution = PlaybookExecution.query.get_or_404(data['execution_id'])
    user = get_current_user()

    execution.approved_by = user.username
    execution.status = PlaybookExecutionStatus.RUNNING
    db.session.commit()

    # Trigger actual execution
    from backend.orchestrator import execute_playbook_async
    execute_playbook_async.delay(execution.id)

    create_audit_log(
        action='approve_playbook_execution',
        resource_type='playbook_execution',
        resource_id=execution.id,
        details={'playbook_id': playbook_id}
    )

    return jsonify({
        'message': 'Playbook execution approved and started',
        'execution': execution.to_dict()
    }), 200
