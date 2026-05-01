import csv
from collections import defaultdict
import hashlib
import io
import json
import secrets
import threading
from math import isfinite
from datetime import datetime, timedelta, timezone
from zoneinfo import ZoneInfo

import numpy as np
from flask import Flask, Response, flash, jsonify, redirect, render_template, request, url_for
from flask_login import LoginManager, current_user, login_required, login_user, logout_user
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from flask_wtf.csrf import CSRFError, CSRFProtect, generate_csrf
from geopy.distance import geodesic
from itsdangerous import BadSignature, SignatureExpired, URLSafeTimedSerializer
from sqlalchemy import func, inspect, text
from sqlalchemy.exc import IntegrityError
from werkzeug.security import check_password_hash, generate_password_hash

from config import Config
from firebase_service import init_firebase, sync_attendance_attempt, sync_session_attendance
from email_service import send_attendance_email, send_password_reset_email
from models import (
    Attendance,
    AttendanceAttempt,
    BulkEnrollment,
    ClassSession,
    Course,
    Enrollment,
    SessionAttendance,
    TeacherAssignment,
    User,
    db,
)

app = Flask(__name__)
app.config.from_object(Config)
if not app.config.get("SECRET_KEY"):
    if app.config.get("FLASK_ENV") == "production" and app.config.get("ENFORCE_SECRET_KEY_IN_PRODUCTION", True):
        raise RuntimeError("SECRET_KEY must be configured before starting the app in production.")
    # Stable dev fallback for local development.
    app.config["SECRET_KEY"] = "dev-insecure-change-me"

csrf = CSRFProtect(app)
db.init_app(app)
limiter = Limiter(key_func=get_remote_address, app=app, default_limits=["200 per day", "60 per hour"])
init_firebase(app)

login_manager = LoginManager()
login_manager.login_view = "login"
login_manager.init_app(app)

# This function loads user from database for session management
@login_manager.user_loader
def load_user(user_id):
    return db.session.get(User, int(user_id))


@app.context_processor
def inject_template_globals():
    firebase_web_config = {
        "apiKey": app.config.get("FIREBASE_API_KEY", ""),
        "authDomain": app.config.get("FIREBASE_AUTH_DOMAIN", ""),
        "databaseURL": app.config.get("FIREBASE_DATABASE_URL", ""),
        "projectId": app.config.get("FIREBASE_PROJECT_ID", ""),
        "storageBucket": app.config.get("FIREBASE_STORAGE_BUCKET", ""),
        "messagingSenderId": app.config.get("FIREBASE_MESSAGING_SENDER_ID", ""),
        "appId": app.config.get("FIREBASE_APP_ID", ""),
    }
    liveness_config = {
        "enabled": app.config.get("LIVENESS_DETECTION_ENABLED", True),
        "requireBlink": app.config.get("LIVENESS_REQUIRE_BLINK", True),
        "requireHeadMovement": app.config.get("LIVENESS_REQUIRE_HEAD_MOVEMENT", True),
        "timeoutSeconds": app.config.get("LIVENESS_TIMEOUT_SECONDS", 15),
        "blinkThreshold": app.config.get("LIVENESS_BLINK_THRESHOLD", 0.25),
        "movementThreshold": app.config.get("LIVENESS_MOVEMENT_THRESHOLD", 15),
        "qualityThreshold": app.config.get("LIVENESS_QUALITY_THRESHOLD", 0.6),
    }
    return {
        "csrf_token": generate_csrf,
        "app_name": app.config["APP_NAME"],
        "app_program_name": app.config["APP_PROGRAM_NAME"],
        "app_geofence_label": app.config["APP_GEOFENCE_LABEL"],
        "app_timezone": app.config["APP_TIMEZONE"],
        "firebase_web_config": firebase_web_config,
        "firebase_enabled": app.extensions.get("firebase_enabled", False),
        "firebase_error": app.extensions.get("firebase_error", ""),
        "liveness_config": liveness_config,
    }


@app.template_filter("localdt")
def local_datetime_filter(value):
    if not value:
        return "-"
    if value.tzinfo is None:
        value = value.replace(tzinfo=timezone.utc)
    return value.astimezone(ZoneInfo(app.config["APP_TIMEZONE"]))


@app.template_filter("localdtfmt")
def local_datetime_format_filter(value, fmt="%d %b %Y %I:%M %p"):
    localized = local_datetime_filter(value)
    if localized == "-":
        return "-"
    return localized.strftime(fmt)


@app.errorhandler(CSRFError)
def handle_csrf_error(error):
    if request.path.startswith("/api/") or request.is_json:
        return jsonify({"success": False, "message": "Security token missing or expired. Refresh page and try again."}), 400
    flash("Security check failed. Please retry the action.", "danger")
    return redirect(url_for("index"))


@app.errorhandler(404)
def handle_404(error):
    """Handle 404 Not Found errors gracefully."""
    if request.path.startswith("/api/"):
        return jsonify({"success": False, "message": "Resource not found."}), 404
    flash("Page not found.", "warning")
    return redirect(url_for("index"))


@app.errorhandler(403)
def handle_403(error):
    """Handle 403 Forbidden errors gracefully."""
    if request.path.startswith("/api/"):
        return jsonify({"success": False, "message": "Access denied."}), 403
    flash("Access denied.", "danger")
    return redirect(url_for("index"))


@app.errorhandler(500)
def handle_500(error):
    """Handle 500 Internal Server errors gracefully."""
    app.logger.error("500 error: %s", str(error), exc_info=True)
    if request.path.startswith("/api/") or request.is_json:
        return jsonify({"success": False, "message": "Server error. Please try again later."}), 500
    flash("An unexpected error occurred. Please try again.", "danger")
    return redirect(url_for("index"))


def now_utc_naive():
    return datetime.now(timezone.utc).replace(tzinfo=None)


def now_local():
    return datetime.now(ZoneInfo(app.config["APP_TIMEZONE"]))


def today_local_date():
    return now_local().date()


def generate_sessions_from_timetable():
    """
    Auto-generate class sessions from timetable entries.
    
    This function should be called periodically (e.g., via cron job or scheduler).
    It creates sessions 15 minutes before the scheduled class time.
    
    Logic:
    1. Get current day of week and time
    2. Find timetable entries for today
    3. For entries starting in next 15-30 minutes, create session if not exists
    4. Auto-close sessions that ended 15+ minutes ago
    """
    from models import Timetable
    
    now = now_local()
    current_day = now.weekday()  # 0=Monday, 6=Sunday
    current_time = now.time()
    
    # Calculate time window: 15-30 minutes from now
    window_start = (now + timedelta(minutes=15)).time()
    window_end = (now + timedelta(minutes=30)).time()
    
    # Find timetable entries for today that start in the window
    timetable_entries = Timetable.query.filter(
        Timetable.day_of_week == current_day,
        Timetable.is_active == True,
        Timetable.start_time >= window_start,
        Timetable.start_time < window_end
    ).all()
    
    sessions_created = 0
    sessions_closed = 0
    
    for entry in timetable_entries:
        # Check if session already exists for today
        today_date = now.date()
        
        # Combine date and time for session start/end
        starts_at_local = datetime.combine(today_date, entry.start_time)
        ends_at_local = datetime.combine(today_date, entry.end_time)
        
        # Convert to UTC naive for database
        starts_at_utc = starts_at_local.replace(tzinfo=ZoneInfo(app.config["APP_TIMEZONE"])).astimezone(timezone.utc).replace(tzinfo=None)
        ends_at_utc = ends_at_local.replace(tzinfo=ZoneInfo(app.config["APP_TIMEZONE"])).astimezone(timezone.utc).replace(tzinfo=None)
        
        # Check if session already exists
        existing_session = ClassSession.query.filter(
            ClassSession.course_id == entry.course_id,
            ClassSession.teacher_id == entry.teacher_id,
            ClassSession.section == entry.section,
            ClassSession.starts_at == starts_at_utc
        ).first()
        
        if not existing_session:
            # Create new session
            try:
                new_session = ClassSession(
                    title=entry.course.title,
                    course_code=entry.course.code,
                    room=entry.room,
                    course_id=entry.course_id,
                    section=entry.section,
                    starts_at=starts_at_utc,
                    ends_at=ends_at_utc,
                    teacher_id=entry.teacher_id,
                    is_active=True,
                    location_lat=None,  # Will be set when teacher starts session
                    location_lng=None,
                    location_radius_meters=app.config["SESSION_LOCATION_RADIUS_METERS"],
                )
                db.session.add(new_session)
                sessions_created += 1
                
                app.logger.info(
                    f"Auto-generated session: {entry.course.code} - Section {entry.section} - {entry.get_day_name()} {entry.start_time}"
                )
            except Exception as e:
                app.logger.error(f"Error creating auto-session: {str(e)}")
                db.session.rollback()
                continue
    
    # Auto-close sessions that ended 15+ minutes ago
    close_threshold = now_utc_naive() - timedelta(minutes=15)
    expired_sessions = ClassSession.query.filter(
        ClassSession.is_active == True,
        ClassSession.ends_at < close_threshold
    ).all()
    
    for session in expired_sessions:
        session.is_active = False
        sessions_closed += 1
        app.logger.info(f"Auto-closed session: {session.course_code} - Session ID {session.id}")
    
    try:
        db.session.commit()
        app.logger.info(f"Auto-session generation complete: {sessions_created} created, {sessions_closed} closed")
    except Exception as e:
        db.session.rollback()
        app.logger.error(f"Error committing auto-sessions: {str(e)}")
    
    return {
        "sessions_created": sessions_created,
        "sessions_closed": sessions_closed
    }


def password_validation_error(password):
    if len(password) < 8:
        return "Password must be at least 8 characters long."
    if not any(c.isdigit() for c in password):
        return "Password must contain at least one number."
    if not any(c.isupper() for c in password):
        return "Password must contain at least one uppercase letter."
    return None


def password_reset_serializer():
    return URLSafeTimedSerializer(app.config["SECRET_KEY"])


def password_reset_signature(user):
    payload = f"{user.id}:{user.email}:{user.password_hash}"
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def generate_password_reset_token(user):
    return password_reset_serializer().dumps(
        {"user_id": user.id, "sig": password_reset_signature(user)},
        salt=app.config["PASSWORD_RESET_SALT"],
    )


def get_user_from_reset_token(token):
    try:
        data = password_reset_serializer().loads(
            token,
            salt=app.config["PASSWORD_RESET_SALT"],
            max_age=int(app.config["PASSWORD_RESET_TOKEN_MAX_AGE_MINUTES"]) * 60,
        )
    except (BadSignature, SignatureExpired, TypeError, ValueError):
        return None

    user_id = data.get("user_id")
    user = db.session.get(User, int(user_id)) if user_id is not None else None
    if not user:
        return None

    signature = data.get("sig", "")
    if not secrets.compare_digest(signature, password_reset_signature(user)):
        return None
    return user


def is_within_invertis(lat, lng):
    if not app.config.get("GEOFENCE_ENFORCED", True):
        return True
    if lat is None or lng is None:
        return False
    try:
        lat = float(lat)
        lng = float(lng)
    except (ValueError, TypeError):
        return False
        
    user_location = (lat, lng)
    invertis_location = (app.config["INVERTIS_LAT"], app.config["INVERTIS_LNG"])
    distance = geodesic(user_location, invertis_location).meters
    
    # ── LOGGING DISTANCE FOR DEBUGGING ──
    app.logger.info(f"Geofence Check: User Location {user_location} -> Distance to allowed zone: {distance:.2f} meters")
    
    return distance <= app.config["ALLOWED_RADIUS_METERS"]


def _parse_coordinates(lat, lng):
    try:
        parsed_lat = float(lat)
        parsed_lng = float(lng)
    except (ValueError, TypeError):
        return None, None
    return parsed_lat, parsed_lng


def classroom_geofence_status(session, lat, lng):
    parsed_lat, parsed_lng = _parse_coordinates(lat, lng)
    if parsed_lat is None or parsed_lng is None:
        return {
            "ok": False,
            "reason": "missing_location",
            "message": "Current location is required for classroom attendance.",
        }

    if session.location_lat is None or session.location_lng is None:
        return {
            "ok": False,
            "reason": "session_location_missing",
            "message": "Teacher classroom location is unavailable for this session.",
        }

    radius = int(session.location_radius_meters or app.config["SESSION_LOCATION_RADIUS_METERS"])
    distance = geodesic(
        (parsed_lat, parsed_lng),
        (float(session.location_lat), float(session.location_lng)),
    ).meters
    return {
        "ok": distance <= radius,
        "reason": "outside_classroom_radius" if distance > radius else "inside_classroom_radius",
        "distance": distance,
        "radius": radius,
        "message": (
            f"Go to the classroom to mark attendance. You are about {distance:.0f} meters away from the live class area."
            if distance > radius
            else ""
        ),
    }


def get_request_meta(data):
    device_id = (data or {}).get("device_id") or ""
    device_hash = hashlib.sha256(device_id.encode("utf-8")).hexdigest() if device_id else None
    ip_address = (request.headers.get("X-Forwarded-For", request.remote_addr) or "").split(",")[0].strip()[:64]
    user_agent = (request.user_agent.string or "")[:255]
    return device_hash, ip_address, user_agent


def record_attempt(session_id, student_id, success, reason, lat=None, lng=None, face_distance=None, device_hash=None, ip_address=None, user_agent=None):
    attempt = AttendanceAttempt(
        session_id=session_id,
        student_id=student_id,
        success=success,
        reason=reason,
        latitude=lat,
        longitude=lng,
        face_distance=face_distance,
        device_hash=device_hash,
        ip_address=ip_address,
        user_agent=user_agent,
    )
    db.session.add(attempt)
    sync_attendance_attempt(
        app,
        {
            "sessionId": session_id,
            "studentId": student_id,
            "success": bool(success),
            "reason": reason,
            "latitude": lat,
            "longitude": lng,
            "faceDistance": face_distance,
            "deviceHash": device_hash,
            "ipAddress": ip_address,
            "userAgent": user_agent,
            "createdAt": datetime.now(timezone.utc).isoformat(),
        },
    )


