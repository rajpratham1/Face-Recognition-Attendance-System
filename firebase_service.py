import json
import logging
from datetime import datetime, timezone

try:
    import firebase_admin
    from firebase_admin import credentials, db, auth
    FIREBASE_AVAILABLE = True
except ImportError:
    firebase_admin = None
    credentials = None
    db = None
    auth = None
    FIREBASE_AVAILABLE = False

logger = logging.getLogger(__name__)


def init_firebase(app):
    """Initialize Firebase with enhanced error handling"""
    app.extensions['firebase_enabled'] = False
    app.extensions['firebase_error'] = ''

    if not FIREBASE_AVAILABLE:
        app.extensions['firebase_error'] = 'firebase-admin package not installed. Run: pip install firebase-admin'
        logger.warning("Firebase not available: firebase-admin not installed")
        return

    database_url = app.config.get('FIREBASE_DATABASE_URL', '')
    if not database_url:
        app.extensions['firebase_error'] = 'FIREBASE_DATABASE_URL missing in .env file'
        logger.warning("Firebase not configured: DATABASE_URL missing")
        return

    cred_obj = None
    service_path = app.config.get('FIREBASE_SERVICE_ACCOUNT_PATH', '').strip()
    
    # Build service account from environment variables
    project_id = app.config.get('FIREBASE_PROJECT_ID', '').strip()
    private_key = app.config.get('FIREBASE_PRIVATE_KEY', '').strip()
    client_email = app.config.get('FIREBASE_CLIENT_EMAIL', '').strip()

    try:
        if service_path:
            cred_obj = credentials.Certificate(service_path)
            logger.info("Firebase: Using service account file")
        elif project_id and private_key and client_email:
            # Build service account from env variables
            service_account_info = {
                "type": "service_account",
                "project_id": project_id,
                "private_key": private_key.replace('\\n', '\n'),
                "client_email": client_email,
                "token_uri": "https://oauth2.googleapis.com/token",
            }
            cred_obj = credentials.Certificate(service_account_info)
            logger.info("Firebase: Using service account from environment variables")
        else:
            app.extensions['firebase_error'] = 'Firebase service account credentials missing'
            logger.warning("Firebase: No valid credentials found")
            return

        if not firebase_admin._apps:
            firebase_admin.initialize_app(cred_obj, {'databaseURL': database_url})
            logger.info(f"Firebase initialized successfully: {database_url}")
        
        app.extensions['firebase_enabled'] = True
        logger.info("✅ Firebase Real-time Database connected!")
        
    except Exception as exc:
        app.extensions['firebase_error'] = str(exc)
        logger.error(f"Firebase initialization failed: {exc}")


def firebase_enabled(app):
    """Check if Firebase is enabled"""
    return bool(app.extensions.get('firebase_enabled'))


def get_firebase_status(app):
    """Get Firebase connection status"""
    return {
        'enabled': firebase_enabled(app),
        'error': app.extensions.get('firebase_error', ''),
        'available': FIREBASE_AVAILABLE
    }


# ═══════════════════════════════════════════════════════════════════════════
# SYNC FUNCTIONS - Sync SQLite data to Firebase
# ═══════════════════════════════════════════════════════════════════════════

def sync_user_registration(app, user):
    """Sync user registration to Firebase"""
    if not firebase_enabled(app):
        return
    try:
        ref = db.reference(f"users/{user.id}")
        ref.set({
            'id': user.id,
            'name': user.name,
            'email': user.email,
            'role': user.role,
            'department': user.department or '',
            'section': user.section or '',
            'year': user.year or '',
            'semester': user.semester or '',
            'college_id': user.college_id or '',
            'face_registered': user.face_registered,
            'is_active': user.is_active,
            'registered_at': user.registered_at.isoformat() if user.registered_at else None,
            'synced_at': datetime.now(timezone.utc).isoformat()
        })
        logger.info(f"✅ User {user.id} synced to Firebase")
    except Exception as exc:
        logger.warning(f"Firebase sync_user_registration failed: {exc}")


def sync_course_creation(app, course):
    """Sync course creation to Firebase"""
    if not firebase_enabled(app):
        return
    try:
        ref = db.reference(f"courses/{course.id}")
        ref.set({
            'id': course.id,
            'code': course.code,
            'title': course.title,
            'section': course.section or '',
            'teacher_id': course.teacher_id,
            'is_active': course.is_active,
            'created_at': course.created_at.isoformat() if course.created_at else None,
            'synced_at': datetime.now(timezone.utc).isoformat()
        })
        logger.info(f"✅ Course {course.id} synced to Firebase")
    except Exception as exc:
        logger.warning(f"Firebase sync_course_creation failed: {exc}")


