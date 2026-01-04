# Quick Start Guide

## Step 1: Backend Setup

### 1.1 Activate Virtual Environment and Install Dependencies
```bash
cd backend
source ../venv/bin/activate  # The venv was already created
pip install -r requirements.txt
```

### 1.2 Create MySQL Database
First, make sure MySQL is running. Then create the database:
```bash
mysql -u root -p
```

In MySQL prompt:
```sql
CREATE DATABASE codingflashcard CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
EXIT;
```

### 1.3 Create .env File
Create `backend/.env` file with your database credentials:
```bash
cd backend
cat > .env << EOF
DB_NAME=codingflashcard
DB_USER=root
DB_PASSWORD=your_mysql_password_here
DB_HOST=localhost
DB_PORT=3306
SECRET_KEY=django-insecure-dev-key-change-in-production
BREVO_API_KEY=your-brevo-api-key-here
BREVO_FROM_EMAIL=info@jobdistributor.net
BREVO_FROM_NAME=CodingFlashcard
FRONTEND_URL=http://localhost:3000
EOF
```

**Important**: Replace `your_mysql_password_here` with your actual MySQL root password, and `your-brevo-api-key-here` with your Brevo API key.

### 1.4 Run Migrations
```bash
python manage.py makemigrations
python manage.py migrate
```

### 1.5 Create Superuser (Optional)
```bash
python manage.py createsuperuser
```

### 1.6 Start Backend Server
```bash
python manage.py runserver
```

Backend will run on `http://localhost:8000`

---

## Step 2: Frontend Setup

### 2.1 Install Node Dependencies
Open a **new terminal window** (keep backend running):
```bash
cd frontend
npm install
```

### 2.2 Create .env File
```bash
cat > .env << EOF
REACT_APP_API_URL=http://localhost:8000/api
EOF
```

### 2.3 Start Frontend Server
```bash
npm start
```

Frontend will run on `http://localhost:3000` and automatically open in your browser.

---

## Step 3: Use the Application

1. Open `http://localhost:3000` in your browser
2. Register a new account
3. Click "Add Problem" and paste a Leetcode URL
4. Start practicing!

---

## Troubleshooting

### MySQL Connection Error
- Make sure MySQL is running: `brew services list` (on macOS) or check your MySQL service
- Verify database credentials in `backend/.env`
- Test connection: `mysql -u root -p -e "USE codingflashcard;"`

### Port Already in Use
- Backend: Change port with `python manage.py runserver 8001`
- Frontend: It will prompt you to use a different port

### Module Not Found Errors
- Make sure virtual environment is activated: `source ../venv/bin/activate`
- Reinstall dependencies: `pip install -r requirements.txt`

### CORS Errors
- Make sure backend is running on port 8000
- Check `backend/codingflashcard/settings.py` CORS settings

