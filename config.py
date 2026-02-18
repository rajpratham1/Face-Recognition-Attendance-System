import os

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY', 'invertis-face-attendance-secret-2024')
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL', 'sqlite:///attendance.db')
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # Invertis University, Bareilly, UP coordinates
    INVERTIS_LAT = 28.325764684367748
    INVERTIS_LNG = 79.46097110207619
    ALLOWED_RADIUS_METERS = 100  # 1 km radius around campus
