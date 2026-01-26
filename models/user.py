"""
User model.
"""
from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash
from extensions import db


class User(db.Model):
    """User account model."""
    
    __tablename__ = 'users'
    
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    
    # Profile
    profile_image = db.Column(db.String(255), nullable=True)
    
    # Preferences
    timezone = db.Column(db.String(64), nullable=True, default='UTC')
    
    # Daily email settings
    daily_email_enabled = db.Column(db.Boolean, default=False)
    daily_email_time = db.Column(db.String(5), nullable=True, default='06:00')
    daily_email_last_sent_at = db.Column(db.DateTime, nullable=True)
    
    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    problems = db.relationship(
        'Problem',
        backref='user',
        lazy=True,
        cascade='all, delete-orphan'
    )
    reset_tokens = db.relationship(
        'PasswordResetToken',
        backref='user',
        lazy=True,
        cascade='all, delete-orphan'
    )
    
    def set_password(self, password: str) -> None:
        """Hash and set the user's password."""
        self.password_hash = generate_password_hash(password)
    
    def check_password(self, password: str) -> bool:
        """Check if the provided password matches the hash."""
        return check_password_hash(self.password_hash, password)
    
    def __repr__(self) -> str:
        return f'<User {self.username}>'
