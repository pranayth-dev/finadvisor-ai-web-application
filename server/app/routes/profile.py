from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from ..models import User
from ..extensions import db

profile_bp = Blueprint('profile', __name__)


@profile_bp.route('', methods=['GET'])
@jwt_required()
def get_profile():
    user_id = int(get_jwt_identity())
    user = db.session.get(User, user_id)
    if not user:
        return jsonify({'error': 'User not found'}), 404
    return jsonify({'user': user.to_dict()}), 200


@profile_bp.route('', methods=['PUT'])
@jwt_required()
def update_profile():
    user_id = int(get_jwt_identity())
    user = db.session.get(User, user_id)
    if not user:
        return jsonify({'error': 'User not found'}), 404

    data = request.get_json()
    allowed = ['first_name', 'last_name', 'phone', 'currency', 'monthly_income_preference',
               'theme', 'account_mode', 'notification_budget_alerts',
               'notification_goal_milestones', 'notification_monthly_summary']
    
    for field in allowed:
        if field in data:
            val = data[field]
            if field in ['first_name', 'last_name'] and not str(val).strip():
                return jsonify({'error': f'{field} cannot be empty'}), 400
            setattr(user, field, val)

    db.session.commit()
    return jsonify({'user': user.to_dict(), 'message': 'Profile updated'}), 200


@profile_bp.route('/settings', methods=['GET'])
@jwt_required()
def get_settings():
    user_id = int(get_jwt_identity())
    user = db.session.get(User, user_id)
    if not user:
        return jsonify({'error': 'User not found'}), 404
    return jsonify({
        'currency': user.currency,
        'theme': user.theme,
        'account_mode': user.account_mode,
        'monthly_income_preference': user.monthly_income_preference,
        'notification_budget_alerts': user.notification_budget_alerts,
        'notification_goal_milestones': user.notification_goal_milestones,
        'notification_monthly_summary': user.notification_monthly_summary,
    }), 200


@profile_bp.route('/settings', methods=['PUT'])
@jwt_required()
def update_settings():
    return update_profile()


@profile_bp.route('/delete', methods=['DELETE'])
@jwt_required()
def delete_account():
    user_id = int(get_jwt_identity())
    data = request.get_json()
    
    user = db.session.get(User, user_id)
    if not user:
        return jsonify({'error': 'User not found'}), 404

    if not data or not data.get('password'):
        return jsonify({'error': 'Password confirmation required'}), 400

    if not user.check_password(data['password']):
        return jsonify({'error': 'Incorrect password'}), 401

    user.is_active = False
    db.session.commit()
    return jsonify({'message': 'Account deactivated successfully'}), 200
