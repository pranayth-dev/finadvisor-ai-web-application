#!/usr/bin/env python3
"""
Seed script — creates demo user and realistic demo transactions/budgets/goals.
Run from the server/ directory: python seed_data.py
Demo credentials:
  Email: demo@finadvisor.ai
  Password: Demo@1234
"""
import sys
import os
from datetime import date, timedelta
import random

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('FLASK_ENV', 'development')

from app import create_app
from app.extensions import db
from app.models import User, Transaction, Budget, SavingsGoal, Notification

app = create_app('development')

DEMO_EMAIL = 'demo@finadvisor.ai'
DEMO_PASSWORD = 'Demo@1234'

def seed():
    with app.app_context():
        db.create_all()

        # Remove existing demo user
        existing = User.query.filter_by(email=DEMO_EMAIL).first()
        if existing:
            db.session.delete(existing)
            db.session.commit()
            print("Removed existing demo user.")

        # Create demo user
        user = User(
            email=DEMO_EMAIL,
            first_name='Priya',
            last_name='Sharma',
            phone='+91-9876543210',
            account_mode='individual',
            currency='INR',
            monthly_income_preference=75000,
        )
        user.set_password(DEMO_PASSWORD)
        db.session.add(user)
        db.session.commit()
        print(f"Created demo user: {DEMO_EMAIL}")

        today = date.today()
        uid = user.id

        # Helper: create transaction
        def add_txn(desc, amount, txn_type, category, days_ago, notes=None, method='UPI'):
            t = Transaction(
                user_id=uid,
                description=desc,
                amount=amount,
                type=txn_type,
                category=category,
                date=today - timedelta(days=days_ago),
                notes=notes,
                payment_method=method,
            )
            db.session.add(t)

        # ---- Current month ----
        add_txn('Monthly Salary', 75000, 'income', 'Salary', 5, 'Net salary credit', 'Net Banking')
        add_txn('Freelance Project - ABC Corp', 15000, 'income', 'Freelancing', 12, None, 'UPI')
        add_txn('Grocery Shopping - Big Bazaar', 4200, 'expense', 'Food', 2, None, 'Credit Card')
        add_txn('Restaurant - Dinner', 1800, 'expense', 'Food', 4, 'Family dinner', 'UPI')
        add_txn('Monthly Rent', 18000, 'expense', 'Housing', 3, 'Apartment rent', 'Net Banking')
        add_txn('Electricity Bill', 2200, 'expense', 'Utilities', 7, None, 'Net Banking')
        add_txn('Internet Bill', 1200, 'expense', 'Utilities', 7, None, 'UPI')
        add_txn('Petrol', 2500, 'expense', 'Transport', 6, None, 'Cash')
        add_txn('Metro Card Recharge', 500, 'expense', 'Transport', 10, None, 'UPI')
        add_txn('Online Shopping - Amazon', 3500, 'expense', 'Shopping', 8, 'Clothes', 'Credit Card')
        add_txn('Mobile Recharge', 599, 'expense', 'Utilities', 1, None, 'UPI')
        add_txn('Netflix Subscription', 649, 'expense', 'Entertainment', 5, None, 'Credit Card')
        add_txn('Doctor Visit', 800, 'expense', 'Healthcare', 9, 'General checkup', 'Cash')
        add_txn('Books - Programming', 1200, 'expense', 'Education', 14, None, 'UPI')
        add_txn('Mutual Fund SIP', 5000, 'expense', 'Investments', 1, 'Monthly SIP', 'Net Banking')
        add_txn('Swiggy - Lunch', 450, 'expense', 'Food', 3, None, 'UPI')
        add_txn('Zomato - Dinner', 620, 'expense', 'Food', 6, None, 'UPI')
        add_txn('Gym Membership', 1500, 'expense', 'Healthcare', 1, 'Monthly membership', 'UPI')

        # ---- Last month ----
        add_txn('Monthly Salary', 75000, 'income', 'Salary', 35, 'Net salary credit', 'Net Banking')
        add_txn('Grocery Shopping', 3800, 'expense', 'Food', 32, None, 'Credit Card')
        add_txn('Monthly Rent', 18000, 'expense', 'Housing', 33, None, 'Net Banking')
        add_txn('Electricity Bill', 1900, 'expense', 'Utilities', 37, None, 'Net Banking')
        add_txn('Internet Bill', 1200, 'expense', 'Utilities', 37, None, 'UPI')
        add_txn('Petrol', 2000, 'expense', 'Transport', 36, None, 'Cash')
        add_txn('Movie Tickets', 700, 'expense', 'Entertainment', 40, None, 'UPI')
        add_txn('Shopping - Clothing', 2200, 'expense', 'Shopping', 38, None, 'Credit Card')
        add_txn('Mutual Fund SIP', 5000, 'expense', 'Investments', 31, 'Monthly SIP', 'Net Banking')
        add_txn('Mobile Recharge', 599, 'expense', 'Utilities', 31, None, 'UPI')
        add_txn('Swiggy - Multiple orders', 1200, 'expense', 'Food', 34, None, 'UPI')
        add_txn('Doctor Visit', 500, 'expense', 'Healthcare', 39, None, 'Cash')

        # ---- Two months ago ----
        add_txn('Monthly Salary', 75000, 'income', 'Salary', 65, None, 'Net Banking')
        add_txn('Grocery Shopping', 4100, 'expense', 'Food', 62, None, 'Credit Card')
        add_txn('Monthly Rent', 18000, 'expense', 'Housing', 63, None, 'Net Banking')
        add_txn('Electricity Bill', 2100, 'expense', 'Utilities', 67, None, 'Net Banking')
        add_txn('Petrol', 2200, 'expense', 'Transport', 66, None, 'Cash')
        add_txn('Mutual Fund SIP', 5000, 'expense', 'Investments', 61, None, 'Net Banking')
        add_txn('Weekend Trip', 8000, 'expense', 'Entertainment', 68, 'Goa trip', 'Credit Card')
        add_txn('Freelance Project', 20000, 'income', 'Freelancing', 70, None, 'UPI')

        db.session.commit()
        print(f"Added demo transactions.")

        # ---- Budgets for current month ----
        budgets = [
            ('Food', 8000),
            ('Transport', 4000),
            ('Shopping', 3000),
            ('Entertainment', 2000),
            ('Healthcare', 2000),
            ('Utilities', 5000),
            ('Housing', 20000),
            ('Investments', 6000),
        ]
        for cat, limit in budgets:
            b = Budget(
                user_id=uid,
                category=cat,
                limit_amount=limit,
                month=today.month,
                year=today.year,
            )
            db.session.add(b)
        db.session.commit()
        print("Added demo budgets.")

        # ---- Savings Goals ----
        goals = [
            ('Emergency Fund', 225000, 45000, today.replace(year=today.year + 1), 'Emergency Fund'),
            ('New Laptop', 85000, 30000, today + timedelta(days=120), 'Electronics'),
            ('Family Vacation - Europe', 150000, 25000, today + timedelta(days=300), 'Travel'),
            ('Higher Education Fund', 500000, 50000, today.replace(year=today.year + 3), 'Education'),
        ]
        for name, target, current, tdate, category in goals:
            g = SavingsGoal(
                user_id=uid,
                name=name,
                target_amount=target,
                current_amount=current,
                target_date=tdate,
                category=category,
            )
            db.session.add(g)
        db.session.commit()
        print("Added demo savings goals.")

        # ---- Demo Notifications ----
        notifs = [
            ('Budget Warning: Food', 'You have used 88% of your Food budget this month.', 'budget'),
            ('Savings Goal Progress', 'You are 33% closer to your Emergency Fund goal!', 'goal'),
            ('Monthly Summary Ready', f'Your financial summary for this month is ready. Check your reports.', 'summary'),
        ]
        for title, message, ntype in notifs:
            n = Notification(user_id=uid, title=title, message=message, notification_type=ntype)
            db.session.add(n)
        db.session.commit()
        print("Added demo notifications.")

        print("\nDemo data seeded successfully!")
        print(f"   Email:    {DEMO_EMAIL}")
        print(f"   Password: {DEMO_PASSWORD}")


if __name__ == '__main__':
    seed()
