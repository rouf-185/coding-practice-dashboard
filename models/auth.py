"""
Authentication-related models.
"""
from datetime import datetime
from extensions import db


class PasswordResetToken(db.Model):
    """Token for password reset requests."""
    
    __tablename__ = 'password_reset_tokens'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    token = db.Column(db.String(64), unique=True, nullable=False)
    expires_at = db.Column(db.DateTime, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def is_expired(self) -> bool:
        """Check if the token has expired."""
        return datetime.utcnow() > self.expires_at
    
    def __repr__(self) -> str:
        return f'<PasswordResetToken {self.token[:8]}...>'


class EmailChangeRequest(db.Model):
    """Pending email change verification."""
    
    __tablename__ = 'email_change_requests'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    
    current_email = db.Column(db.String(120), nullable=False)
    new_email = db.Column(db.String(120), nullable=False)
    
    current_email_code = db.Column(db.String(10), nullable=False)
    new_email_code = db.Column(db.String(10), nullable=False)
    
    verified_current = db.Column(db.Boolean, default=False)
    verified_new = db.Column(db.Boolean, default=False)
    
    expires_at = db.Column(db.DateTime, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationship
    user = db.relationship(
        'User',
        backref=db.backref('email_change_requests', lazy=True, cascade='all, delete-orphan')
    )
    
    def is_expired(self) -> bool:
        """Check if the verification codes have expired."""
        return datetime.utcnow() > self.expires_at