def student_active_sessions(student_id):
    now = now_utc_naive()
    course_ids = [
        row[0]
        for row in db.session.query(Enrollment.course_id).filter(Enrollment.student_id == student_id).all()
    ]
    if not course_ids:
        return []
    return (
        ClassSession.query.filter(
            ClassSession.course_id.in_(course_ids),
            ClassSession.is_active.is_(True),
            ClassSession.starts_at <= now,
            ClassSession.ends_at >= now,
        )
        .order_by(ClassSession.ends_at.asc())
        .all()
    )


def teacher_students_query(teacher_id):
    return (
        User.query.join(Enrollment, Enrollment.student_id == User.id)
        .join(Course, Course.id == Enrollment.course_id)
        .filter(Course.teacher_id == teacher_id, User.role == "student")
        .distinct()
    )


def get_teacher_assigned_courses(teacher_id):
    """Get all courses assigned to a teacher (via TeacherAssignment table)"""
    assignments = TeacherAssignment.query.filter_by(
        teacher_id=teacher_id,
        is_active=True
    ).all()
    
    course_ids = [a.course_id for a in assignments]
    if not course_ids:
        return []
    
    return Course.query.filter(
        Course.id.in_(course_ids),
        Course.is_active == True
    ).order_by(Course.code.asc()).all()


def get_teacher_assigned_sections(teacher_id, course_id):
    """Get sections assigned to a teacher for a specific course"""
    assignments = TeacherAssignment.query.filter_by(
        teacher_id=teacher_id,
        course_id=course_id,
        is_active=True
    ).all()
    
    return [a.section for a in assignments]


def is_teacher_assigned_to_course(teacher_id, course_id, section=None):
    """Check if teacher is assigned to teach a course (optionally specific section)"""
    query = TeacherAssignment.query.filter_by(
        teacher_id=teacher_id,
        course_id=course_id,
        is_active=True
    )
    
    if section:
        query = query.filter_by(section=section)
    
    return query.first() is not None


def build_session_roster(session):
    enrolled_students = []
    enrolled_by_id = {}
    if session.course_id:
        # Build query for enrolled students
        query = (
            User.query.join(Enrollment, Enrollment.student_id == User.id)
            .filter(Enrollment.course_id == session.course_id, User.role == "student")
        )
        
        # Filter by section if session has a section specified
        if session.section:
            query = query.filter(User.section == session.section)
        
        enrolled_students = query.order_by(User.name.asc()).all()
        enrolled_by_id = {student.id: student for student in enrolled_students}

    marked_entries = []
    marked_ids = set()
    marked_rows = (
        db.session.query(SessionAttendance, User)
        .join(User, User.id == SessionAttendance.student_id)
        .filter(SessionAttendance.session_id == session.id)
        .order_by(SessionAttendance.marked_at.desc())
        .all()
    )
    for attendance_row, student in marked_rows:
        marked_ids.add(student.id)
        marked_entries.append(
            {
                "student": student,
                "attendance": attendance_row,
                "enrolled": student.id in enrolled_by_id,
            }
        )

    failed_attempt_groups = {}
    failed_attempt_rows = (
        db.session.query(AttendanceAttempt, User)
        .outerjoin(User, User.id == AttendanceAttempt.student_id)
        .filter(
            AttendanceAttempt.session_id == session.id,
            AttendanceAttempt.success.is_(False),
        )
        .order_by(AttendanceAttempt.created_at.desc())
        .all()
    )
    for attempt, student in failed_attempt_rows:
        student_key = attempt.student_id if attempt.student_id is not None else f"attempt:{attempt.id}"
        if student_key not in failed_attempt_groups:
            failed_attempt_groups[student_key] = {
                "student_id": attempt.student_id,
                "student": student,
                "attempt_count": 0,
                "last_reason": attempt.reason,
                "last_attempt_at": attempt.created_at,
                "reasons": defaultdict(int),
                "enrolled": bool(student and student.id in enrolled_by_id),
            }

        group = failed_attempt_groups[student_key]
        group["attempt_count"] += 1
        group["reasons"][attempt.reason] += 1

    failed_entries = []
    failed_student_ids = set()
    for entry in failed_attempt_groups.values():
        if entry["student_id"] in marked_ids:
            continue
        entry["reason_summary"] = ", ".join(
            f"{reason} ({count})" for reason, count in sorted(entry["reasons"].items())
        )
        failed_entries.append(entry)
        if entry["student_id"] is not None:
            failed_student_ids.add(entry["student_id"])

    failed_entries.sort(
        key=lambda item: item["last_attempt_at"] or datetime.min.replace(tzinfo=timezone.utc),
        reverse=True,
    )

    pending_entries = []
    for student in enrolled_students:
        if student.id in marked_ids or student.id in failed_student_ids:
            continue
        pending_entries.append({"student": student})

    return {
        "marked_entries": marked_entries,
        "failed_entries": failed_entries,
        "pending_entries": pending_entries,
        "counts": {
            "enrolled": len(enrolled_students),
            "marked": len(marked_entries),
            "failed": len(failed_entries),
            "pending": len(pending_entries),
        },
    }


def ensure_schema_compatibility():
    try:
        db.create_all()
    except Exception as e:
        # Ignore errors if tables/indexes already exist
        app.logger.warning(f"db.create_all() warning (safe to ignore): {e}")

    def _columns(conn, table_name):
        inspector = inspect(conn)
        return {column["name"] for column in inspector.get_columns(table_name)}

    with db.engine.begin() as conn:
        # ClassSession table updates
        class_session_columns = _columns(conn, "class_sessions")
        if "course_id" not in class_session_columns:
            conn.execute(text("ALTER TABLE class_sessions ADD COLUMN course_id INTEGER"))
        if "section" not in class_session_columns:
            conn.execute(text("ALTER TABLE class_sessions ADD COLUMN section VARCHAR(10)"))
        if "location_lat" not in class_session_columns:
            conn.execute(text("ALTER TABLE class_sessions ADD COLUMN location_lat FLOAT"))
        if "location_lng" not in class_session_columns:
            conn.execute(text("ALTER TABLE class_sessions ADD COLUMN location_lng FLOAT"))
        if "location_radius_meters" not in class_session_columns:
            conn.execute(text("ALTER TABLE class_sessions ADD COLUMN location_radius_meters INTEGER DEFAULT 50"))
        if "updated_at" not in class_session_columns:
            conn.execute(text("ALTER TABLE class_sessions ADD COLUMN updated_at DATETIME"))

        # SessionAttendance table updates
        session_attendance_columns = _columns(conn, "session_attendance")
        if "device_hash" not in session_attendance_columns:
            conn.execute(text("ALTER TABLE session_attendance ADD COLUMN device_hash VARCHAR(128)"))
        if "ip_address" not in session_attendance_columns:
            conn.execute(text("ALTER TABLE session_attendance ADD COLUMN ip_address VARCHAR(64)"))
        if "user_agent" not in session_attendance_columns:
            conn.execute(text("ALTER TABLE session_attendance ADD COLUMN user_agent VARCHAR(255)"))
        if "is_late" not in session_attendance_columns:
            conn.execute(text("ALTER TABLE session_attendance ADD COLUMN is_late BOOLEAN DEFAULT 0"))
        if "is_locked" not in session_attendance_columns:
            conn.execute(text("ALTER TABLE session_attendance ADD COLUMN is_locked BOOLEAN DEFAULT 0"))
        
        # Users table updates
        users_columns = _columns(conn, "users")
        if "phone" not in users_columns:
            conn.execute(text("ALTER TABLE users ADD COLUMN phone VARCHAR(15)"))
        if "assignment_status" not in users_columns:
            conn.execute(text("ALTER TABLE users ADD COLUMN assignment_status VARCHAR(20) DEFAULT 'pending'"))
        if "college_id" not in users_columns:
            conn.execute(text("ALTER TABLE users ADD COLUMN college_id VARCHAR(50)"))
        if "section" not in users_columns:
            conn.execute(text("ALTER TABLE users ADD COLUMN section VARCHAR(10)"))
        if "year" not in users_columns:
            conn.execute(text("ALTER TABLE users ADD COLUMN year VARCHAR(10)"))
        if "semester" not in users_columns:
            conn.execute(text("ALTER TABLE users ADD COLUMN semester VARCHAR(10)"))
        if "updated_at" not in users_columns:
            conn.execute(text("ALTER TABLE users ADD COLUMN updated_at DATETIME"))
        if "is_active" not in users_columns:
            conn.execute(text("ALTER TABLE users ADD COLUMN is_active BOOLEAN DEFAULT 1"))
        if "last_login" not in users_columns:
            conn.execute(text("ALTER TABLE users ADD COLUMN last_login DATETIME"))

        # Attendance table updates
        attendance_columns = _columns(conn, "attendance")
        if "created_at" not in attendance_columns:
            conn.execute(text("ALTER TABLE attendance ADD COLUMN created_at DATETIME"))

        # Course table updates
        course_columns = _columns(conn, "courses")
        if "updated_at" not in course_columns:
            conn.execute(text("ALTER TABLE courses ADD COLUMN updated_at DATETIME"))
        if "is_active" not in course_columns:
            conn.execute(text("ALTER TABLE courses ADD COLUMN is_active BOOLEAN DEFAULT 1"))
        if "department" not in course_columns:
            conn.execute(text("ALTER TABLE courses ADD COLUMN department VARCHAR(100) DEFAULT 'General'"))
        if "academic_year" not in course_columns:
            conn.execute(text("ALTER TABLE courses ADD COLUMN academic_year VARCHAR(20) DEFAULT '2025-26'"))
        if "semester" not in course_columns:
            conn.execute(text("ALTER TABLE courses ADD COLUMN semester VARCHAR(10) DEFAULT '1'"))
        if "credits" not in course_columns:
            conn.execute(text("ALTER TABLE courses ADD COLUMN credits INTEGER DEFAULT 3"))
        if "created_by_admin_id" not in course_columns:
            conn.execute(text("ALTER TABLE courses ADD COLUMN created_by_admin_id INTEGER"))

        # Enrollment table updates
        enrollment_columns = _columns(conn, "enrollments")
        if "is_active" not in enrollment_columns:
            conn.execute(text("ALTER TABLE enrollments ADD COLUMN is_active BOOLEAN DEFAULT 1"))
@app.after_request
def add_header(response):
    """Add security headers and cache control to all responses."""
    # Prevent caching of sensitive content (override for static assets if needed)
    response.headers['Cache-Control'] = 'no-store, no-cache, must-revalidate, post-check=0, pre-check=0, max-age=0'
    response.headers['Pragma'] = 'no-cache'
    response.headers['Expires'] = '-1'
    
    # Security headers
    response.headers['X-Content-Type-Options'] = 'nosniff'  # Prevent MIME type sniffing
    response.headers['X-Frame-Options'] = 'SAMEORIGIN'  # Prevent clickjacking
    response.headers['X-XSS-Protection'] = '1; mode=block'  # Enable XSS protection
    response.headers['Referrer-Policy'] = 'strict-origin-when-cross-origin'  # Control referrer info
    response.headers['Permissions-Policy'] = 'geolocation=(self), microphone=(), camera=(self)'  # Feature permissions
    
    # Strict Transport Security (only in production)
    if app.config.get('FLASK_ENV') == 'production':
        response.headers['Strict-Transport-Security'] = 'max-age=31536000; includeSubDomains'
    
    return response


@app.before_request
def auto_close_expired_sessions():
    """Silently close any ClassSession whose ends_at has passed but is still marked active."""
    try:
        now = now_utc_naive()
        expired = ClassSession.query.filter(
            ClassSession.is_active.is_(True),
            ClassSession.ends_at < now,
        ).all()
        if expired:
            for s in expired:
                s.is_active = False
            db.session.commit()
    except Exception:
        db.session.rollback()

@app.context_processor
def inject_geo_vars():
    return {
        "APP_INVERTIS_LAT": app.config.get("INVERTIS_LAT"),
        "APP_INVERTIS_LNG": app.config.get("INVERTIS_LNG"),
        "APP_ALLOWED_RADIUS": app.config.get("ALLOWED_RADIUS_METERS"),
        "APP_SESSION_RADIUS": app.config.get("SESSION_LOCATION_RADIUS_METERS"),
        "APP_GEOFENCE_ENFORCED": app.config.get("GEOFENCE_ENFORCED", True),
    }

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/privacy-policy")
def privacy_policy():
    return render_template("privacy_policy.html")

@app.route("/terms-and-conditions")
def terms():
    return render_template("terms_and_conditions.html")

@app.route("/about-us")
def about():
    return render_template("about_us.html")


# ── Live Classroom Kiosk Mode ─────────────────────────────────────────────────

@app.route("/kiosk/<int:session_id>")
@login_required
def kiosk(session_id):
    """Renders the fullscreen auto-scan kiosk for a teacher's active session."""
    if current_user.role not in ("teacher", "admin"):
        flash("Only teachers can access the Kiosk scanner.", "danger")
        return redirect(url_for("dashboard"))
    session = ClassSession.query.filter_by(id=session_id, teacher_id=current_user.id).first_or_404()
    return render_template("kiosk.html", session=session)


