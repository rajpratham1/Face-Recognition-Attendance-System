import hashlib
import json
import secrets
from math import isfinite
from datetime import datetime, timedelta, timezone
from zoneinfo import ZoneInfo

import numpy as np
from flask import Flask, flash, jsonify, redirect, render_template, request, url_for
from flask_login import LoginManager, current_user, login_required, login_user, logout_user
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from flask_wtf.csrf import CSRFError, CSRFProtect, generate_csrf
from geopy.distance import geodesic
from sqlalchemy import func, text
from werkzeug.security import check_password_hash, generate_password_hash

from config import Config
from firebase_service import init_firebase, sync_attendance_attempt, sync_session_attendance
from models import (
    Attendance,
    AttendanceAttempt,
    ClassSession,
    Course,
    Enrollment,
    SessionAttendance,
    User,
    db,
)

app = Flask(__name__)
app.config.from_object(Config)
if not app.config.get("SECRET_KEY"):
    # Stable dev fallback; set SECRET_KEY in env for production.
    app.config["SECRET_KEY"] = "dev-insecure-change-me"

csrf = CSRFProtect(app)
db.init_app(app)
limiter = Limiter(key_func=get_remote_address, app=app, default_limits=["200 per day", "60 per hour"])
init_firebase(app)

login_manager = LoginManager()
login_manager.login_view = "login"
login_manager.init_app(app)


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
    return {
        "csrf_token": generate_csrf,
        "app_timezone": app.config["APP_TIMEZONE"],
        "firebase_web_config": firebase_web_config,
        "firebase_enabled": app.extensions.get("firebase_enabled", False),
        "firebase_error": app.extensions.get("firebase_error", ""),
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


def now_utc_naive():
    return datetime.now(timezone.utc).replace(tzinfo=None)


def now_local():
    return datetime.now(ZoneInfo(app.config["APP_TIMEZONE"]))


def today_local_date():
    return now_local().date()


def is_within_invertis(lat, lng):
    if lat is None or lng is None:
        return False
    user_location = (lat, lng)
    invertis_location = (app.config["INVERTIS_LAT"], app.config["INVERTIS_LNG"])
    distance = geodesic(user_location, invertis_location).meters
    return distance <= app.config["ALLOWED_RADIUS_METERS"]


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


def ensure_schema_compatibility():
    db.create_all()
    if not str(db.engine.url).startswith("sqlite"):
        return

    def _columns(conn, table_name):
        rows = conn.execute(text(f"PRAGMA table_info({table_name})")).fetchall()
        return {row[1] for row in rows}

    with db.engine.begin() as conn:
        class_session_columns = _columns(conn, "class_sessions")
        if "course_id" not in class_session_columns:
            conn.execute(text("ALTER TABLE class_sessions ADD COLUMN course_id INTEGER"))

        session_attendance_columns = _columns(conn, "session_attendance")
        if "device_hash" not in session_attendance_columns:
            conn.execute(text("ALTER TABLE session_attendance ADD COLUMN device_hash VARCHAR(128)"))
        if "ip_address" not in session_attendance_columns:
            conn.execute(text("ALTER TABLE session_attendance ADD COLUMN ip_address VARCHAR(64)"))
        if "user_agent" not in session_attendance_columns:
            conn.execute(text("ALTER TABLE session_attendance ADD COLUMN user_agent VARCHAR(255)"))


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/register", methods=["GET", "POST"])
@limiter.limit("20 per hour")
def register():
    if request.method == "POST":
        name = request.form.get("name", "").strip()
        email = request.form.get("email", "").strip().lower()
        department = request.form.get("department", "").strip()
        password = request.form.get("password", "")
        role = request.form.get("role", "student")
        consent = request.form.get("consent") == "yes"

        if role not in ["teacher", "student"]:
            flash("Invalid role selected", "danger")
            return redirect(url_for("register"))
        if not consent:
            flash("You must accept biometric and privacy consent to continue.", "warning")
            return redirect(url_for("register"))
        if User.query.filter_by(email=email).first():
            flash("Email already registered", "danger")
            return redirect(url_for("register"))

        new_user = User(
            name=name,
            email=email,
            department=department,
            role=role,
            password_hash=generate_password_hash(password, method="scrypt"),
        )
        db.session.add(new_user)
        db.session.commit()

        login_user(new_user)
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
            return jsonify({"success": False, "message": "Attendance can only be marked within Invertis University campus!"}), 400

        today = today_local_date()
        existing = Attendance.query.filter_by(user_id=current_user.id, date=today).first()
        if existing:
            return jsonify({"success": False, "message": "Attendance already marked for today!"}), 400

        if not descriptor:
            return jsonify({"success": False, "message": "No face detected!"}), 400

        known_encoding = np.array(json.loads(current_user.face_encoding))
        unknown_encoding = np.array(descriptor)
        distance = float(np.linalg.norm(known_encoding - unknown_encoding))

        if distance < 0.6:
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
            return jsonify({"success": True, "message": "Attendance marked successfully!"})

        return jsonify({"success": False, "message": "Face verification failed!"}), 400

    return render_template("mark_attendance.html")


@app.route("/teacher/courses/create", methods=["POST"])
@login_required
def create_course():
    if current_user.role != "teacher":
        flash("Only teachers can create courses.", "danger")
        return redirect(url_for("dashboard"))

    code = request.form.get("code", "").strip().upper()
    title = request.form.get("title", "").strip()
    section = request.form.get("section", "").strip().upper()

    if not code or not title or not section:
        flash("All course fields are required.", "warning")
        return redirect(url_for("dashboard"))

    exists = Course.query.filter_by(code=code, section=section, teacher_id=current_user.id).first()
    if exists:
        flash("Course already exists for this section.", "warning")
        return redirect(url_for("dashboard"))

    course = Course(code=code, title=title, section=section, teacher_id=current_user.id)
    db.session.add(course)
    db.session.commit()
    flash("Course created successfully.", "success")
    return redirect(url_for("dashboard"))


@app.route("/teacher/courses/<int:course_id>/enroll", methods=["POST"])
@login_required
def enroll_student(course_id):
    if current_user.role != "teacher":
        flash("Only teachers can enroll students.", "danger")
        return redirect(url_for("dashboard"))

    course = Course.query.filter_by(id=course_id, teacher_id=current_user.id).first_or_404()
    student_email = request.form.get("student_email", "").strip().lower()
    student = User.query.filter_by(email=student_email, role="student").first()

    if not student:
        flash("Student not found with this email.", "warning")
        return redirect(url_for("dashboard"))

    existing = Enrollment.query.filter_by(course_id=course.id, student_id=student.id).first()
    if existing:
        flash("Student already enrolled in this course.", "info")
        return redirect(url_for("dashboard"))

    db.session.add(Enrollment(course_id=course.id, student_id=student.id))
    db.session.commit()
    flash("Student enrolled successfully.", "success")
    return redirect(url_for("dashboard"))


@app.route("/teacher/sessions/create", methods=["POST"])
@login_required
def create_session():
    if current_user.role != "teacher":
        flash("Only teachers can create class sessions.", "danger")
        return redirect(url_for("dashboard"))

    course_id_raw = request.form.get("course_id", "").strip()
    room = request.form.get("room", "").strip()
    duration_raw = request.form.get("duration", "15").strip()

    try:
        course_id = int(course_id_raw)
    except ValueError:
        flash("Invalid course selected.", "warning")
        return redirect(url_for("dashboard"))

    course = Course.query.filter_by(id=course_id, teacher_id=current_user.id).first()
    if not course:
        flash("Course not found for this teacher.", "warning")
        return redirect(url_for("dashboard"))

    if not room:
        flash("Room/Lab is required.", "warning")
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
        starts_at=starts_at,
        ends_at=ends_at,
        teacher_id=current_user.id,
        is_active=True,
    )
    db.session.add(new_session)
    db.session.commit()
    flash("Class session created and is now live for enrolled students.", "success")
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

    now = now_utc_naive()
    if not (session.is_active and session.starts_at <= now <= session.ends_at):
        record_attempt(session.id, current_user.id, False, "Session inactive", lat, lng, None, device_hash, ip_address, user_agent)
        db.session.commit()
        return jsonify({"success": False, "message": "This session is not active now."}), 400

    if not is_within_invertis(lat, lng):
        record_attempt(session.id, current_user.id, False, "Outside campus", lat, lng, None, device_hash, ip_address, user_agent)
        db.session.commit()
        return jsonify({"success": False, "message": "Attendance can only be marked within Invertis University campus."}), 400

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

    if distance >= 0.6:
        record_attempt(session.id, current_user.id, False, "Face mismatch", lat, lng, distance, device_hash, ip_address, user_agent)
        db.session.commit()
        return jsonify({"success": False, "message": "Face verification failed. Please try again."}), 400

    entry = SessionAttendance(
        session_id=session.id,
        student_id=current_user.id,
        latitude=lat,
        longitude=lng,
        face_distance=distance,
        device_hash=device_hash,
        ip_address=ip_address,
        user_agent=user_agent,
    )
    db.session.add(entry)
    record_attempt(session.id, current_user.id, True, "Attendance marked", lat, lng, distance, device_hash, ip_address, user_agent)
    db.session.commit()
    sync_session_attendance(app, entry, session, current_user)

    return jsonify({"success": True, "message": f"Attendance marked for {session.course_code} ({session.title})."})


