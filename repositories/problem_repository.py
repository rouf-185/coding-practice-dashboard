"""
Problem repository - Database operations for problems.
"""
from typing import Optional, List
from datetime import datetime
from extensions import db
from models import Problem, ProblemHistory


class ProblemRepository:
    """Repository for Problem database operations."""
    
    @staticmethod
    def get_by_id(problem_id: int, user_id: int) -> Optional[Problem]:
        """Get problem by ID for a specific user."""
        return Problem.query.filter_by(id=problem_id, user_id=user_id).first()
    
    @staticmethod
    def get_by_url(user_id: int, leetcode_url: str) -> Optional[Problem]:
        """Get problem by Leetcode URL for a specific user."""
        return Problem.query.filter_by(user_id=user_id, leetcode_url=leetcode_url).first()
    
    @staticmethod
    def get_all_for_user(user_id: int) -> List[Problem]:
        """Get all problems for a user."""
        return Problem.query.filter_by(user_id=user_id).all()
    
    @staticmethod
    def get_problems_by_solved_date(user_id: int, target_date) -> List[Problem]:
        """Get problems solved on a specific date."""
        return Problem.query.filter(
            Problem.user_id == user_id,
            db.func.date(Problem.solved_date) == target_date
        ).all()
    
    @staticmethod
    def get_problems_in_date_range(
        user_id: int,
        start_utc: datetime,
        end_utc: datetime
    ) -> List[Problem]:
        """Get problems solved within a UTC date range."""
        return Problem.query.filter(
            Problem.user_id == user_id,
            Problem.solved_date >= start_utc,
            Problem.solved_date < end_utc
        ).all()
    
    @staticmethod
    def get_problems_excluding_ids(user_id: int, exclude_ids: set) -> List[Problem]:
        """Get all problems for user except those in exclude_ids."""
        query = Problem.query.filter(Problem.user_id == user_id)
        if exclude_ids:
            query = query.filter(~Problem.id.in_(exclude_ids))
        return query.all()
    
    @staticmethod
    def get_paginated(
        user_id: int,
        page: int = 1,
        per_page: int = 10,
        search_query: Optional[str] = None
    ):
        """Get paginated problems with optional search."""
        query = Problem.query.filter_by(user_id=user_id)
        
        if search_query:
            query = query.filter(
                db.or_(
                    Problem.title.ilike(f'%{search_query}%'),
                    Problem.leetcode_url.ilike(f'%{search_query}%'),
                    Problem.difficulty.ilike(f'%{search_query}%')
                )
            )
        
        # Sort by most recently updated
        query = query.order_by(
            db.func.coalesce(Problem.last_practiced, Problem.created_at).desc()
        )
        
        return query.paginate(page=page, per_page=per_page, error_out=False)
    
    @staticmethod
    def create(
        user_id: int,
        title: str,
        leetcode_url: str,
        difficulty: str,
        solved_date: Optional[datetime] = None
    ) -> Problem:
        """Create a new problem."""
        now = solved_date or datetime.utcnow()
        problem = Problem(
            user_id=user_id,
            title=title,
            leetcode_url=leetcode_url,
            difficulty=difficulty,
            solved_date=now,
            last_practiced=now
        )
        db.session.add(problem)
        db.session.flush()  # Get the ID
        
        # Add initial history entry
        history = ProblemHistory(problem_id=problem.id, practiced_at=now)
        db.session.add(history)
        db.session.commit()
        
        return problem
    
    @staticmethod
    def update(problem: Problem) -> Problem:
        """Update problem in database."""
        db.session.commit()
        return problem
    
    @staticmethod
    def delete(problem: Problem) -> None:
        """Delete a problem (cascade deletes history)."""
        db.session.delete(problem)
        db.session.commit()
    
    @staticmethod
    def mark_practiced(problem: Problem) -> Problem:
        """Mark a problem as practiced (increment count, add history)."""
        problem.last_practiced = datetime.utcnow()
        problem.practice_count += 1
        
        history = ProblemHistory(problem_id=problem.id, practiced_at=datetime.utcnow())
        db.session.add(history)
        db.session.commit()
        
        return problem
    
    @staticmethod
    def add_history_entry(problem: Problem) -> ProblemHistory:
        """Add a practice history entry."""
        now = datetime.utcnow()
        problem.solved_date = now
        problem.last_practiced = now
        
        history = ProblemHistory(problem_id=problem.id, practiced_at=now)
        db.session.add(history)
        db.session.commit()
        
        return history
    
    @staticmethod
    def get_history_for_month(
        user_id: int,
        start_date: datetime,
        end_date: datetime
    ) -> List[ProblemHistory]:
        """Get practice history entries for a date range."""
        return db.session.query(ProblemHistory).join(Problem).filter(
            Problem.user_id == user_id,
            ProblemHistory.practiced_at >= start_date,
            ProblemHistory.practiced_at <= end_date
        ).all()
