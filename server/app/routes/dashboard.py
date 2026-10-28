from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from ..models import Transaction, Budget, SavingsGoal, Bill
from ..extensions import db
from datetime import date, datetime, timedelta
from sqlalchemy import func, extract
from collections import defaultdict

dashboard_bp = Blueprint('dashboard', __name__)


def get_dashboard_data(user_id, month=None, year=None):
    today = date.today()
    if not month:
        month = today.month
    if not year:
        year = today.year

    # All transactions for the user
    all_transactions = Transaction.query.filter_by(user_id=user_id).all()
    
    # Current month transactions
    month_txns = [t for t in all_transactions 
                  if t.date.month == month and t.date.year == year]

    total_income = sum(t.amount for t in month_txns if t.type == 'income')
    total_expenses = sum(t.amount for t in month_txns if t.type == 'expense')
    net_savings = total_income - total_expenses
    savings_rate = (net_savings / total_income * 100) if total_income > 0 else 0

    # Category breakdown for expenses
    category_spending = defaultdict(float)
    for t in month_txns:
        if t.type == 'expense':
            category_spending[t.category] += t.amount

    # Budgets for current month
    budgets = Budget.query.filter_by(user_id=user_id, month=month, year=year).all()
    budget_data = []
    for b in budgets:
        spent = category_spending.get(b.category, 0)
        budget_data.append(b.to_dict(spent=spent))

    # Savings goals
    goals = SavingsGoal.query.filter_by(user_id=user_id, is_completed=False).all()

    # Upcoming bills (next 30 days)
    today_date = date.today()
    upcoming_bills = Bill.query.filter_by(user_id=user_id, is_active=True).filter(
        Bill.next_due_date >= today_date,
        Bill.next_due_date <= today_date + timedelta(days=30),
    ).order_by(Bill.next_due_date.asc()).limit(5).all()

    # Total monthly bills
    all_bills = Bill.query.filter_by(user_id=user_id, is_active=True).all()
    monthly_bills_total = sum(
        b.amount if b.frequency == 'monthly' else
        b.amount * 52 / 12 if b.frequency == 'weekly' else
        b.amount / 12 if b.frequency == 'yearly' else 0
        for b in all_bills
    )

    # Recent transactions (last 10)
    recent = sorted(all_transactions, key=lambda t: (t.date, t.id), reverse=True)[:10]

    return {
        'summary': {
            'total_income': round(total_income, 2),
            'total_expenses': round(total_expenses, 2),
            'net_savings': round(net_savings, 2),
            'savings_rate': round(savings_rate, 1),
            'month': month,
            'year': year,
            'monthly_bills_total': round(monthly_bills_total, 2),
        },
        'category_spending': [{'category': k, 'amount': round(v, 2)}
                               for k, v in sorted(category_spending.items(), key=lambda x: -x[1])],
        'budgets': budget_data,
        'goals': [g.to_dict() for g in goals],
        'recent_transactions': [t.to_dict() for t in recent],
        'upcoming_bills': [b.to_dict() for b in upcoming_bills],
    }


