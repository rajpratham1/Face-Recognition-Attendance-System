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


def send_low_attendance_alert(app, student, low_courses):
    """
    Send email alert to student about low attendance in courses.
    
    Args:
        app: Flask application instance
        student: User object (student)
        low_courses: List of dicts with course info and attendance data
    """
    if not student.email:
        logger.warning(f"No email for student {student.id}, skipping low attendance alert")
        return False
    
    subject = "⚠️ Low Attendance Alert - Action Required"
    
    # Build course list HTML
    course_rows = ""
    for course_data in low_courses:
        course = course_data['course']
        percentage = course_data['percentage']
        attended = course_data['attended']
        total = course_data['total']
        required = max(0, int((75 * total / 100) - attended))
        
        status_color = "#dc3545" if percentage < 50 else "#ffc107"
        
        course_rows += f"""
        <tr style="background-color: #fff3cd;">
          <td style="padding: 10px 14px; color: #333; border-bottom: 1px solid #e0e0e0;">{course.code}</td>
          <td style="padding: 10px 14px; color: #333; border-bottom: 1px solid #e0e0e0;">{course.title}</td>
          <td style="padding: 10px 14px; color: {status_color}; font-weight: bold; border-bottom: 1px solid #e0e0e0;">{percentage}%</td>
          <td style="padding: 10px 14px; color: #555; border-bottom: 1px solid #e0e0e0;">{attended}/{total}</td>
          <td style="padding: 10px 14px; color: #dc3545; font-weight: bold; border-bottom: 1px solid #e0e0e0;">{required}</td>
        </tr>
        """
    
    html_body = f"""
    <html>
    <body style="font-family: Arial, sans-serif; background-color: #f4f6f9; padding: 30px;">
      <div style="max-width: 600px; margin: auto; background: white; border-radius: 10px;
                  box-shadow: 0 2px 8px rgba(0,0,0,0.1); overflow: hidden;">
        <div style="background: linear-gradient(135deg, #dc3545, #c82333); padding: 24px; text-align: center;">
          <h2 style="color: white; margin: 0;">⚠️ Low Attendance Alert</h2>
        </div>
        <div style="padding: 28px;">
          <p style="font-size: 16px; color: #333;">Hello <strong>{student.name}</strong>,</p>
          <p style="color: #555;">
            Your attendance has fallen below the required 75% threshold in the following course(s).
            This may affect your eligibility to appear in exams.
          </p>
          
          <div style="background: #fff3cd; border-left: 4px solid #ffc107; padding: 12px; margin: 20px 0;">
            <strong style="color: #856404;">⚠️ Action Required:</strong>
            <p style="color: #856404; margin: 8px 0 0 0;">
              Attend all upcoming classes to improve your attendance percentage.
            </p>
          </div>
          
          <table style="width: 100%; border-collapse: collapse; margin-top: 16px;">
            <thead>
              <tr style="background-color: #f0f4ff;">
                <th style="padding: 10px 14px; text-align: left; color: #333; border-bottom: 2px solid #0d47a1;">Code</th>
                <th style="padding: 10px 14px; text-align: left; color: #333; border-bottom: 2px solid #0d47a1;">Course</th>
                <th style="padding: 10px 14px; text-align: left; color: #333; border-bottom: 2px solid #0d47a1;">%</th>
                <th style="padding: 10px 14px; text-align: left; color: #333; border-bottom: 2px solid #0d47a1;">Attended</th>
                <th style="padding: 10px 14px; text-align: left; color: #333; border-bottom: 2px solid #0d47a1;">Need</th>
              </tr>
            </thead>
            <tbody>
              {course_rows}
            </tbody>
          </table>
          
          <p style="margin-top: 24px; color: #555;">
            <strong>What you should do:</strong>
          </p>
          <ul style="color: #555;">
            <li>Attend all upcoming classes without fail</li>
            <li>Contact your course teacher if you have valid reasons for absences</li>
            <li>Check your attendance regularly on the portal</li>
            <li>Aim for 100% attendance in remaining sessions</li>
          </ul>
          
          <p style="margin-top: 24px; color: #777; font-size: 13px;">
            If you have any concerns or need assistance, please contact your academic advisor or course coordinator.
          </p>
        </div>
        <div style="background: #f9f9f9; padding: 14px; text-align: center; border-top: 1px solid #eee;">
          <p style="color: #aaa; font-size: 12px; margin: 0;">
            This is an automated daily alert from the Attendance System.
          </p>
        </div>
      </div>
    </body>
    </html>
    """
    
    # Build text version
    text_body = f"Hello {student.name},\n\n"
    text_body += "Your attendance has fallen below 75% in the following courses:\n\n"
    
    for course_data in low_courses:
        course = course_data['course']
        percentage = course_data['percentage']
        attended = course_data['attended']
        total = course_data['total']
        required = max(0, int((75 * total / 100) - attended))
        
        text_body += f"- {course.code} ({course.title}): {percentage}% ({attended}/{total} sessions)\n"
        text_body += f"  You need to attend {required} more sessions to reach 75%\n\n"
    
    text_body += "\nAction Required:\n"
    text_body += "- Attend all upcoming classes\n"
    text_body += "- Contact your teacher if you have valid reasons\n"
    text_body += "- Check your attendance regularly\n\n"
    text_body += "-- Attendance System"
    
    return _send_email(app, student.email, subject, text_body, html_body)


