# CodingFlashcard

A spaced repetition dashboard for practicing Leetcode problems. Track your solved problems and get daily reminders to practice them at optimal intervals (2, 5, 10, and 30 days).

## Features

- **Spaced Repetition**: Automatically shows problems solved 2, 5, 10, and 30 days ago
- **Weekend Random Pick**: Extra random problems on Saturday/Sunday
- **Problem Tracking**: Store title, difficulty, solve date, and practice history
- **Dashboard Stats**: View practice progress with charts
- **Daily Email Reminders**: Get your practice list at a configurable time
- **User Accounts**: Registration, login, password reset via email

## Requirements

- Python 3.10+
- Chrome browser (for Leetcode scraping)

## Setup

1. **Clone and enter the directory**
   ```bash
   cd coding-practice-dashboard
   ```

2. **Create a virtual environment**
   ```bash
   python3 -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Configure environment variables**

   Create a `.env` file in the project root:
   ```env
   SECRET_KEY=your-secret-key-here
   BREVO_API_KEY=your-brevo-api-key
   BREVO_FROM_EMAIL=your-sender@email.com
   BREVO_FROM_NAME=CodingFlashcard
   FRONTEND_URL=http://localhost:5000
   ```

   - `SECRET_KEY`: Any random string for session security
   - `BREVO_API_KEY`: Get from [Brevo](https://www.brevo.com/) for email functionality
   - `FRONTEND_URL`: Your app's URL (used in password reset emails)

## Running the Application

### Development
```bash
source venv/bin/activate
python app.py
```
The app runs at `http://localhost:5000`

### Production
```bash
export FLASK_ENV=production
export FLASK_DEBUG=false
python app.py
```

Or use a WSGI server like Gunicorn:
```bash
pip install gunicorn
gunicorn -w 4 -b 0.0.0.0:5000 app:app
```

### Daily Email Worker (Optional)

To send daily practice reminder emails, run the background worker in a separate terminal:
```bash
source venv/bin/activate
python daily_email_worker.py
```

This checks every minute and sends emails at each user's configured time.

## Project Structure

```
coding-practice-dashboard/
├── app.py                    # Application factory
├── config.py                 # Configuration
├── extensions.py             # Flask extensions
├── daily_email_worker.py     # Background email worker
├── models/                   # Database models
├── repositories/             # Database queries
├── services/                 # Business logic
├── routes/                   # HTTP endpoints
├── utils/                    # Helpers (scraper, decorators)
├── templates/                # HTML templates
├── static/                   # CSS, images
└── instance/                 # SQLite database (auto-created)
```

## Usage

1. Register an account at `/register`
2. Log in at `/login`
3. Click the **+** button to add a Leetcode problem URL
4. Practice problems shown on the dashboard
5. Click **Done** after solving a problem
6. Configure settings (timezone, daily email) in the settings page
