from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from ..models import FamilyGroup, FamilyInvitation, FamilySavingsGoal, User, Transaction
from ..extensions import db
from datetime import date, datetime, timezone
from sqlalchemy import extract
from collections import defaultdict

family_bp = Blueprint('family', __name__)


def _require_member(user_id: int):
    """Return (user, group) if the user belongs to a group, else raise."""
    user = db.session.get(User, user_id)
    if not user or not user.family_group_id:
        return None, None
    group = db.session.get(FamilyGroup, user.family_group_id)
    return user, group


def _is_owner(user_id: int, group: FamilyGroup) -> bool:
    return group.created_by == user_id


# ---------------------------------------------------------------------------
# Group info
# ---------------------------------------------------------------------------

@family_bp.route('', methods=['GET'])
@jwt_required()
def get_family():
    user_id = int(get_jwt_identity())
    user = db.session.get(User, user_id)
    if not user or not user.family_group_id:
        return jsonify({'family': None, 'message': 'Not part of a family group'}), 200

    group = db.session.get(FamilyGroup, user.family_group_id)
    if not group:
        return jsonify({'family': None}), 200

    members = User.query.filter_by(family_group_id=group.id, is_active=True).all()
    pending = FamilyInvitation.query.filter_by(group_id=group.id, status='pending').all()
    return jsonify({
        'family': {
            **group.to_dict(),
            'is_owner': _is_owner(user_id, group),
            'members': [
                {
                    'id': m.id,
                    'name': m.first_name + ' ' + m.last_name,
                    'email': m.email,
                    'is_owner': m.id == group.created_by,
                }
                for m in members
            ],
            'pending_invitations': [i.to_dict() for i in pending] if _is_owner(user_id, group) else [],
        }
    }), 200


# ---------------------------------------------------------------------------
# Create group
# ---------------------------------------------------------------------------

@family_bp.route('/create', methods=['POST'])
@jwt_required()
def create_family():
    user_id = int(get_jwt_identity())
    user = db.session.get(User, user_id)
    data = request.get_json(silent=True)

    if not data or not data.get('name', '').strip():
        return jsonify({'error': 'Family group name is required'}), 400

    if user.family_group_id:
        return jsonify({'error': 'Already in a family group'}), 409

    group = FamilyGroup(
        name=data['name'].strip(),
        created_by=user_id,
        description=data.get('description', '').strip() or None,
    )
    db.session.add(group)
    db.session.flush()

    user.family_group_id = group.id
    user.account_mode = 'family'
    db.session.commit()

    return jsonify({'family': group.to_dict(), 'message': 'Family group created'}), 201


# ---------------------------------------------------------------------------
# Leave group
# ---------------------------------------------------------------------------

@family_bp.route('/leave', methods=['POST'])
@jwt_required()
def leave_family():
    user_id = int(get_jwt_identity())
    user = db.session.get(User, user_id)
    if not user or not user.family_group_id:
        return jsonify({'error': 'Not part of a family group'}), 400

    group = db.session.get(FamilyGroup, user.family_group_id)
    if group and group.created_by == user_id:
        # Owner leaving — check if there are other members
        other_members = User.query.filter(
            User.family_group_id == group.id,
            User.id != user_id,
            User.is_active == True
        ).count()
        if other_members > 0:
            return jsonify({'error': 'As the owner, transfer ownership or remove other members first'}), 409

    user.family_group_id = None
    user.account_mode = 'individual'
    db.session.commit()
    return jsonify({'message': 'Left family group'}), 200


# ---------------------------------------------------------------------------
# Invite a member
# ---------------------------------------------------------------------------

