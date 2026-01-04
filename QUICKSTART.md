# Quick Start Guide

## Step 1: Install Dependencies

```bash
pip install -r requirements.txt
```

## Step 2: Create .env File

Create a `.env` file in the root directory:

```bash
cat > .env << EOF
SECRET_KEY=$(python -c "import secrets; print(secrets.token_hex(16))")
BREVO_API_KEY=your-brevo-api-key-here
BREVO_FROM_EMAIL=info@jobdistributor.net
BREVO_FROM_NAME=CodingFlashcard
FRONTEND_URL=http://localhost:5000
EOF
```

**Note**: Replace `your-brevo-api-key-here` with your actual Brevo API key, or leave it empty if you don't need password reset emails.

## Step 3: Run the Application

```bash
python app.py
```

The application will:
- Automatically create the SQLite database
- Start on `http://localhost:5000`

## Step 4: Use It!

1. Open `http://localhost:5000` in your browser
2. Register a new account
3. Click "Add Problem" and paste a Leetcode URL
4. Start practicing!

That's it! No MySQL, no Node.js, no complex setup. Just Python and Flask.
