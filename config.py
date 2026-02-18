import os

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY')
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL', 'sqlite:///attendance.db')
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    APP_TIMEZONE = os.environ.get('APP_TIMEZONE', 'Asia/Kolkata')
    FLASK_ENV = os.environ.get('FLASK_ENV', 'production')
    DEBUG = FLASK_ENV == 'development'

    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = 'Lax'
    SESSION_COOKIE_SECURE = os.environ.get('SESSION_COOKIE_SECURE', '0') == '1'
    REMEMBER_COOKIE_HTTPONLY = True
    REMEMBER_COOKIE_SAMESITE = 'Lax'
    REMEMBER_COOKIE_SECURE = os.environ.get('SESSION_COOKIE_SECURE', '0') == '1'
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

    # Invertis University, Bareilly, UP coordinates (User Updated)
    INVERTIS_LAT = 28.325764684367748
    INVERTIS_LNG = 79.46097110207619
    ALLOWED_RADIUS_METERS = 100  # 100 meters radius as requested
