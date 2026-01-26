"""
CodingFlashcard - A spaced repetition coding practice tracker.

Main application factory and entry point.
"""
import os
from flask import Flask
from config import get_config
from extensions import db


def create_app(config_class=None):
    """Create and configure the Flask application."""
    app = Flask(__name__)
    
    # Load configuration
    if config_class is None:
        config_class = get_config()
    app.config.from_object(config_class)
    
    # Initialize extensions
    db.init_app(app)
    
    # Register blueprints
    from routes import register_blueprints
    register_blueprints(app)
    
    # Create database tables and run migrations
    with app.app_context():
        _create_tables()
        _migrate_database()
    
    return app


def _create_tables():
    """Create database tables if they don't exist."""
    # Import models to register them with SQLAlchemy
    from models import User, Problem, ProblemHistory, PasswordResetToken, EmailChangeRequest, DailyGoal
    db.create_all()


def _migrate_database():
    """Run database migrations for schema changes."""
    from sqlalchemy import text
    
    # Check and add missing columns
    migrations = [
        # User table migrations
        ("users", "profile_image", "VARCHAR(255)"),
        ("users", "timezone", "VARCHAR(64) DEFAULT 'UTC'"),
        ("users", "daily_email_enabled", "BOOLEAN DEFAULT 0"),
        ("users", "daily_email_time", "VARCHAR(5) DEFAULT '06:00'"),
        ("users", "daily_email_last_sent_at", "DATETIME"),
        
        # Problem table migrations
        ("problems", "practice_count", "INTEGER DEFAULT 0"),
        ("problems", "last_practiced", "DATETIME"),
    ]
    
    for table, column, column_type in migrations:
        if not _column_exists(table, column):
            try:
                db.session.execute(text(f"ALTER TABLE {table} ADD COLUMN {column} {column_type}"))
                db.session.commit()
                print(f"Added column {column} to {table}")
            except Exception as e:
                db.session.rollback()
                print(f"Migration error ({table}.{column}): {e}")
    
    # Create tables that might be missing
    _create_tables()


def _column_exists(table: str, column: str) -> bool:
    """Check if a column exists in a table."""
    from sqlalchemy import text
    try:
        result = db.session.execute(text(f"PRAGMA table_info({table})"))
        columns = [row[1] for row in result.fetchall()]
        return column in columns
    except Exception:
        return False


# Create the application instance
app = create_app()


if __name__ == '__main__':
    debug = os.getenv('FLASK_DEBUG', 'true').lower() == 'true'
    host = os.getenv('FLASK_HOST', '0.0.0.0')
    port = int(os.getenv('FLASK_PORT', 5000))
    
    app.run(debug=debug, host=host, port=port)
