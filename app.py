import os
from flask import Flask, render_template, request, redirect, url_for, session, flash, jsonify
from datetime import datetime, timedelta
from werkzeug.security import generate_password_hash
from werkzeug.utils import secure_filename
import secrets
import sib_api_v3_sdk
from sib_api_v3_sdk.rest import ApiException
from dotenv import load_dotenv
from sqlalchemy import inspect
from models import db, User, Problem, PasswordResetToken, ProblemHistory
from utils import scrape_leetcode_problem

load_dotenv()

app = Flask(__name__)
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', secrets.token_hex(16))

# Ensure instance directory exists
instance_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'instance')
os.makedirs(instance_path, exist_ok=True)

app.config['SQLALCHEMY_DATABASE_URI'] = f'sqlite:///{os.path.join(instance_path, "codingflashcard.db")}'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db.init_app(app)

# Brevo configuration
BREVO_API_KEY = os.getenv('BREVO_API_KEY', '')
BREVO_FROM_EMAIL = os.getenv('BREVO_FROM_EMAIL', 'info@jobdistributor.net')
BREVO_FROM_NAME = os.getenv('BREVO_FROM_NAME', 'CodingFlashcard')
FRONTEND_URL = os.getenv('FRONTEND_URL', 'http://localhost:5000')


def require_login(f):
    """Decorator to require login for routes"""
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            flash('Please login to access this page.', 'error')
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    decorated_function.__name__ = f.__name__
    return decorated_function


@app.route('/')
@require_login
def dashboard():
    """Main dashboard showing problems to practice"""
    user_id = session['user_id']
    today = datetime.utcnow().date()
    problems = []
    problem_ids = set()
    
    # Problems solved 2, 5, 10 days ago
    for days_ago in [2, 5, 10]:
        target_date = today - timedelta(days=days_ago)
        date_problems = Problem.query.filter(
            Problem.user_id == user_id,
            db.func.date(Problem.solved_date) == target_date
        ).all()
        
        for problem in date_problems:
            if problem.id not in problem_ids:
                problem_ids.add(problem.id)
                problems.append({
                    'problem': problem,
                    'category': f'Solved {days_ago} days ago'
                })
    
    # Weekend random problems (Saturday=5, Sunday=6)
    if today.weekday() in [5, 6]:
        query = Problem.query.filter(Problem.user_id == user_id)
        if problem_ids:
            query = query.filter(~Problem.id.in_(problem_ids))
        # Use date-based seed for consistent random selection per day
        import random
        date_str = today.strftime('%m-%d-%Y')
        random.seed(hash(date_str))
        all_problems = query.all()
        if all_problems:
            random.shuffle(all_problems)
            random_problems = all_problems[:min(2, len(all_problems))]
        else:
            random_problems = []
        
        for problem in random_problems:
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
        # Check if problem was solved in last 12 hours
        problem = item['problem']
        solved_recently = False
        if problem.last_practiced:
            solved_recently = problem.last_practiced >= twelve_hours_ago
        elif problem.solved_date:
            # Also check solved_date if it was added recently
            solved_recently = problem.solved_date >= twelve_hours_ago
        
        grouped[category].append({
            'problem': problem,
            'solved_recently': solved_recently
        })
    
    # Calculate practice statistics
    all_user_problems = Problem.query.filter_by(user_id=user_id).all()
    today = datetime.utcnow().date()
    yesterday = today - timedelta(days=1)
    
    fully_practiced = sum(1 for p in all_user_problems if p.practice_count >= 3)
    partially_practiced = sum(1 for p in all_user_problems if p.practice_count == 2)
    solved_once = sum(1 for p in all_user_problems if p.practice_count == 1)
    not_practiced = sum(1 for p in all_user_problems if p.practice_count == 0)
    
    # Count problems practiced today and yesterday
    # A problem is "practiced today" if:
    # - last_practiced is today, OR
    # - solved_date is today (recently added), OR
    # - has a history entry from today
    practiced_today_set = set()
    practiced_yesterday_set = set()
    
    for problem in all_user_problems:
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
            for history_entry in problem.history:
                entry_date = history_entry.practiced_at.date()
                if entry_date == today:
                    practiced_today_set.add(problem.id)
                elif entry_date == yesterday:
                    practiced_yesterday_set.add(problem.id)
    
    practiced_today = len(practiced_today_set)
    practiced_yesterday = len(practiced_yesterday_set)
    
    stats = {
        'fully_practiced': fully_practiced,
        'partially_practiced': partially_practiced,
        'solved_once': solved_once,
        'not_practiced': not_practiced,
        'practiced_today': practiced_today,
        'practiced_yesterday': practiced_yesterday,
        'total': len(all_user_problems)
    }
    
    from datetime import datetime as dt
    now = dt.utcnow()
    
    return render_template('dashboard.html', grouped_problems=grouped, user=User.query.get(user_id), stats=stats, now=now)