@family_bp.route('/invite', methods=['POST'])
@jwt_required()
def invite_member():
    user_id = int(get_jwt_identity())
    user, group = _require_member(user_id)
    if not group:
        return jsonify({'error': 'Not part of a family group'}), 403
    if not _is_owner(user_id, group):
        return jsonify({'error': 'Only the group owner can invite members'}), 403

    data = request.get_json(silent=True)
    if not data:
        return jsonify({'error': 'Invalid request'}), 400

    email = data.get('email', '').strip().lower()
    if not email:
        return jsonify({'error': 'Email address is required'}), 400

    # Cannot invite yourself
    if email == user.email:
        return jsonify({'error': 'You cannot invite yourself'}), 400

    # Check if already a member
    already_member = User.query.filter_by(email=email, family_group_id=group.id, is_active=True).first()
    if already_member:
        return jsonify({'error': f'{email} is already a member of this group'}), 409

    # Check for existing pending invitation
    existing = FamilyInvitation.query.filter_by(
        group_id=group.id, invited_email=email, status='pending'
    ).first()
    if existing:
        return jsonify({'error': f'A pending invitation already exists for {email}'}), 409

    # Check if the email belongs to an existing user
    invited_user = User.query.filter_by(email=email, is_active=True).first()
    if not invited_user:
        return jsonify({'error': f'No registered user found with email {email}'}), 404

    # Check if invited user is in another group
    if invited_user.family_group_id:
        return jsonify({'error': f'{email} is already part of another family group'}), 409

    invitation = FamilyInvitation(
        group_id=group.id,
        invited_email=email,
        invited_by=user_id,
    )
    db.session.add(invitation)
    db.session.commit()

    return jsonify({
        'invitation': invitation.to_dict(),
        'message': f'Invitation sent to {email}',
    }), 201


# ---------------------------------------------------------------------------
# My pending invitations (received)
# ---------------------------------------------------------------------------

@family_bp.route('/my-invitations', methods=['GET'])
@jwt_required()
def my_invitations():
    user_id = int(get_jwt_identity())
    user = db.session.get(User, user_id)
    if not user:
        return jsonify({'error': 'User not found'}), 404

    invitations = FamilyInvitation.query.filter_by(
        invited_email=user.email, status='pending'
    ).all()

    result = []
    for inv in invitations:
        group = db.session.get(FamilyGroup, inv.group_id)
        inviter = db.session.get(User, inv.invited_by)
        result.append({
            **inv.to_dict(),
            'group_name': group.name if group else None,
            'invited_by_name': f"{inviter.first_name} {inviter.last_name}" if inviter else None,
        })

    return jsonify({'invitations': result}), 200


# ---------------------------------------------------------------------------
# Respond to invitation (accept / reject)
# ---------------------------------------------------------------------------

@family_bp.route('/invitations/<int:invitation_id>/respond', methods=['POST'])
@jwt_required()
def respond_invitation(invitation_id):
    user_id = int(get_jwt_identity())
    user = db.session.get(User, user_id)
    if not user:
        return jsonify({'error': 'User not found'}), 404

    data = request.get_json(silent=True)
    action = (data or {}).get('action', '').lower()
    if action not in ('accept', 'reject'):
        return jsonify({'error': 'action must be "accept" or "reject"'}), 400

    invitation = FamilyInvitation.query.filter_by(
        id=invitation_id, invited_email=user.email, status='pending'
    ).first()
    if not invitation:
        return jsonify({'error': 'Invitation not found'}), 404

    if action == 'accept':
        if user.family_group_id:
            return jsonify({'error': 'You are already in a family group'}), 409
        user.family_group_id = invitation.group_id
        user.account_mode = 'family'
        invitation.status = 'accepted'
        invitation.responded_at = datetime.now(timezone.utc)
        db.session.commit()
        return jsonify({'message': 'Invitation accepted. Welcome to the family group!'}), 200
    else:
        invitation.status = 'rejected'
        invitation.responded_at = datetime.now(timezone.utc)
        db.session.commit()
        return jsonify({'message': 'Invitation declined'}), 200


# ---------------------------------------------------------------------------
# Remove a member (owner only)
# ---------------------------------------------------------------------------

@family_bp.route('/members/<int:member_id>', methods=['DELETE'])
@jwt_required()
def remove_member(member_id):
    user_id = int(get_jwt_identity())
    user, group = _require_member(user_id)
    if not group:
        return jsonify({'error': 'Not part of a family group'}), 403
    if not _is_owner(user_id, group):
        return jsonify({'error': 'Only the group owner can remove members'}), 403
    if member_id == user_id:
        return jsonify({'error': 'Cannot remove yourself. Use the leave endpoint.'}), 400

    member = User.query.filter_by(id=member_id, family_group_id=group.id, is_active=True).first()
    if not member:
        return jsonify({'error': 'Member not found in this group'}), 404

    member.family_group_id = None
    member.account_mode = 'individual'
    db.session.commit()
    return jsonify({'message': f'{member.first_name} {member.last_name} removed from group'}), 200


# ---------------------------------------------------------------------------
# Family transactions (shared + all members' transactions for the group)
# ---------------------------------------------------------------------------

