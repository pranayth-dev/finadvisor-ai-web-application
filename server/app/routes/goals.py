from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from ..models import SavingsGoal
from ..extensions import db
from datetime import date, datetime

goals_bp = Blueprint('goals', __name__)


@goals_bp.route('', methods=['GET'])
@jwt_required()
def get_goals():
    user_id = int(get_jwt_identity())
    include_completed = request.args.get('include_completed', 'false').lower() == 'true'
    query = SavingsGoal.query.filter_by(user_id=user_id)
    if not include_completed:
        query = query.filter_by(is_completed=False)
    goals = query.order_by(SavingsGoal.created_at.desc()).all()
    return jsonify({'goals': [g.to_dict() for g in goals]}), 200


@goals_bp.route('', methods=['POST'])
@jwt_required()
def create_goal():
    user_id = int(get_jwt_identity())
    data = request.get_json()
    if not data:
        return jsonify({'error': 'No data provided'}), 400

    name = data.get('name', '').strip()
    target_amount = data.get('target_amount')
    current_amount = data.get('current_amount', 0)

    if not name:
        return jsonify({'error': 'Goal name is required'}), 400
    try:
        target_amount = float(target_amount)
        if target_amount <= 0:
            raise ValueError
    except (TypeError, ValueError):
        return jsonify({'error': 'Target amount must be a positive number'}), 400
    try:
        current_amount = float(current_amount)
        if current_amount < 0:
            current_amount = 0
    except (TypeError, ValueError):
        current_amount = 0

    target_date = None
    if data.get('target_date'):
        try:
            target_date = datetime.strptime(data['target_date'], '%Y-%m-%d').date()
        except ValueError:
            return jsonify({'error': 'Invalid target_date format (use YYYY-MM-DD)'}), 400

    goal = SavingsGoal(
        user_id=user_id,
        name=name,
        target_amount=target_amount,
        current_amount=current_amount,
        target_date=target_date,
        category=data.get('category', 'Other'),
        notes=data.get('notes', '').strip() or None,
        is_completed=current_amount >= target_amount,
    )
    db.session.add(goal)
    db.session.commit()
    return jsonify({'goal': goal.to_dict(), 'message': 'Savings goal created'}), 201


@goals_bp.route('/<int:goal_id>', methods=['PUT'])
@jwt_required()
def update_goal(goal_id):
    user_id = int(get_jwt_identity())
    goal = SavingsGoal.query.filter_by(id=goal_id, user_id=user_id).first()
    if not goal:
        return jsonify({'error': 'Savings goal not found'}), 404

    data = request.get_json()
    if data.get('name'):
        goal.name = data['name'].strip()
    if data.get('target_amount') is not None:
        try:
            ta = float(data['target_amount'])
            if ta <= 0:
                raise ValueError
            goal.target_amount = ta
        except (TypeError, ValueError):
            return jsonify({'error': 'Target amount must be a positive number'}), 400
    if data.get('current_amount') is not None:
        try:
            ca = float(data['current_amount'])
            if ca < 0:
                ca = 0
            goal.current_amount = ca
        except (TypeError, ValueError):
            return jsonify({'error': 'Current amount must be a non-negative number'}), 400
    if data.get('target_date') is not None:
        if data['target_date'] == '':
            goal.target_date = None
        else:
            try:
                goal.target_date = datetime.strptime(data['target_date'], '%Y-%m-%d').date()
            except ValueError:
                return jsonify({'error': 'Invalid target_date format'}), 400
    if data.get('category'):
        goal.category = data['category']
    if data.get('notes') is not None:
        goal.notes = data['notes'].strip() or None
    if data.get('is_completed') is not None:
        goal.is_completed = bool(data['is_completed'])
    else:
        goal.is_completed = goal.current_amount >= goal.target_amount

    db.session.commit()
    return jsonify({'goal': goal.to_dict(), 'message': 'Savings goal updated'}), 200


@goals_bp.route('/<int:goal_id>', methods=['DELETE'])
@jwt_required()
def delete_goal(goal_id):
    user_id = int(get_jwt_identity())
    goal = SavingsGoal.query.filter_by(id=goal_id, user_id=user_id).first()
    if not goal:
        return jsonify({'error': 'Savings goal not found'}), 404
    db.session.delete(goal)
    db.session.commit()
    return jsonify({'message': 'Savings goal deleted'}), 200
