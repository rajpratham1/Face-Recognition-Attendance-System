import os

os.environ.setdefault("SECRET_KEY", "test-secret")

from app import app


def test_index_page_loads():
    app.config["TESTING"] = True
    client = app.test_client()
    response = client.get("/")
    assert response.status_code == 200


def test_security_cookie_flags_set():
    assert app.config["SESSION_COOKIE_HTTPONLY"] is True
    assert app.config["SESSION_COOKIE_SAMESITE"] == "Lax"