@app.route("/api/kiosk_data/<int:session_id>")
@login_required
def kiosk_data(session_id):
    """Returns kiosk roster data without exposing stored biometric templates to the browser."""
    if current_user.role not in ("teacher", "admin"):
        return jsonify({"success": False, "message": "Unauthorized"}), 403

    session = ClassSession.query.filter_by(id=session_id, teacher_id=current_user.id).first_or_404()

    enrolled_students = (
        User.query.join(Enrollment, Enrollment.student_id == User.id)
        .filter(
            Enrollment.course_id == session.course_id,
            User.role == "student",
        )
        .order_by(User.name.asc())
        .all()
    )

    marked_ids = {
        row.student_id
        for row in SessionAttendance.query.filter_by(session_id=session_id).all()
    }

    students_data = []
    for student in enrolled_students:
        students_data.append({
            "id": student.id,
            "name": student.name,
            "college_id": student.college_id or "",
            "already_marked": student.id in marked_ids,
            "face_ready": bool(student.face_registered and student.face_encoding),
        })

    now = now_utc_naive()
    is_active = bool(session.is_active and session.starts_at <= now <= session.ends_at)

    return jsonify({
        "success": True,
        "session": {
            "id": session.id,
            "title": session.title,
            "course_code": session.course_code,
            "room": session.room,
            "is_active": is_active,
        },
        "students": students_data,
    })


@app.route("/api/kiosk_mark", methods=["POST"])
@login_required
@limiter.limit("120 per minute")
def kiosk_mark():
    """Marks a student present via the kiosk after server-side face verification."""
    if current_user.role not in ("teacher", "admin"):
        return jsonify({"success": False, "message": "Unauthorized"}), 403

    data = request.json or {}
    session_id = data.get("session_id")
    student_id = data.get("student_id")
    descriptor = data.get("descriptor")

    if not session_id or not student_id:
        return jsonify({"success": False, "message": "Missing session or student ID."}), 400

    session = ClassSession.query.filter_by(id=session_id, teacher_id=current_user.id).first()
    if not session:
        return jsonify({"success": False, "message": "Session not found."}), 404

    now = now_utc_naive()
    if not (session.is_active and session.starts_at <= now <= session.ends_at):
        return jsonify({"success": False, "message": "Session is no longer active."}), 400

    student = User.query.filter_by(id=student_id, role="student").first()
    if not student:
        return jsonify({"success": False, "message": "Student not found."}), 404

    enrollment = Enrollment.query.filter_by(course_id=session.course_id, student_id=student.id).first()
    if not enrollment:
        return jsonify({"success": False, "message": "Student is not enrolled for this course."}), 403

    if not student.face_registered or not student.face_encoding:
        return jsonify({"success": False, "message": "Student has not completed face registration."}), 400

    # Prevent duplicate marking
    already_marked = SessionAttendance.query.filter_by(session_id=session_id, student_id=student_id).first()
    if already_marked:
        return jsonify({"success": False, "already_marked": True, "message": f"{student.name} already marked."})

    if not isinstance(descriptor, list) or len(descriptor) != 128:
        return jsonify({"success": False, "message": "A valid face scan is required."}), 400

    try:
        normalized_descriptor = [float(v) for v in descriptor]
    except (TypeError, ValueError):
        return jsonify({"success": False, "message": "Face scan contained invalid values."}), 400

    if any(not isfinite(v) for v in normalized_descriptor):
        return jsonify({"success": False, "message": "Face scan contained invalid values."}), 400

    try:
        known_encoding = np.array(json.loads(student.face_encoding), dtype=float)
    except Exception:
        app.logger.exception("Corrupt kiosk face encoding for student_id=%s", student.id)
        return jsonify({"success": False, "message": "Stored face data is unavailable for this student."}), 500

    unknown_encoding = np.array(normalized_descriptor, dtype=float)
    face_distance = float(np.linalg.norm(known_encoding - unknown_encoding))
    
    FACE_THRESHOLD = app.config.get('FACE_RECOGNITION_THRESHOLD', 0.45)
    
    if face_distance >= FACE_THRESHOLD:
        return jsonify({"success": False, "message": "Face verification failed for the selected student."}), 400

    ip_address = (request.headers.get("X-Forwarded-For", request.remote_addr) or "").split(",")[0].strip()[:64]

    entry = SessionAttendance(
        session_id=session.id,
        student_id=student_id,
        latitude=session.location_lat,
        longitude=session.location_lng,
        face_distance=face_distance,
        ip_address=ip_address,
        user_agent="Kiosk-AssistedVerify/2.0",
    )
    db.session.add(entry)

    # Also update the daily attendance record
    local_now = now_local()
    today_date = local_now.date()
    daily_exists = Attendance.query.filter_by(user_id=student_id, date=today_date).first()
    if not daily_exists:
        daily_entry = Attendance(
            user_id=student_id,
            date=today_date,
            time=local_now.time().replace(microsecond=0),
            latitude=session.location_lat,
            longitude=session.location_lng,
        )
        db.session.add(daily_entry)

    record_attempt(
        session.id, student_id, True, "Kiosk assisted verification",
        session.location_lat, session.location_lng, face_distance,
        None, ip_address, "Kiosk-AssistedVerify/2.0"
    )
    db.session.commit()

    # Non-blocking email notification
    threading.Thread(
        target=send_attendance_email,
        args=(app, student.name, student.email, session.course_code, session.title, datetime.now(timezone.utc)),
        daemon=True,
    ).start()

    return jsonify({"success": True, "message": f"✅ {student.name} marked present!", "student_name": student.name})

# ─────────────────────────────────────────────────────────────────────────────

@app.route("/register", methods=["GET", "POST"])
@limiter.limit("20 per hour")
def register():
    """Register a new user account with face recognition setup."""
    if request.method == "POST":
        name = request.form.get("name", "").strip()
        email = request.form.get("email", "").strip().lower()
        phone = request.form.get("phone", "").strip()
        department = request.form.get("department", "").strip()
        college_id = request.form.get("college_id", "").strip()
        year = request.form.get("year", "").strip()
        semester = request.form.get("semester", "").strip()
        password = request.form.get("password", "")
        requested_role = request.form.get("role", "student").strip().lower()
        role = "student"
        consent = request.form.get("consent") == "yes"

        # Validate name
        if not name or len(name) < 2 or len(name) > 100:
            flash("Name must be between 2 and 100 characters.", "warning")
            return redirect(url_for("register"))
        
        # Validate email format (basic check)
        if not email or "@" not in email or "." not in email:
            flash("Please enter a valid email address.", "warning")
            return redirect(url_for("register"))
        
        # Validate phone number
        if not phone or not phone.isdigit() or len(phone) != 10:
            flash("Please enter a valid 10-digit phone number.", "warning")
            return redirect(url_for("register"))
        
        # Validate department
        if not department or len(department) < 2:
            flash("Department is required.", "warning")
            return redirect(url_for("register"))
        
        # Public registration is student-only.
        if requested_role not in ["", "student"]:
            flash("Teacher and admin accounts are provisioned by administrators only.", "warning")
            return redirect(url_for("register"))
        
        # Validate consent
        if not consent:
            flash("You must accept biometric and privacy consent to continue.", "warning")
            return redirect(url_for("register"))
        
        password_error = password_validation_error(password)
        if password_error:
            flash(password_error, "warning")
            return redirect(url_for("register"))
        
        # Check for existing email
        if User.query.filter_by(email=email).first():
            flash("Email already registered.", "danger")
            return redirect(url_for("register"))
        
        # Check for existing phone
        if User.query.filter_by(phone=phone).first():
            flash("Phone number already registered.", "danger")
            return redirect(url_for("register"))
        
        # Validate student-specific fields (section NOT required during registration)
        if role == "student" and not (college_id and year and semester):
            flash("Students must provide College ID, Year, and Semester.", "warning")
            return redirect(url_for("register"))

        # Create new user (section will be assigned by admin later)
        try:
            new_user = User(
                name=name,
                email=email,
                phone=phone,
                department=department,
                college_id=college_id if role == "student" else None,
                section=None,  # Section assigned by admin, not during registration
                year=year if role == "student" else None,
                semester=semester if role == "student" else None,
                assignment_status='pending',  # Pending section assignment
                role=role,
                password_hash=generate_password_hash(password, method="scrypt"),
            )
            db.session.add(new_user)
            db.session.commit()
            app.logger.info("New user registered: email=%s, phone=%s, role=%s", email, phone, role)
        except Exception as e:
            db.session.rollback()
            app.logger.error("Registration error: %s", str(e))
            flash("Registration failed. Please try again.", "danger")
            return redirect(url_for("register"))

        login_user(new_user)
        flash("Registration successful! Please register your face to continue.", "success")
        return redirect(url_for("register_face"))

    return render_template("register.html")


@app.route("/register_face")
@login_required
def register_face():
    return render_template("register_face.html")


@app.route("/save_face", methods=["POST"])
@login_required
@limiter.limit("30 per hour")
def save_face():
    """
    Save a user's facial encoding (128-dimensional vector).
    
    This function:
    1. Validates the face descriptor format and values
    2. Checks for duplicate faces across all users (prevents multi-account abuse)
    3. Stores the face encoding in the database
    
    Returns:
        - 200 with success if face saved
        - 400 if validation fails
        - 409 if duplicate face detected
        - 500 if database save fails
    """
    # This function saves user's face encoding after registration
    # Face data is stored as a 128-dimension vector
    # It also checks for duplicate faces across ALL users (any role)
    data = request.json or {}
    descriptor = data.get("descriptor")

    if not descriptor:
        return jsonify({"success": False, "message": "No face data received"})
    if not isinstance(descriptor, list):
        return jsonify({"success": False, "message": "Invalid face data format."}), 400
    if len(descriptor) != 128:
        return jsonify({"success": False, "message": "Invalid face data size. Please scan again."}), 400

    try:
        normalized_descriptor = [float(v) for v in descriptor]
    except (TypeError, ValueError):
        return jsonify({"success": False, "message": "Face data contains invalid values."}), 400

    if any(not isfinite(v) for v in normalized_descriptor):
        return jsonify({"success": False, "message": "Face data contains invalid values."}), 400

    # ── Duplicate face check across ALL existing users (vectorized) ──────────────
    # Batch-compare new face against all registered faces using numpy,
    # preventing one person creating multiple accounts (student/teacher).
    new_vec = np.array(normalized_descriptor)
    FACE_DUPLICATE_THRESHOLD = app.config.get('FACE_DUPLICATE_THRESHOLD', 0.50)
    existing_users = User.query.filter(
        User.face_registered.is_(True),
        User.face_encoding.isnot(None),
        User.id != current_user.id,
    ).all()

    if existing_users:
        try:
            all_encodings = []
            valid_users = []
            for u in existing_users:
                try:
                    enc = json.loads(u.face_encoding)
                    if isinstance(enc, list) and len(enc) == 128:
                        all_encodings.append(enc)
                        valid_users.append(u)
                except Exception:
                    continue  # skip corrupted encodings

            if all_encodings:
                enc_matrix = np.array(all_encodings)           # shape (N, 128)
                distances = np.linalg.norm(enc_matrix - new_vec, axis=1)  # shape (N,)
                min_idx = int(np.argmin(distances))
                if distances[min_idx] < FACE_DUPLICATE_THRESHOLD:
                    match_user = valid_users[min_idx]
                    app.logger.warning(
                        "Duplicate face attempt: user_id=%s vs existing user_id=%s (distance=%.4f)",
                        current_user.id, match_user.id, distances[min_idx],
                    )
                    role_label = match_user.role.capitalize()
                    return jsonify({
                        "success": False,
                        "message": (
                            f"⚠ This face is already registered to another {role_label} account. "
                            "Each person can only have one account across all roles."
                        ),
                    }), 409
        except Exception:
            app.logger.exception("Face duplicate vectorized check failed for user_id=%s", current_user.id)
    # ──────────────────────────────────────────────────────────────────────────────

    try:
        current_user.face_encoding = json.dumps(normalized_descriptor)
        current_user.face_registered = True
        db.session.commit()
    except Exception:
        db.session.rollback()
        app.logger.exception("Failed saving face descriptor for user_id=%s", current_user.id)
        return jsonify({"success": False, "message": "Unable to save face data right now. Please try again."}), 500

    return jsonify({"success": True})


@app.route("/mark_attendance", methods=["GET", "POST"])
@login_required
@limiter.limit("20 per minute")
def mark_attendance():
    """
    Mark daily attendance with face verification and location check.
    
    For Students:
    - Shows list of active class sessions
    
    For Teachers:
    - Accepts POST requests with face descriptor and location
    - Verifies user's face against stored encoding
    - Validates user is within campus bounds
    - Prevents duplicate attendance marking
    - Sends email notification on success
    """
    if not current_user.face_registered:
        flash("Please register your face first!", "warning")
        return redirect(url_for("register_face"))

    if current_user.role == "student":
        active_sessions = student_active_sessions(current_user.id)
        return render_template("student_mark_attendance.html", active_sessions=active_sessions)

    if request.method == "POST":
        data = request.json or {}
        descriptor = data.get("descriptor")
        lat = data.get("lat")
        lng = data.get("lng")

        if not is_within_invertis(lat, lng):
            return jsonify({"success": False, "message": f"Attendance can only be marked within the {app.config['APP_GEOFENCE_LABEL']}!"}), 400

        today = today_local_date()
        existing = Attendance.query.filter_by(user_id=current_user.id, date=today).first()
        if existing:
            return jsonify({"success": False, "message": "Attendance already marked for today!"}), 400

        if not descriptor:
            return jsonify({"success": False, "message": "No face detected!"}), 400

        known_encoding = np.array(json.loads(current_user.face_encoding))
        unknown_encoding = np.array(descriptor)
        distance = float(np.linalg.norm(known_encoding - unknown_encoding))

        FACE_THRESHOLD = app.config.get('FACE_RECOGNITION_THRESHOLD', 0.45)
        
        if distance < FACE_THRESHOLD:
            local_now = now_local()
            new_attendance = Attendance(
                user_id=current_user.id,
                date=local_now.date(),
                time=local_now.time().replace(microsecond=0),
                latitude=lat,
                longitude=lng,
            )
            db.session.add(new_attendance)
            db.session.commit()
            # ── Email Notification (background thread – non-blocking) ───────────
            threading.Thread(
                target=send_attendance_email,
                args=(app, current_user.name, current_user.email, "General", "Daily Attendance", datetime.now(timezone.utc)),
                daemon=True,
            ).start()
            # ────────────────────────────────────────────────────────────────────
            return jsonify({"success": True, "message": "Attendance marked successfully!"})

        return jsonify({"success": False, "message": "Face verification failed!"}), 400

    return render_template("mark_attendance.html")



