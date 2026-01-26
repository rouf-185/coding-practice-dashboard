"""
Authentication routes - login, register, logout, password management.
"""
from flask import Blueprint, render_template, request, redirect, url_for, flash, current_app
from services import AuthService
from utils.decorators import require_login

auth_bp = Blueprint('auth', __name__)


@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    """Login page."""
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        
        success, message = AuthService.login(username, password)
        flash(message, 'success' if success else 'error')
        
        if success:
            return redirect(url_for('dashboard.index'))
    
    return render_template('login.html')


@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    """Registration page."""
    if request.method == 'POST':
        username = request.form.get('username')
        email = request.form.get('email')
        password = request.form.get('password')
        password_confirm = request.form.get('password_confirm')
        
        success, message = AuthService.register(username, email, password, password_confirm)
        flash(message, 'success' if success else 'error')
        
        if success:
            return redirect(url_for('auth.login'))
    
    return render_template('register.html')


@auth_bp.route('/logout')
def logout():
    """Logout."""
    AuthService.logout()
    flash('Logged out successfully.', 'success')
    return redirect(url_for('auth.login'))


@auth_bp.route('/change-password', methods=['GET', 'POST'])
@require_login
def change_password():
    """Change password for logged-in user."""
    user = AuthService.get_current_user()
    
    if not user:
        flash('Please login again.', 'error')
        return redirect(url_for('auth.login'))
    
    if request.method == 'POST':
        current_password = request.form.get('current_password', '').strip()
        new_password = request.form.get('new_password', '')
        new_password_confirm = request.form.get('new_password_confirm', '')
        
        success, message = AuthService.change_password(
            user, current_password, new_password, new_password_confirm
        )
        flash(message, 'success' if success else 'error')
        
        if success:
            return redirect(url_for('auth.login'))
    
    return render_template('change_password.html')


@auth_bp.route('/forgot-password', methods=['GET', 'POST'])
def forgot_password():
    """Forgot password page."""
    if request.method == 'POST':
        email = request.form.get('email')
        
        if not email:
            flash('Please provide your email address.', 'error')
            return render_template('forgot_password.html')
        
        success, message, token = AuthService.request_password_reset(email)
        
        if token:
            # Send email
            from urllib.parse import quote
            from services import EmailService
            
            encoded_token = quote(token, safe='')
            frontend_url = current_app.config.get('FRONTEND_URL', 'http://localhost:5000')
            reset_link = f"{frontend_url}/reset-password/{encoded_token}"
            
            EmailService.send_password_reset_email(email, reset_link)
        
        flash(message, 'success')
    
    return render_template('forgot_password.html')


@auth_bp.route('/reset-password/<path:token>', methods=['GET', 'POST'])
def reset_password(token):
    """Reset password page."""
    valid, message = AuthService.validate_reset_token(token)
    
    if not valid:
        flash(message, 'error')
        return redirect(url_for('auth.forgot_password'))
    
    if request.method == 'POST':
        new_password = request.form.get('new_password')
        new_password_confirm = request.form.get('new_password_confirm')
        
        success, message = AuthService.reset_password(token, new_password, new_password_confirm)
        flash(message, 'success' if success else 'error')
        
        if success:
            return redirect(url_for('auth.login'))
        
        return render_template('reset_password.html', token=token)
    
    return render_template('reset_password.html', token=token)
