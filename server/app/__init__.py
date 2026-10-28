from flask import Flask
from flask_cors import CORS
from flask_jwt_extended import JWTManager
from .extensions import db
from config import config
import os


def create_app(config_name=None):
    if config_name is None:
        config_name = os.environ.get('FLASK_ENV', 'development')

    app = Flask(__name__)
    app.config.from_object(config.get(config_name, config['default']))

    # Initialize extensions
    db.init_app(app)
    JWTManager(app)
    CORS(app, resources={r"/api/*": {"origins": app.config['CORS_ORIGINS']}},
         supports_credentials=True)

    # Initialise MongoDB (optional — does not crash if unavailable)
    from .mongo import init_mongo
    init_mongo(app)

    # Register blueprints
    from .routes.auth import auth_bp
    from .routes.transactions import transactions_bp
    from .routes.dashboard import dashboard_bp
    from .routes.budgets import budgets_bp
    from .routes.goals import goals_bp
    from .routes.advisor import advisor_bp
    from .routes.reports import reports_bp
    from .routes.profile import profile_bp
    from .routes.notifications import notifications_bp
    from .routes.family import family_bp
    from .routes.bills import bills_bp

    app.register_blueprint(auth_bp, url_prefix='/api/auth')
    app.register_blueprint(transactions_bp, url_prefix='/api/transactions')
    app.register_blueprint(dashboard_bp, url_prefix='/api/dashboard')
    app.register_blueprint(budgets_bp, url_prefix='/api/budgets')
    app.register_blueprint(goals_bp, url_prefix='/api/goals')
    app.register_blueprint(advisor_bp, url_prefix='/api/advisor')
    app.register_blueprint(reports_bp, url_prefix='/api/reports')
    app.register_blueprint(profile_bp, url_prefix='/api/profile')
    app.register_blueprint(notifications_bp, url_prefix='/api/notifications')
    app.register_blueprint(family_bp, url_prefix='/api/family')
    app.register_blueprint(bills_bp, url_prefix='/api/bills')

    with app.app_context():
        db.create_all()

    return app
