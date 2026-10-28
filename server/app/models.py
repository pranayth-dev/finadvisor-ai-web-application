from datetime import datetime, date, timezone

def _now():
    return datetime.now(timezone.utc).replace(tzinfo=None)
from .extensions import db
import bcrypt


class User(db.Model):
    __tablename__ = 'users'

    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(255), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(255), nullable=False)
    first_name = db.Column(db.String(100), nullable=False)
    last_name = db.Column(db.String(100), nullable=False)
    phone = db.Column(db.String(20), nullable=True)
    account_mode = db.Column(db.String(20), default='individual')  # individual / family
    currency = db.Column(db.String(10), default='INR')
    monthly_income_preference = db.Column(db.Float, default=0.0)
    theme = db.Column(db.String(20), default='light')
    notification_budget_alerts = db.Column(db.Boolean, default=True)
    notification_goal_milestones = db.Column(db.Boolean, default=True)
    notification_monthly_summary = db.Column(db.Boolean, default=True)
    family_group_id = db.Column(db.Integer, db.ForeignKey('family_groups.id'), nullable=True)
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=_now)
    updated_at = db.Column(db.DateTime, default=_now, onupdate=_now)

    transactions = db.relationship('Transaction', backref='user', lazy='dynamic', cascade='all, delete-orphan')
    budgets = db.relationship('Budget', backref='user', lazy='dynamic', cascade='all, delete-orphan')
    savings_goals = db.relationship('SavingsGoal', backref='user', lazy='dynamic', cascade='all, delete-orphan')
    insights = db.relationship('FinancialInsight', backref='user', lazy='dynamic', cascade='all, delete-orphan')
    notifications = db.relationship('Notification', backref='user', lazy='dynamic', cascade='all, delete-orphan')
    bills = db.relationship('Bill', backref='user', lazy='dynamic', cascade='all, delete-orphan')
    chat_messages = db.relationship('ChatMessage', backref='user', lazy='dynamic',
                                    cascade='all, delete-orphan',
                                    foreign_keys='ChatMessage.user_id')

    def set_password(self, password):
        salt = bcrypt.gensalt()
        self.password_hash = bcrypt.hashpw(password.encode('utf-8'), salt).decode('utf-8')

    def check_password(self, password):
        return bcrypt.checkpw(password.encode('utf-8'), self.password_hash.encode('utf-8'))

    def to_dict(self):
        return {
            'id': self.id,
            'email': self.email,
            'first_name': self.first_name,
            'last_name': self.last_name,
            'full_name': f"{self.first_name} {self.last_name}",
            'phone': self.phone,
            'account_mode': self.account_mode,
            'currency': self.currency,
            'monthly_income_preference': self.monthly_income_preference,
            'theme': self.theme,
            'notification_budget_alerts': self.notification_budget_alerts,
            'notification_goal_milestones': self.notification_goal_milestones,
            'notification_monthly_summary': self.notification_monthly_summary,
            'family_group_id': self.family_group_id,
            'created_at': self.created_at.isoformat() if self.created_at else None,
        }


class Transaction(db.Model):
    __tablename__ = 'transactions'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False, index=True)
    description = db.Column(db.String(255), nullable=False)
    amount = db.Column(db.Float, nullable=False)
    type = db.Column(db.String(20), nullable=False)  # income / expense
    category = db.Column(db.String(100), nullable=False)
    date = db.Column(db.Date, nullable=False, index=True)
    notes = db.Column(db.Text, nullable=True)
    payment_method = db.Column(db.String(50), nullable=True, default='Cash')
    is_shared = db.Column(db.Boolean, default=False)  # family shared expense
    family_group_id = db.Column(db.Integer, db.ForeignKey('family_groups.id'), nullable=True)
    created_at = db.Column(db.DateTime, default=_now)
    updated_at = db.Column(db.DateTime, default=_now, onupdate=_now)

    def to_dict(self):
        return {
            'id': self.id,
            'user_id': self.user_id,
            'description': self.description,
            'amount': self.amount,
            'type': self.type,
            'category': self.category,
            'date': self.date.isoformat() if self.date else None,
            'notes': self.notes,
            'payment_method': self.payment_method,
            'is_shared': self.is_shared,
            'family_group_id': self.family_group_id,
            'created_at': self.created_at.isoformat() if self.created_at else None,
        }


class Budget(db.Model):
    __tablename__ = 'budgets'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False, index=True)
    category = db.Column(db.String(100), nullable=False)
    limit_amount = db.Column(db.Float, nullable=False)
    period = db.Column(db.String(20), default='monthly')  # monthly
    month = db.Column(db.Integer, nullable=False)
    year = db.Column(db.Integer, nullable=False)
    notes = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, default=_now)
    updated_at = db.Column(db.DateTime, default=_now, onupdate=_now)

    __table_args__ = (
        db.UniqueConstraint('user_id', 'category', 'month', 'year', name='uq_budget_user_cat_period'),
    )

    def to_dict(self, spent=0.0):
        remaining = self.limit_amount - spent
        utilization = (spent / self.limit_amount * 100) if self.limit_amount > 0 else 0
        if utilization >= 100:
            status = 'over_budget'
        elif utilization >= 80:
            status = 'near_limit'
        else:
            status = 'within_budget'
        return {
            'id': self.id,
            'user_id': self.user_id,
            'category': self.category,
            'limit_amount': self.limit_amount,
            'period': self.period,
            'month': self.month,
            'year': self.year,
            'notes': self.notes,
            'spent': spent,
            'remaining': remaining,
            'utilization_percent': round(utilization, 1),
            'status': status,
            'created_at': self.created_at.isoformat() if self.created_at else None,
        }


