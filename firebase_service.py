import json
from datetime import datetime, timezone

try:
    import firebase_admin
    from firebase_admin import credentials, db
except ImportError:
    firebase_admin = None
    credentials = None
    db = None


def init_firebase(app):
    app.extensions['firebase_enabled'] = False
    app.extensions['firebase_error'] = ''

    if not firebase_admin:
        app.extensions['firebase_error'] = 'firebase-admin package not installed'
        return

    database_url = app.config.get('FIREBASE_DATABASE_URL', '')
    if not database_url:
        app.extensions['firebase_error'] = 'FIREBASE_DATABASE_URL missing'
        return

    cred_obj = None
    service_path = app.config.get('FIREBASE_SERVICE_ACCOUNT_PATH', '').strip()
    service_json = app.config.get('FIREBASE_SERVICE_ACCOUNT_JSON', '').strip()

    try:
        if service_path:
            cred_obj = credentials.Certificate(service_path)
        elif service_json:
            cred_obj = credentials.Certificate(json.loads(service_json))
        else:
            app.extensions['firebase_error'] = 'service account missing'
            return

        if not firebase_admin._apps:
            firebase_admin.initialize_app(cred_obj, {'databaseURL': database_url})
        app.extensions['firebase_enabled'] = True
    except Exception as exc:
        app.extensions['firebase_error'] = str(exc)


def firebase_enabled(app):
    return bool(app.extensions.get('firebase_enabled'))


def sync_session_attendance(app, entry, session, student):
    if not firebase_enabled(app):
        return
    try:
        ref = db.reference(f"attendance/{student.id}/{session.id}")
        ref.set({
            'studentId': student.id,
            'studentName': student.name,
            'courseCode': session.course_code,
            'sessionTitle': session.title,
            'sessionId': session.id,
            'room': session.room,
            'markedAt': datetime.now(timezone.utc).isoformat(),
            'latitude': entry.latitude,
            'longitude': entry.longitude,
            'faceDistance': entry.face_distance,
            'deviceHash': entry.device_hash,
        })
    except Exception:
        return


def sync_attendance_attempt(app, payload):
    if not firebase_enabled(app):
        return
    try:
        day_key = datetime.now(timezone.utc).strftime('%Y-%m-%d')
        ref = db.reference(f"attendance_attempts/{day_key}")
        ref.push(payload)
    except Exception:
        return
