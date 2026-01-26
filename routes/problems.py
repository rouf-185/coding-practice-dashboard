"""
Problems routes - add, mark done, delete, view all.
"""
from datetime import datetime, timedelta
from flask import Blueprint, render_template, request, redirect, url_for, flash, session
from services import AuthService, ProblemService
from repositories import ProblemRepository
from utils.decorators import require_login

problems_bp = Blueprint('problems', __name__)


@problems_bp.route('/add-problem', methods=['POST'])
@require_login
def add_problem():
    """Add a new problem."""
    user_id = session['user_id']
    leetcode_url = request.form.get('leetcode_url')
    form_difficulty = request.form.get('difficulty', '').strip().lower()
    
    success, message = ProblemService.add_problem(user_id, leetcode_url, form_difficulty)
    flash(message, 'success' if success else 'error')
    
    return redirect(url_for('dashboard.index'))


@problems_bp.route('/mark-done/<int:problem_id>', methods=['POST'])
@require_login
def mark_done(problem_id):
    """Mark a problem as practiced."""
    user_id = session['user_id']
    
    success, message = ProblemService.mark_done(user_id, problem_id)
    flash(message, 'success' if success else 'error')
    
    # Redirect back to the page that called this
    referer = request.headers.get('Referer', url_for('dashboard.index'))
    if 'all-problems' in referer:
        return redirect(url_for('problems.all_problems'))
    return redirect(url_for('dashboard.index'))


@problems_bp.route('/delete-problem/<int:problem_id>', methods=['POST'])
@require_login
def delete_problem(problem_id):
    """Delete a problem."""
    user_id = session['user_id']
    
    success, message = ProblemService.delete_problem(user_id, problem_id)
    flash(message, 'success' if success else 'error')
    
    # Redirect back to the page that called this
    referer = request.headers.get('Referer', url_for('dashboard.index'))
    if 'all-problems' in referer:
        return redirect(url_for('problems.all_problems'))
    return redirect(url_for('dashboard.index'))


@problems_bp.route('/all-problems')
@require_login
def all_problems():
    """View all problems with pagination and search."""
    user = AuthService.get_current_user()
    if not user:
        return redirect(url_for('auth.login'))
    
    page = request.args.get('page', 1, type=int)
    search_query = request.args.get('search', '', type=str).strip()
    
    # Get paginated problems
    pagination = ProblemRepository.get_paginated(
        user.id, page=page, per_page=10, search_query=search_query
    )
    
    # Add solved_recently flag
    now = datetime.utcnow()
    twelve_hours_ago = now - timedelta(hours=12)
    
    problems_with_flag = []
    for problem in pagination.items:
        solved_recently = False
        if problem.last_practiced:
            solved_recently = problem.last_practiced >= twelve_hours_ago
        elif problem.solved_date:
            solved_recently = problem.solved_date >= twelve_hours_ago
        
        problems_with_flag.append({
            'problem': problem,
            'solved_recently': solved_recently
        })
    
    return render_template(
        'all_problems.html',
        problems=problems_with_flag,
        user=user,
        pagination=pagination,
        search_query=search_query
    )
