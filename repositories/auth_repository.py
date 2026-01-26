"""
Auth repository - Database operations for authentication tokens.
"""
from typing import Optional
from datetime import datetime, timedelta
import secrets
from extensions import db
from models import PasswordResetToken, EmailChangeRequest, User


class AuthRepository:
    """Repository for authentication-related database operations."""
    
    # ===== Password Reset Tokens =====
    
    @staticmethod
    def get_reset_token(token: str) -> Optional[PasswordResetToken]:
        """Get a password reset token by token string."""
        return PasswordResetToken.query.filter_by(token=token).first()
    
    @staticmethod
    def create_reset_token(user: User, expires_hours: int = 1) -> PasswordResetToken:
        """Create a new password reset token for a user."""
        # Delete any existing tokens
        PasswordResetToken.query.filter_by(user_id=user.id).delete()
        
        token = secrets.token_urlsafe(32)
        expires_at = datetime.utcnow() + timedelta(hours=expires_hours)
        
        reset_token = PasswordResetToken(
            user_id=user.id,
            token=token,
            expires_at=expires_at
        )
        db.session.add(reset_token)
        db.session.commit()
        
        return reset_token
    
    @staticmethod
    def delete_reset_token(reset_token: PasswordResetToken) -> None:
        """Delete a password reset token."""
        db.session.delete(reset_token)
        db.session.commit()
    
    # ===== Email Change Requests =====
    
    @staticmethod
    def get_email_change_request(user_id: int) -> Optional[EmailChangeRequest]:
        """Get the most recent email change request for a user."""
        return EmailChangeRequest.query.filter_by(user_id=user_id) \
            .order_by(EmailChangeRequest.created_at.desc()).first()
    
    @staticmethod
    def create_email_change_request(
        user: User,
        new_email: str,
        expires_minutes: int = 10
    ) -> EmailChangeRequest:
        """Create a new email change request."""
        # Delete any existing requests
        EmailChangeRequest.query.filter_by(user_id=user.id).delete()
        
        current_code = f"{secrets.randbelow(1_000_000):06d}"
        new_code = f"{secrets.randbelow(1_000_000):06d}"
        expires_at = datetime.utcnow() + timedelta(minutes=expires_minutes)
        
        request = EmailChangeRequest(
            user_id=user.id,
            current_email=user.email,
            new_email=new_email,
            current_email_code=current_code,
            new_email_code=new_code,
            expires_at=expires_at
        )
        db.session.add(request)
        db.session.commit()
        
        return request
    
    @staticmethod
    def delete_email_change_request(request: EmailChangeRequest) -> None:
        """Delete an email change request."""
        db.session.delete(request)
        db.session.commit()
    
    @staticmethod
    def cleanup_expired_request(request: EmailChangeRequest) -> bool:
        """Delete request if expired. Returns True if deleted."""
        if request and request.is_expired():
            db.session.delete(request)
            db.session.commit()
            return True
        return False