# ══════════════════════════════════════════════════════════════════════════════
# DEPRECATED TEACHER ROUTES (Removed - Admin handles these now)
# ══════════════════════════════════════════════════════════════════════════════
# The following routes have been removed as part of RBAC improvements:
# - /teacher/courses/create (POST) - Only admins can create courses now
# - /teacher/courses/<id>/enroll (POST) - Only admins can enroll students
# - /teacher/courses/<id>/unenroll/<student_id> (POST) - Only admins can unenroll
# - /teacher/courses/<id>/delete (POST) - Only admins can delete courses
#
# Teachers now work with ASSIGNED courses via TeacherAssignment table
# ══════════════════════════════════════════════════════════════════════════════


@app.route("/teacher/sessions/create", methods=["POST"])
@login_required
def create_session():
    if current_user.role != "teacher":
        flash("Only teachers can create class sessions.", "danger")
        return redirect(url_for("dashboard"))

    course_id_raw = request.form.get("course_id", "").strip()
    section = request.form.get("section", "").strip().upper()
    room = request.form.get("room", "").strip()
    duration_raw = request.form.get("duration", "15").strip()
    teacher_lat_raw = request.form.get("teacher_lat", "").strip()
    teacher_lng_raw = request.form.get("teacher_lng", "").strip()

    try:
        course_id = int(course_id_raw)
    except ValueError:
        flash("Invalid course selected.", "warning")
        return redirect(url_for("dashboard"))

    # CHECK: Is teacher assigned to this course and section?
    if not is_teacher_assigned_to_course(current_user.id, course_id, section):
        flash("You are not assigned to teach this course section.", "danger")
        return redirect(url_for("dashboard"))

    course = Course.query.filter_by(id=course_id, is_active=True).first()
    if not course:
        flash("Course not found.", "warning")
        return redirect(url_for("dashboard"))

    if not room:
        flash("Room/Lab is required.", "warning")
        return redirect(url_for("dashboard"))

    teacher_lat, teacher_lng = _parse_coordinates(teacher_lat_raw, teacher_lng_raw)
    if teacher_lat is None or teacher_lng is None:
        flash("Location access is required. Go to the classroom and allow location before starting a session.", "warning")
        return redirect(url_for("dashboard"))

    if not is_within_invertis(teacher_lat, teacher_lng):
        flash(f"Go to the classroom inside the {app.config['APP_GEOFENCE_LABEL']} before starting a live session.", "warning")
        return redirect(url_for("dashboard"))

    try:
        duration = int(duration_raw)
    except ValueError:
        duration = 15

    duration = max(5, min(duration, 120))
    starts_at = now_utc_naive()
    ends_at = starts_at + timedelta(minutes=duration)

    new_session = ClassSession(
        title=course.title,
        course_code=course.code,
        room=room,
        course_id=course.id,
        section=section,  # Store section with session
        starts_at=starts_at,
        ends_at=ends_at,
        teacher_id=current_user.id,
        is_active=True,
        location_lat=teacher_lat,
        location_lng=teacher_lng,
        location_radius_meters=app.config["SESSION_LOCATION_RADIUS_METERS"],
    )
    db.session.add(new_session)
    db.session.commit()
    flash(
        f"Class session created. Students must be within {app.config['SESSION_LOCATION_RADIUS_METERS']} meters of the classroom to mark attendance.",
        "success",
    )
    return redirect(url_for("dashboard"))


@app.route("/teacher/sessions/<int:session_id>/close", methods=["POST"])
@login_required
def close_session(session_id):
    if current_user.role != "teacher":
        flash("Only teachers can close class sessions.", "danger")
        return redirect(url_for("dashboard"))

    session = ClassSession.query.filter_by(id=session_id, teacher_id=current_user.id).first_or_404()
    session.is_active = False
    session.ends_at = now_utc_naive()
    db.session.commit()
    flash("Class session closed.", "info")
    return redirect(url_for("dashboard"))


# ══════════════════════════════════════════════════════════════════════════════
# TIMETABLE MANAGEMENT ROUTES
# ══════════════════════════════════════════════════════════════════════════════

@app.route("/teacher/timetable")
@login_required
def teacher_timetable():
    """View teacher's weekly timetable"""
    if current_user.role != "teacher":
        flash("Only teachers can access timetable.", "danger")
        return redirect(url_for("dashboard"))
    
    # Get teacher's timetable entries
    from models import Timetable
    timetable_entries = Timetable.query.filter_by(
        teacher_id=current_user.id,
        is_active=True
    ).order_by(Timetable.day_of_week.asc(), Timetable.start_time.asc()).all()
    
    # Get assigned courses for dropdown
    teacher_assignments = TeacherAssignment.query.filter_by(
        teacher_id=current_user.id,
        is_active=True
    ).all()
    
    return render_template(
        "teacher_timetable.html",
        timetable_entries=timetable_entries,
        teacher_assignments=teacher_assignments
    )


@app.route("/teacher/timetable/create", methods=["POST"])
@login_required
def teacher_create_timetable():
    """Create a new timetable entry"""
    if current_user.role != "teacher":
        flash("Only teachers can create timetable entries.", "danger")
        return redirect(url_for("dashboard"))
    
    from models import Timetable
    
    course_id = request.form.get("course_id")
    section = request.form.get("section", "").strip().upper()
    day_of_week = request.form.get("day_of_week")
    start_time_str = request.form.get("start_time")
    end_time_str = request.form.get("end_time")
    room = request.form.get("room", "").strip()
    class_type = request.form.get("class_type", "Lecture").strip()
    
    # Validation
    if not all([course_id, section, day_of_week, start_time_str, end_time_str, room]):
        flash("All fields are required.", "warning")
        return redirect(url_for("teacher_timetable"))
    
    try:
        course_id = int(course_id)
        day_of_week = int(day_of_week)
    except ValueError:
        flash("Invalid course or day selection.", "warning")
        return redirect(url_for("teacher_timetable"))
    
    # Check if teacher is assigned to this course+section
    if not is_teacher_assigned_to_course(current_user.id, course_id, section):
        flash("You are not assigned to teach this course section.", "danger")
        return redirect(url_for("teacher_timetable"))
    
    # Parse time
    try:
        from datetime import datetime
        start_time = datetime.strptime(start_time_str, "%H:%M").time()
        end_time = datetime.strptime(end_time_str, "%H:%M").time()
    except ValueError:
        flash("Invalid time format. Use HH:MM format.", "warning")
        return redirect(url_for("teacher_timetable"))
    
    # Validate time range
    if end_time <= start_time:
        flash("End time must be after start time.", "warning")
        return redirect(url_for("teacher_timetable"))
    
    # Check for conflicts
    existing = Timetable.query.filter_by(
        course_id=course_id,
        section=section,
        day_of_week=day_of_week,
        start_time=start_time,
        is_active=True
    ).first()
    
    if existing:
        flash("A timetable entry already exists for this slot.", "warning")
        return redirect(url_for("teacher_timetable"))
    
    # Create timetable entry
    try:
        timetable_entry = Timetable(
            course_id=course_id,
            teacher_id=current_user.id,
            section=section,
            day_of_week=day_of_week,
            start_time=start_time,
            end_time=end_time,
            room=room,
            class_type=class_type
        )
        db.session.add(timetable_entry)
        db.session.commit()
        
        course = Course.query.get(course_id)
        flash(f"✅ Timetable entry created: {course.code} - Section {section} on {timetable_entry.get_day_name()} at {start_time_str}", "success")
        
    except Exception as e:
        db.session.rollback()
        app.logger.error(f"Error creating timetable: {str(e)}")
        flash("Failed to create timetable entry. Please try again.", "danger")
    
    return redirect(url_for("teacher_timetable"))


@app.route("/teacher/timetable/<int:timetable_id>/delete", methods=["POST"])
@login_required
def teacher_delete_timetable(timetable_id):
    """Delete a timetable entry"""
    if current_user.role != "teacher":
        flash("Only teachers can delete timetable entries.", "danger")
        return redirect(url_for("dashboard"))
    
    from models import Timetable
    
    timetable_entry = Timetable.query.filter_by(
        id=timetable_id,
        teacher_id=current_user.id
    ).first_or_404()
    
    try:
        timetable_entry.is_active = False
        db.session.commit()
        flash("Timetable entry deleted.", "info")
    except Exception as e:
        db.session.rollback()
        app.logger.error(f"Error deleting timetable: {str(e)}")
        flash("Failed to delete timetable entry.", "danger")
    
    return redirect(url_for("teacher_timetable"))


@app.route("/teacher/sessions/<int:session_id>/roster")
@login_required
def teacher_session_roster(session_id):
    if current_user.role != "teacher":
        flash("Only teachers can view session rosters.", "danger")
        return redirect(url_for("dashboard"))

    session = ClassSession.query.filter_by(id=session_id, teacher_id=current_user.id).first_or_404()
    roster = build_session_roster(session)
    is_live = bool(session.is_active and session.ends_at >= now_utc_naive())
    return render_template(
        "teacher_session_roster.html",
        session=session,
        roster=roster,
        is_live=is_live,
    )


@app.route("/teacher/sessions/<int:session_id>/lock_attendance", methods=["POST"])
@login_required
def teacher_lock_attendance(session_id):
    """Lock attendance for a session to prevent further changes"""
    if current_user.role != "teacher":
        flash("Only teachers can lock attendance.", "danger")
        return redirect(url_for("dashboard"))
    
    session = ClassSession.query.filter_by(id=session_id, teacher_id=current_user.id).first_or_404()
    
    # Lock all attendance records for this session
    attendance_records = SessionAttendance.query.filter_by(session_id=session_id).all()
    
    for record in attendance_records:
        record.is_locked = True
    
    try:
        db.session.commit()
        flash(f"✅ Attendance locked for {session.course_code}. No further changes allowed.", "success")
    except Exception as e:
        db.session.rollback()
        app.logger.error(f"Error locking attendance: {str(e)}")
        flash("Failed to lock attendance.", "danger")
    
    return redirect(url_for("teacher_session_roster", session_id=session_id))


@app.route("/teacher/sessions/<int:session_id>/unlock_attendance", methods=["POST"])
@login_required
def teacher_unlock_attendance(session_id):
    """Unlock attendance for a session to allow changes"""
    if current_user.role != "teacher":
        flash("Only teachers can unlock attendance.", "danger")
        return redirect(url_for("dashboard"))
    
    session = ClassSession.query.filter_by(id=session_id, teacher_id=current_user.id).first_or_404()
    
    # Unlock all attendance records for this session
    attendance_records = SessionAttendance.query.filter_by(session_id=session_id).all()
    
    for record in attendance_records:
        record.is_locked = False
    
    try:
        db.session.commit()
        flash(f"✅ Attendance unlocked for {session.course_code}. Changes are now allowed.", "info")
    except Exception as e:
        db.session.rollback()
        app.logger.error(f"Error unlocking attendance: {str(e)}")
        flash("Failed to unlock attendance.", "danger")
    
    return redirect(url_for("teacher_session_roster", session_id=session_id))


@app.route("/api/active_sessions")
@login_required
def active_sessions():
    if current_user.role != "student":
        return jsonify({"sessions": []})

    sessions = student_active_sessions(current_user.id)
    return jsonify(
        {
            "sessions": [
                {
                    "id": s.id,
                    "title": s.title,
                    "course_code": s.course_code,
                    "room": s.room,
                    "ends_at": local_datetime_filter(s.ends_at).strftime("%Y-%m-%d %I:%M %p"),
                }
                for s in sessions
            ]
        }
    )


