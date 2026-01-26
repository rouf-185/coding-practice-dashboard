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
    """Get practice chart data."""
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
    return jsonify(data)