def send_session_start_notification(app, student, session):
    """
    Send email notification when a teacher starts a live session.
    
    Args:
        app: Flask application instance
        student: User object (student)
        session: ClassSession object
    """
    if not student.email:
        return False
    
    settings = _mail_settings(app)
    
    # Convert session time to local timezone
    if session.ends_at.tzinfo is None:
        ends_at = session.ends_at.replace(tzinfo=timezone.utc)
    else:
        ends_at = session.ends_at
    
    local_end_time = ends_at.astimezone(ZoneInfo(settings["app_tz"]))
    formatted_end_time = local_end_time.strftime("%I:%M %p")
    
    subject = f"🔴 Live Session Started - {session.course_code}"
    
    html_body = f"""
    <html>
    <body style="font-family: Arial, sans-serif; background-color: #f4f6f9; padding: 30px;">
      <div style="max-width: 500px; margin: auto; background: white; border-radius: 10px;
                  box-shadow: 0 2px 8px rgba(0,0,0,0.1); overflow: hidden;">
        <div style="background: linear-gradient(135deg, #28a745, #218838); padding: 24px; text-align: center;">
          <h2 style="color: white; margin: 0;">🔴 Live Session Started</h2>
        </div>
        <div style="padding: 28px;">
          <p style="font-size: 16px; color: #333;">Hello <strong>{student.name}</strong>,</p>
          <p style="color: #555;">
            Your teacher has started a live class session. Mark your attendance now!
          </p>
          
          <div style="background: #d4edda; border-left: 4px solid #28a745; padding: 12px; margin: 20px 0;">
            <strong style="color: #155724;">Session Details:</strong>
            <p style="color: #155724; margin: 8px 0 0 0;">
              <strong>{session.course_code}</strong> - {session.title}<br>
              Room: {session.room}<br>
              Ends at: {formatted_end_time}
            </p>
          </div>
          
          <p style="margin: 24px 0; text-align: center;">
            <a href="#" style="display: inline-block; padding: 12px 22px; border-radius: 8px;
               background: #28a745; color: white; text-decoration: none; font-weight: 600;">
              Mark Attendance Now
            </a>
          </p>
          
          <p style="color: #777; font-size: 13px;">
            ⚠️ Remember: You must be in the classroom to mark attendance.
          </p>
        </div>
        <div style="background: #f9f9f9; padding: 14px; text-align: center; border-top: 1px solid #eee;">
          <p style="color: #aaa; font-size: 12px; margin: 0;">
            This is an automated notification from the Attendance System.
          </p>
        </div>
      </div>
    </body>
    </html>
    """
    
    text_body = (
        f"Hello {student.name},\n\n"
        f"A live class session has started:\n\n"
        f"Course: {session.course_code} - {session.title}\n"
        f"Room: {session.room}\n"
        f"Ends at: {formatted_end_time}\n\n"
        f"Mark your attendance now! Remember to be in the classroom.\n\n"
        f"-- Attendance System"
    )
    
    return _send_email(app, student.email, subject, text_body, html_body)
