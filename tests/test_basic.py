import os
import sys
import uuid
import json
from datetime import datetime, timedelta, timezone
from pathlib import Path

from werkzeug.security import check_password_hash, generate_password_hash

os.environ.setdefault("SECRET_KEY", "test-secret")
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import app as attendance_app

app = attendance_app.app
db = attendance_app.db
User = attendance_app.User
Course = attendance_app.Course
Enrollment = attendance_app.Enrollment
ClassSession = attendance_app.ClassSession


def _create_test_user():
    email = f"reset-{uuid.uuid4().hex[:10]}@example.com"
    with app.app_context():
        user = User(
            name="Reset Test User",
            email=email,
            department="Computer Science",
            role="student",
            college_id="TEST001",
            section="A",
            year="1",
            semester="1",
            password_hash=generate_password_hash("OldPass123", method="scrypt"),
        )
        db.session.add(user)
        db.session.commit()
        token = attendance_app.generate_password_reset_token(user)
    return email, token


def _delete_test_user(email):
    with app.app_context():
        user = User.query.filter_by(email=email).first()
        if user:
            db.session.delete(user)
            db.session.commit()


def _create_kiosk_fixture():
    teacher_email = f"teacher-{uuid.uuid4().hex[:10]}@example.com"
    student_email = f"student-{uuid.uuid4().hex[:10]}@example.com"

    with app.app_context():
        teacher = User(
            name="Fixture Teacher",
            email=teacher_email,
            department="Computer Science",
            role="teacher",
            password_hash=generate_password_hash("TeacherPass1", method="scrypt"),
        )
        student = User(
            name="Fixture Student",
            email=student_email,
            department="Computer Science",
            role="student",
            college_id="STU001",
            section="A",
            year="1",
            semester="1",
            face_registered=True,
            face_encoding=json.dumps([0.1] * 128),
            password_hash=generate_password_hash("StudentPass1", method="scrypt"),
        )
        db.session.add_all([teacher, student])
        db.session.commit()

        course = Course(code="CSE101", title="Secure Systems", section="A", teacher_id=teacher.id)
        db.session.add(course)
        db.session.commit()

        enrollment = Enrollment(course_id=course.id, student_id=student.id)
        session = ClassSession(
            title=course.title,
            course_code=course.code,
            room="Lab 1",
            course_id=course.id,
            teacher_id=teacher.id,
            starts_at=datetime.now(timezone.utc).replace(tzinfo=None) - timedelta(minutes=5),
            ends_at=datetime.now(timezone.utc).replace(tzinfo=None) + timedelta(minutes=10),
            is_active=True,
            location_lat=28.325645,
            location_lng=79.461063,
            location_radius_meters=50,
        )
        db.session.add_all([enrollment, session])
        db.session.commit()

        return {
            "teacher_email": teacher_email,
            "student_email": student_email,
            "session_id": session.id,
        }


def _cleanup_kiosk_fixture(teacher_email, student_email):
    with app.app_context():
        teacher = User.query.filter_by(email=teacher_email).first()
        if teacher:
            db.session.delete(teacher)
        student = User.query.filter_by(email=student_email).first()
        if student:
            db.session.delete(student)
        db.session.commit()


def test_index_page_loads():
    app.config["TESTING"] = True
    client = app.test_client()
    response = client.get("/")
    assert response.status_code == 200


def test_security_cookie_flags_set():
    assert app.config["SESSION_COOKIE_HTTPONLY"] is True
    assert app.config["SESSION_COOKIE_SAMESITE"] == "Lax"
    assert app.config["SESSION_COOKIE_SECURE"] is False
    assert app.config["GEOFENCE_ENFORCED"] is False
    assert app.config["SESSION_LOCATION_RADIUS_METERS"] == 50


def test_teacher_session_roster_requires_login():
    app.config["TESTING"] = True
    client = app.test_client()
    response = client.get("/teacher/sessions/1/roster")
    assert response.status_code in (301, 302)


def test_forgot_password_post_shows_generic_success(monkeypatch):
    email, _token = _create_test_user()
    sent_emails = []

    def fake_send_password_reset_email(*args, **kwargs):
        sent_emails.append((args, kwargs))
        return True

    monkeypatch.setattr(attendance_app, "send_password_reset_email", fake_send_password_reset_email)
    app.config["TESTING"] = True
    app.config["WTF_CSRF_ENABLED"] = False
    client = app.test_client()

    try:
        response = client.post("/forgot-password", data={"email": email}, follow_redirects=True)
        assert response.status_code == 200
        assert b"password reset link has been sent" in response.data
        assert len(sent_emails) == 1
    finally:
        _delete_test_user(email)


def test_reset_password_updates_password_hash():
    email, token = _create_test_user()
    app.config["TESTING"] = True
    app.config["WTF_CSRF_ENABLED"] = False
    client = app.test_client()

    try:
        response = client.post(
            f"/reset-password/{token}",
            data={"password": "NewPass123", "confirm_password": "NewPass123"},
            follow_redirects=True,
        )
        assert response.status_code == 200
        assert b"Password updated successfully" in response.data

        with app.app_context():
            user = User.query.filter_by(email=email).first()
            assert user is not None
            assert check_password_hash(user.password_hash, "NewPass123")
    finally:
        _delete_test_user(email)


def test_public_registration_rejects_teacher_role():
    email = f"teacher-{uuid.uuid4().hex[:10]}@example.com"
    app.config["TESTING"] = True
    app.config["WTF_CSRF_ENABLED"] = False
    client = app.test_client()

    response = client.post(
        "/register",
        data={
            "name": "Teacher Signup Attempt",
            "role": "teacher",
            "department": "Computer Science",
            "email": email,
            "password": "ValidPass1",
            "consent": "yes",
        },
        follow_redirects=True,
    )

    try:
        assert response.status_code == 200
        assert b"provisioned by administrators only" in response.data
        with app.app_context():
            assert User.query.filter_by(email=email).first() is None
    finally:
        _delete_test_user(email)


def test_kiosk_data_does_not_expose_face_descriptors():
    fixture = _create_kiosk_fixture()
    app.config["TESTING"] = True
    app.config["WTF_CSRF_ENABLED"] = False
    client = app.test_client()

    try:
        login_response = client.post(
            "/login",
            data={"email": fixture["teacher_email"], "password": "TeacherPass1"},
            follow_redirects=False,
        )
        assert login_response.status_code in (302, 303)

        response = client.get(f"/api/kiosk_data/{fixture['session_id']}")
        assert response.status_code == 200

        payload = response.get_json()
        assert payload["success"] is True
        assert payload["students"]
        assert "descriptor" not in payload["students"][0]
        assert "face_ready" in payload["students"][0]
    finally:
        _cleanup_kiosk_fixture(fixture["teacher_email"], fixture["student_email"])
