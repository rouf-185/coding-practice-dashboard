"""
Authentication service - Business logic for auth operations.
"""
from typing import Optional, Tuple
from flask import session
from repositories import UserRepository, AuthRepository
from models import User


class AuthService:
    """Service for authentication operations."""
    
    @staticmethod
    def login(username: str, password: str) -> Tuple[bool, str]:
        """
        Attempt to log in a user.
        
        Returns:
            Tuple of (success, message)
        """
        if not username or not password:
            return False, 'Please provide both username and password.'
        
        user = UserRepository.get_by_username(username)
        
        if user and user.check_password(password):
            session['user_id'] = user.id
            session['username'] = user.username
            return True, 'Login successful!'
        
        return False, 'Invalid username or password.'
    
    @staticmethod
    def register(
        username: str,
        email: str,
        password: str,
        password_confirm: str
    ) -> Tuple[bool, str]:
        """
        Register a new user.
        
        Returns:
            Tuple of (success, message)
        """
        if not username or not email or not password:
            return False, 'Please fill in all fields.'
        
        if password != password_confirm:
            return False, 'Passwords do not match.'
        
        if len(password) < 8:
            return False, 'Password must be at least 8 characters long.'
        
        if UserRepository.username_exists(username):
            return False, 'Username already exists.'
        
        if UserRepository.email_exists(email):
            return False, 'Email already exists.'
        
        UserRepository.create(username, email, password)
        return True, 'Registration successful! Please login.'
    
    @staticmethod
    def logout() -> None:
        """Log out the current user."""
        session.clear()
    
    @staticmethod
    def get_current_user() -> Optional[User]:
        """Get the currently logged in user."""
        user_id = session.get('user_id')
        if not user_id:
            return None
        return UserRepository.get_by_id(user_id)
    
    @staticmethod
    def change_password(
        user: User,
        current_password: str,
        new_password: str,
        new_password_confirm: str
    ) -> Tuple[bool, str]:
        """
        Change user's password.
        
        Returns:
            Tuple of (success, message)
        """
        if not current_password or not new_password or not new_password_confirm:
            return False, 'Please fill in all fields.'
        
        if not user.check_password(current_password):
            return False, 'Current password is incorrect.'
        
        if new_password != new_password_confirm:
            return False, 'New passwords do not match.'
        
        if len(new_password) < 8:
            return False, 'New password must be at least 8 characters long.'
        
        if user.check_password(new_password):
            return False, 'New password must be different from the current password.'
        
        user.set_password(new_password)
        UserRepository.update(user)
        session.clear()
        
        return True, 'Password changed. Please log in again.'
    
    @staticmethod
    def request_password_reset(email: str) -> Tuple[bool, str, Optional[str]]:
        """
        Create a password reset token.
        
        Returns:
            Tuple of (success, message, token or None)
        """
        if not email:
            return False, 'Please provide your email address.', None
        
        user = UserRepository.get_by_email(email)
        
        # Always return same message for security
        if not user:
            return True, 'If an account exists with this email, a password reset link has been sent.', None
        
        reset_token = AuthRepository.create_reset_token(user)
        return True, 'If an account exists with this email, a password reset link has been sent.', reset_token.token
    
    @staticmethod
    def reset_password(
        token: str,
        new_password: str,
        new_password_confirm: str
    ) -> Tuple[bool, str]:
        """
        Reset password using a token.
        
        Returns:
            Tuple of (success, message)
        """
        from urllib.parse import unquote
        token = unquote(token)
        
        reset_token = AuthRepository.get_reset_token(token)
        
        if not reset_token:
            return False, 'Invalid reset token. Please request a new password reset.'
        
        if reset_token.is_expired():
            return False, 'Reset token has expired. Please request a new password reset.'
        
        if not new_password or not new_password_confirm:
            return False, 'Please fill in all fields.'
        
        if new_password != new_password_confirm:
            return False, 'Passwords do not match.'
        
        if len(new_password) < 8:
            return False, 'Password must be at least 8 characters long.'
        
        user = reset_token.user
        user.set_password(new_password)
        AuthRepository.delete_reset_token(reset_token)
        
        return True, 'Password reset successful! Please login.'
    
    @staticmethod
    def validate_reset_token(token: str) -> Tuple[bool, str]:
        """
        Validate a reset token.
        
        Returns:
            Tuple of (valid, message)
        """
        from urllib.parse import unquote
        token = unquote(token)
        
        reset_token = AuthRepository.get_reset_token(token)
        
        if not reset_token:
            return False, 'Invalid reset token. Please request a new password reset.'
        
        if reset_token.is_expired():
            return False, 'Reset token has expired. Please request a new password reset.'
        
        return True, ''
