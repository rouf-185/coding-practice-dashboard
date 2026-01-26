"""
User repository - Database operations for users.
"""
from typing import Optional, List
from extensions import db
from models import User


class UserRepository:
    """Repository for User database operations."""
    
    @staticmethod
    def get_by_id(user_id: int) -> Optional[User]:
        """Get user by ID."""
        return User.query.get(user_id)
    
    @staticmethod
    def get_by_username(username: str) -> Optional[User]:
        """Get user by username."""
        return User.query.filter_by(username=username).first()
    
    @staticmethod
    def get_by_email(email: str) -> Optional[User]:
        """Get user by email."""
        return User.query.filter_by(email=email).first()
    
    @staticmethod
    def username_exists(username: str, exclude_user_id: Optional[int] = None) -> bool:
        """Check if username is already taken."""
        query = User.query.filter(User.username == username)
        if exclude_user_id:
            query = query.filter(User.id != exclude_user_id)
        return query.first() is not None
    
    @staticmethod
    def email_exists(email: str, exclude_user_id: Optional[int] = None) -> bool:
        """Check if email is already taken."""
        query = User.query.filter(User.email == email)
        if exclude_user_id:
            query = query.filter(User.id != exclude_user_id)
        return query.first() is not None
    
    @staticmethod
    def create(username: str, email: str, password: str) -> User:
        """Create a new user."""
        user = User(username=username, email=email)
        user.set_password(password)
        db.session.add(user)
        db.session.commit()
        return user
    
    @staticmethod
    def update(user: User) -> User:
        """Update user in database."""
        db.session.commit()
        return user
    
    @staticmethod
    def get_users_with_daily_email_enabled() -> List[User]:
        """Get all users who have daily email enabled."""
        return User.query.filter(User.daily_email_enabled == True).all()  # noqa: E712