def sync_session_creation(app, session):
    """Sync class session creation to Firebase"""
    if not firebase_enabled(app):
        return
    try:
        ref = db.reference(f"sessions/{session.id}")
        ref.set({
            'id': session.id,
            'course_id': session.course_id,
            'course_code': session.course_code,
            'title': session.title,
            'room': session.room or '',
            'teacher_id': session.teacher_id,
            'is_active': session.is_active,
            'starts_at': session.starts_at.isoformat() if session.starts_at else None,
            'ends_at': session.ends_at.isoformat() if session.ends_at else None,
            'location_lat': session.location_lat,
            'location_lng': session.location_lng,
            'created_at': session.created_at.isoformat() if session.created_at else None,
            'synced_at': datetime.now(timezone.utc).isoformat()
        })
        logger.info(f"✅ Session {session.id} synced to Firebase")
    except Exception as exc:
        logger.warning(f"Firebase sync_session_creation failed: {exc}")


def sync_session_attendance(app, entry, session, student):
    """Sync attendance marking to Firebase"""
    if not firebase_enabled(app):
        return
    try:
        # Sync to student's attendance record
        ref = db.reference(f"attendance/students/{student.id}/{session.id}")
        ref.set({
            'studentId': student.id,
            'studentName': student.name,
            'studentEmail': student.email,
            'courseCode': session.course_code,
            'courseTitle': session.title,
            'sessionId': session.id,
            'room': session.room or '',
            'markedAt': entry.marked_at.isoformat() if entry.marked_at else datetime.now(timezone.utc).isoformat(),
            'latitude': entry.latitude,
            'longitude': entry.longitude,
            'faceDistance': entry.face_distance,
            'deviceHash': entry.device_hash or '',
            'synced_at': datetime.now(timezone.utc).isoformat()
        })
        
        # Also sync to session's attendance list
        session_ref = db.reference(f"attendance/sessions/{session.id}/{student.id}")
        session_ref.set({
            'studentId': student.id,
            'studentName': student.name,
            'markedAt': entry.marked_at.isoformat() if entry.marked_at else datetime.now(timezone.utc).isoformat(),
            'faceDistance': entry.face_distance,
            'synced_at': datetime.now(timezone.utc).isoformat()
        })
        
        logger.info(f"✅ Attendance synced: Student {student.id} → Session {session.id}")
    except Exception as exc:
        logger.warning(f"Firebase sync_session_attendance failed: {exc}")


def sync_attendance_attempt(app, payload):
    """Sync attendance attempt (success/failure) to Firebase"""
    if not firebase_enabled(app):
        return
    try:
        day_key = datetime.now(timezone.utc).strftime('%Y-%m-%d')
        ref = db.reference(f"attendance_attempts/{day_key}")
        attempt_ref = ref.push(payload)
        logger.info(f"✅ Attendance attempt logged to Firebase: {attempt_ref.key}")
    except Exception as exc:
        logger.warning(f"Firebase sync_attendance_attempt failed: {exc}")


def sync_enrollment(app, enrollment):
    """Sync student enrollment to Firebase"""
    if not firebase_enabled(app):
        return
    try:
        ref = db.reference(f"enrollments/{enrollment.student_id}/{enrollment.course_id}")
        ref.set({
            'enrollment_id': enrollment.id,
            'student_id': enrollment.student_id,
            'course_id': enrollment.course_id,
            'is_active': enrollment.is_active,
            'enrolled_at': enrollment.enrolled_at.isoformat() if enrollment.enrolled_at else None,
            'synced_at': datetime.now(timezone.utc).isoformat()
        })
        logger.info(f"✅ Enrollment synced: Student {enrollment.student_id} → Course {enrollment.course_id}")
    except Exception as exc:
        logger.warning(f"Firebase sync_enrollment failed: {exc}")


def update_session_status(app, session_id, is_active):
    """Update session active status in Firebase"""
    if not firebase_enabled(app):
        return
    try:
        ref = db.reference(f"sessions/{session_id}/is_active")
        ref.set(is_active)
        logger.info(f"✅ Session {session_id} status updated: {is_active}")
    except Exception as exc:
        logger.warning(f"Firebase update_session_status failed: {exc}")