@app.route('/login', methods=['GET', 'POST'])
def login():
    """Login page"""
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        
        if not username or not password:
            flash('Please provide both username and password.', 'error')
            return render_template('login.html')
        
        user = User.query.filter_by(username=username).first()
        
        if user and user.check_password(password):
            session['user_id'] = user.id
            session['username'] = user.username
            flash('Login successful!', 'success')
            return redirect(url_for('dashboard'))
        else:
            flash('Invalid username or password.', 'error')
    
    return render_template('login.html')


@app.route('/register', methods=['GET', 'POST'])
def register():
    """Registration page"""
    if request.method == 'POST':
        username = request.form.get('username')
        email = request.form.get('email')
        password = request.form.get('password')
        password_confirm = request.form.get('password_confirm')
        
        if not username or not email or not password:
            flash('Please fill in all fields.', 'error')
            return render_template('register.html')
        
        if password != password_confirm:
            flash('Passwords do not match.', 'error')
            return render_template('register.html')
        
        if len(password) < 8:
            flash('Password must be at least 8 characters long.', 'error')
            return render_template('register.html')
        
        # Check if username or email already exists
        if User.query.filter_by(username=username).first():
            flash('Username already exists.', 'error')
            return render_template('register.html')
        
        if User.query.filter_by(email=email).first():
            flash('Email already exists.', 'error')
            return render_template('register.html')
        
        # Create new user
        user = User(username=username, email=email)
        user.set_password(password)
        db.session.add(user)
        db.session.commit()
        
        flash('Registration successful! Please login.', 'success')
        return redirect(url_for('login'))
    
    return render_template('register.html')


@app.route('/logout')
def logout():
    """Logout"""
    session.clear()
    flash('Logged out successfully.', 'success')
    return redirect(url_for('login'))


@app.route('/change-password', methods=['GET', 'POST'])
@require_login
def change_password():
    """Change password for logged-in user. Forces re-login on success."""
    user_id = session.get('user_id')
    user = User.query.get(user_id) if user_id else None

    if not user:
        session.clear()
        flash('Please login again.', 'error')
        return redirect(url_for('login'))

    if request.method == 'POST':
        current_password = (request.form.get('current_password') or '').strip()
        new_password = request.form.get('new_password') or ''
        new_password_confirm = request.form.get('new_password_confirm') or ''

        if not current_password or not new_password or not new_password_confirm:
            flash('Please fill in all fields.', 'error')
            return render_template('change_password.html')

        if not user.check_password(current_password):
            flash('Current password is incorrect.', 'error')
            return render_template('change_password.html')

        if new_password != new_password_confirm:
            flash('New passwords do not match.', 'error')
            return render_template('change_password.html')

        if len(new_password) < 8:
            flash('New password must be at least 8 characters long.', 'error')
            return render_template('change_password.html')

        if user.check_password(new_password):
            flash('New password must be different from the current password.', 'error')
            return render_template('change_password.html')

        user.set_password(new_password)
        db.session.commit()

        session.clear()
        flash('Password changed. Please log in again.', 'success')
        return redirect(url_for('login'))

    return render_template('change_password.html')