@app.route("/login", methods=["GET", "POST"])
@limiter.limit("5 per minute")
def login():
    if request.method == "POST":
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")
        user = User.query.filter_by(email=email).first()

        if user and check_password_hash(user.password_hash, password):
            login_user(user)
            return redirect(url_for("dashboard"))
        flash("Invalid credentials", "danger")

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

        return render_template(
            "admin_dashboard.html",
            users=users,
            recent_dates=recent_dates,
            user_attendance_map=user_attendance_map,
            today_count=today_count,
        )

    if current_user.role == "teacher":
        today = today_local_date()
        recent_dates = [today - timedelta(days=i) for i in range(7)]
        recent_dates.reverse()

        students = teacher_students_query(current_user.id).order_by(User.name.asc()).all()
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
        teacher_courses = Course.query.filter_by(teacher_id=current_user.id).order_by(Course.created_at.desc()).all()
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

        my_attendance = Attendance.query.filter_by(user_id=current_user.id).order_by(Attendance.date.desc()).all()
        return render_template(
            "teacher_dashboard.html",
            attendance=my_attendance,
            students=students,
            recent_dates=recent_dates,
            student_attendance_map=student_attendance_map,
            student_today_count=student_today_count,
            teacher_courses=teacher_courses,
            course_enrollment_count_map=course_enrollment_count_map,
            teacher_sessions=teacher_sessions,
            active_session_count=active_session_count,
            session_attendance_count_map=session_attendance_count_map,
            now=now,
        )

    my_attendance = Attendance.query.filter_by(user_id=current_user.id).order_by(Attendance.date.desc()).all()
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
    )


with app.app_context():
    ensure_schema_compatibility()


if __name__ == "__main__":
    app.run(debug=app.config["DEBUG"])