@app.route("/api/session_attendance/mark", methods=["POST"])
@login_required
@limiter.limit("10 per minute")
def mark_session_attendance():
    """
    Mark attendance for a live class session via API endpoint.
    
    This endpoint:
    1. Validates student enrollment in course
    2. Checks session is currently active
    3. Verifies student is within classroom geofence
    4. Performs face recognition verification
    5. Records attendance attempt and real face mismatch
    6. Sends email notification on success
    7. Logs device/IP information for security auditing
    
    Request JSON Parameters:
        - session_id: ID of the class session
        - descriptor: 128-dim face vector from face.js
        - lat/lng: Student's current coordinates
        - device_id: Browser device identifier (hashed to device_hash)
    
    Returns:
        - 200 with success if attendance marked
        - 400 if validation fails
        - 403 if unauthorized
    """
    if current_user.role != "student":
        return jsonify({"success": False, "message": "Only students can use session attendance."}), 403

    if not current_user.face_registered or not current_user.face_encoding:
        return jsonify({"success": False, "message": "Face registration is required before marking attendance."}), 400

    data = request.json or {}
    session_id = data.get("session_id")
    descriptor = data.get("descriptor")
    lat = data.get("lat")
    lng = data.get("lng")
    device_hash, ip_address, user_agent = get_request_meta(data)

    if not session_id:
        record_attempt(None, current_user.id, False, "Missing session id", lat, lng, None, device_hash, ip_address, user_agent)
        db.session.commit()
        return jsonify({"success": False, "message": "Session is required."}), 400

    try:
        session_id = int(session_id)
    except ValueError:
        record_attempt(None, current_user.id, False, "Invalid session id", lat, lng, None, device_hash, ip_address, user_agent)
        db.session.commit()
        return jsonify({"success": False, "message": "Session id is invalid."}), 400

    session = ClassSession.query.filter_by(id=session_id).first()
    if not session:
        record_attempt(session_id, current_user.id, False, "Session not found", lat, lng, None, device_hash, ip_address, user_agent)
        db.session.commit()
        return jsonify({"success": False, "message": "Session not found."}), 400

    enrolled = Enrollment.query.filter_by(course_id=session.course_id, student_id=current_user.id).first()
    if not enrolled:
        record_attempt(session.id, current_user.id, False, "Student not enrolled", lat, lng, None, device_hash, ip_address, user_agent)
        db.session.commit()
        return jsonify({"success": False, "message": "You are not enrolled for this course."}), 403
    
    # Check if student has section assigned
    if not current_user.section:
        record_attempt(session.id, current_user.id, False, "Section not assigned", lat, lng, None, device_hash, ip_address, user_agent)
        db.session.commit()
        return jsonify({"success": False, "message": "Your section is not assigned yet. Contact admin to assign your section."}), 403
    
    # Check if session has section and if student's section matches
    if session.section and session.section != current_user.section:
        record_attempt(session.id, current_user.id, False, f"Wrong section (student: {current_user.section}, session: {session.section})", lat, lng, None, device_hash, ip_address, user_agent)
        db.session.commit()
        return jsonify({"success": False, "message": f"This session is for Section {session.section}. You are in Section {current_user.section}."}), 403

    now = now_utc_naive()
    if not (session.is_active and session.starts_at <= now <= session.ends_at):
        record_attempt(session.id, current_user.id, False, "Session inactive", lat, lng, None, device_hash, ip_address, user_agent)
        db.session.commit()
        return jsonify({"success": False, "message": "This session is not active now."}), 400

    classroom_status = classroom_geofence_status(session, lat, lng)
    if not classroom_status["ok"]:
        failure_reason = {
            "missing_location": "Student location unavailable",
            "session_location_missing": "Teacher classroom location missing",
            "outside_classroom_radius": "Outside classroom radius",
        }.get(classroom_status["reason"], "Classroom location check failed")
        record_attempt(session.id, current_user.id, False, failure_reason, lat, lng, None, device_hash, ip_address, user_agent)
        db.session.commit()
        if classroom_status["reason"] == "session_location_missing":
            return jsonify({
                "success": False,
                "message": "Teacher classroom location is missing for this session. Ask your teacher to restart the live class from the classroom.",
            }), 400
        return jsonify({
            "success": False,
            "message": classroom_status["message"] or "Go to the classroom to mark attendance.",
        }), 400

    already_marked = SessionAttendance.query.filter_by(session_id=session.id, student_id=current_user.id).first()
    if already_marked:
        record_attempt(session.id, current_user.id, False, "Duplicate mark", lat, lng, already_marked.face_distance, device_hash, ip_address, user_agent)
        db.session.commit()
        return jsonify({"success": False, "message": "Attendance already marked for this class session."}), 400

    if not descriptor:
        record_attempt(session.id, current_user.id, False, "No face descriptor", lat, lng, None, device_hash, ip_address, user_agent)
        db.session.commit()
        return jsonify({"success": False, "message": "No face detected!"}), 400


    known_encoding = np.array(json.loads(current_user.face_encoding))
    unknown_encoding = np.array(descriptor)
    distance = float(np.linalg.norm(known_encoding - unknown_encoding))

    FACE_THRESHOLD = app.config.get('FACE_RECOGNITION_THRESHOLD', 0.45)
    SPOOFING_THRESHOLD = app.config.get('FACE_SPOOFING_THRESHOLD', 0.80)

    # Detect possible spoofing attack (photo/video)
    if distance > SPOOFING_THRESHOLD:
        app.logger.warning(
            "🚨 Possible spoofing attempt detected: user_id=%s, session_id=%s, distance=%.4f",
            current_user.id, session.id, distance
        )
        record_attempt(
            session.id,
            current_user.id,
            False,
            "Possible spoofing attempt (photo attack)",
            lat,
            lng,
            distance,
            device_hash,
            ip_address,
            user_agent
        )
        db.session.commit()
        return jsonify({
            "success": False,
            "message": "⚠ Spoofing attempt detected! Please use live camera."
        }), 400

    # UNKNOWN PERSON ALERT - Face doesn't match registered face
    if distance >= FACE_THRESHOLD:
        record_attempt(
            session.id,
            current_user.id,
            False,
            "Face verification failed - unknown person",
            lat,
            lng,
            distance,
            device_hash,
            ip_address,
            user_agent
        )

        db.session.commit()

        app.logger.warning(
            "⚠ Face verification failed: user_id=%s, session_id=%s, distance=%.4f (threshold=%.2f)",
            current_user.id, session.id, distance, FACE_THRESHOLD
        )

        return jsonify({
            "success": False,
            "message": f"⚠ Face verification failed! Your face doesn't match the registered face. (Distance: {distance:.2f})"
        }), 400


    # FACE VERIFIED → MARK ATTENDANCE
    app.logger.info(
        "✅ Face verified successfully: user_id=%s, session_id=%s, distance=%.4f",
        current_user.id, session.id, distance
    )
    
    # Check if marking is late (>10 min after session start)
    now = now_utc_naive()
    late_threshold = session.starts_at + timedelta(minutes=10)
    is_late = now > late_threshold
    
    entry = SessionAttendance(
        session_id=session.id,
        student_id=current_user.id,
        latitude=lat,
        longitude=lng,
        face_distance=distance,
        device_hash=device_hash,
        ip_address=ip_address,
        user_agent=user_agent,
        is_late=is_late,
    )

    db.session.add(entry)

    # ── Also update the Daily Attendance record ───────────────────────────
    # So "My Daily Attendance Records" on the student dashboard reflects this session.
    local_now = now_local()
    today_date = local_now.date()
    daily_exists = Attendance.query.filter_by(
        user_id=current_user.id,
        date=today_date,
    ).first()
    if not daily_exists:
        daily_entry = Attendance(
            user_id=current_user.id,
            date=today_date,
            time=local_now.time().replace(microsecond=0),
            latitude=lat,
            longitude=lng,
        )
        db.session.add(daily_entry)
    # ─────────────────────────────────────────────────────────────────────

    record_attempt(
        session.id,
        current_user.id,
        True,
        "Attendance marked",
        lat,
        lng,
        distance,
        device_hash,
        ip_address,
        user_agent
    )

    db.session.commit()

    sync_session_attendance(app, entry, session, current_user)

    # ── Email Notification (background thread – non-blocking) ──────────────────
    threading.Thread(
        target=send_attendance_email,
        args=(app, current_user.name, current_user.email, session.course_code, session.title, datetime.now(timezone.utc)),
        daemon=True,
    ).start()
    # ────────────────────────────────────────────────────────────────────────────

    return jsonify({
        "success": True,
        "message": f"Attendance marked for {session.course_code} ({session.title})."
    })


# ══════════════════════════════════════════════════════════════════════════════
# STUDENT FEATURES - Phase 3
# ══════════════════════════════════════════════════════════════════════════════

@app.route("/student/failed_attempts")
@login_required
def student_failed_attempts():
    """Show student why their attendance attempts failed"""
    if current_user.role != "student":
        flash("Students only.", "danger")
        return redirect(url_for("dashboard"))
    
    # Get failed attempts for this student
    failed_attempts = (
        AttendanceAttempt.query.filter_by(
            student_id=current_user.id,
            success=False
        )
        .order_by(AttendanceAttempt.created_at.desc())
        .limit(50)
        .all()
    )
    
    # Group by session
    attempts_by_session = {}
    for attempt in failed_attempts:
        if attempt.session_id not in attempts_by_session:
            session = ClassSession.query.get(attempt.session_id) if attempt.session_id else None
            attempts_by_session[attempt.session_id] = {
                'session': session,
                'attempts': []
            }
        attempts_by_session[attempt.session_id]['attempts'].append(attempt)
    
    return render_template(
        "student_failed_attempts.html",
        attempts_by_session=attempts_by_session,
        total_failed=len(failed_attempts)
    )


@app.route("/api/student/attendance_alert")
@login_required
def student_attendance_alert():
    """Check if student has low attendance and return alert data"""
    if current_user.role != "student":
        return jsonify({"alert": False})
    
    enrolled_courses = (
        Course.query.join(Enrollment, Enrollment.course_id == Course.id)
        .filter(Enrollment.student_id == current_user.id, Enrollment.is_active == True)
        .all()
    )
    
    low_courses = []
    WARNING_THRESHOLD = 75.0
    
    for course in enrolled_courses:
        # Get all sessions for this course
        sessions = ClassSession.query.filter_by(course_id=course.id).all()
        total = len(sessions)
        
        if total == 0:
            continue
        
        # Get attended sessions
        session_ids = [s.id for s in sessions]
        attended = SessionAttendance.query.filter(
            SessionAttendance.student_id == current_user.id,
            SessionAttendance.session_id.in_(session_ids)
        ).count()
        
        percentage = round((attended / total) * 100, 1)
        
        if percentage < WARNING_THRESHOLD:
            low_courses.append({
                "course_code": course.code,
                "course_title": course.title,
                "department": course.department,
                "percentage": percentage,
                "attended": attended,
                "total": total,
                "required": int((WARNING_THRESHOLD / 100) * total) - attended
            })
    
    return jsonify({
        "alert": len(low_courses) > 0,
        "low_courses": low_courses,
        "threshold": WARNING_THRESHOLD
    })


@app.route("/api/student/attendance_stats")
@login_required
def student_attendance_stats():
    """Get detailed attendance statistics for student"""
    if current_user.role != "student":
        return jsonify({"error": "Unauthorized"}), 403
    
    # Overall stats
    enrolled_courses = Enrollment.query.filter_by(
        student_id=current_user.id,
        is_active=True
    ).all()
    
    total_courses = len(enrolled_courses)
    
    # Total sessions across all courses
    course_ids = [e.course_id for e in enrolled_courses]
    total_sessions = ClassSession.query.filter(
        ClassSession.course_id.in_(course_ids),
        ClassSession.starts_at <= now_utc_naive()
    ).count() if course_ids else 0
    
    # Total attended
    total_attended = SessionAttendance.query.filter_by(
        student_id=current_user.id
    ).count()
    
    # Overall percentage
    overall_percentage = round((total_attended / total_sessions * 100), 1) if total_sessions > 0 else 0.0
    
    # Failed attempts count
    failed_attempts = AttendanceAttempt.query.filter_by(
        student_id=current_user.id,
        success=False
    ).count()
    
    # Recent attendance (last 7 days)
    seven_days_ago = now_utc_naive() - timedelta(days=7)
    recent_attended = SessionAttendance.query.filter(
        SessionAttendance.student_id == current_user.id,
        SessionAttendance.marked_at >= seven_days_ago
    ).count()
    
    return jsonify({
        "total_courses": total_courses,
        "total_sessions": total_sessions,
        "total_attended": total_attended,
        "overall_percentage": overall_percentage,
        "failed_attempts": failed_attempts,
        "recent_attended": recent_attended,
        "status": "good" if overall_percentage >= 75 else "warning" if overall_percentage >= 60 else "critical"
    })


# ══════════════════════════════════════════════════════════════════════════════
# END STUDENT FEATURES
# ══════════════════════════════════════════════════════════════════════════════


# ── Student: Reset/Re-enroll Face ─────────────────────────────────────────────
@app.route("/student/reset_face", methods=["POST"])
@login_required
def reset_face():
    """Allows a student to clear their face and re-register."""
    if current_user.role not in ("student", "teacher"):
        flash("Unauthorised.", "danger")
        return redirect(url_for("dashboard"))
    current_user.face_registered = False
    current_user.face_encoding = None
    db.session.commit()
    flash("Face data cleared. Please re-register your face.", "info")
    return redirect(url_for("register_face"))
# ──────────────────────────────────────────────────────────────────────────────


# ── Teacher: Export Attendance CSV ────────────────────────────────────────────
@app.route("/teacher/attendance/export")
@login_required
def export_attendance():
    """Download a CSV of all session attendance for the teacher's courses."""
    if current_user.role != "teacher":
        flash("Only teachers can export attendance.", "danger")
        return redirect(url_for("dashboard"))


    course_id_filter = request.args.get("course_id", type=int)

    # Build base query
    query = (
        db.session.query(
            SessionAttendance,
            ClassSession,
            User,
            Course,
        )
        .join(ClassSession, ClassSession.id == SessionAttendance.session_id)
        .join(User, User.id == SessionAttendance.student_id)
        .join(Course, Course.id == ClassSession.course_id)
        .filter(ClassSession.teacher_id == current_user.id)
    )
    if course_id_filter:
        query = query.filter(Course.id == course_id_filter)

    rows = query.order_by(Course.code, User.name, SessionAttendance.marked_at).all()

    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(["Course Code", "Course Title", "Section", "Student Name",
                     "College ID", "Marked At", "Room", "Face Distance"])
    app_tz = ZoneInfo(app.config["APP_TIMEZONE"])
    for sa, sess, student, course in rows:
        marked = sa.marked_at
        if marked and marked.tzinfo is None:
            marked = marked.replace(tzinfo=timezone.utc)
        local_marked = marked.astimezone(app_tz).strftime("%d %b %Y %I:%M %p") if marked else "-"
        writer.writerow([
            course.code,
            course.title,
            course.section,
            student.name,
            student.college_id or "-",
            local_marked,
            sess.room,
            f"{sa.face_distance:.4f}" if sa.face_distance is not None else "-",
        ])

    output.seek(0)
    filename = f"attendance_export_{today_local_date().isoformat()}.csv"
    return Response(
        output.getvalue(),
        mimetype="text/csv",
        headers={"Content-Disposition": f"attachment; filename={filename}"},
    )
# ──────────────────────────────────────────────────────────────────────────────


