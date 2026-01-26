"""
DailyGoal model - tracks daily practice goal achievement.
"""
from datetime import datetime, date
from extensions import db


class DailyGoal(db.Model):
    """Tracks whether daily practice goals were achieved."""
    
    __tablename__ = 'daily_goals'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    
    # The date this goal is for
    goal_date = db.Column(db.Date, nullable=False)
    
    # Goal tracking
    total_scheduled = db.Column(db.Integer, default=0)  # Problems scheduled for this day
    completed = db.Column(db.Integer, default=0)  # Problems completed
    achieved = db.Column(db.Boolean, default=False)  # Was goal met?
    
    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Unique constraint: one record per user per day
    __table_args__ = (
        db.UniqueConstraint('user_id', 'goal_date', name='unique_user_daily_goal'),
    )
    
    def __repr__(self) -> str:
        return f'<DailyGoal user={self.user_id} date={self.goal_date} {self.completed}/{self.total_scheduled}>'
