"""
Settings routes - user profile, preferences, email change.
"""
from flask import Blueprint, render_template, request, redirect, url_for, flash, session
from zoneinfo import available_timezones
from sqlalchemy.exc import IntegrityError
from services import AuthService, AvatarService, EmailService
from repositories import UserRepository, AuthRepository
from extensions import db
from utils.decorators import require_login

settings_bp = Blueprint('settings', __name__)


@settings_bp.route('/settings')
@require_login
def index():
    """Settings page."""
    user = AuthService.get_current_user()
    if not user:
        flash('Please login again.', 'error')
        return redirect(url_for('auth.login'))
    
    # Check for pending email change request
    pending = AuthRepository.get_email_change_request(user.id)
    if pending:
        AuthRepository.cleanup_expired_request(pending)
        pending = AuthRepository.get_email_change_request(user.id)
    
    tzs = sorted(available_timezones())
    
    return render_template(
        'settings.html',
        user=user,
        pending_email_change=pending,
        timezones=tzs
    )


@settings_bp.route('/settings/username', methods=['POST'])
@require_login
def update_username():
    """Update username."""
    user = AuthService.get_current_user()
    if not user:
        flash('Please login again.', 'error')
        return redirect(url_for('auth.login'))
    
    new_username = (request.form.get('username') or '').strip()
    
    if not new_username:
        flash('Username cannot be empty.', 'error')
        return redirect(url_for('settings.index'))
    
    if new_username == user.username:
        flash('Username is unchanged.', 'success')
        return redirect(url_for('settings.index'))
    
    if UserRepository.username_exists(new_username, exclude_user_id=user.id):
        flash('That username is already taken.', 'error')
        return redirect(url_for('settings.index'))
    
    user.username = new_username
    try:
        UserRepository.update(user)
        session['username'] = user.username
        flash('Username updated.', 'success')
    except IntegrityError:
        db.session.rollback()
        flash('That username is already taken.', 'error')
    
    return redirect(url_for('settings.index'))


@settings_bp.route('/settings/timezone', methods=['POST'])
@require_login
def update_timezone():
    """Update timezone."""
    user = AuthService.get_current_user()
    if not user:
        flash('Please login again.', 'error')
        return redirect(url_for('auth.login'))
    
    tz = (request.form.get('timezone') or '').strip()
    
    if not tz or tz not in available_timezones():
        flash('Please select a valid timezone.', 'error')
        return redirect(url_for('settings.index'))
    
    user.timezone = tz
    UserRepository.update(user)
    flash('Timezone updated.', 'success')
    
    return redirect(url_for('settings.index'))


@settings_bp.route('/settings/daily-email', methods=['POST'])
@require_login
def update_daily_email():
    """Update daily email settings."""
    user = AuthService.get_current_user()
    if not user:
        flash('Please login again.', 'error')
        return redirect(url_for('auth.login'))
    
    enabled = request.form.get('daily_email_enabled') == 'on'
    send_time = (request.form.get('daily_email_time') or '06:00').strip()
    
    # Validate HH:MM
    try:
        hh, mm = send_time.split(':', 1)
        hh_i = int(hh)
        mm_i = int(mm)
        if not (0 <= hh_i <= 23 and 0 <= mm_i <= 59):
            raise ValueError("out of range")
        send_time = f"{hh_i:02d}:{mm_i:02d}"
    except Exception:
        flash('Please provide a valid time (HH:MM).', 'error')
        return redirect(url_for('settings.index'))
    
    user.daily_email_enabled = enabled
    user.daily_email_time = send_time
    UserRepository.update(user)
    flash('Daily email settings updated.', 'success')
    
    return redirect(url_for('settings.index'))


@settings_bp.route('/settings/profile-picture', methods=['POST'])
@require_login
def upload_profile_picture():
    """Upload profile picture."""
    user = AuthService.get_current_user()
    if not user:
        flash('Please login again.', 'error')
        return redirect(url_for('auth.login'))
    
    file = request.files.get('profile_picture')
    success, message = AvatarService.upload_avatar(user, file)
    flash(message, 'success' if success else 'error')
    
    return redirect(url_for('settings.index'))


@settings_bp.route('/settings/profile-picture/delete', methods=['POST'])
@require_login
def delete_profile_picture():
    """Delete profile picture."""
    user = AuthService.get_current_user()
    if not user:
        flash('Please login again.', 'error')
        return redirect(url_for('auth.login'))
    
    success, message = AvatarService.delete_avatar(user)
    flash(message, 'success' if success else 'error')
    
    return redirect(url_for('settings.index'))


@settings_bp.route('/settings/email/request', methods=['POST'])
@require_login
def request_email_change():
    """Request email change (sends verification codes)."""
    user = AuthService.get_current_user()
    if not user:
        flash('Please login again.', 'error')
        return redirect(url_for('auth.login'))
    
    new_email = (request.form.get('new_email') or '').strip().lower()
    
    if not new_email:
        flash('New email cannot be empty.', 'error')
        return redirect(url_for('settings.index'))
    
    if new_email == user.email.lower():
        flash('New email must be different from the current email.', 'error')
        return redirect(url_for('settings.index'))
    
    if UserRepository.email_exists(new_email, exclude_user_id=user.id):
        flash('That email is already in use.', 'error')
        return redirect(url_for('settings.index'))
    
    # Create request and send codes
    email_request = AuthRepository.create_email_change_request(user, new_email)
    
    try:
        EmailService.send_email_verification_code(
            user.email,
            email_request.current_email_code,
            is_current_email=True
        )
        EmailService.send_email_verification_code(
            new_email,
            email_request.new_email_code,
            is_current_email=False
        )
        flash('Verification codes sent to both your current and new email.', 'success')
    except Exception as e:
        print(f"Email change send error: {e}")
        flash('Could not send verification codes. Check email settings and try again.', 'error')
    
    return redirect(url_for('settings.index'))


@settings_bp.route('/settings/email/confirm', methods=['POST'])
@require_login
def confirm_email_change():
    """Confirm email change with verification codes."""
    user = AuthService.get_current_user()
    if not user:
        flash('Please login again.', 'error')
        return redirect(url_for('auth.login'))
    
    current_code = (request.form.get('current_email_code') or '').strip()
    new_code = (request.form.get('new_email_code') or '').strip()
    
    email_request = AuthRepository.get_email_change_request(user.id)
    
    if not email_request:
        flash('No pending email change request. Start again.', 'error')
        return redirect(url_for('settings.index'))
    
    if email_request.is_expired():
        AuthRepository.delete_email_change_request(email_request)
        flash('Email verification codes expired. Please request again.', 'error')
        return redirect(url_for('settings.index'))
    
    # Validate codes
    if current_code != email_request.current_email_code:
        flash('Current email verification code is incorrect.', 'error')
        return redirect(url_for('settings.index'))
    
    if new_code != email_request.new_email_code:
        flash('New email verification code is incorrect.', 'error')
        return redirect(url_for('settings.index'))
    
    # Ensure new email still available
    if UserRepository.email_exists(email_request.new_email, exclude_user_id=user.id):
        flash('That new email is already in use. Please request again.', 'error')
        AuthRepository.delete_email_change_request(email_request)
        return redirect(url_for('settings.index'))
    
    # Update email
    user.email = email_request.new_email
    try:
        UserRepository.update(user)
        AuthRepository.delete_email_change_request(email_request)
        flash('Email updated successfully.', 'success')
    except IntegrityError:
        db.session.rollback()
        flash('That new email is already in use. Please request again.', 'error')
    
    return redirect(url_for('settings.index'))
