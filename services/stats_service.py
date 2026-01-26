"""
Stats service - Business logic for practice statistics.
"""
from typing import Dict, Any, List
from datetime import datetime, timedelta
from calendar import monthrange
from repositories import ProblemRepository
from models import Problem


class StatsService:
    """Service for statistics calculations."""
    
    @staticmethod
    def get_practice_stats(user_id: int) -> Dict[str, int]:
        """
        Calculate practice statistics for a user.
        
        Returns:
            Dictionary with stats counts.
        """
        all_problems = ProblemRepository.get_all_for_user(user_id)
        today = datetime.utcnow().date()
        yesterday = today - timedelta(days=1)
        
        # Count by practice level
        fully_practiced = sum(1 for p in all_problems if p.practice_count >= 3)
        partially_practiced = sum(1 for p in all_problems if p.practice_count == 2)
        solved_once = sum(1 for p in all_problems if p.practice_count == 1)
        not_practiced = sum(1 for p in all_problems if p.practice_count == 0)
        
        # Count practiced today and yesterday
        practiced_today_set = set()
        practiced_yesterday_set = set()
        
        for problem in all_problems:
            # Check last_practiced
            if problem.last_practiced:
                if problem.last_practiced.date() == today:
                    practiced_today_set.add(problem.id)
                elif problem.last_practiced.date() == yesterday:
                    practiced_yesterday_set.add(problem.id)
            
            # Check solved_date (if added today, counts as practiced today)
            if problem.solved_date.date() == today:
                practiced_today_set.add(problem.id)
            
            # Check history entries
            if problem.history:
                for entry in problem.history:
                    entry_date = entry.practiced_at.date()
                    if entry_date == today:
                        practiced_today_set.add(problem.id)
                    elif entry_date == yesterday:
                        practiced_yesterday_set.add(problem.id)
        
        return {
            'fully_practiced': fully_practiced,
            'partially_practiced': partially_practiced,
            'solved_once': solved_once,
            'not_practiced': not_practiced,
            'practiced_today': len(practiced_today_set),
            'practiced_yesterday': len(practiced_yesterday_set),
            'total': len(all_problems)
        }
    
    @staticmethod
    def get_monthly_practice_data(
        user_id: int,
        year: int,
        month: int
    ) -> Dict[str, Any]:
        """
        Get practice data for a specific month.
        
        Returns:
            Dictionary with days, counts, year, and month.
        """
        # Get date range
        days_in_month = monthrange(year, month)[1]
        start_date = datetime(year, month, 1)
        end_date = datetime(year, month, days_in_month, 23, 59, 59)
        
        # Get history entries for the month
        history_entries = ProblemRepository.get_history_for_month(
            user_id, start_date, end_date
        )
        
        # Count per day
        daily_counts = {}
        for entry in history_entries:
            day = entry.practiced_at.day
            daily_counts[day] = daily_counts.get(day, 0) + 1
        
        # Build response
        days = list(range(1, days_in_month + 1))
        counts = [daily_counts.get(day, 0) for day in days]
        
        return {
            'days': days,
            'counts': counts,
            'year': year,
            'month': month
        }
