from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from ..models import Bill
from ..extensions import db
from datetime import date, datetime, timedelta
import calendar

bills_bp = Blueprint('bills', __name__)

VALID_FREQUENCIES = ['monthly', 'weekly', 'yearly', 'one-time']


def compute_next_due(frequency: str, due_day: int | None, from_date: date | None) -> date | None:
    """Compute the next due date from today based on frequency and due_day."""
    today = date.today()
    if from_date and from_date >= today:
        return from_date
    if frequency == 'monthly' and due_day:
        m, y = today.month, today.year
        last = calendar.monthrange(y, m)[1]
        d = min(due_day, last)
        candidate = date(y, m, d)
        if candidate < today:
            # push to next month
            if m == 12:
                m, y = 1, y + 1
            else:
                m += 1
            last = calendar.monthrange(y, m)[1]
            d = min(due_day, last)
            candidate = date(y, m, d)
        return candidate
    elif frequency == 'weekly':
        return today + timedelta(days=7)
    elif frequency == 'yearly':
        try:
            return date(today.year + 1, today.month, today.day)
        except ValueError:
            return date(today.year + 1, today.month, 28)
    return from_date


@bills_bp.route('', methods=['GET'])
@jwt_required()
def get_bills():
    user_id = int(get_jwt_identity())
    include_inactive = request.args.get('include_inactive', 'false').lower() == 'true'
    query = Bill.query.filter_by(user_id=user_id)
    if not include_inactive:
        query = query.filter_by(is_active=True)
    bills = query.order_by(Bill.next_due_date.asc().nullslast()).all()
    
    total_monthly = sum(
        b.amount if b.frequency == 'monthly' else
        b.amount * 52 / 12 if b.frequency == 'weekly' else
        b.amount / 12 if b.frequency == 'yearly' else 0
        for b in bills if b.is_active
    )
    
    return jsonify({
        'bills': [b.to_dict() for b in bills],
        'total_monthly_estimated': round(total_monthly, 2),
        'count': len(bills),
    }), 200


@bills_bp.route('/upcoming', methods=['GET'])
@jwt_required()
def upcoming_bills():
    """Bills due in the next N days."""
    user_id = int(get_jwt_identity())
    days = request.args.get('days', 30, type=int)
    today = date.today()
    cutoff = today + timedelta(days=days)
    
    bills = Bill.query.filter_by(user_id=user_id, is_active=True).all()
    upcoming = [
        b.to_dict() for b in bills
        if b.next_due_date and b.next_due_date <= cutoff
    ]
    upcoming.sort(key=lambda x: x['next_due_date'] or '9999-12-31')
    
    return jsonify({'upcoming': upcoming, 'days': days}), 200


@bills_bp.route('', methods=['POST'])
@jwt_required()
def create_bill():
    user_id = int(get_jwt_identity())
    data = request.get_json()
    if not data:
        return jsonify({'error': 'No data provided'}), 400

    name = data.get('name', '').strip()
    if not name:
        return jsonify({'error': 'Bill name is required'}), 400
    
    try:
        amount = float(data.get('amount', 0))
        if amount <= 0:
            raise ValueError
    except (TypeError, ValueError):
        return jsonify({'error': 'Amount must be a positive number'}), 400

    frequency = data.get('frequency', 'monthly')
    if frequency not in VALID_FREQUENCIES:
        return jsonify({'error': f'Frequency must be one of: {", ".join(VALID_FREQUENCIES)}'}), 400

    due_day = data.get('due_day')
    if due_day is not None:
        try:
            due_day = int(due_day)
            if not (1 <= due_day <= 31):
                raise ValueError
        except (TypeError, ValueError):
            return jsonify({'error': 'due_day must be 1–31'}), 400

    next_due_date = None
    if data.get('next_due_date'):
        try:
            next_due_date = datetime.strptime(data['next_due_date'], '%Y-%m-%d').date()
        except ValueError:
            return jsonify({'error': 'Invalid next_due_date format (YYYY-MM-DD)'}), 400
    else:
        next_due_date = compute_next_due(frequency, due_day, None)

    bill = Bill(
        user_id=user_id,
        name=name,
        amount=amount,
        category=data.get('category', 'Utilities'),
        frequency=frequency,
        due_day=due_day,
        next_due_date=next_due_date,
        is_active=True,
        auto_pay=bool(data.get('auto_pay', False)),
        notes=data.get('notes', '').strip() or None,
        payment_method=data.get('payment_method', 'Net Banking'),
    )
    db.session.add(bill)
    db.session.commit()
    return jsonify({'bill': bill.to_dict(), 'message': 'Bill created'}), 201


