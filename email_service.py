# Email Notification Service for Attendance System
# Sends email to student whenever attendance is marked successfully
# Uses SMTP (Gmail supported). Configure via environment variables.

import smtplib
import logging
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from datetime import datetime
from zoneinfo import ZoneInfo

logger = logging.getLogger(__name__)


def send_attendance_email(app, student_name: str, student_email: str, course_code: str, course_title: str, marked_at: datetime):
    """
    Send an attendance confirmation email to the student.

    Required environment variables (set in .env or system env):
        MAIL_USERNAME  - Your Gmail address (e.g. yourname@gmail.com)
        MAIL_PASSWORD  - Gmail App Password (NOT your normal password)
        MAIL_FROM_NAME - Sender display name (default: Attendance System)

    How to create Gmail App Password:
        1. Go to https://myaccount.google.com/security
        2. Enable 2-Step Verification
        3. Go to App passwords → create one for "Mail"
        4. Use that 16-character password as MAIL_PASSWORD
    """

    # Read config from Flask app config (which reads from environment)
    smtp_host   = app.config.get("MAIL_SERVER", "smtp.gmail.com")
    smtp_port   = int(app.config.get("MAIL_PORT", 587))
    username    = app.config.get("MAIL_USERNAME", "")
    password    = app.config.get("MAIL_PASSWORD", "")
    from_name   = app.config.get("MAIL_FROM_NAME", "Attendance System")
    app_tz      = app.config.get("APP_TIMEZONE", "Asia/Kolkata")

    if not username or not password:
        logger.warning("Email credentials not configured. Skipping email notification.")
        return

    # Format the time in local timezone
    if marked_at.tzinfo is None:
        from datetime import timezone
        marked_at = marked_at.replace(tzinfo=timezone.utc)
    local_time = marked_at.astimezone(ZoneInfo(app_tz))
    formatted_time = local_time.strftime("%d %B %Y, %I:%M %p")

    subject = f"✅ Attendance Marked – {course_code}"

    # HTML email body
    html_body = f"""
    <html>
    <body style="font-family: Arial, sans-serif; background-color: #f4f6f9; padding: 30px;">
      <div style="max-width: 500px; margin: auto; background: white; border-radius: 10px;
                  box-shadow: 0 2px 8px rgba(0,0,0,0.1); overflow: hidden;">

        <div style="background: linear-gradient(135deg, #1a73e8, #0d47a1); padding: 24px; text-align: center;">
          <h2 style="color: white; margin: 0;">Attendance Confirmed ✅</h2>
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
              <td style="padding: 10px 14px; font-weight: bold; color: #333;">Date & Time</td>
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

    # Plain text fallback
    text_body = (
        f"Hello {student_name},\n\n"
        f"Your attendance has been marked successfully.\n\n"
        f"Course Code : {course_code}\n"
        f"Course Name : {course_title}\n"
        f"Date & Time : {formatted_time}\n\n"
        f"If you did not mark this attendance, contact your teacher immediately.\n\n"
        f"-- Attendance System"
    )

    try:
        msg = MIMEMultipart("alternative")
        msg["Subject"] = subject
        msg["From"]    = f"{from_name} <{username}>"
        msg["To"]      = student_email

        msg.attach(MIMEText(text_body, "plain"))
        msg.attach(MIMEText(html_body, "html"))

        with smtplib.SMTP(smtp_host, smtp_port, timeout=10) as server:
            server.ehlo()
            server.starttls()
            server.login(username, password)
            server.sendmail(username, student_email, msg.as_string())

        logger.info(f"Attendance email sent to {student_email} for course {course_code}")

    except smtplib.SMTPAuthenticationError:
        logger.error("Email authentication failed. Check MAIL_USERNAME and MAIL_PASSWORD.")
    except smtplib.SMTPException as e:
        logger.error(f"SMTP error while sending email: {e}")
    except Exception as e:
        logger.error(f"Unexpected error sending attendance email: {e}")
