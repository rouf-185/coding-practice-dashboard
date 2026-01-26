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
    
    return render_template(
        'dashboard.html',
        grouped_problems=grouped_problems,
        user=user,
        stats=stats,
        now=datetime.utcnow()
    )
