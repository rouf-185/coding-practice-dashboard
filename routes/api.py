"""
API routes - JSON endpoints for AJAX calls.
"""
from datetime import datetime
from flask import Blueprint, request, jsonify, session
from services import ProblemService, StatsService
from utils.decorators import require_login

api_bp = Blueprint('api', __name__, url_prefix='/api')


@api_bp.route('/problem-history/<int:problem_id>')
@require_login
def get_problem_history(problem_id):
    """Get problem history as JSON."""
    user_id = session['user_id']
    history_data = ProblemService.get_problem_history(user_id, problem_id)
    
    if not history_data:
        return jsonify({'error': 'Problem not found'}), 404
    
    return jsonify(history_data)


@api_bp.route('/practice-data')
@require_login
def get_practice_data():
    """Get practice chart data with goal achievement info."""
    user_id = session['user_id']
    now = datetime.utcnow()
    
    year = request.args.get('year', default=now.year, type=int)
    month = request.args.get('month', default=now.month, type=int)
    
    # Validate year and month
    if year < 2020 or year > 2100:
        year = now.year
    if month < 1 or month > 12:
        month = now.month
    
    data = StatsService.get_monthly_practice_data(user_id, year, month)
    
    # Add goal achievement data
    from repositories import DailyGoalRepository
    goals = DailyGoalRepository.get_for_month(user_id, year, month)
    
    # Create goals dict: day -> achieved
    data['goals'] = {
        day: goals[day].achieved if day in goals else False
        for day in data['days']
    }
    
    return jsonify(data)


@api_bp.route('/difficulty-stats')
@require_login
def get_difficulty_stats():
    """Get difficulty distribution stats with time filtering."""
    user_id = session['user_id']
    period = request.args.get('period', 'lifetime')
    
    # Validate period
    valid_periods = ['today', 'week', 'month', 'year', 'lifetime']
    if period not in valid_periods:
        period = 'lifetime'
    
    data = StatsService.get_difficulty_stats(user_id, period)
    return jsonify(data)


@api_bp.route('/heatmap-data')
@require_login
def get_heatmap_data():
    """Get daily activity heatmap data."""
    user_id = session['user_id']
    now = datetime.utcnow()
    
    year = request.args.get('year', default=now.year, type=int)
    
    # Validate year
    if year < 2020 or year > 2100:
        year = now.year
    
    data = StatsService.get_heatmap_data(user_id, year)
    return jsonify(data)