# ── Teacher: Per-Course Attendance Report ─────────────────────────────────────
@app.route("/teacher/courses/<int:course_id>/report")
@login_required
def course_attendance_report(course_id):
    """Show per-student attendance % for a specific course."""
    if current_user.role != "teacher":
        flash("Only teachers can view course reports.", "danger")
        return redirect(url_for("dashboard"))

    course = Course.query.get_or_404(course_id)
    
    # CHECK: Is teacher assigned to this course?
    if not is_teacher_assigned_to_course(current_user.id, course_id):
        flash("You are not assigned to teach this course.", "danger")
        return redirect(url_for("dashboard"))

    # All sessions ever held for this course
    all_sessions = ClassSession.query.filter_by(course_id=course.id).all()
    total_sessions = len(all_sessions)
    session_ids = [s.id for s in all_sessions]

    # All enrolled students
    enrollments = (
        User.query.join(Enrollment, Enrollment.student_id == User.id)
        .filter(Enrollment.course_id == course.id)
        .order_by(User.name.asc())
        .all()
    )

    # Per-student attendance count
    report = []
    WARNING_THRESHOLD = 75.0
    for student in enrollments:
        attended = SessionAttendance.query.filter(
            SessionAttendance.student_id == student.id,
            SessionAttendance.session_id.in_(session_ids),
        ).count() if session_ids else 0
        pct = round((attended / total_sessions) * 100, 1) if total_sessions > 0 else 0.0
        report.append({
            "student": student,
            "attended": attended,
            "total": total_sessions,
            "percentage": pct,
            "low": pct < WARNING_THRESHOLD,
        })

    return render_template(
        "course_report.html",
        course=course,
        report=report,
        total_sessions=total_sessions,
        teacher_courses=get_teacher_assigned_courses(current_user.id),
    )
# ──────────────────────────────────────────────────────────────────────────────


# ══════════════════════════════════════════════════════════════════════════════
# ADMIN ROUTES - Course & Enrollment Management
# ══════════════════════════════════════════════════════════════════════════════

@app.route("/admin/courses/create", methods=["POST"])
@login_required
def admin_create_course():
    """Admin creates a new course"""
    if current_user.role != "admin":
        flash("Only admins can create courses.", "danger")
        return redirect(url_for("dashboard"))
    
    code = request.form.get("code", "").strip().upper()
    title = request.form.get("title", "").strip()
    department = request.form.get("department", "").strip()
    academic_year = request.form.get("academic_year", "").strip()
    semester = request.form.get("semester", "").strip()
    credits = request.form.get("credits", "3").strip()
    
    if not all([code, title, department, academic_year, semester]):
        flash("All fields are required.", "warning")
        return redirect(url_for("dashboard"))
    
    try:
        credits = int(credits)
    except ValueError:
        credits = 3
    
    # Check if course already exists
    existing = Course.query.filter_by(
        code=code,
        department=department,
        academic_year=academic_year,
        semester=semester
    ).first()
    
    if existing:
        flash(f"Course {code} already exists for {department} ({academic_year} Sem {semester}).", "warning")
        return redirect(url_for("dashboard"))
    
    course = Course(
        code=code,
        title=title,
        department=department,
        academic_year=academic_year,
        semester=semester,
        credits=credits,
        created_by_admin_id=current_user.id
    )
    db.session.add(course)
    db.session.commit()
    
    flash(f"Course '{code} - {title}' created successfully.", "success")
    return redirect(url_for("dashboard"))


@app.route("/admin/courses/<int:course_id>/delete", methods=["POST"])
@login_required
def admin_delete_course(course_id):
    """Admin deletes a course"""
    if current_user.role != "admin":
        flash("Only admins can delete courses.", "danger")
        return redirect(url_for("dashboard"))
    
    course = Course.query.get_or_404(course_id)
    
    # Check if course has active sessions
    active_sessions = ClassSession.query.filter_by(course_id=course.id, is_active=True).count()
    if active_sessions > 0:
        flash(f"Cannot delete course with {active_sessions} active session(s). Close them first.", "danger")
        return redirect(url_for("dashboard"))
    
    course_name = f"{course.code} - {course.title}"
    db.session.delete(course)
    db.session.commit()
    
    flash(f"Course '{course_name}' deleted successfully.", "info")
    return redirect(url_for("dashboard"))


@app.route("/admin/teachers/assign", methods=["POST"])
@login_required
def admin_assign_teacher():
    """Admin assigns a teacher to a course section"""
    if current_user.role != "admin":
        flash("Only admins can assign teachers.", "danger")
        return redirect(url_for("dashboard"))
    
    teacher_id = request.form.get("teacher_id")
    course_id = request.form.get("course_id")
    section = request.form.get("section", "").strip().upper()
    
    if not all([teacher_id, course_id, section]):
        flash("Teacher, course, and section are required.", "warning")
        return redirect(url_for("dashboard"))
    
    teacher = User.query.filter_by(id=teacher_id, role="teacher").first()
    if not teacher:
        flash("Teacher not found.", "warning")
        return redirect(url_for("dashboard"))
    
    course = Course.query.get(course_id)
    if not course:
        flash("Course not found.", "warning")
        return redirect(url_for("dashboard"))
    
    # Check if already assigned
    existing = TeacherAssignment.query.filter_by(
        teacher_id=teacher_id,
        course_id=course_id,
        section=section
    ).first()
    
    if existing:
        if existing.is_active:
            flash(f"{teacher.name} is already assigned to {course.code} Section {section}.", "info")
        else:
            # Reactivate
            existing.is_active = True
            db.session.commit()
            flash(f"{teacher.name} re-assigned to {course.code} Section {section}.", "success")
        return redirect(url_for("dashboard"))
    
    assignment = TeacherAssignment(
        teacher_id=teacher_id,
        course_id=course_id,
        section=section,
        assigned_by_admin_id=current_user.id
    )
    db.session.add(assignment)
    db.session.commit()
    
    flash(f"{teacher.name} assigned to {course.code} Section {section}.", "success")
    return redirect(url_for("dashboard"))


@app.route("/admin/teachers/<int:assignment_id>/unassign", methods=["POST"])
@login_required
def admin_unassign_teacher(assignment_id):
    """Admin removes a teacher assignment"""
    if current_user.role != "admin":
        flash("Only admins can unassign teachers.", "danger")
        return redirect(url_for("dashboard"))
    
    assignment = TeacherAssignment.query.get_or_404(assignment_id)
    teacher = User.query.get(assignment.teacher_id)
    course = Course.query.get(assignment.course_id)
    
    assignment.is_active = False
    db.session.commit()
    
    flash(f"{teacher.name} unassigned from {course.code} Section {assignment.section}.", "info")
    return redirect(url_for("dashboard"))


@app.route("/admin/students/bulk_enroll", methods=["POST"])
@login_required
@limiter.limit("10 per hour")
def admin_bulk_enroll():
    """
    Admin bulk enrolls students via CSV upload
    
    CSV Format:
    college_id,name,email,department,section,year,semester,course_code
    2021001,Rahul Kumar,rahul@example.com,CSE,A,3,5,CS301
    """
    if current_user.role != "admin":
        flash("Only admins can bulk enroll students.", "danger")
        return redirect(url_for("dashboard"))
    
    if 'file' not in request.files:
        flash("No file uploaded.", "warning")
        return redirect(url_for("dashboard"))
    
    file = request.files['file']
    if file.filename == '':
        flash("No file selected.", "warning")
        return redirect(url_for("dashboard"))
    
    if not file.filename.endswith('.csv'):
        flash("Only CSV files are allowed.", "warning")
        return redirect(url_for("dashboard"))
    
    # Process CSV
    import csv
    import io
    
    try:
        stream = io.StringIO(file.stream.read().decode("UTF8"), newline=None)
        csv_reader = csv.DictReader(stream)
        
        successful = 0
        failed = 0
        errors = []
        total_rows = 0
        
        for row in csv_reader:
            total_rows += 1
            try:
                # Validate required fields
                required_fields = ['college_id', 'name', 'email', 'department', 'section', 'year', 'semester', 'course_code']
                missing = [f for f in required_fields if f not in row or not row[f].strip()]
                if missing:
                    errors.append(f"Row {total_rows}: Missing fields: {', '.join(missing)}")
                    failed += 1
                    continue
                
                email = row['email'].strip().lower()
                college_id = row['college_id'].strip()
                
                # Check if student exists
                student = User.query.filter_by(email=email).first()
                
                if not student:
                    # Create new student with default password = college_id
                    student = User(
                        name=row['name'].strip(),
                        email=email,
                        college_id=college_id,
                        section=row['section'].strip().upper(),
                        year=row['year'].strip(),
                        semester=row['semester'].strip(),
                        department=row['department'].strip(),
                        role='student',
                        password_hash=generate_password_hash(college_id, method="scrypt")
                    )
                    db.session.add(student)
                    db.session.flush()  # Get student.id
                
                # Find course
                course_code = row['course_code'].strip().upper()
                course = Course.query.filter_by(code=course_code, is_active=True).first()
                
                if not course:
                    errors.append(f"Row {total_rows}: Course '{course_code}' not found")
                    failed += 1
                    continue
                
                # Check if already enrolled
                existing = Enrollment.query.filter_by(
                    course_id=course.id,
                    student_id=student.id
                ).first()
                
                if not existing:
                    enrollment = Enrollment(
                        course_id=course.id,
                        student_id=student.id
                    )
                    db.session.add(enrollment)
                
                successful += 1
                
            except Exception as e:
                failed += 1
                errors.append(f"Row {total_rows}: {str(e)}")
                app.logger.error(f"Bulk enrollment error on row {total_rows}: {str(e)}")
                continue
        
        # Save bulk enrollment record
        bulk_record = BulkEnrollment(
            uploaded_by_admin_id=current_user.id,
            filename=file.filename,
            total_rows=total_rows,
            successful=successful,
            failed=failed,
            error_log=json.dumps(errors[:50])  # Store first 50 errors
        )
        db.session.add(bulk_record)
        db.session.commit()
        
        if failed == 0:
            flash(f"✅ Bulk enrollment complete: {successful} students enrolled successfully!", "success")
        else:
            flash(f"⚠️ Bulk enrollment complete: {successful} successful, {failed} failed.", "warning")
            for error in errors[:5]:  # Show first 5 errors
                flash(error, "danger")
        
    except Exception as e:
        db.session.rollback()
        app.logger.exception("Bulk enrollment failed")
        flash(f"Bulk enrollment failed: {str(e)}", "danger")
    
    return redirect(url_for("dashboard"))


@app.route("/admin/students/bulk_assign_sections", methods=["POST"])
@login_required
@limiter.limit("10 per hour")
def admin_bulk_assign_sections():
    """
    Admin bulk assigns sections to students via CSV upload
    
    CSV Format:
    email,section,year,semester
    rahul@example.com,A,2,3
    priya@example.com,A,2,3
    """
    if current_user.role != "admin":
        flash("Only admins can bulk assign sections.", "danger")
        return redirect(url_for("dashboard"))
    
    if 'file' not in request.files:
        flash("No file uploaded.", "warning")
        return redirect(url_for("dashboard"))
    
    file = request.files['file']
    if file.filename == '':
        flash("No file selected.", "warning")
        return redirect(url_for("dashboard"))
    
    if not file.filename.endswith('.csv'):
        flash("Only CSV files are allowed.", "warning")
        return redirect(url_for("dashboard"))
    
    # Process CSV
    try:
        stream = io.StringIO(file.stream.read().decode("UTF8"), newline=None)
        csv_reader = csv.DictReader(stream)
        
        successful = 0
        failed = 0
        errors = []
        total_rows = 0
        
        for row in csv_reader:
            total_rows += 1
            try:
                # Validate required fields
                required_fields = ['email', 'section']
                missing = [f for f in required_fields if f not in row or not row[f].strip()]
                if missing:
                    errors.append(f"Row {total_rows}: Missing fields: {', '.join(missing)}")
                    failed += 1
                    continue
                
                email = row['email'].strip().lower()
                section = row['section'].strip().upper()
                year = row.get('year', '').strip()
                semester = row.get('semester', '').strip()
                
                # Find student
                student = User.query.filter_by(email=email, role='student').first()
                
                if not student:
                    errors.append(f"Row {total_rows}: Student with email '{email}' not found")
                    failed += 1
                    continue
                
                # Update section
                student.section = section
                if year:
                    student.year = year
                if semester:
                    student.semester = semester
                
                # Update assignment status
                if student.assignment_status == 'pending':
                    student.assignment_status = 'assigned'
                
                successful += 1
                
            except Exception as e:
                failed += 1
                errors.append(f"Row {total_rows}: {str(e)}")
                app.logger.error(f"Bulk section assignment error on row {total_rows}: {str(e)}")
                continue
        
        db.session.commit()
        
        if failed == 0:
            flash(f"✅ Bulk section assignment complete: {successful} students assigned successfully!", "success")
        else:
            flash(f"⚠️ Bulk section assignment complete: {successful} successful, {failed} failed.", "warning")
            for error in errors[:5]:  # Show first 5 errors
                flash(error, "danger")
        
    except Exception as e:
        db.session.rollback()
        app.logger.exception("Bulk section assignment failed")
        flash(f"Bulk section assignment failed: {str(e)}", "danger")
    
    return redirect(url_for("dashboard"))


