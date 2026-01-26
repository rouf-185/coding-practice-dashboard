#!/usr/bin/env python3
"""
Daily Email Worker - Background process to send daily practice emails.

Usage:
    python daily_email_worker.py

This worker runs continuously and checks every minute if any users
need to receive their daily practice email based on their timezone
and preferred send time.
"""
import time
from datetime import datetime
from zoneinfo import ZoneInfo


def send_daily_practice_emails():
    """
    Send daily practice emails to eligible users.
    
    Checks each user with daily email enabled and sends if:
    1. Current time in user's timezone is >= their preferred send time
    2. Email hasn't been sent today (in user's timezone)
    """
    from repositories import UserRepository
    from services import PracticeService, EmailService
    from extensions import db
    
    utc_now = datetime.utcnow()
    users = UserRepository.get_users_with_daily_email_enabled()
    
    for user in users:
        try:
            user_tz = PracticeService.get_user_timezone(user)
            local_now = utc_now.replace(tzinfo=ZoneInfo('UTC')).astimezone(user_tz)
            local_today = local_now.date()
            
            # Parse preferred send time
            send_time_str = user.daily_email_time or '06:00'
            try:
                hh, mm = send_time_str.split(':')
                send_hour = int(hh)
                send_minute = int(mm)
            except ValueError:
                send_hour, send_minute = 6, 0
            
            # Check if it's time to send
            if local_now.hour < send_hour:
                continue
            if local_now.hour == send_hour and local_now.minute < send_minute:
                continue
            
            # Check if already sent today
            if user.daily_email_last_sent_at:
                last_sent_local = user.daily_email_last_sent_at.replace(
                    tzinfo=ZoneInfo('UTC')
                ).astimezone(user_tz)
                if last_sent_local.date() == local_today:
                    continue
            
            # Get practice items
            practice_items = PracticeService.get_practice_items_for_email(user, utc_now)
            date_label = local_today.strftime('%A, %B %d, %Y')
            
            # Send email
            success = EmailService.send_daily_practice_email(
                user.email,
                date_label,
                practice_items
            )
            
            if success:
                user.daily_email_last_sent_at = utc_now
                db.session.commit()
                print(f"[{datetime.utcnow().isoformat()}] Sent daily email to {user.email}")
            else:
                print(f"[{datetime.utcnow().isoformat()}] Failed to send email to {user.email}")
                
        except Exception as e:
            print(f"[{datetime.utcnow().isoformat()}] Error processing user {user.id}: {e}")
            continue


def main():
    """Main worker loop."""
    from app import app
    
    print("Starting daily email worker...")
    print("Press Ctrl+C to stop.")
    
    with app.app_context():
        while True:
            try:
                send_daily_practice_emails()
            except Exception as e:
                print(f"[{datetime.utcnow().isoformat()}] Worker error: {e}")
            
            # Sleep for 1 minute
            time.sleep(60)


if __name__ == '__main__':
    main()