@app.route('/forgot-password', methods=['GET', 'POST'])
def forgot_password():
    """Forgot password page"""
    if request.method == 'POST':
        email = request.form.get('email')
        
        if not email:
            flash('Please provide your email address.', 'error')
            return render_template('forgot_password.html')
        
        user = User.query.filter_by(email=email).first()
        
        # Don't reveal if email exists for security
        if not user:
            flash('If an account exists with this email, a password reset link has been sent.', 'success')
            return render_template('forgot_password.html')
        
        # Generate reset token
        token = secrets.token_urlsafe(32)
        expires_at = datetime.utcnow() + timedelta(hours=1)
        
        # Delete old tokens for this user
        PasswordResetToken.query.filter_by(user_id=user.id).delete()
        
        # Create new token
        reset_token = PasswordResetToken(
            user_id=user.id,
            token=token,
            expires_at=expires_at
        )
        db.session.add(reset_token)
        db.session.commit()
        
        # Send email via Brevo
        if BREVO_API_KEY:
            try:
                configuration = sib_api_v3_sdk.Configuration()
                configuration.api_key['api-key'] = BREVO_API_KEY
                
                api_instance = sib_api_v3_sdk.TransactionalEmailsApi(sib_api_v3_sdk.ApiClient(configuration))
                
                # URL encode the token to handle special characters
                from urllib.parse import quote
                encoded_token = quote(token, safe='')
                reset_link = f"{FRONTEND_URL}/reset-password/{encoded_token}"
                
                send_smtp_email = sib_api_v3_sdk.SendSmtpEmail(
                    to=[{"email": email}],
                    sender={"name": BREVO_FROM_NAME, "email": BREVO_FROM_EMAIL},
                    subject="Password Reset - CodingFlashcard",
                    html_content=f"""
                    <h2>Password Reset Request</h2>
                    <p>You requested a password reset for your CodingFlashcard account.</p>
                    <p>Click the link below to reset your password:</p>
                    <p><a href="{reset_link}">{reset_link}</a></p>
                    <p>This link will expire in 1 hour.</p>
                    <p>If you didn't request this, please ignore this email.</p>
                    """
                )
                
                api_instance.send_transac_email(send_smtp_email)
            except ApiException as e:
                print(f"Error sending email: {e}")
        
        flash('If an account exists with this email, a password reset link has been sent.', 'success')
    
    return render_template('forgot_password.html')


@app.route('/reset-password/<path:token>', methods=['GET', 'POST'])
def reset_password(token):
    """Reset password page - no login required"""
    # Handle URL-encoded tokens
    from urllib.parse import unquote
    token = unquote(token)
    
    try:
        reset_token = PasswordResetToken.query.filter_by(token=token).first()
    except Exception as e:
        print(f"Database error in reset_password: {e}")
        import traceback
        traceback.print_exc()
        flash('Error accessing reset token. Please try again.', 'error')
        return redirect(url_for('forgot_password'))
    
    if not reset_token:
        flash('Invalid reset token. Please request a new password reset.', 'error')
        return redirect(url_for('forgot_password'))
    
    if reset_token.is_expired():
        flash('Reset token has expired. Please request a new password reset.', 'error')
        return redirect(url_for('forgot_password'))
    
    if request.method == 'POST':
        new_password = request.form.get('new_password')
        new_password_confirm = request.form.get('new_password_confirm')
        
        if not new_password or not new_password_confirm:
            flash('Please fill in all fields.', 'error')
            return render_template('reset_password.html', token=token)
        
        if new_password != new_password_confirm:
            flash('Passwords do not match.', 'error')
            return render_template('reset_password.html', token=token)
        
        if len(new_password) < 8:
            flash('Password must be at least 8 characters long.', 'error')
            return render_template('reset_password.html', token=token)
        
        # Reset password
        user = reset_token.user
        user.set_password(new_password)
        
        # Delete the token
        db.session.delete(reset_token)
        db.session.commit()
        
        flash('Password reset successful! Please login.', 'success')
        return redirect(url_for('login'))
    
    return render_template('reset_password.html', token=token)