class SavingsGoal(db.Model):
    __tablename__ = 'savings_goals'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False, index=True)
    name = db.Column(db.String(255), nullable=False)
    target_amount = db.Column(db.Float, nullable=False)
    current_amount = db.Column(db.Float, default=0.0)
    target_date = db.Column(db.Date, nullable=True)
    category = db.Column(db.String(100), default='Other')
    notes = db.Column(db.Text, nullable=True)
    is_completed = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=_now)
    updated_at = db.Column(db.DateTime, default=_now, onupdate=_now)

    def to_dict(self):
        remaining = max(0, self.target_amount - self.current_amount)
        progress = (self.current_amount / self.target_amount * 100) if self.target_amount > 0 else 0
        
        # Calculate monthly contribution needed
        monthly_needed = None
        if self.target_date and not self.is_completed:
            today = date.today()
            if self.target_date > today:
                months_remaining = (self.target_date.year - today.year) * 12 + (self.target_date.month - today.month)
                if months_remaining > 0 and remaining > 0:
                    monthly_needed = round(remaining / months_remaining, 2)

        return {
            'id': self.id,
            'user_id': self.user_id,
            'name': self.name,
            'target_amount': self.target_amount,
            'current_amount': self.current_amount,
            'remaining_amount': remaining,
            'progress_percent': round(min(100, progress), 1),
            'target_date': self.target_date.isoformat() if self.target_date else None,
            'category': self.category,
            'notes': self.notes,
            'is_completed': self.is_completed,
            'monthly_needed': monthly_needed,
            'created_at': self.created_at.isoformat() if self.created_at else None,
        }


class FinancialInsight(db.Model):
    __tablename__ = 'financial_insights'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False, index=True)
    title = db.Column(db.String(255), nullable=False)
    message = db.Column(db.Text, nullable=False)
    insight_type = db.Column(db.String(50), nullable=False)  # spending/savings/budget/goal/health
    priority = db.Column(db.String(20), default='medium')  # low/medium/high/critical
    category = db.Column(db.String(100), nullable=True)
    action_label = db.Column(db.String(100), nullable=True)
    action_url = db.Column(db.String(255), nullable=True)
    is_read = db.Column(db.Boolean, default=False)
    month = db.Column(db.Integer, nullable=True)
    year = db.Column(db.Integer, nullable=True)
    created_at = db.Column(db.DateTime, default=_now)

    def to_dict(self):
        return {
            'id': self.id,
            'user_id': self.user_id,
            'title': self.title,
            'message': self.message,
            'insight_type': self.insight_type,
            'priority': self.priority,
            'category': self.category,
            'action_label': self.action_label,
            'action_url': self.action_url,
            'is_read': self.is_read,
            'month': self.month,
            'year': self.year,
            'created_at': self.created_at.isoformat() if self.created_at else None,
        }


class Notification(db.Model):
    __tablename__ = 'notifications'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False, index=True)
    title = db.Column(db.String(255), nullable=False)
    message = db.Column(db.Text, nullable=False)
    notification_type = db.Column(db.String(50), nullable=False)  # budget/goal/summary/info
    is_read = db.Column(db.Boolean, default=False)
    link = db.Column(db.String(255), nullable=True)
    created_at = db.Column(db.DateTime, default=_now)

    def to_dict(self):
        return {
            'id': self.id,
            'user_id': self.user_id,
            'title': self.title,
            'message': self.message,
            'notification_type': self.notification_type,
            'is_read': self.is_read,
            'link': self.link,
            'created_at': self.created_at.isoformat() if self.created_at else None,
        }


class Bill(db.Model):
    """Recurring / scheduled bills and payments."""
    __tablename__ = 'bills'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False, index=True)
    name = db.Column(db.String(255), nullable=False)
    amount = db.Column(db.Float, nullable=False)
    category = db.Column(db.String(100), nullable=False, default='Utilities')
    frequency = db.Column(db.String(20), nullable=False, default='monthly')  # monthly/weekly/yearly/one-time
    due_day = db.Column(db.Integer, nullable=True)       # day of month (1–31) for monthly bills
    next_due_date = db.Column(db.Date, nullable=True)    # next expected due date
    is_active = db.Column(db.Boolean, default=True)
    auto_pay = db.Column(db.Boolean, default=False)
    notes = db.Column(db.Text, nullable=True)
    payment_method = db.Column(db.String(50), nullable=True, default='Net Banking')
    created_at = db.Column(db.DateTime, default=_now)
    updated_at = db.Column(db.DateTime, default=_now, onupdate=_now)

    def to_dict(self):
        today = date.today()
        days_until = None
        is_overdue = False
        if self.next_due_date:
            days_until = (self.next_due_date - today).days
            is_overdue = days_until < 0
        return {
            'id': self.id,
            'user_id': self.user_id,
            'name': self.name,
            'amount': self.amount,
            'category': self.category,
            'frequency': self.frequency,
            'due_day': self.due_day,
            'next_due_date': self.next_due_date.isoformat() if self.next_due_date else None,
            'is_active': self.is_active,
            'auto_pay': self.auto_pay,
            'notes': self.notes,
            'payment_method': self.payment_method,
            'days_until_due': days_until,
            'is_overdue': is_overdue,
            'created_at': self.created_at.isoformat() if self.created_at else None,
        }