@app.route("/admin/students/enroll", methods=["POST"])
@login_required
def admin_enroll_student():
    """Admin manually enrolls a student in a course section"""
    if current_user.role != "admin":
        flash("Only admins can enroll students.", "danger")
        return redirect(url_for("dashboard"))
    
    student_id = request.form.get("student_id")
    course_id = request.form.get("course_id")
    section = request.form.get("section", "").strip().upper()
    
    if not all([student_id, course_id, section]):
        flash("Student, course, and section are required.", "warning")
        return redirect(url_for("dashboard"))
    
    student = User.query.filter_by(id=student_id, role='student').first()
    if not student:
        flash("Student not found.", "warning")
        return redirect(url_for("dashboard"))
    
    course = Course.query.get(course_id)
    if not course:
        flash("Course not found.", "warning")
        return redirect(url_for("dashboard"))
    
    # Check if teacher is assigned to this course section
    teacher_assigned = TeacherAssignment.query.filter_by(
        course_id=course_id,
        section=section,
        is_active=True
    ).first()
    
    if not teacher_assigned:
        flash(f"⚠️ Warning: No teacher assigned to {course.code} Section {section} yet.", "warning")
    
    # Check if student's section matches enrollment section
    if student.section and student.section != section:
        flash(f"⚠️ Warning: Student is in Section {student.section} but enrolling in Section {section}. Consider updating student's section first.", "warning")
    
    # Check if already enrolled
    existing = Enrollment.query.filter_by(
        student_id=student_id,
        course_id=course_id
    ).first()
    
    if existing:
        if existing.is_active:
            flash(f"{student.name} is already enrolled in {course.code}.", "info")
        else:
            # Reactivate enrollment
            existing.is_active = True
            db.session.commit()
            flash(f"{student.name} re-enrolled in {course.code} Section {section}.", "success")
        return redirect(url_for("dashboard"))
    
    try:
        enrollment = Enrollment(
            student_id=student_id,
            course_id=course_id
        )
        db.session.add(enrollment)
        db.session.commit()
        
        flash(f"✅ {student.name} enrolled in {course.code} Section {section} successfully!", "success")
        
    except Exception as e:
        db.session.rollback()
        app.logger.error(f"Error enrolling student: {str(e)}")
        flash("Failed to enroll student. Please try again.", "danger")
    
    return redirect(url_for("dashboard"))


@app.route("/admin/students/<int:student_id>/change_section", methods=["POST"])
@login_required
def admin_change_student_section(student_id):
    """Admin changes a student's section"""
    if current_user.role != "admin":
        flash("Only admins can change student sections.", "danger")
        return redirect(url_for("dashboard"))
    
    student = User.query.filter_by(id=student_id, role='student').first_or_404()
    
    new_section = request.form.get("section", "").strip().upper()
    new_year = request.form.get("year", "").strip()
    new_semester = request.form.get("semester", "").strip()
    
    if not new_section:
        flash("Section is required.", "warning")
        return redirect(url_for("dashboard"))
    
    old_section = student.section
    old_year = student.year
    old_semester = student.semester
    
    student.section = new_section
    if new_year:
        student.year = new_year
    if new_semester:
        student.semester = new_semester
    
    # Update assignment status to 'assigned' when section is set
    if new_section and student.assignment_status == 'pending':
        student.assignment_status = 'assigned'
    
    try:
        db.session.commit()
        
        if old_section:
            flash(f"✅ {student.name}'s section changed from {old_section} to {new_section}.", "success")
        else:
            flash(f"✅ {student.name} assigned to Section {new_section}.", "success")
            
    except Exception as e:
        db.session.rollback()
        app.logger.error(f"Error changing section: {str(e)}")
        flash("Failed to change section. Please try again.", "danger")
    
    return redirect(url_for("dashboard"))


@app.route("/admin/enrollments/<int:enrollment_id>/delete", methods=["POST"])
@login_required
def admin_delete_enrollment(enrollment_id):
    """Admin removes a student enrollment"""
    if current_user.role != "admin":
        flash("Only admins can delete enrollments.", "danger")
        return redirect(url_for("dashboard"))
    
    enrollment = Enrollment.query.get_or_404(enrollment_id)
    student = User.query.get(enrollment.student_id)
    course = Course.query.get(enrollment.course_id)
    
    db.session.delete(enrollment)
    db.session.commit()
    
    flash(f"{student.name} unenrolled from {course.code}.", "info")
    return redirect(url_for("dashboard"))


# ══════════════════════════════════════════════════════════════════════════════
# END ADMIN ROUTES
# ══════════════════════════════════════════════════════════════════════════════


# ── Teacher: Unenroll a Student from a Course ─────────────────────────────────
# DEPRECATED: Moved to admin_delete_enrollment
# ──────────────────────────────────────────────────────────────────────────────


# ── Teacher: Delete a Course ──────────────────────────────────────────────────
# DEPRECATED: Moved to admin_delete_course
# ──────────────────────────────────────────────────────────────────────────────


# ── Admin: Delete a User ──────────────────────────────────────────────────────
@app.route("/admin/users/<int:user_id>/edit", methods=["GET", "POST"])
@login_required
def admin_edit_user(user_id):
    if current_user.role != "admin":
        flash("Admins only.", "danger")
        return redirect(url_for("dashboard"))

    user = db.session.get(User, user_id)
    if not user:
        flash("User not found.", "warning")
        return redirect(url_for("dashboard"))

    if user.role == "admin":
        flash("Admin accounts cannot be edited from this panel.", "warning")
        return redirect(url_for("dashboard"))

    if request.method == "POST":
        name = request.form.get("name", "").strip()
        department = request.form.get("department", "").strip()
        college_id = request.form.get("college_id", "").strip()
        section = request.form.get("section", "").strip()
        year = request.form.get("year", "").strip()
        semester = request.form.get("semester", "").strip()

        if not name:
            flash("Name is required.", "warning")
            return render_template("admin_edit_user.html", user=user)
        if not department:
            flash("Department is required.", "warning")
            return render_template("admin_edit_user.html", user=user)

        if user.role == "student" and not (college_id and section and year and semester):
            flash("Student requires College ID, Section, Year and Semester.", "warning")
            return render_template("admin_edit_user.html", user=user)

        user.name = name
        user.department = department

        if user.role == "student":
            user.college_id = college_id
            user.section = section
            user.year = year
            user.semester = semester

        try:
            db.session.commit()
        except IntegrityError:
            db.session.rollback()
            flash("Unable to update user due to a data conflict.", "danger")
            return render_template("admin_edit_user.html", user=user)

        flash(f"User '{user.name}' updated successfully.", "success")
        return redirect(url_for("dashboard"))

    return render_template("admin_edit_user.html", user=user)


@app.route("/admin/users/<int:user_id>/change_role", methods=["GET", "POST"])
@login_required
def admin_change_user_role(user_id):
    if current_user.role != "admin":
        flash("Admins only.", "danger")
        return redirect(url_for("dashboard"))

    user = db.session.get(User, user_id)
    if not user:
        flash("User not found.", "warning")
        return redirect(url_for("dashboard"))

    if user.role == "admin":
        flash("Admin account role cannot be changed from this panel.", "warning")
        return redirect(url_for("dashboard"))

    if request.method == "POST":
        new_role = request.form.get("role", "").strip().lower()
        college_id = request.form.get("college_id", "").strip()
        section = request.form.get("section", "").strip()
        year = request.form.get("year", "").strip()
        semester = request.form.get("semester", "").strip()

        if new_role not in ["student", "teacher"]:
            flash("Only Student or Teacher role is allowed from this action.", "danger")
            return render_template("admin_change_role.html", user=user)

        if user.role == new_role:
            flash("User already has this role.", "info")
            return redirect(url_for("dashboard"))

        if new_role == "student" and not (college_id and section and year and semester):
            flash("College ID, Section, Year and Semester are required when switching to Student.", "warning")
            return render_template("admin_change_role.html", user=user)

        old_role = user.role
        user.role = new_role

        if new_role == "student":
            user.college_id = college_id
            user.section = section
            user.year = year
            user.semester = semester
        else:
            user.college_id = None
            user.section = None
            user.year = None
            user.semester = None

        try:
            db.session.commit()
        except IntegrityError:
            db.session.rollback()
            flash("Role change failed due to data conflict.", "danger")
            return render_template("admin_change_role.html", user=user)

        flash(f"Role updated: {user.name} ({old_role} -> {new_role}).", "success")
        return redirect(url_for("dashboard"))

    return render_template("admin_change_role.html", user=user)


# ── Admin: Delete a User ──────────────────────────────────────────────────────
@app.route("/admin/users/<int:user_id>/delete", methods=["POST"])
@login_required
def admin_delete_user(user_id):
    if current_user.role != "admin":
        flash("Admins only.", "danger")
        return redirect(url_for("dashboard"))
    user = db.session.get(User, user_id)
    if not user:
        flash("User not found.", "warning")
        return redirect(url_for("dashboard"))
    if user.id == current_user.id:
        flash("You cannot delete your own admin account.", "danger")
        return redirect(url_for("dashboard"))
    db.session.delete(user)
    try:
        db.session.commit()
    except IntegrityError:
        db.session.rollback()
        flash("User could not be deleted because related records still exist. Please contact admin to clean linked data.", "danger")
        return redirect(url_for("dashboard"))
    flash(f"User '{user.name}' deleted.", "info")
    return redirect(url_for("dashboard"))
# ──────────────────────────────────────────────────────────────────────────────


# ── Admin: Clear a User's Face Data ──────────────────────────────────────────
@app.route("/admin/users/<int:user_id>/clear_face", methods=["POST"])
@login_required
def admin_clear_face(user_id):
    if current_user.role != "admin":
        flash("Admins only.", "danger")
        return redirect(url_for("dashboard"))
    user = db.session.get(User, user_id)
    if not user:
        flash("User not found.", "warning")
        return redirect(url_for("dashboard"))
    user.face_registered = False
    user.face_encoding = None
    db.session.commit()
    flash(f"Face data cleared for '{user.name}'.", "info")
    return redirect(url_for("dashboard"))
# ──────────────────────────────────────────────────────────────────────────────


# ── Admin: Secret Credentials View (2-step check) ────────────────────────────
# ──────────────────────────────────────────────────────────────────────────────


# ══════════════════════════════════════════════════════════════════════════════
# ADMIN API ENDPOINTS
# ══════════════════════════════════════════════════════════════════════════════

@app.route("/api/admin/courses")
@login_required
def api_admin_courses():
    """Get all courses for admin dropdowns"""
    if current_user.role != "admin":
        return jsonify({"courses": []}), 403
    
    courses = Course.query.filter_by(is_active=True).order_by(Course.code.asc()).all()
    
    return jsonify({
        "courses": [
            {
                "id": c.id,
                "code": c.code,
                "title": c.title,
                "department": c.department,
                "academic_year": c.academic_year,
                "semester": c.semester,
                "credits": c.credits
            }
            for c in courses
        ]
    })


@app.route("/api/admin/teacher_assignments")
@login_required
def api_admin_teacher_assignments():
    """Get all teacher assignments for admin view"""
    if current_user.role != "admin":
        return jsonify({"assignments": []}), 403
    
    assignments = (
        db.session.query(TeacherAssignment, User, Course)
        .join(User, User.id == TeacherAssignment.teacher_id)
        .join(Course, Course.id == TeacherAssignment.course_id)
        .filter(TeacherAssignment.is_active == True)
        .order_by(Course.code.asc(), TeacherAssignment.section.asc())
        .all()
    )
    
    return jsonify({
        "assignments": [
            {
                "id": a.id,
                "teacher_name": t.name,
                "teacher_email": t.email,
                "course_code": c.code,
                "course_title": c.title,
                "section": a.section,
                "department": c.department
            }
            for a, t, c in assignments
        ]
    })


@app.route("/api/admin/course_sections/<int:course_id>")
@login_required
def api_admin_course_sections(course_id):
    """Get available sections for a course (sections with teacher assignments)"""
    if current_user.role != "admin":
        return jsonify({"sections": []}), 403
    
    course = Course.query.get(course_id)
    if not course:
        return jsonify({"sections": [], "error": "Course not found"}), 404
    
    # Get all sections that have teacher assignments for this course
    assignments = TeacherAssignment.query.filter_by(
        course_id=course_id,
        is_active=True
    ).order_by(TeacherAssignment.section.asc()).all()
    
    sections = []
    for assignment in assignments:
        teacher = User.query.get(assignment.teacher_id)
        sections.append({
            "section": assignment.section,
            "teacher_name": teacher.name if teacher else "Unknown",
            "teacher_id": assignment.teacher_id
        })
    
    return jsonify({
        "course_code": course.code,
        "course_title": course.title,
        "sections": sections
    })


@app.route("/api/admin/generate_sessions", methods=["POST"])
@login_required
def api_admin_generate_sessions():
    """Manually trigger auto-session generation (for testing/admin control)"""
    if current_user.role != "admin":
        return jsonify({"success": False, "message": "Admin access required"}), 403
    
    try:
        result = generate_sessions_from_timetable()
        return jsonify({
            "success": True,
            "sessions_created": result["sessions_created"],
            "sessions_closed": result["sessions_closed"],
            "message": f"Generated {result['sessions_created']} sessions, closed {result['sessions_closed']} expired sessions"
        })
    except Exception as e:
        app.logger.error(f"Manual session generation failed: {str(e)}")
        return jsonify({
            "success": False,
            "message": f"Session generation failed: {str(e)}"
        }), 500


# ══════════════════════════════════════════════════════════════════════════════
# END ADMIN API ENDPOINTS
# ══════════════════════════════════════════════════════════════════════════════


# ── API: Live session attendance counts (for teacher polling) ─────────────────
@app.route("/api/session_counts")
@login_required
def api_session_counts():
    """Returns current attendance counts for all of this teacher's active sessions."""
    if current_user.role != "teacher":
        return jsonify({}), 403
    rows = (
        db.session.query(SessionAttendance.session_id, func.count(SessionAttendance.id))
        .join(ClassSession, ClassSession.id == SessionAttendance.session_id)
        .filter(ClassSession.teacher_id == current_user.id)
        .group_by(SessionAttendance.session_id)
        .all()
    )
    return jsonify({str(sid): count for sid, count in rows})
# ──────────────────────────────────────────────────────────────────────────────


