# CodingFlashcard

A simple spaced repetition coding practice dashboard to help you remember and practice Leetcode problems you've solved.

## Features

- **Spaced Repetition**: Automatically shows problems you solved 2, 5, and 10 days ago
- **Weekend Random Practice**: On weekends, shows 2 additional random problems
- **Easy Problem Addition**: Just paste a Leetcode URL and the system extracts the problem details
- **User Authentication**: Register, login, and password reset via email
- **Simple & Clean**: Single Flask application with HTML/CSS - no complex setup needed

## Tech Stack

- **Backend**: Flask with SQLite database
- **Frontend**: HTML/CSS templates
- **Email Service**: Brevo (formerly Sendinblue) for password reset

## Quick Start

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Create Environment File

Create a `.env` file in the root directory:

```env
SECRET_KEY=your-secret-key-here
BREVO_API_KEY=your-brevo-api-key
BREVO_FROM_EMAIL=info@jobdistributor.net
BREVO_FROM_NAME=CodingFlashcard
FRONTEND_URL=http://localhost:5000
```

**Note**: The `SECRET_KEY` is required. You can generate one with:
```python
import secrets
print(secrets.token_hex(16))
```

The `BREVO_API_KEY` is optional - password reset will work but won't send emails without it.

### 3. Run the Application

```bash
python app.py
```

The application will:
- Automatically create the SQLite database in `instance/codingflashcard.db`
- Start the server on `http://localhost:5000`

### 4. Use the Application

1. Open `http://localhost:5000` in your browser
2. Register a new account
3. Click "Add Problem" and paste a Leetcode URL (e.g., `https://leetcode.com/problems/four-divisors/description/`)
4. The system will automatically extract the problem title and difficulty
5. View your practice problems on the dashboard
6. Click "Done" when you've practiced a problem

## Project Structure

```
coding-practice-dashboard/
├── app.py                 # Main Flask application
├── models.py              # SQLite database models
├── utils.py               # Leetcode scraper
├── requirements.txt       # Python dependencies
├── templates/             # HTML templates
│   ├── base.html
│   ├── login.html
│   ├── register.html
│   ├── forgot_password.html
│   ├── reset_password.html
│   └── dashboard.html
├── static/               # CSS files
│   └── style.css
└── instance/             # SQLite database (auto-created)
    └── codingflashcard.db
```

## Routes

- `GET /` - Dashboard (requires login)
- `GET /login` - Login page
- `POST /login` - Process login
- `GET /register` - Registration page
- `POST /register` - Process registration
- `GET /logout` - Logout
- `GET /forgot-password` - Forgot password page
- `POST /forgot-password` - Send reset email
- `GET /reset-password/<token>` - Reset password page
- `POST /reset-password/<token>` - Process password reset
- `POST /add-problem` - Add new problem
- `POST /mark-done/<id>` - Mark problem as practiced

## Advantages

- ✅ Single application (no separate frontend/backend)
- ✅ No Node.js required
- ✅ SQLite - no database server needed
- ✅ Simple deployment
- ✅ All in Python
- ✅ Easy to understand and modify

## Notes

- The password reset tokens are stored in the database
- The Leetcode scraper may need updates if Leetcode changes their page structure
- SQLite database is created automatically in the `instance/` directory
- For production, set `debug=False` in `app.py`

## License

MIT