@family_bp.route('/transactions', methods=['GET'])
@jwt_required()
def family_transactions():
    user_id = int(get_jwt_identity())
    user, group = _require_member(user_id)
    if not group:
        return jsonify({'error': 'Not part of a family group'}), 403

    members = User.query.filter_by(family_group_id=group.id, is_active=True).all()
    member_ids = [m.id for m in members]

    today = date.today()
    month = request.args.get('month', type=int, default=today.month)
    year = request.args.get('year', type=int, default=today.year)

    txns = Transaction.query.filter(
        Transaction.user_id.in_(member_ids),
        extract('month', Transaction.date) == month,
        extract('year', Transaction.date) == year,
    ).order_by(Transaction.date.desc()).all()

    member_map = {m.id: f"{m.first_name} {m.last_name}" for m in members}

    result = []
    for t in txns:
        d = t.to_dict()
        d['member_name'] = member_map.get(t.user_id, 'Unknown')
        result.append(d)

    return jsonify({'transactions': result, 'month': month, 'year': year}), 200


# ---------------------------------------------------------------------------
# Overview / dashboard
# ---------------------------------------------------------------------------

@family_bp.route('/overview', methods=['GET'])
@jwt_required()
def family_overview():
    user_id = int(get_jwt_identity())
    user = db.session.get(User, user_id)
    if not user or not user.family_group_id:
        return jsonify({'error': 'Not part of a family group'}), 403

    members = User.query.filter_by(family_group_id=user.family_group_id, is_active=True).all()
    member_ids = [m.id for m in members]

    today = date.today()
    month = request.args.get('month', type=int, default=today.month)
    year = request.args.get('year', type=int, default=today.year)

    all_txns = Transaction.query.filter(
        Transaction.user_id.in_(member_ids),
        extract('month', Transaction.date) == month,
        extract('year', Transaction.date) == year,
    ).all()

    combined_income = sum(t.amount for t in all_txns if t.type == 'income')
    combined_expenses = sum(t.amount for t in all_txns if t.type == 'expense')

    # Category breakdown
    cat_spending: dict = defaultdict(float)
    for t in all_txns:
        if t.type == 'expense':
            cat_spending[t.category] += t.amount

    member_data = []
    for m in members:
        m_txns = [t for t in all_txns if t.user_id == m.id]
        member_data.append({
            'member': {
                'id': m.id,
                'name': m.first_name + ' ' + m.last_name,
                'is_owner': m.id == user.family_group_id and db.session.get(FamilyGroup, user.family_group_id).created_by == m.id,
            },
            'income': round(sum(t.amount for t in m_txns if t.type == 'income'), 2),
            'expenses': round(sum(t.amount for t in m_txns if t.type == 'expense'), 2),
        })

    # Shared savings goals
    group = db.session.get(FamilyGroup, user.family_group_id)
    goals = FamilySavingsGoal.query.filter_by(group_id=group.id, is_completed=False).all()

    # Recent transactions (last 10)
    recent = sorted(all_txns, key=lambda t: (t.date, t.id), reverse=True)[:10]
    member_map = {m.id: f"{m.first_name} {m.last_name}" for m in members}
    recent_list = []
    for t in recent:
        d = t.to_dict()
        d['member_name'] = member_map.get(t.user_id, 'Unknown')
        recent_list.append(d)

    return jsonify({
        'combined_income': round(combined_income, 2),
        'combined_expenses': round(combined_expenses, 2),
        'net_savings': round(combined_income - combined_expenses, 2),
        'savings_rate': round((combined_income - combined_expenses) / combined_income * 100 if combined_income > 0 else 0, 1),
        'category_spending': [
            {'category': k, 'amount': round(v, 2)}
            for k, v in sorted(cat_spending.items(), key=lambda x: -x[1])
        ],
        'month': month,
        'year': year,
        'members': member_data,
        'goals': [g.to_dict() for g in goals],
        'recent_transactions': recent_list,
    }), 200


# ---------------------------------------------------------------------------
# Family savings goals
# ---------------------------------------------------------------------------

@family_bp.route('/goals', methods=['GET'])
@jwt_required()
def list_goals():
    user_id = int(get_jwt_identity())
    user, group = _require_member(user_id)
    if not group:
        return jsonify({'error': 'Not part of a family group'}), 403

    goals = FamilySavingsGoal.query.filter_by(group_id=group.id).order_by(
        FamilySavingsGoal.is_completed.asc(),
        FamilySavingsGoal.created_at.desc()
    ).all()
    return jsonify({'goals': [g.to_dict() for g in goals]}), 200


