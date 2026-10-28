from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from ..models import Transaction
from ..extensions import db
from datetime import date, datetime
from sqlalchemy import and_

transactions_bp = Blueprint('transactions', __name__)

VALID_CATEGORIES = [
    'Salary', 'Freelancing', 'Business', 'Investments', 'Other Income',
    'Food', 'Transport', 'Shopping', 'Housing', 'Education',
    'Healthcare', 'Utilities', 'Entertainment', 'Other'
]
VALID_TYPES = ['income', 'expense']
VALID_PAYMENT_METHODS = ['Cash', 'UPI', 'Credit Card', 'Debit Card', 'Net Banking', 'Cheque', 'Other']


def validate_transaction(data):
    errors = []
    if not data.get('description', '').strip():
        errors.append('Description is required')
    try:
        amount = float(data.get('amount', 0))
        if amount <= 0:
            errors.append('Amount must be a positive number')
    except (ValueError, TypeError):
        errors.append('Amount must be a valid number')
    if data.get('type', '').lower() not in VALID_TYPES:
        errors.append(f"Type must be one of: {', '.join(VALID_TYPES)}")
    if not data.get('date'):
        errors.append('Date is required')
    else:
        try:
            datetime.strptime(data['date'], '%Y-%m-%d')
        except ValueError:
            errors.append('Invalid date format (use YYYY-MM-DD)')
    return errors


@transactions_bp.route('', methods=['GET'])
@jwt_required()
def get_transactions():
    user_id = int(get_jwt_identity())
    
    query = Transaction.query.filter_by(user_id=user_id)

    # Filters
    txn_type = request.args.get('type')
    category = request.args.get('category')
    search = request.args.get('search', '').strip()
    start_date = request.args.get('start_date')
    end_date = request.args.get('end_date')
    sort_by = request.args.get('sort_by', 'date')
    sort_order = request.args.get('sort_order', 'desc')
    page = int(request.args.get('page', 1))
    per_page = min(int(request.args.get('per_page', 50)), 200)

    if txn_type and txn_type in VALID_TYPES:
        query = query.filter(Transaction.type == txn_type)
    if category:
        query = query.filter(Transaction.category == category)
    if search:
        query = query.filter(Transaction.description.ilike(f'%{search}%'))
    if start_date:
        try:
            query = query.filter(Transaction.date >= datetime.strptime(start_date, '%Y-%m-%d').date())
        except ValueError:
            pass
    if end_date:
        try:
            query = query.filter(Transaction.date <= datetime.strptime(end_date, '%Y-%m-%d').date())
        except ValueError:
            pass

    if sort_by == 'amount':
        col = Transaction.amount
    else:
        col = Transaction.date
    query = query.order_by(col.desc() if sort_order == 'desc' else col.asc())

    total = query.count()
    transactions = query.offset((page - 1) * per_page).limit(per_page).all()

    return jsonify({
        'transactions': [t.to_dict() for t in transactions],
        'total': total,
        'page': page,
        'per_page': per_page,
        'pages': (total + per_page - 1) // per_page,
    }), 200


@transactions_bp.route('', methods=['POST'])
@jwt_required()
def create_transaction():
    user_id = int(get_jwt_identity())
    data = request.get_json()
    if not data:
        return jsonify({'error': 'No data provided'}), 400

    errors = validate_transaction(data)
    if errors:
        return jsonify({'errors': errors}), 400

    txn = Transaction(
        user_id=user_id,
        description=data['description'].strip(),
        amount=float(data['amount']),
        type=data['type'].lower(),
        category=data.get('category', 'Other'),
        date=datetime.strptime(data['date'], '%Y-%m-%d').date(),
        notes=data.get('notes', '').strip() or None,
        payment_method=data.get('payment_method', 'Cash'),
        is_shared=data.get('is_shared', False),
    )
    db.session.add(txn)
    db.session.commit()
    return jsonify({'transaction': txn.to_dict(), 'message': 'Transaction created'}), 201


@transactions_bp.route('/<int:txn_id>', methods=['PUT'])
@jwt_required()
def update_transaction(txn_id):
    user_id = int(get_jwt_identity())
    txn = Transaction.query.filter_by(id=txn_id, user_id=user_id).first()
    if not txn:
        return jsonify({'error': 'Transaction not found'}), 404

    data = request.get_json()
    errors = validate_transaction(data)
    if errors:
        return jsonify({'errors': errors}), 400

    txn.description = data['description'].strip()
    txn.amount = float(data['amount'])
    txn.type = data['type'].lower()
    txn.category = data.get('category', txn.category)
    txn.date = datetime.strptime(data['date'], '%Y-%m-%d').date()
    txn.notes = data.get('notes', '').strip() or None
    txn.payment_method = data.get('payment_method', txn.payment_method)
    txn.is_shared = data.get('is_shared', txn.is_shared)
    db.session.commit()
    return jsonify({'transaction': txn.to_dict(), 'message': 'Transaction updated'}), 200


@transactions_bp.route('/<int:txn_id>', methods=['DELETE'])
@jwt_required()
def delete_transaction(txn_id):
    user_id = int(get_jwt_identity())
    txn = Transaction.query.filter_by(id=txn_id, user_id=user_id).first()
    if not txn:
        return jsonify({'error': 'Transaction not found'}), 404
    db.session.delete(txn)
    db.session.commit()
    return jsonify({'message': 'Transaction deleted'}), 200
