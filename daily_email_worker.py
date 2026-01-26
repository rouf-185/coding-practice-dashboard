import time
from datetime import datetime

from app import app, db, migrate_database, send_daily_practice_emails


def main():
    """
    Background worker that checks once per minute and sends daily practice emails
    at the user's configured local time.

    Run this in a separate process from the Flask web server:
      python3 daily_email_worker.py
    """
    with app.app_context():
        migrate_database()
        while True:
            try:
                sent = send_daily_practice_emails(datetime.utcnow())
                if sent:
                    print(f"Daily email worker: sent {sent} email(s)")
            except Exception as e:
                print(f"Daily email worker error: {e}")
            time.sleep(60)


if __name__ == "__main__":
    main()