@app.route('/add-problem', methods=['POST'])
@require_login
def add_problem():
    """Add a new problem or update existing one"""
    user_id = session['user_id']
    leetcode_url = request.form.get('leetcode_url')
    
    if not leetcode_url:
        flash('Please provide a Leetcode URL.', 'error')
        return redirect(url_for('dashboard'))
    
    # Normalize URL (remove trailing slash, etc.)
    leetcode_url = leetcode_url.strip().rstrip('/')
    
    # Check if problem already exists for this user
    existing_problem = Problem.query.filter_by(
        user_id=user_id,
        leetcode_url=leetcode_url
    ).first()
    
    if existing_problem:
        # Problem already exists, just update solved_date and add history
        existing_problem.solved_date = datetime.utcnow()
        existing_problem.last_practiced = datetime.utcnow()  # Mark as practiced today
        # Add history entry for this addition
        history_entry = ProblemHistory(
            problem_id=existing_problem.id,
            practiced_at=datetime.utcnow()
        )
        db.session.add(history_entry)
        db.session.commit()
        flash('Problem already exists. Added to history!', 'success')
        return redirect(url_for('dashboard'))
    
    # Get difficulty from form (user selection takes priority)
    form_difficulty = request.form.get('difficulty', '').strip().lower()
    
    # Scrape problem details
    problem_data = scrape_leetcode_problem(leetcode_url)
    
    if not problem_data:
        # Try to extract from URL as fallback
        from urllib.parse import urlparse
        parsed = urlparse(leetcode_url)
        path_parts = parsed.path.strip('/').split('/')
        if 'problems' in path_parts:
            idx = path_parts.index('problems')
            if idx + 1 < len(path_parts):
                slug = path_parts[idx + 1]
                title = ' '.join(word.capitalize() for word in slug.split('-'))
                problem_data = {
                    'title': title,
                    'difficulty': form_difficulty if form_difficulty in ['easy', 'medium', 'hard'] else 'medium'
                }
        
        if not problem_data:
            flash('Failed to scrape problem details. Please check the URL and try again.', 'error')
            return redirect(url_for('dashboard'))
    
    # Use form difficulty if provided, otherwise use scraped difficulty
    if form_difficulty in ['easy', 'medium', 'hard']:
        difficulty = form_difficulty
    else:
        difficulty = problem_data.get('difficulty', 'medium')
    
    # Create new problem
    now = datetime.utcnow()
    problem = Problem(
        user_id=user_id,
        title=problem_data['title'],
        leetcode_url=leetcode_url,
        difficulty=difficulty,
        solved_date=now,
        last_practiced=now  # Mark as practiced today when added
    )
    db.session.add(problem)
    db.session.flush()  # Get the problem ID
    
    # Add initial history entry
    history_entry = ProblemHistory(
        problem_id=problem.id,
        practiced_at=now
    )
    db.session.add(history_entry)
    db.session.commit()
    
    flash('Problem added successfully!', 'success')
    return redirect(url_for('dashboard'))


@app.route('/mark-done/<int:problem_id>', methods=['POST'])
@require_login
def mark_done(problem_id):
    """Mark a problem as practiced"""
    user_id = session['user_id']
    problem = Problem.query.filter_by(id=problem_id, user_id=user_id).first()
    
    if not problem:
        flash('Problem not found.', 'error')
        return redirect(url_for('dashboard'))
    
    # Update last_practiced and practice_count
    problem.last_practiced = datetime.utcnow()
    problem.practice_count += 1
    
    # Add history entry
    history_entry = ProblemHistory(
        problem_id=problem.id,
        practiced_at=datetime.utcnow()
    )
    db.session.add(history_entry)
    db.session.commit()
    
    flash('Problem marked as done!', 'success')
    # Redirect back to the page that called this (dashboard or all_problems)
    referer = request.headers.get('Referer', url_for('dashboard'))
    if 'all-problems' in referer:
        return redirect(url_for('all_problems'))
    return redirect(url_for('dashboard'))


@app.route('/problem-history/<int:problem_id>')
@require_login
def problem_history(problem_id):
    """Get problem history as JSON"""
    user_id = session['user_id']
    problem = Problem.query.filter_by(id=problem_id, user_id=user_id).first()
    
    if not problem:
        return jsonify({'error': 'Problem not found'}), 404
    
    history = [
        {
            'practiced_at': entry.practiced_at.strftime('%Y-%m-%d %H:%M:%S'),
            'date': entry.practiced_at.strftime('%Y-%m-%d'),
            'time': entry.practiced_at.strftime('%H:%M:%S')
        }
        for entry in problem.history
    ]
    
    return jsonify({
        'title': problem.title,
        'created_at': problem.created_at.strftime('%Y-%m-%d %H:%M:%S'),
        'practice_count': problem.practice_count,
        'total_sessions': len(history),
        'history': history
    })


