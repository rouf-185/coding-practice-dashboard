"""
Practice service - Business logic for spaced repetition practice.
"""
from typing import List, Dict, Any
from datetime import datetime, timedelta
import random
from zoneinfo import ZoneInfo
from repositories import ProblemRepository
from models import User, Problem


class PracticeService:
    """Service for practice-related operations."""
    
    PRACTICE_INTERVALS = [2, 5, 10, 30]  # Days ago
    
    @staticmethod
    def get_user_timezone(user: User) -> ZoneInfo:
        """Get user's timezone as ZoneInfo object."""
        tz_name = (getattr(user, 'timezone', None) or 'UTC').strip()
        try:
            return ZoneInfo(tz_name)
        except Exception:
            return ZoneInfo('UTC')
    
    @staticmethod
    def _local_day_bounds_to_utc(
        user_tz: ZoneInfo,
        local_day
    ) -> tuple[datetime, datetime]:
        """
        Convert a local day to UTC datetime bounds.
        
        Returns:
            Tuple of (start_utc_naive, end_utc_naive) covering local_day [00:00, 24:00)
        """
        from datetime import time as dtime
        start_local = datetime.combine(local_day, dtime.min).replace(tzinfo=user_tz)
        end_local = start_local + timedelta(days=1)
        start_utc = start_local.astimezone(ZoneInfo('UTC')).replace(tzinfo=None)
        end_utc = end_local.astimezone(ZoneInfo('UTC')).replace(tzinfo=None)
        return start_utc, end_utc
    
    @staticmethod
    def get_problems_to_practice(user_id: int) -> Dict[str, List[Dict[str, Any]]]:
        """
        Get grouped problems to practice today.
        
        Returns:
            Dictionary with category names as keys and lists of problem dicts as values.
            Each problem dict has 'problem' (Problem object) and 'solved_recently' (bool).
        """
        today = datetime.utcnow().date()
        problems = []
        problem_ids = set()
        
        # Problems solved N days ago
        for days_ago in PracticeService.PRACTICE_INTERVALS:
            target_date = today - timedelta(days=days_ago)
            date_problems = ProblemRepository.get_problems_by_solved_date(user_id, target_date)
            
            for problem in date_problems:
                if problem.id not in problem_ids:
                    problem_ids.add(problem.id)
                    problems.append({
                        'problem': problem,
                        'category': f'Solved {days_ago} days ago'
                    })
        
        # Weekend random problems (Saturday=5, Sunday=6)
        if today.weekday() in [5, 6]:
            remaining = ProblemRepository.get_problems_excluding_ids(user_id, problem_ids)
            if remaining:
                # Use date-based seed for consistent random selection per day
                date_str = today.strftime('%m-%d-%Y')
                random.seed(hash(date_str))
                random.shuffle(remaining)
                
                for problem in remaining[:min(2, len(remaining))]:
                    problem_ids.add(problem.id)
                    problems.append({
                        'problem': problem,
                        'category': 'Random Practice'
                    })
        
        # Group by category and add solved_recently flag
        grouped = {}
        now = datetime.utcnow()
        twelve_hours_ago = now - timedelta(hours=12)
        
        for item in problems:
            category = item['category']
            if category not in grouped:
                grouped[category] = []
            
            problem = item['problem']
            solved_recently = False
            
            if problem.last_practiced:
                solved_recently = problem.last_practiced >= twelve_hours_ago
            elif problem.solved_date:
                solved_recently = problem.solved_date >= twelve_hours_ago
            
            grouped[category].append({
                'problem': problem,
                'solved_recently': solved_recently
            })
        
        return grouped
    
    @staticmethod
    def get_practice_items_for_email(user: User, utc_now: datetime) -> List[Dict[str, str]]:
        """
        Get today's practice list for email (timezone-aware).
        
        Returns:
            List of dicts with title, leetcode_url, difficulty.
        """
        user_tz = PracticeService.get_user_timezone(user)
        local_now = utc_now.replace(tzinfo=ZoneInfo('UTC')).astimezone(user_tz)
        local_today = local_now.date()
        
        items = []
        seen_ids = set()
        
        # Problems solved N days ago (based on user's local date)
        for days_ago in PracticeService.PRACTICE_INTERVALS:
            target_local_day = local_today - timedelta(days=days_ago)
            start_utc, end_utc = PracticeService._local_day_bounds_to_utc(user_tz, target_local_day)
            
            problems = ProblemRepository.get_problems_in_date_range(
                user.id, start_utc, end_utc
            )
            
            for p in problems:
                if p.id not in seen_ids:
                    seen_ids.add(p.id)
                    items.append({
                        'title': p.title,
                        'leetcode_url': p.leetcode_url,
                        'difficulty': p.difficulty
                    })
        
        # Weekend random problems
        if local_today.weekday() in [5, 6]:
            remaining = ProblemRepository.get_problems_excluding_ids(user.id, seen_ids)
            
            date_str = local_today.strftime('%m-%d-%Y')
            random.seed(hash(f"{user.id}-{date_str}"))
            random.shuffle(remaining)
            
            for p in remaining[:min(2, len(remaining))]:
                if p.id not in seen_ids:
                    seen_ids.add(p.id)
                    items.append({
                        'title': p.title,
                        'leetcode_url': p.leetcode_url,
                        'difficulty': p.difficulty
                    })
        
        return items