def get_live_attendance_count(app, session_id):
    """Get real-time attendance count from Firebase"""
    if not firebase_enabled(app):
        return 0
    try:
        ref = db.reference(f"attendance/sessions/{session_id}")
        data = ref.get()
        return len(data) if data else 0
    except Exception as exc:
        logger.warning(f"Firebase get_live_attendance_count failed: {exc}")
        return 0


def get_student_attendance_summary(app, student_id):
    """Get student's attendance summary from Firebase"""
    if not firebase_enabled(app):
        return {}
    try:
        ref = db.reference(f"attendance/students/{student_id}")
        data = ref.get()
        return data if data else {}
    except Exception as exc:
        logger.warning(f"Firebase get_student_attendance_summary failed: {exc}")
        return {}



# ═══════════════════════════════════════════════════════════════════════════
# FIREBASE AUTHENTICATION FUNCTIONS
# ═══════════════════════════════════════════════════════════════════════════

def create_firebase_user(app, email, password, name, user_id):
    """Create a Firebase Authentication user"""
    if not firebase_enabled(app):
        logger.warning("Firebase not enabled, skipping user creation")
        return None
    
    try:
        # Create Firebase Auth user
        firebase_user = auth.create_user(
            uid=str(user_id),  # Use SQLite user ID as Firebase UID
            email=email,
            password=password,
            display_name=name,
            email_verified=False
        )
        logger.info(f"✅ Firebase Auth user created: {email} (UID: {firebase_user.uid})")
        return firebase_user.uid
    except auth.EmailAlreadyExistsError:
        logger.warning(f"Firebase Auth: Email already exists: {email}")
        return None
    except Exception as exc:
        logger.error(f"Firebase create_user failed: {exc}")
        return None


def verify_firebase_user(app, email, password):
    """Verify user credentials using Firebase Authentication
    Note: Firebase Admin SDK doesn't support password verification directly.
    This function checks if user exists in Firebase Auth.
    For actual password verification, we'll use custom tokens or REST API.
    """
    if not firebase_enabled(app):
        return None
    
    try:
        # Get user by email
        firebase_user = auth.get_user_by_email(email)
        logger.info(f"✅ Firebase user found: {email}")
        return firebase_user.uid
    except auth.UserNotFoundError:
        logger.warning(f"Firebase Auth: User not found: {email}")
        return None
    except Exception as exc:
        logger.error(f"Firebase verify_user failed: {exc}")
        return None


def create_custom_token(app, user_id):
    """Create a custom Firebase token for a user"""
    if not firebase_enabled(app):
        return None
    
    try:
        custom_token = auth.create_custom_token(str(user_id))
        logger.info(f"✅ Custom token created for user: {user_id}")
        return custom_token.decode('utf-8')
    except Exception as exc:
        logger.error(f"Firebase create_custom_token failed: {exc}")
        return None


def update_firebase_user(app, user_id, **kwargs):
    """Update Firebase Authentication user"""
    if not firebase_enabled(app):
        return False
    
    try:
        auth.update_user(str(user_id), **kwargs)
        logger.info(f"✅ Firebase Auth user updated: {user_id}")
        return True
    except Exception as exc:
        logger.error(f"Firebase update_user failed: {exc}")
        return False


def delete_firebase_user(app, user_id):
    """Delete Firebase Authentication user"""
    if not firebase_enabled(app):
        return False
    
    try:
        auth.delete_user(str(user_id))
        logger.info(f"✅ Firebase Auth user deleted: {user_id}")
        return True
    except Exception as exc:
        logger.error(f"Firebase delete_user failed: {exc}")
        return False


def get_firebase_user(app, user_id):
    """Get Firebase Authentication user by ID"""
    if not firebase_enabled(app):
        return None
    
    try:
        firebase_user = auth.get_user(str(user_id))
        return {
            'uid': firebase_user.uid,
            'email': firebase_user.email,
            'display_name': firebase_user.display_name,
            'email_verified': firebase_user.email_verified,
            'disabled': firebase_user.disabled
        }
    except Exception as exc:
        logger.error(f"Firebase get_user failed: {exc}")
        return None


def verify_firebase_token(app, id_token):
    """Verify Firebase ID token"""
    if not firebase_enabled(app):
        return None
    
    try:
        decoded_token = auth.verify_id_token(id_token)
        return decoded_token
    except Exception as exc:
        logger.error(f"Firebase verify_token failed: {exc}")
        return None
