"""
Dashboard routes - main dashboard view.
"""
from datetime import datetime
from flask import Blueprint, render_template, redirect, url_for
from services import AuthService, PracticeService, StatsService
from utils.decorators import require_login

dashboard_bp = Blueprint('dashboard', __name__)


@dashboard_bp.route('/')
@require_login
def index():
    """Main dashboard showing problems to practice."""
    user = AuthService.get_current_user()
    
    if not user:
        return redirect(url_for('auth.login'))
    
    # Get practice problems grouped by category
    grouped_problems = PracticeService.get_problems_to_practice(user.id)
    
    # Get practice statistics
    stats = StatsService.get_practice_stats(user.id)
    
    # Calculate today's goal progress
    total_today = 0
    done_today = 0
    for category, items in grouped_problems.items():
        for item in items:
            total_today += 1
            if item.get('solved_recently', False):
                done_today += 1
    
    goal_progress = {
        'total': total_today,
        'done': done_today,
        'remaining': total_today - done_today,
        'percentage': round((done_today / total_today * 100) if total_today > 0 else 0)
    }
    
    return render_template(
        'dashboard.html',
        grouped_problems=grouped_problems,
        user=user,
        stats=stats,
        goal_progress=goal_progress,
        now=datetime.utcnow()
    )
