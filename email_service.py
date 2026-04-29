import logging
import smtplib
from datetime import datetime, timezone
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from zoneinfo import ZoneInfo

logger = logging.getLogger(__name__)


def _mail_settings(app):
    return {
        "smtp_host": app.config.get("MAIL_SERVER", "smtp.gmail.com"),
        "smtp_port": int(app.config.get("MAIL_PORT", 587)),
        "username": app.config.get("MAIL_USERNAME", ""),
        "password": app.config.get("MAIL_PASSWORD", ""),
        "from_name": app.config.get("MAIL_FROM_NAME", "Attendance System"),
        "app_tz": app.config.get("APP_TIMEZONE", "Asia/Kolkata"),
    }


def _send_email(app, recipient_email, subject, text_body, html_body):
    settings = _mail_settings(app)
    username = settings["username"]
    password = settings["password"]

    if not username or not password:
        logger.warning("Email credentials not configured. Skipping outbound email for %s.", recipient_email)
        return False

    try:
        msg = MIMEMultipart("alternative")
        msg["Subject"] = subject
        msg["From"] = f'{settings["from_name"]} <{username}>'
        msg["To"] = recipient_email
        msg.attach(MIMEText(text_body, "plain"))
        msg.attach(MIMEText(html_body, "html"))

        with smtplib.SMTP(settings["smtp_host"], settings["smtp_port"], timeout=10) as server:
            server.ehlo()
            server.starttls()
            server.login(username, password)
            server.sendmail(username, recipient_email, msg.as_string())

        logger.info("Email sent to %s with subject %s", recipient_email, subject)
        return True
    except smtplib.SMTPAuthenticationError:
        logger.error("Email authentication failed. Check MAIL_USERNAME and MAIL_PASSWORD.")
    except smtplib.SMTPException as exc:
        logger.error("SMTP error while sending email: %s", exc)
    except Exception as exc:
        logger.error("Unexpected error sending email: %s", exc)
    return False


def send_attendance_email(app, student_name, student_email, course_code, course_title, marked_at):
    settings = _mail_settings(app)

    if marked_at.tzinfo is None:
        marked_at = marked_at.replace(tzinfo=timezone.utc)
    local_time = marked_at.astimezone(ZoneInfo(settings["app_tz"]))
    formatted_time = local_time.strftime("%d %B %Y, %I:%M %p")

    subject = f"Attendance Marked - {course_code}"
    html_body = f"""
    <html>
    <body style="font-family: Arial, sans-serif; background-color: #f4f6f9; padding: 30px;">
      <div style="max-width: 500px; margin: auto; background: white; border-radius: 10px;
                  box-shadow: 0 2px 8px rgba(0,0,0,0.1); overflow: hidden;">
        <div style="background: linear-gradient(135deg, #1a73e8, #0d47a1); padding: 24px; text-align: center;">
          <h2 style="color: white; margin: 0;">Attendance Confirmed</h2>
        </div>
        <div style="padding: 28px;">
          <p style="font-size: 16px; color: #333;">Hello <strong>{student_name}</strong>,</p>
          <p style="color: #555;">Your attendance has been successfully marked. Here are the details:</p>
          <table style="width: 100%; border-collapse: collapse; margin-top: 16px;">
            <tr style="background-color: #f0f4ff;">
              <td style="padding: 10px 14px; font-weight: bold; color: #333; border-bottom: 1px solid #e0e0e0;">Course Code</td>
              <td style="padding: 10px 14px; color: #555; border-bottom: 1px solid #e0e0e0;">{course_code}</td>
            </tr>
            <tr>
              <td style="padding: 10px 14px; font-weight: bold; color: #333; border-bottom: 1px solid #e0e0e0;">Course Name</td>
              <td style="padding: 10px 14px; color: #555; border-bottom: 1px solid #e0e0e0;">{course_title}</td>
            </tr>
            <tr style="background-color: #f0f4ff;">
              <td style="padding: 10px 14px; font-weight: bold; color: #333;">Date and Time</td>
              <td style="padding: 10px 14px; color: #555;">{formatted_time}</td>
            </tr>
          </table>
          <p style="margin-top: 24px; color: #777; font-size: 13px;">
            If you did not mark this attendance or believe this is an error, please contact your teacher immediately.
          </p>
        </div>
        <div style="background: #f9f9f9; padding: 14px; text-align: center; border-top: 1px solid #eee;">
          <p style="color: #aaa; font-size: 12px; margin: 0;">
            This is an automated message from the Face Recognition Attendance System. Do not reply.
          </p>
        </div>
      </div>
    </body>
    </html>
    """
    text_body = (
        f"Hello {student_name},\n\n"
        f"Your attendance has been marked successfully.\n\n"
        f"Course Code : {course_code}\n"
        f"Course Name : {course_title}\n"
        f"Date and Time : {formatted_time}\n\n"
        f"If you did not mark this attendance, contact your teacher immediately.\n\n"
        f"-- Attendance System"
    )
    return _send_email(app, student_email, subject, text_body, html_body)


def send_password_reset_email(app, user_name, user_email, reset_url, expires_in_minutes):
    subject = "Reset Your Attendance Portal Password"
    html_body = f"""
    <html>
    <body style="font-family: Arial, sans-serif; background-color: #f4f6f9; padding: 30px;">
      <div style="max-width: 500px; margin: auto; background: white; border-radius: 10px;
                  box-shadow: 0 2px 8px rgba(0,0,0,0.1); overflow: hidden;">
        <div style="background: linear-gradient(135deg, #0f766e, #115e59); padding: 24px; text-align: center;">
          <h2 style="color: white; margin: 0;">Password Reset Request</h2>
        </div>
        <div style="padding: 28px;">
          <p style="font-size: 16px; color: #333;">Hello <strong>{user_name}</strong>,</p>
          <p style="color: #555;">
            We received a request to reset your password for the attendance portal.
            Use the button below to choose a new password.
          </p>
          <p style="margin: 24px 0; text-align: center;">
            <a href="{reset_url}" style="display: inline-block; padding: 12px 22px; border-radius: 8px;
               background: #0f766e; color: white; text-decoration: none; font-weight: 600;">
              Reset Password
            </a>
          </p>
          <p style="color: #555;">
            This link expires in {expires_in_minutes} minutes. If you did not request a password reset,
            you can ignore this email and your current password will continue to work.
          </p>
        </div>
        <div style="background: #f9f9f9; padding: 14px; text-align: center; border-top: 1px solid #eee;">
          <p style="color: #aaa; font-size: 12px; margin: 0;">
            If the button does not work, copy this link into your browser:<br>{reset_url}
          </p>
        </div>
      </div>
    </body>
    </html>
    """
    text_body = (
        f"Hello {user_name},\n\n"
        "We received a request to reset your password for the attendance portal.\n\n"
        f"Reset your password here: {reset_url}\n\n"
        f"This link expires in {expires_in_minutes} minutes.\n"
        "If you did not request this change, you can ignore this email.\n\n"
        "-- Attendance System"
    )
    return _send_email(app, user_email, subject, text_body, html_body)
