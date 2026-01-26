"""
Routes package - Endpoint layer.

All routes are organized into blueprints for modularity.
"""
from routes.auth import auth_bp
from routes.dashboard import dashboard_bp
from routes.problems import problems_bp
from routes.settings import settings_bp
from routes.api import api_bp


def register_blueprints(app):
    """Register all blueprints with the Flask app."""
    app.register_blueprint(auth_bp)
    app.register_blueprint(dashboard_bp)
    app.register_blueprint(problems_bp)
    app.register_blueprint(settings_bp)
    app.register_blueprint(api_bp)


__all__ = [
    'register_blueprints',
    'auth_bp',
    'dashboard_bp',
    'problems_bp',
    'settings_bp',
    'api_bp',
]
