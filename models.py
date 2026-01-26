from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash

db = SQLAlchemy()


class User(db.Model):
    __tablename__ = 'users'
    
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    profile_image = db.Column(db.String(255), nullable=True)  # static-relative path: uploads/avatars/<file>
    timezone = db.Column(db.String(64), nullable=True, default='UTC')  # IANA timezone, e.g. 'America/New_York'
    daily_email_enabled = db.Column(db.Boolean, default=False)
    daily_email_time = db.Column(db.String(5), nullable=True, default='06:00')  # HH:MM (local)
    daily_email_last_sent_at = db.Column(db.DateTime, nullable=True)  # stored as UTC
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    problems = db.relationship('Problem', backref='user', lazy=True, cascade='all, delete-orphan')
    reset_tokens = db.relationship('PasswordResetToken', backref='user', lazy=True, cascade='all, delete-orphan')
    
    def set_password(self, password):
        self.password_hash = generate_password_hash(password)
    
    def check_password(self, password):
        return check_password_hash(self.password_hash, password)
    
    def __repr__(self):
        return f'<User {self.username}>'


class Problem(db.Model):
    __tablename__ = 'problems'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    title = db.Column(db.String(255), nullable=False)
    leetcode_url = db.Column(db.Text, nullable=False)
    difficulty = db.Column(db.String(10), nullable=False)  # easy, medium, hard
    solved_date = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    last_practiced = db.Column(db.DateTime, nullable=True)
    practice_count = db.Column(db.Integer, default=0)  # Total number of practice sessions
    
    history = db.relationship('ProblemHistory', backref='problem', lazy=True, cascade='all, delete-orphan', order_by='ProblemHistory.practiced_at.desc()')
    
    def __repr__(self):
        return f'<Problem {self.title}>'


class ProblemHistory(db.Model):
    __tablename__ = 'problem_history'
    
    id = db.Column(db.Integer, primary_key=True)
    problem_id = db.Column(db.Integer, db.ForeignKey('problems.id'), nullable=False)
    practiced_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    
    def __repr__(self):
        return f'<ProblemHistory {self.problem_id} at {self.practiced_at}>'


class PasswordResetToken(db.Model):
    __tablename__ = 'password_reset_tokens'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    token = db.Column(db.String(64), unique=True, nullable=False)
    expires_at = db.Column(db.DateTime, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def is_expired(self):
        return datetime.utcnow() > self.expires_at
    
    def __repr__(self):
        return f'<PasswordResetToken {self.token[:8]}...>'


class EmailChangeRequest(db.Model):
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

    user = db.relationship('User', backref=db.backref('email_change_requests', lazy=True, cascade='all, delete-orphan'))

    def is_expired(self):
        return datetime.utcnow() > self.expires_at


