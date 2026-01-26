"""
Problem service - Business logic for problem operations.
"""
from typing import Optional, Tuple, List, Set
from datetime import datetime, timedelta
from urllib.parse import urlparse
from repositories import ProblemRepository, DailyGoalRepository
from models import Problem


class ProblemService:
    """Service for problem-related operations."""
    
    PRACTICE_INTERVALS = [2, 5, 10, 30]  # Days ago
    
    @staticmethod
    def add_problem(
        user_id: int,
        leetcode_url: str,
        form_difficulty: Optional[str] = None
    ) -> Tuple[bool, str]:
        """
        Add a new problem or update existing one.
        
        Returns:
            Tuple of (success, message)
        """
        if not leetcode_url:
            return False, 'Please provide a Leetcode URL.'
        
        # Normalize URL
        leetcode_url = leetcode_url.strip().rstrip('/')
        
        # Check if problem already exists
        existing = ProblemRepository.get_by_url(user_id, leetcode_url)
        
        if existing:
            ProblemRepository.add_history_entry(existing)
            return True, 'Problem already exists. Added to history!'
        
        # Try to scrape problem details
        from utils.scraper import scrape_leetcode_problem
        problem_data = scrape_leetcode_problem(leetcode_url)
        
        if not problem_data:
            # Extract from URL as fallback
            problem_data = ProblemService._extract_from_url(leetcode_url, form_difficulty)
            
            if not problem_data:
                return False, 'Failed to scrape problem details. Please check the URL and try again.'
        
        # Determine difficulty
        if form_difficulty and form_difficulty.lower() in ['easy', 'medium', 'hard']:
            difficulty = form_difficulty.lower()
        else:
            difficulty = problem_data.get('difficulty', 'medium')
        
        # Create the problem
        ProblemRepository.create(
            user_id=user_id,
            title=problem_data['title'],
            leetcode_url=leetcode_url,
            difficulty=difficulty
        )
        
        return True, 'Problem added successfully!'
    
    @staticmethod
    def _extract_from_url(
        url: str,
        form_difficulty: Optional[str] = None
    ) -> Optional[dict]:
        """Extract problem info from URL slug."""
        parsed = urlparse(url)
        path_parts = parsed.path.strip('/').split('/')
        
        if 'problems' in path_parts:
            idx = path_parts.index('problems')
            if idx + 1 < len(path_parts):
                slug = path_parts[idx + 1]
                title = ' '.join(word.capitalize() for word in slug.split('-'))
                difficulty = form_difficulty if form_difficulty in ['easy', 'medium', 'hard'] else 'medium'
                return {'title': title, 'difficulty': difficulty}
        
        return None
    
    @staticmethod
    def _get_scheduled_problem_ids(user_id: int) -> Set[int]:
        """Get the set of problem IDs scheduled for practice today."""
        today = datetime.utcnow().date()
        problem_ids = set()
        
        # Problems solved N days ago
        for days_ago in ProblemService.PRACTICE_INTERVALS:
            target_date = today - timedelta(days=days_ago)
            date_problems = ProblemRepository.get_problems_by_solved_date(user_id, target_date)
            for p in date_problems:
                problem_ids.add(p.id)
        
        # Weekend random problems (Saturday=5, Sunday=6)
        if today.weekday() in [5, 6]:
            remaining = ProblemRepository.get_problems_excluding_ids(user_id, problem_ids)
            if remaining:
                import random
                date_str = today.strftime('%m-%d-%Y')
                random.seed(hash(date_str))
                random.shuffle(remaining)
                for p in remaining[:min(2, len(remaining))]:
                    problem_ids.add(p.id)
        
        return problem_ids
    
    @staticmethod
    def _count_completed_today(user_id: int, scheduled_ids: Set[int]) -> int:
        """Count how many scheduled problems were completed today."""
        today = datetime.utcnow().date()
        twelve_hours_ago = datetime.utcnow() - timedelta(hours=12)
        
        completed = 0
        for problem_id in scheduled_ids:
            problem = ProblemRepository.get_by_id(problem_id, user_id)
            if not problem:
                continue
            
            # Check if practiced today (within last 12 hours to match dashboard logic)
            if problem.last_practiced and problem.last_practiced >= twelve_hours_ago:
                completed += 1
            elif problem.solved_date and problem.solved_date >= twelve_hours_ago:
                completed += 1
        
        return completed
    
    @staticmethod
    def mark_done(user_id: int, problem_id: int) -> Tuple[bool, str]:
        """
        Mark a problem as practiced and update daily goal tracking.
        
        Returns:
            Tuple of (success, message)
        """
        problem = ProblemRepository.get_by_id(problem_id, user_id)
        
        if not problem:
            return False, 'Problem not found.'
        
        ProblemRepository.mark_practiced(problem)
        
        # Update daily goal tracking
        today = datetime.utcnow().date()
        scheduled_ids = ProblemService._get_scheduled_problem_ids(user_id)
        total_scheduled = len(scheduled_ids)
        
        # Count completed (including the one just marked)
        completed = ProblemService._count_completed_today(user_id, scheduled_ids)
        
        # Update or create daily goal record
        DailyGoalRepository.create_or_update(
            user_id=user_id,
            goal_date=today,
            total_scheduled=total_scheduled,
            completed=completed
        )
        
        return True, 'Problem marked as done!'
    
    @staticmethod
    def delete_problem(user_id: int, problem_id: int) -> Tuple[bool, str]:
        """
        Delete a problem.
        
        Returns:
            Tuple of (success, message)
        """
        problem = ProblemRepository.get_by_id(problem_id, user_id)
        
        if not problem:
            return False, 'Problem not found.'
        
        ProblemRepository.delete(problem)
        return True, 'Problem deleted successfully!'
    
    @staticmethod
    def get_problem_history(user_id: int, problem_id: int) -> Optional[dict]:
        """Get problem history for display."""
        problem = ProblemRepository.get_by_id(problem_id, user_id)
        
        if not problem:
            return None
        
        history = [
            {
                'practiced_at': entry.practiced_at.strftime('%Y-%m-%d %H:%M:%S'),
                'date': entry.practiced_at.strftime('%Y-%m-%d'),
                'time': entry.practiced_at.strftime('%H:%M:%S')
            }
            for entry in problem.history
        ]
        
        return {
            'title': problem.title,
            'created_at': problem.created_at.strftime('%Y-%m-%d %H:%M:%S'),
            'practice_count': problem.practice_count,
            'total_sessions': len(history),
            'history': history
        }
