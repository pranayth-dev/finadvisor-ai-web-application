from flask import Blueprint, request, jsonify, make_response
from flask_jwt_extended import jwt_required, get_jwt_identity
from ..models import Transaction, Budget, SavingsGoal
from ..extensions import db
from datetime import date, datetime
from collections import defaultdict
from sqlalchemy import extract
import csv
import io

reports_bp = Blueprint('reports', __name__)


def get_month_transactions(user_id, month, year):
    return Transaction.query.filter_by(user_id=user_id).filter(
        extract('month', Transaction.date) == month,
        extract('year', Transaction.date) == year,
    ).all()


@reports_bp.route('/monthly', methods=['GET'])
@jwt_required()
def monthly_report():
    user_id = int(get_jwt_identity())
    today = date.today()
    month = request.args.get('month', type=int, default=today.month)
    year = request.args.get('year', type=int, default=today.year)

    txns = get_month_transactions(user_id, month, year)
    income = sum(t.amount for t in txns if t.type == 'income')
    expenses = sum(t.amount for t in txns if t.type == 'expense')
    net_savings = income - expenses
    savings_rate = (net_savings / income * 100) if income > 0 else 0

    # Category breakdown
    income_by_cat = defaultdict(float)
    expense_by_cat = defaultdict(float)
    for t in txns:
        if t.type == 'income':
            income_by_cat[t.category] += t.amount
        else:
            expense_by_cat[t.category] += t.amount

    month_names = ['January', 'February', 'March', 'April', 'May', 'June',
                   'July', 'August', 'September', 'October', 'November', 'December']

    # Financial story text
    if income > 0 or expenses > 0:
        top_expense_cat = max(expense_by_cat, key=expense_by_cat.get) if expense_by_cat else 'N/A'
        story = (
            f"In {month_names[month-1]} {year}, you earned ₹{income:,.0f} and spent ₹{expenses:,.0f}, "
            f"leaving ₹{net_savings:,.0f} in net savings. Your savings rate was {savings_rate:.1f}%. "
        )
        if expense_by_cat:
            story += f"Your largest spending category was {top_expense_cat} (₹{expense_by_cat[top_expense_cat]:,.0f})."
        if savings_rate >= 20:
            story += " You are doing great — keep it up!"
        elif savings_rate >= 10:
            story += " There's room to improve your savings rate."
        elif net_savings < 0:
            story += " Your expenses exceeded your income — review your spending urgently."
    else:
        story = f"No transactions found for {month_names[month-1]} {year}. Add transactions to see your financial story."

    return jsonify({
        'month': month,
        'year': year,
        'month_name': month_names[month - 1],
        'total_income': round(income, 2),
        'total_expenses': round(expenses, 2),
        'net_savings': round(net_savings, 2),
        'savings_rate': round(savings_rate, 1),
        'income_by_category': [{'category': k, 'amount': round(v, 2)} for k, v in income_by_cat.items()],
        'expense_by_category': [{'category': k, 'amount': round(v, 2)} 
                                  for k, v in sorted(expense_by_cat.items(), key=lambda x: -x[1])],
        'transaction_count': len(txns),
        'financial_story': story,
    }), 200


@reports_bp.route('/categories', methods=['GET'])
@jwt_required()
def categories_report():
    user_id = int(get_jwt_identity())
    today = date.today()
    start_date = request.args.get('start_date')
    end_date = request.args.get('end_date')

    query = Transaction.query.filter_by(user_id=user_id)
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

    txns = query.all()
    expense_by_cat = defaultdict(float)
    income_by_cat = defaultdict(float)
    for t in txns:
        if t.type == 'expense':
            expense_by_cat[t.category] += t.amount
        else:
            income_by_cat[t.category] += t.amount

    total_expenses = sum(expense_by_cat.values())
    categories = []
    for cat, amt in sorted(expense_by_cat.items(), key=lambda x: -x[1]):
        categories.append({
            'category': cat,
            'amount': round(amt, 2),
            'percentage': round(amt / total_expenses * 100, 1) if total_expenses > 0 else 0,
        })

    return jsonify({
        'expense_categories': categories,
        'income_categories': [{'category': k, 'amount': round(v, 2)} for k, v in income_by_cat.items()],
        'total_expenses': round(total_expenses, 2),
    }), 200


@reports_bp.route('/export', methods=['GET'])
@jwt_required()
def export_csv():
    user_id = int(get_jwt_identity())
    query = Transaction.query.filter_by(user_id=user_id)
    
    start_date = request.args.get('start_date')
    end_date = request.args.get('end_date')
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

    transactions = query.order_by(Transaction.date.desc()).all()

    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(['Date', 'Description', 'Type', 'Category', 'Amount (INR)', 'Payment Method', 'Notes'])
    for t in transactions:
        writer.writerow([
            t.date.isoformat(),
            t.description,
            t.type.capitalize(),
            t.category,
            f'{t.amount:.2f}',
            t.payment_method or '',
            t.notes or '',
        ])

    response = make_response(output.getvalue())
    response.headers['Content-Type'] = 'text/csv'
    response.headers['Content-Disposition'] = 'attachment; filename=transactions.csv'
    return response