@bills_bp.route('/<int:bill_id>', methods=['PUT'])
@jwt_required()
def update_bill(bill_id):
    user_id = int(get_jwt_identity())
    bill = Bill.query.filter_by(id=bill_id, user_id=user_id).first()
    if not bill:
        return jsonify({'error': 'Bill not found'}), 404

    data = request.get_json()
    if data.get('name'):
        bill.name = data['name'].strip()
    if data.get('amount') is not None:
        try:
            a = float(data['amount'])
            if a <= 0:
                raise ValueError
            bill.amount = a
        except (TypeError, ValueError):
            return jsonify({'error': 'Amount must be a positive number'}), 400
    if data.get('category'):
        bill.category = data['category']
    if data.get('frequency') and data['frequency'] in VALID_FREQUENCIES:
        bill.frequency = data['frequency']
    if data.get('due_day') is not None:
        bill.due_day = int(data['due_day']) if data['due_day'] else None
    if data.get('next_due_date') is not None:
        if data['next_due_date'] == '':
            bill.next_due_date = None
        else:
            try:
                bill.next_due_date = datetime.strptime(data['next_due_date'], '%Y-%m-%d').date()
            except ValueError:
                return jsonify({'error': 'Invalid next_due_date format'}), 400
    if data.get('is_active') is not None:
        bill.is_active = bool(data['is_active'])
    if data.get('auto_pay') is not None:
        bill.auto_pay = bool(data['auto_pay'])
    if data.get('notes') is not None:
        bill.notes = data['notes'].strip() or None
    if data.get('payment_method'):
        bill.payment_method = data['payment_method']

    db.session.commit()
    return jsonify({'bill': bill.to_dict(), 'message': 'Bill updated'}), 200


@bills_bp.route('/<int:bill_id>/mark-paid', methods=['POST'])
@jwt_required()
def mark_paid(bill_id):
    """Mark a bill as paid and advance its next_due_date."""
    user_id = int(get_jwt_identity())
    bill = Bill.query.filter_by(id=bill_id, user_id=user_id).first()
    if not bill:
        return jsonify({'error': 'Bill not found'}), 404

    today = date.today()
    # Advance due date
    if bill.frequency == 'monthly':
        next_d = compute_next_due('monthly', bill.due_day, None)
        # ensure it's actually in the future
        if next_d and next_d <= today:
            m = today.month + 1 if today.month < 12 else 1
            y = today.year if today.month < 12 else today.year + 1
            last = calendar.monthrange(y, m)[1]
            d = min(bill.due_day or today.day, last)
            next_d = date(y, m, d)
        bill.next_due_date = next_d
    elif bill.frequency == 'weekly':
        bill.next_due_date = today + timedelta(days=7)
    elif bill.frequency == 'yearly':
        try:
            bill.next_due_date = date(today.year + 1, today.month, today.day)
        except ValueError:
            bill.next_due_date = date(today.year + 1, today.month, 28)
    elif bill.frequency == 'one-time':
        bill.is_active = False

    db.session.commit()
    return jsonify({'bill': bill.to_dict(), 'message': 'Bill marked as paid'}), 200


@bills_bp.route('/<int:bill_id>', methods=['DELETE'])
@jwt_required()
def delete_bill(bill_id):
    user_id = int(get_jwt_identity())
    bill = Bill.query.filter_by(id=bill_id, user_id=user_id).first()
    if not bill:
        return jsonify({'error': 'Bill not found'}), 404
    db.session.delete(bill)
    db.session.commit()
    return jsonify({'message': 'Bill deleted'}), 200
