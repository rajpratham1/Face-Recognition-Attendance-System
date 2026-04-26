import os
import sys
from pathlib import Path

os.environ.setdefault("SECRET_KEY", "test-secret")
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app import app


def test_index_page_loads():
    app.config["TESTING"] = True
    client = app.test_client()
    response = client.get("/")
    assert response.status_code == 200


def test_security_cookie_flags_set():
    assert app.config["SESSION_COOKIE_HTTPONLY"] is True
    assert app.config["SESSION_COOKIE_SAMESITE"] == "Lax"


def test_teacher_session_roster_requires_login():
    app.config["TESTING"] = True
    client = app.test_client()
    response = client.get("/teacher/sessions/1/roster")
    assert response.status_code in (301, 302)
