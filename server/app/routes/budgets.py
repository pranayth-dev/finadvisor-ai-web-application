from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from ..models import Budget, Transaction
from ..extensions import db
from datetime import date, datetime
from collections import defaultdict

budgets_bp = Blueprint('budgets', __name__)


def get_spent_for_budget(user_id, category, month, year):
    txns = Transaction.query.filter_by(user_id=user_id, type='expense', category=category).filter(
        Transaction.date >= date(year, month, 1),
    )
    import calendar
    last_day = calendar.monthrange(year, month)[1]
    txns = txns.filter(Transaction.date <= date(year, month, last_day)).all()
    return sum(t.amount for t in txns)


@budgets_bp.route('', methods=['GET'])
@jwt_required()
def get_budgets():
    user_id = int(get_jwt_identity())
    today = date.today()
    month = request.args.get('month', type=int, default=today.month)
    year = request.args.get('year', type=int, default=today.year)

    budgets = Budget.query.filter_by(user_id=user_id, month=month, year=year).all()
    result = []
    for b in budgets:
        spent = get_spent_for_budget(user_id, b.category, month, year)
        result.append(b.to_dict(spent=spent))

    return jsonify({'budgets': result, 'month': month, 'year': year}), 200


@budgets_bp.route('', methods=['POST'])
@jwt_required()
def create_budget():
    user_id = int(get_jwt_identity())
    data = request.get_json()
    if not data:
        return jsonify({'error': 'No data provided'}), 400

    category = data.get('category', '').strip()
    limit_amount = data.get('limit_amount')
    today = date.today()
    month = data.get('month', today.month)
    year = data.get('year', today.year)

    if not category:
        return jsonify({'error': 'Category is required'}), 400
    try:
        limit_amount = float(limit_amount)
        if limit_amount <= 0:
            raise ValueError
    except (TypeError, ValueError):
        return jsonify({'error': 'Limit amount must be a positive number'}), 400
    
    try:
        month = int(month)
        year = int(year)
        if not (1 <= month <= 12) or year < 2000:
            raise ValueError
    except (TypeError, ValueError):
        return jsonify({'error': 'Invalid month or year'}), 400

    existing = Budget.query.filter_by(user_id=user_id, category=category, month=month, year=year).first()
    if existing:
        return jsonify({'error': f'Budget for {category} in {month}/{year} already exists'}), 409

    budget = Budget(
        user_id=user_id,
        category=category,
        limit_amount=limit_amount,
        month=month,
        year=year,
        notes=data.get('notes', '').strip() or None,
    )
    db.session.add(budget)
    db.session.commit()
    spent = get_spent_for_budget(user_id, category, month, year)
    return jsonify({'budget': budget.to_dict(spent=spent), 'message': 'Budget created'}), 201


@budgets_bp.route('/<int:budget_id>', methods=['PUT'])
@jwt_required()
def update_budget(budget_id):
    user_id = int(get_jwt_identity())
    budget = Budget.query.filter_by(id=budget_id, user_id=user_id).first()
    if not budget:
        return jsonify({'error': 'Budget not found'}), 404

    data = request.get_json()
    if data.get('limit_amount') is not None:
        try:
            limit = float(data['limit_amount'])
            if limit <= 0:
                raise ValueError
            budget.limit_amount = limit
        except (TypeError, ValueError):
            return jsonify({'error': 'Limit amount must be a positive number'}), 400
    if data.get('notes') is not None:
        budget.notes = data['notes'].strip() or None

    db.session.commit()
    spent = get_spent_for_budget(user_id, budget.category, budget.month, budget.year)
    return jsonify({'budget': budget.to_dict(spent=spent), 'message': 'Budget updated'}), 200


@budgets_bp.route('/<int:budget_id>', methods=['DELETE'])
@jwt_required()
def delete_budget(budget_id):
    user_id = int(get_jwt_identity())
    budget = Budget.query.filter_by(id=budget_id, user_id=user_id).first()
    if not budget:
        return jsonify({'error': 'Budget not found'}), 404
    db.session.delete(budget)
    db.session.commit()
    return jsonify({'message': 'Budget deleted'}), 200
