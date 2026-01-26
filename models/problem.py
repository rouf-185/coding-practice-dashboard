"""
Problem and ProblemHistory models.
"""
from datetime import datetime
from extensions import db


class Problem(db.Model):
    """Leetcode problem model."""
    
    __tablename__ = 'problems'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    
    # Problem details
    title = db.Column(db.String(255), nullable=False)
    leetcode_url = db.Column(db.Text, nullable=False)
    difficulty = db.Column(db.String(10), nullable=False)  # easy, medium, hard
    
    # Dates
    solved_date = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    last_practiced = db.Column(db.DateTime, nullable=True)
    
    # Stats
    practice_count = db.Column(db.Integer, default=0)
    
    # Relationships
    history = db.relationship(
        'ProblemHistory',
        backref='problem',
        lazy=True,
        cascade='all, delete-orphan',
        order_by='ProblemHistory.practiced_at.desc()'
    )
    
    def __repr__(self) -> str:
        return f'<Problem {self.title}>'


class ProblemHistory(db.Model):
    """Practice history for a problem."""
    
    __tablename__ = 'problem_history'
    
    id = db.Column(db.Integer, primary_key=True)
    problem_id = db.Column(db.Integer, db.ForeignKey('problems.id'), nullable=False)
    practiced_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    
    def __repr__(self) -> str:
        return f'<ProblemHistory {self.problem_id} at {self.practiced_at}>'