class ChatMessage(db.Model):
    """Persisted advisor conversation messages."""
    __tablename__ = 'chat_messages'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True, index=True)
    # 'personal' requires auth; 'general' may be anonymous (user_id=None)
    advisor_type = db.Column(db.String(20), nullable=False, default='general')
    conversation_id = db.Column(db.String(64), nullable=False, index=True)
    role = db.Column(db.String(20), nullable=False)        # 'user' | 'assistant'
    content = db.Column(db.Text, nullable=False)
    ai_provider = db.Column(db.String(50), nullable=True)  # gemini / openai / builtin
    created_at = db.Column(db.DateTime, default=_now)

    def to_dict(self):
        return {
            'id': self.id,
            'user_id': self.user_id,
            'advisor_type': self.advisor_type,
            'conversation_id': self.conversation_id,
            'role': self.role,
            'content': self.content,
            'ai_provider': self.ai_provider,
            'created_at': self.created_at.isoformat() if self.created_at else None,
        }


class FamilyGroup(db.Model):
    __tablename__ = 'family_groups'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(255), nullable=False)
    created_by = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    description = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, default=_now)

    members = db.relationship('User', backref='family_group',
                              foreign_keys='User.family_group_id', lazy='dynamic')
    invitations = db.relationship('FamilyInvitation', backref='family_group',
                                  lazy='dynamic', cascade='all, delete-orphan',
                                  foreign_keys='FamilyInvitation.group_id')

    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'created_by': self.created_by,
            'description': self.description,
            'created_at': self.created_at.isoformat() if self.created_at else None,
        }


class FamilyInvitation(db.Model):
    """Pending invitations to join a family group."""
    __tablename__ = 'family_invitations'

    id = db.Column(db.Integer, primary_key=True)
    group_id = db.Column(db.Integer, db.ForeignKey('family_groups.id'), nullable=False, index=True)
    invited_email = db.Column(db.String(255), nullable=False)
    invited_by = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    status = db.Column(db.String(20), default='pending')  # pending / accepted / rejected
    created_at = db.Column(db.DateTime, default=_now)
    responded_at = db.Column(db.DateTime, nullable=True)

    __table_args__ = (
        db.UniqueConstraint('group_id', 'invited_email', name='uq_invitation_group_email'),
    )

    def to_dict(self):
        return {
            'id': self.id,
            'group_id': self.group_id,
            'invited_email': self.invited_email,
            'invited_by': self.invited_by,
            'status': self.status,
            'created_at': self.created_at.isoformat() if self.created_at else None,
        }


class FamilySavingsGoal(db.Model):
    """Shared savings goal for a family group."""
    __tablename__ = 'family_savings_goals'

    id = db.Column(db.Integer, primary_key=True)
    group_id = db.Column(db.Integer, db.ForeignKey('family_groups.id'), nullable=False, index=True)
    created_by = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    name = db.Column(db.String(255), nullable=False)
    target_amount = db.Column(db.Float, nullable=False)
    current_amount = db.Column(db.Float, default=0.0)
    target_date = db.Column(db.Date, nullable=True)
    category = db.Column(db.String(100), default='Other')
    notes = db.Column(db.Text, nullable=True)
    is_completed = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=_now)
    updated_at = db.Column(db.DateTime, default=_now, onupdate=_now)

    def to_dict(self):
        remaining = max(0, self.target_amount - self.current_amount)
        progress = (self.current_amount / self.target_amount * 100) if self.target_amount > 0 else 0

        monthly_needed = None
        if self.target_date and not self.is_completed:
            today = date.today()
            if self.target_date > today:
                months_remaining = (
                    (self.target_date.year - today.year) * 12
                    + (self.target_date.month - today.month)
                )
                if months_remaining > 0 and remaining > 0:
                    monthly_needed = round(remaining / months_remaining, 2)

        return {
            'id': self.id,
            'group_id': self.group_id,
            'created_by': self.created_by,
            'name': self.name,
            'target_amount': self.target_amount,
            'current_amount': self.current_amount,
            'remaining_amount': remaining,
            'progress_percent': round(min(100, progress), 1),
            'target_date': self.target_date.isoformat() if self.target_date else None,
            'category': self.category,
            'notes': self.notes,
            'is_completed': self.is_completed,
            'monthly_needed': monthly_needed,
            'created_at': self.created_at.isoformat() if self.created_at else None,
        }