@family_bp.route('/goals', methods=['POST'])
@jwt_required()
def create_goal():
    user_id = int(get_jwt_identity())
    user, group = _require_member(user_id)
    if not group:
        return jsonify({'error': 'Not part of a family group'}), 403

    data = request.get_json(silent=True)
    if not data:
        return jsonify({'error': 'Invalid request'}), 400

    name = data.get('name', '').strip()
    if not name:
        return jsonify({'error': 'Goal name is required'}), 400

    try:
        target_amount = float(data.get('target_amount', 0))
        if target_amount <= 0:
            raise ValueError()
    except (ValueError, TypeError):
        return jsonify({'error': 'Target amount must be a positive number'}), 400

    target_date = None
    if data.get('target_date'):
        try:
            target_date = date.fromisoformat(data['target_date'])
        except ValueError:
            return jsonify({'error': 'Invalid target_date format (use YYYY-MM-DD)'}), 400

    current_amount = max(0.0, float(data.get('current_amount', 0) or 0))

    goal = FamilySavingsGoal(
        group_id=group.id,
        created_by=user_id,
        name=name,
        target_amount=target_amount,
        current_amount=current_amount,
        target_date=target_date,
        category=data.get('category', 'Other'),
        notes=data.get('notes', ''),
    )
    db.session.add(goal)
    db.session.commit()
    return jsonify({'goal': goal.to_dict(), 'message': 'Goal created'}), 201


@family_bp.route('/goals/<int:goal_id>/contribute', methods=['POST'])
@jwt_required()
def contribute_goal(goal_id):
    user_id = int(get_jwt_identity())
    user, group = _require_member(user_id)
    if not group:
        return jsonify({'error': 'Not part of a family group'}), 403

    goal = FamilySavingsGoal.query.filter_by(id=goal_id, group_id=group.id).first()
    if not goal:
        return jsonify({'error': 'Goal not found'}), 404
    if goal.is_completed:
        return jsonify({'error': 'Goal already completed'}), 400

    data = request.get_json(silent=True)
    try:
        amount = float((data or {}).get('amount', 0))
        if amount <= 0:
            raise ValueError()
    except (ValueError, TypeError):
        return jsonify({'error': 'Contribution amount must be a positive number'}), 400

    goal.current_amount = round(goal.current_amount + amount, 2)
    if goal.current_amount >= goal.target_amount:
        goal.is_completed = True

    db.session.commit()
    return jsonify({'goal': goal.to_dict(), 'message': f'Added ₹{amount:,.2f} to {goal.name}'}), 200


@family_bp.route('/goals/<int:goal_id>', methods=['PUT'])
@jwt_required()
def update_goal(goal_id):
    user_id = int(get_jwt_identity())
    user, group = _require_member(user_id)
    if not group:
        return jsonify({'error': 'Not part of a family group'}), 403
    if not _is_owner(user_id, group):
        return jsonify({'error': 'Only the group owner can edit goals'}), 403

    goal = FamilySavingsGoal.query.filter_by(id=goal_id, group_id=group.id).first()
    if not goal:
        return jsonify({'error': 'Goal not found'}), 404

    data = request.get_json(silent=True) or {}
    if 'name' in data:
        goal.name = data['name'].strip() or goal.name
    if 'target_amount' in data:
        try:
            goal.target_amount = float(data['target_amount'])
        except (ValueError, TypeError):
            return jsonify({'error': 'Invalid target_amount'}), 400
    if 'target_date' in data:
        try:
            goal.target_date = date.fromisoformat(data['target_date']) if data['target_date'] else None
        except ValueError:
            return jsonify({'error': 'Invalid target_date format'}), 400
    if 'category' in data:
        goal.category = data['category']
    if 'notes' in data:
        goal.notes = data['notes']

    db.session.commit()
    return jsonify({'goal': goal.to_dict()}), 200


@family_bp.route('/goals/<int:goal_id>', methods=['DELETE'])
@jwt_required()
def delete_goal(goal_id):
    user_id = int(get_jwt_identity())
    user, group = _require_member(user_id)
    if not group:
        return jsonify({'error': 'Not part of a family group'}), 403
    if not _is_owner(user_id, group):
        return jsonify({'error': 'Only the group owner can delete goals'}), 403

    goal = FamilySavingsGoal.query.filter_by(id=goal_id, group_id=group.id).first()
    if not goal:
        return jsonify({'error': 'Goal not found'}), 404

    db.session.delete(goal)
    db.session.commit()
    return jsonify({'message': 'Goal deleted'}), 200