@app.route('/api/practice-data')
@require_login
def practice_data():
    """Get practice data for a specific month/year"""
    user_id = session['user_id']
    year = request.args.get('year', type=int)
    month = request.args.get('month', type=int)
    
    if not year or not month:
        # Default to current month
        now = datetime.utcnow()
        year = now.year
        month = now.month
    
    # Get all practice history entries for the specified month
    from calendar import monthrange
    start_date = datetime(year, month, 1)
    days_in_month = monthrange(year, month)[1]
    end_date = datetime(year, month, days_in_month, 23, 59, 59)
    
    # Query history entries for this month
    # Join with Problem table to filter by user_id
    history_entries = db.session.query(ProblemHistory).join(Problem).filter(
        Problem.user_id == user_id,
        ProblemHistory.practiced_at >= start_date,
        ProblemHistory.practiced_at <= end_date
    ).all()
    
    # Count problems solved per day
    daily_counts = {}
    for entry in history_entries:
        day = entry.practiced_at.day
        if day not in daily_counts:
            daily_counts[day] = 0
        daily_counts[day] += 1
    
    # Create data for all days in the month (fill missing days with 0)
    days = list(range(1, days_in_month + 1))
    counts = [daily_counts.get(day, 0) for day in days]
    
    return jsonify({
        'days': days,
        'counts': counts,
        'year': year,
        'month': month
    })


@app.route('/all-problems')
@require_login
def all_problems():
    """View all problems with pagination and search"""
    user_id = session['user_id']
    page = request.args.get('page', 1, type=int)
    search_query = request.args.get('search', '', type=str).strip()
    
    # Base query
    query = Problem.query.filter_by(user_id=user_id)
    
    # Apply search filter
    if search_query:
        query = query.filter(
            db.or_(
                Problem.title.ilike(f'%{search_query}%'),
                Problem.leetcode_url.ilike(f'%{search_query}%'),
                Problem.difficulty.ilike(f'%{search_query}%')
            )
        )
    
    # Sort by most recently updated (last_practiced or created_at)
    # Use COALESCE to handle NULL last_practiced values
    query = query.order_by(
        db.func.coalesce(Problem.last_practiced, Problem.created_at).desc()
    )
    
    # Paginate: 10 problems per page
    pagination = query.paginate(page=page, per_page=10, error_out=False)
    problems = pagination.items
    
    # Add solved_recently flag for each problem
    now = datetime.utcnow()
    twelve_hours_ago = now - timedelta(hours=12)
    problems_with_flag = []
    for problem in problems:
        solved_recently = False
        if problem.last_practiced:
            solved_recently = problem.last_practiced >= twelve_hours_ago
        elif problem.solved_date:
            solved_recently = problem.solved_date >= twelve_hours_ago
        problems_with_flag.append({
            'problem': problem,
            'solved_recently': solved_recently
        })
    
    user = User.query.get(user_id)
    
    return render_template('all_problems.html', 
                         problems=problems_with_flag, 
                         user=user,
                         pagination=pagination,
                         search_query=search_query)


@app.route('/delete-problem/<int:problem_id>', methods=['POST'])
@require_login
def delete_problem(problem_id):
    """Delete a problem"""
    user_id = session['user_id']
    problem = Problem.query.filter_by(id=problem_id, user_id=user_id).first()
    
    if not problem:
        flash('Problem not found.', 'error')
        return redirect(url_for('dashboard'))
    
    # Delete the problem (cascade will delete history)
    db.session.delete(problem)
    db.session.commit()
    
    flash('Problem deleted successfully!', 'success')
    # Redirect back to the page that called this
    referer = request.headers.get('Referer', url_for('dashboard'))
    if 'all-problems' in referer:
        return redirect(url_for('all_problems'))
    return redirect(url_for('dashboard'))


def migrate_database():
    """Add missing columns and tables to existing database"""
    # Check if practice_count column exists
    try:
        inspector = inspect(db.engine)
        if 'problems' in inspector.get_table_names():
            columns = [col['name'] for col in inspector.get_columns('problems')]
            
            if 'practice_count' not in columns:
                with db.engine.connect() as conn:
                    conn.execute(db.text('ALTER TABLE problems ADD COLUMN practice_count INTEGER DEFAULT 0'))
                    conn.commit()
                print("Added practice_count column to problems table")
    except Exception as e:
        print(f"Migration check: {e}")
    
    # Create all tables (will only create new ones)
    db.create_all()


if __name__ == '__main__':
    with app.app_context():
        migrate_database()
    app.run(host='0.0.0.0', debug=True, port=5000)

