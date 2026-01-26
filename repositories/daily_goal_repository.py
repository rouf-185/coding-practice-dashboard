"""
DailyGoal repository - Database operations for daily goals.
"""
from typing import Optional, List, Dict
from datetime import date, datetime
from extensions import db
from models import DailyGoal


class DailyGoalRepository:
    """Repository for DailyGoal database operations."""
    
    @staticmethod
    def get_for_date(user_id: int, goal_date: date) -> Optional[DailyGoal]:
        """Get daily goal for a specific date."""
        return DailyGoal.query.filter_by(
            user_id=user_id,
            goal_date=goal_date
        ).first()
    
    @staticmethod
    def get_for_date_range(
        user_id: int,
        start_date: date,
        end_date: date
    ) -> List[DailyGoal]:
        """Get daily goals for a date range."""
        return DailyGoal.query.filter(
            DailyGoal.user_id == user_id,
            DailyGoal.goal_date >= start_date,
            DailyGoal.goal_date <= end_date
        ).all()
    
    @staticmethod
    def get_for_month(user_id: int, year: int, month: int) -> Dict[int, DailyGoal]:
        """Get daily goals for a month, keyed by day number."""
        from calendar import monthrange
        
        days_in_month = monthrange(year, month)[1]
        start = date(year, month, 1)
        end = date(year, month, days_in_month)
        
        goals = DailyGoalRepository.get_for_date_range(user_id, start, end)
        return {g.goal_date.day: g for g in goals}
    
    @staticmethod
    def create_or_update(
        user_id: int,
        goal_date: date,
        total_scheduled: int,
        completed: int
    ) -> DailyGoal:
        """Create or update a daily goal record."""
        goal = DailyGoalRepository.get_for_date(user_id, goal_date)
        
        if goal:
            goal.total_scheduled = total_scheduled
            goal.completed = completed
            goal.achieved = completed >= total_scheduled and total_scheduled > 0
            goal.updated_at = datetime.utcnow()
        else:
            goal = DailyGoal(
                user_id=user_id,
                goal_date=goal_date,
                total_scheduled=total_scheduled,
                completed=completed,
                achieved=completed >= total_scheduled and total_scheduled > 0
            )
            db.session.add(goal)
        
        db.session.commit()
        return goal
    
    @staticmethod
    def increment_completed(user_id: int, goal_date: date, total_scheduled: int) -> DailyGoal:
        """Increment the completed count for a daily goal."""
        goal = DailyGoalRepository.get_for_date(user_id, goal_date)
        
        if goal:
            goal.completed += 1
            goal.total_scheduled = total_scheduled  # Update in case it changed
            goal.achieved = goal.completed >= goal.total_scheduled and goal.total_scheduled > 0
            goal.updated_at = datetime.utcnow()
        else:
            goal = DailyGoal(
                user_id=user_id,
                goal_date=goal_date,
                total_scheduled=total_scheduled,
                completed=1,
                achieved=1 >= total_scheduled and total_scheduled > 0
            )
            db.session.add(goal)
        
        db.session.commit()
        return goal
