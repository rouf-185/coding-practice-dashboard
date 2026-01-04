# CodingFlashcard

A spaced repetition coding practice dashboard to help you remember and practice Leetcode problems you've solved.

## Features

- **Spaced Repetition**: Automatically shows problems you solved 2, 5, and 10 days ago
- **Weekend Random Practice**: On weekends, shows 2 additional random problems
- **Easy Problem Addition**: Just paste a Leetcode URL and the system extracts the problem details
- **User Authentication**: Register, login, and password reset via email
- **Modern UI**: Clean, responsive interface for managing your practice

## Tech Stack

- **Frontend**: React with React Router
- **Backend**: Django REST Framework
- **Database**: MySQL
- **Email Service**: Brevo (formerly Sendinblue)

## Setup Instructions

### Prerequisites

- Python 3.8+
- Node.js 14+ and npm
- MySQL 5.7+ or MySQL 8.0+
- Brevo API key (for password reset emails)

### Backend Setup

1. Navigate to the backend directory:
```bash
cd backend
```

2. Create and activate a virtual environment:
```bash
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Create a `.env` file in the `backend` directory:
```env
DB_NAME=codingflashcard
DB_USER=root
DB_PASSWORD=your_mysql_password
DB_HOST=localhost
DB_PORT=3306
SECRET_KEY=your-secret-key-here
BREVO_API_KEY=your-brevo-api-key
BREVO_FROM_EMAIL=info@jobdistributor.net
BREVO_FROM_NAME=CodingFlashcard
```

5. Create the MySQL database:
```sql
CREATE DATABASE codingflashcard CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
```

6. Run migrations:
```bash
python manage.py makemigrations
python manage.py migrate
```

7. Create a superuser (optional, for admin access):
```bash
python manage.py createsuperuser
```

8. Start the development server:
```bash
python manage.py runserver
```

The backend will run on `http://localhost:8000`

### Frontend Setup

1. Navigate to the frontend directory:
```bash
cd frontend
```

2. Install dependencies:
```bash
npm install
```

3. Create a `.env` file in the `frontend` directory:
```env
REACT_APP_API_URL=http://localhost:8000/api
```

4. Start the development server:
```bash
npm start
```

The frontend will run on `http://localhost:3000`

## Usage

1. Register a new account or login
2. Click "Add Problem" and paste a Leetcode problem URL (e.g., `https://leetcode.com/problems/four-divisors/description/`)
3. The system will automatically extract the problem title and difficulty
4. View your practice problems on the dashboard
5. Click "Done" when you've practiced a problem

## API Endpoints

### Authentication
- `POST /api/auth/register/` - Register a new user
- `POST /api/auth/login/` - Login
- `POST /api/auth/logout/` - Logout
- `GET /api/auth/user/` - Get current user info
- `POST /api/auth/password-reset/` - Request password reset
- `POST /api/auth/password-reset-confirm/` - Confirm password reset

### Problems
- `GET /api/problems/practice/` - Get problems to practice today
- `POST /api/problems/add/` - Add a new problem
- `GET /api/problems/` - Get all problems
- `GET /api/problems/<id>/` - Get problem details
- `PUT /api/problems/<id>/` - Update problem
- `DELETE /api/problems/<id>/` - Delete problem
- `POST /api/problems/<id>/done/` - Mark problem as practiced

## Project Structure

```
coding-practice-dashboard/
├── backend/
│   ├── accounts/          # Authentication app
│   ├── api/               # Problem management app
│   ├── codingflashcard/   # Django project settings
│   └── manage.py
├── frontend/
│   ├── src/
│   │   ├── components/    # React components
│   │   ├── pages/         # Page components
│   │   ├── services/      # API services
│   │   └── App.js
│   └── package.json
└── README.md
```

## Notes

- The password reset tokens are stored in memory (for development). In production, use Redis or a database.
- The Leetcode scraper may need updates if Leetcode changes their page structure.
- Make sure CORS is properly configured for your production domain.

## License

MIT

