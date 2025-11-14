"""
Authentication Routes
Handles user login, logout, and token management
"""
from datetime import datetime
from flask import Blueprint, request, jsonify
from flask_login import login_user, logout_user, current_user

from backend.models import User, db
from backend.auth import generate_token, login_required, admin_required, create_audit_log

auth_bp = Blueprint('auth_routes', __name__)


@auth_bp.route('/login', methods=['POST'])
def login():
    """User login endpoint"""
    data = request.get_json()

    if not data or not data.get('username') or not data.get('password'):
        return jsonify({'error': 'Username and password required'}), 400

    user = User.query.filter_by(username=data['username']).first()

    if not user or not user.check_password(data['password']):
        create_audit_log(
            action='login_failed',
            resource_type='user',
            details={'username': data['username'], 'reason': 'invalid_credentials'}
        )
        return jsonify({'error': 'Invalid credentials'}), 401

    if not user.is_active:
        return jsonify({'error': 'Account is disabled'}), 403

    # Update last login
    user.last_login = datetime.utcnow()
    db.session.commit()

    # Generate JWT token
    token = generate_token(user)

    # Login user session
    login_user(user)

    create_audit_log(
        action='login_success',
        resource_type='user',
        resource_id=user.id,
        details={'username': user.username}
    )

    return jsonify({
        'message': 'Login successful',
        'token': token,
        'user': user.to_dict()
    }), 200


@auth_bp.route('/logout', methods=['POST'])
@login_required
def logout():
    """User logout endpoint"""
    user_id = current_user.id if current_user.is_authenticated else None

    logout_user()

    if user_id:
        create_audit_log(
            action='logout',
            resource_type='user',
            resource_id=user_id
        )

    return jsonify({'message': 'Logout successful'}), 200


@auth_bp.route('/me', methods=['GET'])
@login_required
def get_current_user_info():
    """Get current user information"""
    from backend.auth import get_current_user
    user = get_current_user()

    if not user:
        return jsonify({'error': 'Not authenticated'}), 401

    return jsonify(user.to_dict()), 200


@auth_bp.route('/users', methods=['GET'])
@admin_required
def list_users():
    """List all users (admin only)"""
    users = User.query.all()
    return jsonify([user.to_dict() for user in users]), 200


@auth_bp.route('/users', methods=['POST'])
@admin_required
def create_user():
    """Create new user (admin only)"""
    data = request.get_json()

    required_fields = ['username', 'email', 'password', 'role']
    if not all(field in data for field in required_fields):
        return jsonify({'error': 'Missing required fields'}), 400

    # Check if user already exists
    if User.query.filter_by(username=data['username']).first():
        return jsonify({'error': 'Username already exists'}), 409

    if User.query.filter_by(email=data['email']).first():
        return jsonify({'error': 'Email already exists'}), 409

    # Create user
    from backend.models import UserRole
    user = User(
        username=data['username'],
        email=data['email'],
        role=UserRole[data['role'].upper()],
        full_name=data.get('full_name', ''),
        is_active=data.get('is_active', True)
    )
    user.set_password(data['password'])

    db.session.add(user)
    db.session.commit()

    create_audit_log(
        action='create',
        resource_type='user',
        resource_id=user.id,
        details={'username': user.username, 'role': user.role.value}
    )

    return jsonify({
        'message': 'User created successfully',
        'user': user.to_dict()
    }), 201


@auth_bp.route('/users/<int:user_id>', methods=['PUT'])
@admin_required
def update_user(user_id):
    """Update user (admin only)"""
    user = User.query.get_or_404(user_id)
    data = request.get_json()

    old_values = user.to_dict()

    # Update fields
    if 'email' in data:
        user.email = data['email']
    if 'role' in data:
        from backend.models import UserRole
        user.role = UserRole[data['role'].upper()]
    if 'full_name' in data:
        user.full_name = data['full_name']
    if 'is_active' in data:
        user.is_active = data['is_active']
    if 'password' in data:
        user.set_password(data['password'])

    db.session.commit()

    create_audit_log(
        action='update',
        resource_type='user',
        resource_id=user.id,
        old_values=old_values,
        new_values=user.to_dict()
    )

    return jsonify({
        'message': 'User updated successfully',
        'user': user.to_dict()
    }), 200


@auth_bp.route('/users/<int:user_id>', methods=['DELETE'])
@admin_required
def delete_user(user_id):
    """Delete user (admin only)"""
    user = User.query.get_or_404(user_id)

    # Prevent deleting yourself
    from backend.auth import get_current_user
    current = get_current_user()
    if current.id == user_id:
        return jsonify({'error': 'Cannot delete your own account'}), 400

    username = user.username
    db.session.delete(user)
    db.session.commit()

    create_audit_log(
        action='delete',
        resource_type='user',
        resource_id=user_id,
        details={'username': username}
    )

    return jsonify({'message': 'User deleted successfully'}), 200


@auth_bp.route('/change-password', methods=['POST'])
@login_required
def change_password():
    """Change current user's password"""
    from backend.auth import get_current_user
    user = get_current_user()

    data = request.get_json()
    if not data or not data.get('old_password') or not data.get('new_password'):
        return jsonify({'error': 'Old and new passwords required'}), 400

    if not user.check_password(data['old_password']):
        return jsonify({'error': 'Current password is incorrect'}), 401

    user.set_password(data['new_password'])
    db.session.commit()

    create_audit_log(
        action='change_password',
        resource_type='user',
        resource_id=user.id
    )

    return jsonify({'message': 'Password changed successfully'}), 200