# ── Student: Per-course attendance breakdown API ───────────────────────────────
@app.route("/api/my_course_attendance")
@login_required
def api_my_course_attendance():
    """Returns per-course attendance % for the logged-in student."""
    if current_user.role != "student":
        return jsonify([]), 403
    enrolled_courses = (
        Course.query.join(Enrollment, Enrollment.course_id == Course.id)
        .filter(Enrollment.student_id == current_user.id)
        .all()
    )
    result = []
    for course in enrolled_courses:
        session_ids = [s.id for s in ClassSession.query.filter_by(course_id=course.id).all()]
        total = len(session_ids)
        attended = (
            SessionAttendance.query.filter(
                SessionAttendance.student_id == current_user.id,
                SessionAttendance.session_id.in_(session_ids),
            ).count()
            if session_ids else 0
        )
        pct = round((attended / total) * 100, 1) if total > 0 else 0.0
        result.append({
            "course_code": course.code,
            "course_title": course.title,
            "section": course.section,
            "attended": attended,
            "total": total,
            "percentage": pct,
            "low": pct < 75,
        })
    return jsonify(result)


@app.route("/api/my_attendance_calendar")
@login_required
def api_my_attendance_calendar():
    """Returns attendance data formatted for calendar view."""
    if current_user.role != "student":
        return jsonify([]), 403
    
    # Get all attendance records
    attendance_records = Attendance.query.filter_by(user_id=current_user.id).all()
    
    # Get all session attendance records
    session_records = (
        db.session.query(SessionAttendance, ClassSession)
        .join(ClassSession, ClassSession.id == SessionAttendance.session_id)
        .filter(SessionAttendance.student_id == current_user.id)
        .all()
    )
    
    calendar_data = []
    
    # Add daily attendance records
    for record in attendance_records:
        calendar_data.append({
            "date": record.date.isoformat(),
            "status": "present",
            "time": record.time.strftime("%I:%M %p") if record.time else None,
            "type": "daily"
        })
    
    # Add session attendance records
    for sa, session in session_records:
        marked_date = sa.marked_at.date() if sa.marked_at else None
        if marked_date:
            # Check if already added from daily records
            existing = next((item for item in calendar_data if item["date"] == marked_date.isoformat()), None)
            if not existing:
                calendar_data.append({
                    "date": marked_date.isoformat(),
                    "status": "present",
                    "time": sa.marked_at.strftime("%I:%M %p") if sa.marked_at else None,
                    "course_code": session.course_code,
                    "session_title": session.title,
                    "type": "session"
                })
            elif "course_code" not in existing:
                # Enhance existing record with session info
                existing["course_code"] = session.course_code
                existing["session_title"] = session.title
    
    return jsonify(calendar_data)


@app.route("/attendance/calendar")
@login_required
def attendance_calendar():
    """Render attendance calendar view."""
    if current_user.role != "student":
        flash("Calendar view is only available for students.", "warning")
        return redirect(url_for("dashboard"))
    return render_template("attendance_calendar.html")
# ──────────────────────────────────────────────────────────────────────────────

@app.route("/forgot-password", methods=["GET", "POST"])
@limiter.limit("5 per hour")
def forgot_password():
    if current_user.is_authenticated:
        return redirect(url_for("dashboard"))

    if request.method == "POST":
        email = request.form.get("email", "").strip().lower()
        user = User.query.filter_by(email=email).first()

        if user:
            reset_url = url_for("reset_password", token=generate_password_reset_token(user), _external=True)
            sent = send_password_reset_email(
                app,
                user.name,
                user.email,
                reset_url,
                app.config["PASSWORD_RESET_TOKEN_MAX_AGE_MINUTES"],
            )
            if not sent:
                app.logger.warning("Password reset email could not be sent for user_id=%s", user.id)
            if app.config.get("DEBUG"):
                app.logger.info("Password reset link for %s: %s", user.email, reset_url)

        flash("If that email exists in the system, a password reset link has been sent.", "info")
        return redirect(url_for("login"))

    return render_template("forgot_password.html")


@app.route("/reset-password/<token>", methods=["GET", "POST"])
@limiter.limit("10 per hour")
def reset_password(token):
    if current_user.is_authenticated:
        logout_user()

    user = get_user_from_reset_token(token)
    if not user:
        flash("This password reset link is invalid or has expired. Request a new one.", "warning")
        return redirect(url_for("forgot_password"))

    if request.method == "POST":
        password = request.form.get("password", "")
        confirm_password = request.form.get("confirm_password", "")

        password_error = password_validation_error(password)
        if password_error:
            flash(password_error, "warning")
            return render_template("reset_password.html", token=token)

        if password != confirm_password:
            flash("Passwords do not match.", "warning")
            return render_template("reset_password.html", token=token)

        user.password_hash = generate_password_hash(password, method="scrypt")
        try:
            db.session.commit()
        except Exception:
            db.session.rollback()
            app.logger.exception("Password reset failed for user_id=%s", user.id)
            flash("Unable to reset password right now. Please try again.", "danger")
            return render_template("reset_password.html", token=token)

        flash("Password updated successfully. Please log in with your new password.", "success")
        return redirect(url_for("login"))

    return render_template("reset_password.html", token=token)


@app.route("/login", methods=["GET", "POST"])
@limiter.limit("5 per minute")
def login():
    if request.method == "POST":
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")
        
        user = User.query.filter_by(email=email).first()

        if user and check_password_hash(user.password_hash, password):
            login_user(user)
            flash("Login successful!", "success")
            return redirect(url_for("dashboard"))
        
        flash("Invalid email or password. Please try again.", "danger")
        return redirect(url_for("login"))

    return render_template("login.html")


@app.route("/logout")
@login_required
def logout():
    logout_user()
    return redirect(url_for("index"))


@app.route("/dashboard")
@login_required
def dashboard():
    if current_user.role == "admin":
        users = User.query.all()
        today = today_local_date()
        recent_dates = [today - timedelta(days=i) for i in range(7)]
        recent_dates.reverse()

        user_attendance_map = {}
        today_count = 0

        for user in users:
            user_attendance_map[user.id] = {}
            for date in recent_dates:
                att = Attendance.query.filter_by(user_id=user.id, date=date).first()
                if att:
                    user_attendance_map[user.id][date.isoformat()] = att.time.strftime("%I:%M %p")
                    if date == today:
                        today_count += 1
                else:
                    user_attendance_map[user.id][date.isoformat()] = None

        # Get teachers and courses for admin forms
        teachers = User.query.filter_by(role='teacher', is_active=True).order_by(User.name.asc()).all()
        courses = Course.query.filter_by(is_active=True).order_by(Course.code.asc()).all()
        teacher_assignments = TeacherAssignment.query.filter_by(is_active=True).all()
        
        # Registration Statistics
        total_students = User.query.filter_by(role='student', is_active=True).count()
        pending_students = User.query.filter_by(role='student', assignment_status='pending', is_active=True).count()
        assigned_students = User.query.filter_by(role='student', assignment_status='assigned', is_active=True).count()
        
        # Department-wise statistics
        dept_stats = {}
        departments = db.session.query(User.department).filter_by(role='student', is_active=True).distinct().all()
        for (dept,) in departments:
            total = User.query.filter_by(role='student', department=dept, is_active=True).count()
            pending = User.query.filter_by(role='student', department=dept, assignment_status='pending', is_active=True).count()
            assigned = User.query.filter_by(role='student', department=dept, assignment_status='assigned', is_active=True).count()
            dept_stats[dept] = {
                'total': total,
                'pending': pending,
                'assigned': assigned
            }

        return render_template(
            "admin_dashboard.html",
            users=users,
            recent_dates=recent_dates,
            user_attendance_map=user_attendance_map,
            today_count=today_count,
            teachers=teachers,
            courses=courses,
            teacher_assignments=teacher_assignments,
            total_students=total_students,
            pending_students=pending_students,
            assigned_students=assigned_students,
            dept_stats=dept_stats,
        )

    if current_user.role == "teacher":
        today = today_local_date()
        recent_dates = [today - timedelta(days=i) for i in range(7)]
        recent_dates.reverse()

        # Get ASSIGNED courses only (via TeacherAssignment table)
        teacher_courses = get_teacher_assigned_courses(current_user.id)
        
        # Get teacher assignments with section info
        teacher_assignments = TeacherAssignment.query.filter_by(
            teacher_id=current_user.id,
            is_active=True
        ).all()

        # Get students from assigned courses
        assigned_course_ids = [c.id for c in teacher_courses]
        if assigned_course_ids:
            students = (
                User.query.join(Enrollment, Enrollment.student_id == User.id)
                .filter(
                    Enrollment.course_id.in_(assigned_course_ids),
                    User.role == "student"
                )
                .distinct()
                .order_by(User.name.asc())
                .all()
            )
        else:
            students = []
        
        student_attendance_map = {}
        student_today_count = 0

        for student in students:
            student_attendance_map[student.id] = {}
            for date in recent_dates:
                att = Attendance.query.filter_by(user_id=student.id, date=date).first()
                if att:
                    student_attendance_map[student.id][date.isoformat()] = att.time.strftime("%I:%M %p")
                    if date == today:
                        student_today_count += 1
                else:
                    student_attendance_map[student.id][date.isoformat()] = None

        now = now_utc_naive()
        teacher_sessions = (
            ClassSession.query.filter_by(teacher_id=current_user.id)
            .order_by(ClassSession.created_at.desc())
            .limit(12)
            .all()
        )
        active_session_count = ClassSession.query.filter(
            ClassSession.teacher_id == current_user.id,
            ClassSession.is_active.is_(True),
            ClassSession.ends_at >= now,
        ).count()

        course_enrollment_count_map = dict(
            db.session.query(Enrollment.course_id, func.count(Enrollment.id)).group_by(Enrollment.course_id).all()
        )
        session_attendance_count_map = dict(
            db.session.query(SessionAttendance.session_id, func.count(SessionAttendance.id))
            .join(ClassSession, ClassSession.id == SessionAttendance.session_id)
            .filter(ClassSession.teacher_id == current_user.id)
            .group_by(SessionAttendance.session_id)
            .all()
        )
        session_roster_count_map = {}
        for teacher_session in teacher_sessions:
            session_roster_count_map[teacher_session.id] = build_session_roster(teacher_session)["counts"]

        my_attendance = Attendance.query.filter_by(user_id=current_user.id).order_by(Attendance.date.desc()).all()
        return render_template(
            "teacher_dashboard.html",
            attendance=my_attendance,
            students=students,
            recent_dates=recent_dates,
            student_attendance_map=student_attendance_map,
            student_today_count=student_today_count,
            teacher_courses=teacher_courses,
            teacher_assignments=teacher_assignments,
            course_enrollment_count_map=course_enrollment_count_map,
            teacher_sessions=teacher_sessions,
            active_session_count=active_session_count,
            session_attendance_count_map=session_attendance_count_map,
            session_roster_count_map=session_roster_count_map,
            now=now,
        )

    # STUDENT DASHBOARD
    my_attendance = Attendance.query.filter_by(user_id=current_user.id).order_by(Attendance.date.desc()).all()

    present_days = len(my_attendance)

    # Total class sessions the student was eligible to attend
    enrolled_course_ids = [e.course_id for e in Enrollment.query.filter_by(student_id=current_user.id).all()]
    total_sessions_held = 0
    if enrolled_course_ids:
        # Count all sessions that have already started
        total_sessions_held = ClassSession.query.filter(
            ClassSession.course_id.in_(enrolled_course_ids),
            ClassSession.starts_at <= now_utc_naive()
        ).count()

    # Use session attendance for percentage (more accurate than daily record)
    sessions_attended = SessionAttendance.query.filter_by(student_id=current_user.id).count()

    attendance_percentage = 0
    if total_sessions_held > 0:
        # Prevent percentage from exceeding 100% just in case
        clamped_attended = min(sessions_attended, total_sessions_held)
        attendance_percentage = round((clamped_attended / total_sessions_held) * 100, 1)
    elif present_days > 0:
        attendance_percentage = 100.0  # fallback: all days present

    active_sessions = student_active_sessions(current_user.id)

    session_records = (
        SessionAttendance.query.filter_by(student_id=current_user.id)
        .order_by(SessionAttendance.marked_at.desc())
        .limit(15)
        .all()
    )

    enrolled_courses = (
        Course.query.join(Enrollment, Enrollment.course_id == Course.id)
        .filter(Enrollment.student_id == current_user.id)
        .order_by(Course.code.asc())
        .all()
    )

    return render_template(
        "student_dashboard.html",
        attendance=my_attendance,
        active_sessions=active_sessions,
        session_records=session_records,
        enrolled_courses=enrolled_courses,
        attendance_percentage=attendance_percentage,
    )
with app.app_context():
    ensure_schema_compatibility()

    # ── Backfill daily Attendance from existing SessionAttendance records ──
    # Fixes missing daily records for sessions marked before this logic was added.
    try:
        all_session_att = SessionAttendance.query.all()
        backfill_count = 0
        for sa in all_session_att:
            sess = db.session.get(ClassSession, sa.session_id)
            if not sess:
                continue
            from zoneinfo import ZoneInfo as _ZI
            local_marked = sa.marked_at
            if local_marked.tzinfo is None:
                local_marked = local_marked.replace(tzinfo=timezone.utc)
            local_marked = local_marked.astimezone(_ZI(app.config["APP_TIMEZONE"]))
            record_date = local_marked.date()
            exists = Attendance.query.filter_by(user_id=sa.student_id, date=record_date).first()
            if not exists:
                daily = Attendance(
                    user_id=sa.student_id,
                    date=record_date,
                    time=local_marked.time().replace(microsecond=0),
                    latitude=sa.latitude,
                    longitude=sa.longitude,
                )
                db.session.add(daily)
                backfill_count += 1
        if backfill_count:
            db.session.commit()
            app.logger.info("Backfilled %d daily attendance records from session attendance.", backfill_count)
    except Exception:
        db.session.rollback()
        app.logger.exception("Backfill of daily attendance records failed (non-critical).")
    # ─────────────────────────────────────────────────────────────────────


if __name__ == "__main__":
    app.run(debug=app.config["DEBUG"])
