import os

from dotenv import load_dotenv

load_dotenv(override=True)


def _env_float(name, default):
    value = os.environ.get(name)
    if value is None or value.strip() == "":
        return default
    try:
        return float(value)
    except ValueError:
        return default


def _env_int(name, default):
    value = os.environ.get(name)
    if value is None or value.strip() == "":
        return default
    try:
        return int(value)
    except ValueError:
        return default


def _env_bool(name, default):
    value = os.environ.get(name)
    if value is None or value.strip() == "":
        return default
    return value.strip().lower() in {"1", "true", "yes", "on"}

class Config:
    APP_NAME = os.environ.get('APP_NAME', 'Face Attendance')
    APP_PROGRAM_NAME = os.environ.get('APP_PROGRAM_NAME', 'Intel Digital Readiness Bootcamp')
    APP_GEOFENCE_LABEL = os.environ.get('APP_GEOFENCE_LABEL', 'authorized attendance zone')
    SECRET_KEY = os.environ.get('SECRET_KEY')
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL', 'sqlite:///attendance.db')
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    APP_TIMEZONE = os.environ.get('APP_TIMEZONE', 'Asia/Kolkata')
    FLASK_ENV = os.environ.get('FLASK_ENV', 'production').strip().lower()
    DEBUG = FLASK_ENV == 'development'
    ENFORCE_SECRET_KEY_IN_PRODUCTION = _env_bool('ENFORCE_SECRET_KEY_IN_PRODUCTION', True)

    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = 'Lax'
    SESSION_COOKIE_SECURE = _env_bool('SESSION_COOKIE_SECURE', FLASK_ENV == 'production')
    REMEMBER_COOKIE_HTTPONLY = True
    REMEMBER_COOKIE_SAMESITE = 'Lax'
    REMEMBER_COOKIE_SECURE = _env_bool('SESSION_COOKIE_SECURE', FLASK_ENV == 'production')
    WTF_CSRF_TIME_LIMIT = None
    RATELIMIT_STORAGE_URI = os.environ.get('RATELIMIT_STORAGE_URI', 'memory://')
    RATELIMIT_HEADERS_ENABLED = True

    # Firebase (optional but recommended for cloud sync/audit)
    FIREBASE_PROJECT_ID = os.environ.get('FIREBASE_PROJECT_ID', '')
    FIREBASE_DATABASE_URL = os.environ.get('FIREBASE_DATABASE_URL', '')
    FIREBASE_SERVICE_ACCOUNT_PATH = os.environ.get('FIREBASE_SERVICE_ACCOUNT_PATH', '')
    FIREBASE_SERVICE_ACCOUNT_JSON = os.environ.get('FIREBASE_SERVICE_ACCOUNT_JSON', '')

    # Firebase Web SDK config (frontend)
    FIREBASE_API_KEY = os.environ.get('FIREBASE_API_KEY', '')
    FIREBASE_AUTH_DOMAIN = os.environ.get('FIREBASE_AUTH_DOMAIN', '')
    FIREBASE_STORAGE_BUCKET = os.environ.get('FIREBASE_STORAGE_BUCKET', '')
    FIREBASE_MESSAGING_SENDER_ID = os.environ.get('FIREBASE_MESSAGING_SENDER_ID', '')
    FIREBASE_APP_ID = os.environ.get('FIREBASE_APP_ID', '')

    # Campus geofence settings (override from environment for local/dev setups)
    INVERTIS_LAT = _env_float('INVERTIS_LAT', 28.325645)
    INVERTIS_LNG = _env_float('INVERTIS_LNG', 79.461063)
    ALLOWED_RADIUS_METERS = _env_int('ALLOWED_RADIUS_METERS', 100)
    SESSION_LOCATION_RADIUS_METERS = _env_int('SESSION_LOCATION_RADIUS_METERS', 50)
    GEOFENCE_ENFORCED = _env_bool('GEOFENCE_ENFORCED', FLASK_ENV == 'production')

    # ─── Email Notification Settings ────────────────────────────────────────────
    # Set these in your .env file to enable attendance email notifications.
    # MAIL_USERNAME  → your Gmail address   (e.g. yourapp@gmail.com)
    # MAIL_PASSWORD  → Gmail App Password   (16-char, NOT your login password)
    # Get App Password: Google Account → Security → 2-Step → App Passwords
    MAIL_SERVER    = os.environ.get('MAIL_SERVER',    'smtp.gmail.com')
    MAIL_PORT      = int(os.environ.get('MAIL_PORT',  '587'))
    MAIL_USERNAME  = os.environ.get('MAIL_USERNAME',  '')
    MAIL_PASSWORD  = os.environ.get('MAIL_PASSWORD',  '')
    MAIL_FROM_NAME = os.environ.get('MAIL_FROM_NAME', 'Attendance System')
    PASSWORD_RESET_SALT = os.environ.get('PASSWORD_RESET_SALT', 'password-reset')
    PASSWORD_RESET_TOKEN_MAX_AGE_MINUTES = _env_int('PASSWORD_RESET_TOKEN_MAX_AGE_MINUTES', 30)

    # ─── Liveness Detection Settings ────────────────────────────────────────────
    # Enable/disable liveness detection for face verification
    LIVENESS_DETECTION_ENABLED = _env_bool('LIVENESS_DETECTION_ENABLED', True)
    LIVENESS_REQUIRE_BLINK = _env_bool('LIVENESS_REQUIRE_BLINK', True)
    LIVENESS_REQUIRE_HEAD_MOVEMENT = _env_bool('LIVENESS_REQUIRE_HEAD_MOVEMENT', True)
    LIVENESS_TIMEOUT_SECONDS = _env_int('LIVENESS_TIMEOUT_SECONDS', 15)
    LIVENESS_BLINK_THRESHOLD = _env_float('LIVENESS_BLINK_THRESHOLD', 0.25)
    LIVENESS_MOVEMENT_THRESHOLD = _env_int('LIVENESS_MOVEMENT_THRESHOLD', 15)
    LIVENESS_QUALITY_THRESHOLD = _env_float('LIVENESS_QUALITY_THRESHOLD', 0.6)

    # ─── Face Recognition Thresholds ────────────────────────────────────────────
    # Lower value = stricter matching (more secure, may reject valid users)
    # Higher value = looser matching (less secure, may accept wrong users)
    # Recommended: 0.45-0.50 for production
    FACE_RECOGNITION_THRESHOLD = _env_float('FACE_RECOGNITION_THRESHOLD', 0.45)
    FACE_DUPLICATE_THRESHOLD = _env_float('FACE_DUPLICATE_THRESHOLD', 0.50)
    FACE_SPOOFING_THRESHOLD = _env_float('FACE_SPOOFING_THRESHOLD', 0.80)