def calculate_health_score(user_id):
    today = date.today()
    month = today.month
    year = today.year
    
    all_transactions = Transaction.query.filter_by(user_id=user_id).all()
    month_txns = [t for t in all_transactions 
                  if t.date.month == month and t.date.year == year]
    
    total_income = sum(t.amount for t in month_txns if t.type == 'income')
    total_expenses = sum(t.amount for t in month_txns if t.type == 'expense')
    net_savings = total_income - total_expenses
    savings_rate = (net_savings / total_income * 100) if total_income > 0 else 0

    score = 0
    breakdown = []

    # 1. Savings rate (max 30 points)
    if savings_rate >= 30:
        pts = 30
        msg = f"Excellent savings rate of {savings_rate:.1f}%"
    elif savings_rate >= 20:
        pts = 22
        msg = f"Good savings rate of {savings_rate:.1f}%"
    elif savings_rate >= 10:
        pts = 14
        msg = f"Average savings rate of {savings_rate:.1f}%"
    elif savings_rate > 0:
        pts = 6
        msg = f"Low savings rate of {savings_rate:.1f}%"
    else:
        pts = 0
        msg = "No savings this month"
    score += pts
    breakdown.append({'factor': 'Savings Rate', 'score': pts, 'max': 30, 'note': msg})

    # 2. Expense-to-income ratio (max 25 points)
    expense_ratio = (total_expenses / total_income * 100) if total_income > 0 else 100
    if expense_ratio <= 50:
        pts = 25
    elif expense_ratio <= 70:
        pts = 18
    elif expense_ratio <= 90:
        pts = 10
    elif expense_ratio <= 100:
        pts = 4
    else:
        pts = 0
    score += pts
    breakdown.append({'factor': 'Expense-to-Income Ratio', 'score': pts, 'max': 25,
                      'note': f"Spending {expense_ratio:.1f}% of income"})

    # 3. Budget adherence (max 25 points)
    budgets = Budget.query.filter_by(user_id=user_id, month=month, year=year).all()
    category_spending = defaultdict(float)
    for t in month_txns:
        if t.type == 'expense':
            category_spending[t.category] += t.amount

    if budgets:
        over_budget_count = sum(1 for b in budgets 
                                if category_spending.get(b.category, 0) > b.limit_amount)
        adherence_rate = (1 - over_budget_count / len(budgets)) * 100
        if adherence_rate >= 100:
            pts = 25
        elif adherence_rate >= 80:
            pts = 18
        elif adherence_rate >= 60:
            pts = 10
        else:
            pts = 3
        score += pts
        breakdown.append({'factor': 'Budget Adherence', 'score': pts, 'max': 25,
                          'note': f"{adherence_rate:.0f}% budgets within limit"})
    else:
        pts = 10
        score += pts
        breakdown.append({'factor': 'Budget Adherence', 'score': pts, 'max': 25,
                          'note': 'No budgets set — add budgets to improve score'})

    # 4. Emergency savings (max 20 points)
    emergency_goal = SavingsGoal.query.filter_by(user_id=user_id).filter(
        SavingsGoal.name.ilike('%emergency%')
    ).first()
    if emergency_goal:
        eg_pct = (emergency_goal.current_amount / emergency_goal.target_amount * 100
                  if emergency_goal.target_amount > 0 else 0)
        if eg_pct >= 100:
            pts = 20
            enote = "Emergency fund fully funded"
        elif eg_pct >= 50:
            pts = 12
            enote = f"Emergency fund {eg_pct:.0f}% funded"
        else:
            pts = 5
            enote = f"Emergency fund {eg_pct:.0f}% funded"
    else:
        pts = 0
        enote = "No emergency fund goal set"
    score += pts
    breakdown.append({'factor': 'Emergency Fund', 'score': pts, 'max': 20, 'note': enote})

    strengths = [b['factor'] for b in breakdown if b['score'] >= b['max'] * 0.8]
    improvements = [b['factor'] for b in breakdown if b['score'] < b['max'] * 0.5]

    if score >= 80:
        grade = 'Excellent'
    elif score >= 60:
        grade = 'Good'
    elif score >= 40:
        grade = 'Fair'
    else:
        grade = 'Needs Improvement'

    return {
        'score': score,
        'grade': grade,
        'breakdown': breakdown,
        'strengths': strengths,
        'areas_for_improvement': improvements,
    }


@dashboard_bp.route('', methods=['GET'])
@jwt_required()
def dashboard():
    user_id = int(get_jwt_identity())
    month = request.args.get('month', type=int)
    year = request.args.get('year', type=int)
    data = get_dashboard_data(user_id, month, year)
    health = calculate_health_score(user_id)
    data['health_score'] = health
    return jsonify(data), 200


@dashboard_bp.route('/trends', methods=['GET'])
@jwt_required()
def trends():
    user_id = int(get_jwt_identity())
    months_back = int(request.args.get('months', 6))

    today = date.today()
    monthly_data = []

    for i in range(months_back - 1, -1, -1):
        m = today.month - i
        y = today.year
        while m <= 0:
            m += 12
            y -= 1

        txns = Transaction.query.filter_by(user_id=user_id).filter(
            extract('month', Transaction.date) == m,
            extract('year', Transaction.date) == y,
        ).all()

        income = sum(t.amount for t in txns if t.type == 'income')
        expenses = sum(t.amount for t in txns if t.type == 'expense')
        savings = income - expenses

        month_names = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun',
                       'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']
        monthly_data.append({
            'month': month_names[m - 1],
            'month_num': m,
            'year': y,
            'income': round(income, 2),
            'expenses': round(expenses, 2),
            'savings': round(savings, 2),
        })

    return jsonify({'trends': monthly_data}), 200


@dashboard_bp.route('/health-score', methods=['GET'])
@jwt_required()
def health_score():
    user_id = int(get_jwt_identity())
    return jsonify(calculate_health_score(user_id)), 200
