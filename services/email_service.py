"""
Email service - Business logic for sending emails via Brevo.
"""
from typing import Optional
import sib_api_v3_sdk
from sib_api_v3_sdk.rest import ApiException
from flask import current_app


class EmailService:
    """Service for sending emails via Brevo."""
    
    @staticmethod
    def send_email(to_email: str, subject: str, html_content: str) -> bool:
        """
        Send an email via Brevo.
        
        Returns:
            True if sent successfully, False otherwise
        """
        api_key = current_app.config.get('BREVO_API_KEY', '')
        from_email = current_app.config.get('BREVO_FROM_EMAIL', '')
        from_name = current_app.config.get('BREVO_FROM_NAME', 'CodingFlashcard')
        
        if not api_key:
            print("BREVO_API_KEY not configured")
            return False
        
        try:
            configuration = sib_api_v3_sdk.Configuration()
            configuration.api_key['api-key'] = api_key
            
            api_instance = sib_api_v3_sdk.TransactionalEmailsApi(
                sib_api_v3_sdk.ApiClient(configuration)
            )
            
            send_smtp_email = sib_api_v3_sdk.SendSmtpEmail(
                to=[{"email": to_email}],
                sender={"name": from_name, "email": from_email},
                subject=subject,
                html_content=html_content,
            )
            
            api_instance.send_transac_email(send_smtp_email)
            return True
            
        except ApiException as e:
            print(f"Error sending email: {e}")
            return False
        except Exception as e:
            print(f"Unexpected error sending email: {e}")
            return False
    
    @staticmethod
    def send_password_reset_email(email: str, reset_link: str) -> bool:
        """Send password reset email."""
        html_content = f"""
        <h2>Password Reset Request</h2>
        <p>You requested a password reset for your CodingFlashcard account.</p>
        <p>Click the link below to reset your password:</p>
        <p><a href="{reset_link}">{reset_link}</a></p>
        <p>This link will expire in 1 hour.</p>
        <p>If you didn't request this, please ignore this email.</p>
        """
        return EmailService.send_email(
            to_email=email,
            subject="Password Reset - CodingFlashcard",
            html_content=html_content
        )
    
    @staticmethod
    def send_email_verification_code(
        email: str,
        code: str,
        is_current_email: bool = True
    ) -> bool:
        """Send email verification code for email change."""
        email_type = "current" if is_current_email else "new"
        html_content = f"""
        <h2>Email change verification</h2>
        <p>Use this code to verify your <b>{email_type}</b> email address:</p>
        <p style="font-size:24px;font-weight:700;letter-spacing:2px;">{code}</p>
        <p>This code expires in 10 minutes.</p>
        """
        return EmailService.send_email(
            to_email=email,
            subject=f"Verify email change ({email_type} email) - CodingFlashcard",
            html_content=html_content
        )
    
    @staticmethod
    def send_daily_practice_email(
        email: str,
        date_label: str,
        practice_items: list
    ) -> bool:
        """Send daily practice reminder email."""
        if practice_items:
            rows = "\n".join([
                f"""
                <tr>
                  <td style="padding:10px 12px;border-bottom:1px solid #eee;">
                    <a href="{item['leetcode_url']}" style="color:#111;text-decoration:none;font-weight:700;">
                      {item['title']}
                    </a>
                    <div style="margin-top:4px;color:#666;font-size:12px;">{item['leetcode_url']}</div>
                  </td>
                  <td style="padding:10px 12px;border-bottom:1px solid #eee;text-align:right;white-space:nowrap;">
                    <span style="display:inline-block;padding:4px 10px;border-radius:999px;border:2px solid #111;font-weight:900;font-size:12px;">
                      {item['difficulty'].upper()}
                    </span>
                  </td>
                </tr>
                """.strip()
                for item in practice_items
            ])
            
            html_content = f"""
            <div style="font-family:system-ui,-apple-system,Segoe UI,Roboto,Helvetica,Arial,sans-serif;">
              <h2 style="margin:0 0 8px 0;">Today's practice list</h2>
              <div style="color:#666;margin-bottom:14px;">{date_label} • CodingFlashcard</div>
              <table style="width:100%;border-collapse:collapse;border:2px solid #111;border-radius:14px;overflow:hidden;">
                <thead>
                  <tr>
                    <th style="text-align:left;padding:10px 12px;background:#111;color:#fff;">Problem</th>
                    <th style="text-align:right;padding:10px 12px;background:#111;color:#fff;">Difficulty</th>
                  </tr>
                </thead>
                <tbody>
                  {rows}
                </tbody>
              </table>
              <p style="color:#666;margin-top:14px;">Tip: open a problem, solve it, then hit "Done".</p>
            </div>
            """
        else:
            html_content = f"""
            <div style="font-family:system-ui,-apple-system,Segoe UI,Roboto,Helvetica,Arial,sans-serif;">
              <h2 style="margin:0 0 8px 0;">No practice items today</h2>
              <div style="color:#666;margin-bottom:14px;">{date_label} • CodingFlashcard</div>
              <p style="color:#111;">You're all caught up. Add more problems to keep your spaced repetition going.</p>
            </div>
            """
        
        return EmailService.send_email(
            to_email=email,
            subject=f"Today's practice - CodingFlashcard ({date_label})",
            html_content=html_content
        )
