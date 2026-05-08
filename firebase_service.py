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
            'password_hash': user.password_hash,  # Store password hash for login
            'role': user.role,
            'department': user.department or '',
            'section': user.section or '',
            'year': user.year or '',
            'semester': user.semester or '',
            'college_id': user.college_id or '',
            'face_registered': user.face_registered,
            'face_encoding': user.face_encoding,  # Store face encoding
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
            'department': getattr(course, 'department', '') or '',
            'academic_year': getattr(course, 'academic_year', '') or '',
            'semester': getattr(course, 'semester', '') or '',
            'credits': getattr(course, 'credits', 3),
            'section': course.section or '',
            'teacher_id': course.teacher_id,
            'created_by_admin_id': getattr(course, 'created_by_admin_id', None),
            'is_active': course.is_active,
            'updated_at': course.updated_at.isoformat() if getattr(course, 'updated_at', None) else None,
            'created_at': course.created_at.isoformat() if course.created_at else None,
            'synced_at': datetime.now(timezone.utc).isoformat()
        })
        logger.info(f"✅ Course {course.id} synced to Firebase")
    except Exception as exc:
        logger.warning(f"Firebase sync_course_creation failed: {exc}")


def sync_teacher_assignment(app, assignment):
    """Sync teacher assignment to Firebase"""
    if not firebase_enabled(app):
        return
    try:
        ref = db.reference(f"teacher_assignments/{assignment.id}")
        ref.set({
            'id': assignment.id,
            'teacher_id': assignment.teacher_id,
            'course_id': assignment.course_id,
            'section': assignment.section or '',
            'assigned_by_admin_id': assignment.assigned_by_admin_id,
            'assigned_at': assignment.assigned_at.isoformat() if assignment.assigned_at else None,
            'is_active': assignment.is_active,
            'synced_at': datetime.now(timezone.utc).isoformat()
        })
        logger.info(f"✅ Teacher assignment {assignment.id} synced to Firebase")
    except Exception as exc:
        logger.warning(f"Firebase sync_teacher_assignment failed: {exc}")


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
            'section': getattr(session, 'section', '') or '',
            'teacher_id': session.teacher_id,
            'is_active': session.is_active,
            'starts_at': session.starts_at.isoformat() if session.starts_at else None,
            'ends_at': session.ends_at.isoformat() if session.ends_at else None,
            'location_lat': session.location_lat,
            'location_lng': session.location_lng,
            'location_radius_meters': getattr(session, 'location_radius_meters', None),
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


def get_user_from_firebase(app, email):
    """Get user data from Firebase Realtime Database by email"""
    if not firebase_enabled(app):
        return None
    
    try:
        # Query users by email
        ref = db.reference('users')
        users = ref.order_by_child('email').equal_to(email).get()
        
        if users:
            # Return first matching user
            user_id = list(users.keys())[0]
            user_data = users[user_id]
            user_data['id'] = int(user_id)
            return user_data
        return None
    except Exception as exc:
        logger.error(f"Firebase get_user_from_firebase failed: {exc}")
        try:
            users = db.reference('users').get() or {}
            for user_id, user_data in users.items():
                user_data = user_data or {}
                if user_data.get('email', '').strip().lower() == email.strip().lower():
                    user_data['id'] = int(user_id)
                    logger.info("Firebase get_user_from_firebase fallback scan succeeded for %s", email)
                    return user_data
        except Exception as fallback_exc:
            logger.error(f"Firebase get_user_from_firebase fallback failed: {fallback_exc}")
        return None


def sync_firebase_to_sqlite(app, user_data, db_session, User):
    """Sync Firebase user data to SQLite (create or update)"""
    try:
        user = User.query.filter_by(email=user_data['email']).first()
        
        if not user:
            # Create new user in SQLite
            user = User(
                id=user_data['id'],
                name=user_data['name'],
                email=user_data['email'],
                password_hash=user_data.get('password_hash', ''),
                role=user_data.get('role', 'student'),
                department=user_data.get('department', ''),
                college_id=user_data.get('college_id', ''),
                section=user_data.get('section', ''),
                year=user_data.get('year', ''),
                semester=user_data.get('semester', ''),
                face_registered=user_data.get('face_registered', False),
                face_encoding=user_data.get('face_encoding'),
                is_active=user_data.get('is_active', True)
            )
            db_session.add(user)
        else:
            # Update existing user
            user.name = user_data['name']
            user.role = user_data.get('role', user.role)
            user.department = user_data.get('department', user.department)
            user.college_id = user_data.get('college_id', user.college_id)
            user.section = user_data.get('section', user.section)
            user.year = user_data.get('year', user.year)
            user.semester = user_data.get('semester', user.semester)
            user.face_registered = user_data.get('face_registered', user.face_registered)
            user.is_active = user_data.get('is_active', user.is_active)
            if user_data.get('face_encoding'):
                user.face_encoding = user_data['face_encoding']
        
        db_session.commit()
        logger.info(f"✅ Synced Firebase user to SQLite: {user.email}")
        return user
    except Exception as exc:
        db_session.rollback()
        logger.error(f"Firebase sync_firebase_to_sqlite failed: {exc}")
        return None


def sync_reference_data_to_sqlite(app, db_session, User, Course, TeacherAssignment, Enrollment, ClassSession):
    """Hydrate SQLite from Firebase for ephemeral deployments like Render."""
    if not firebase_enabled(app):
        return

    def _parse_dt(value):
        if not value:
            return None
        try:
            return datetime.fromisoformat(str(value).replace('Z', '+00:00'))
        except Exception:
            return None

    try:
        users_data = db.reference('users').get() or {}
        for user_id, payload in users_data.items():
            payload = payload or {}
            existing = db_session.get(User, int(user_id))
            if not existing:
                existing = User(
                    id=int(user_id),
                    name=payload.get('name', 'Unknown'),
                    email=payload.get('email', f'{user_id}@invalid.local'),
                    department=payload.get('department', '') or 'General',
                    password_hash=payload.get('password_hash', ''),
                )
                db_session.add(existing)
            existing.name = payload.get('name', existing.name)
            existing.email = payload.get('email', existing.email)
            if payload.get('password_hash'):
                existing.password_hash = payload.get('password_hash')
            existing.role = payload.get('role', existing.role)
            existing.department = payload.get('department', existing.department)
            existing.college_id = payload.get('college_id', existing.college_id)
            existing.section = payload.get('section', existing.section)
            existing.year = payload.get('year', existing.year)
            existing.semester = payload.get('semester', existing.semester)
            existing.face_registered = payload.get('face_registered', existing.face_registered)
            if payload.get('face_encoding'):
                existing.face_encoding = payload.get('face_encoding')
            existing.is_active = payload.get('is_active', existing.is_active)

        courses_data = db.reference('courses').get() or {}
        for course_id, payload in courses_data.items():
            payload = payload or {}
            existing = db_session.get(Course, int(course_id))
            if not existing:
                existing = Course(
                    id=int(course_id),
                    code=payload.get('code', f'COURSE-{course_id}'),
                    title=payload.get('title', 'Untitled Course'),
                    department=payload.get('department', 'General'),
                    academic_year=payload.get('academic_year', 'N/A'),
                    semester=payload.get('semester', 'N/A'),
                )
                db_session.add(existing)
            existing.code = payload.get('code', existing.code)
            existing.title = payload.get('title', existing.title)
            existing.department = payload.get('department', existing.department)
            existing.academic_year = payload.get('academic_year', existing.academic_year)
            existing.semester = payload.get('semester', existing.semester)
            existing.credits = payload.get('credits', existing.credits or 3)
            existing.teacher_id = payload.get('teacher_id', existing.teacher_id)
            existing.created_by_admin_id = payload.get('created_by_admin_id', getattr(existing, 'created_by_admin_id', None))
            existing.is_active = payload.get('is_active', existing.is_active)
            created_at = _parse_dt(payload.get('created_at'))
            if created_at:
                existing.created_at = created_at

        assignments_data = db.reference('teacher_assignments').get() or {}
        for assignment_id, payload in assignments_data.items():
            payload = payload or {}
            existing = db_session.get(TeacherAssignment, int(assignment_id))
            if not existing:
                existing = TeacherAssignment(
                    id=int(assignment_id),
                    teacher_id=payload.get('teacher_id'),
                    course_id=payload.get('course_id'),
                    section=payload.get('section', ''),
                )
                db_session.add(existing)
            existing.teacher_id = payload.get('teacher_id', existing.teacher_id)
            existing.course_id = payload.get('course_id', existing.course_id)
            existing.section = payload.get('section', existing.section)
            existing.assigned_by_admin_id = payload.get('assigned_by_admin_id', existing.assigned_by_admin_id)
            existing.is_active = payload.get('is_active', existing.is_active)
            assigned_at = _parse_dt(payload.get('assigned_at'))
            if assigned_at:
                existing.assigned_at = assigned_at

        enrollments_data = db.reference('enrollments').get() or {}
        for student_id, course_map in enrollments_data.items():
            for course_id, payload in (course_map or {}).items():
                payload = payload or {}
                existing = None
                if payload.get('enrollment_id'):
                    existing = db_session.get(Enrollment, int(payload['enrollment_id']))
                if not existing:
                    existing = Enrollment.query.filter_by(student_id=int(student_id), course_id=int(course_id)).first()
                if not existing:
                    existing = Enrollment(
                        id=int(payload['enrollment_id']) if payload.get('enrollment_id') else None,
                        student_id=int(student_id),
                        course_id=int(course_id),
                    )
                    db_session.add(existing)
                existing.student_id = int(student_id)
                existing.course_id = int(course_id)
                existing.is_active = payload.get('is_active', existing.is_active)
                enrolled_at = _parse_dt(payload.get('enrolled_at'))
                if enrolled_at:
                    existing.enrolled_at = enrolled_at

        sessions_data = db.reference('sessions').get() or {}
        for session_id, payload in sessions_data.items():
            payload = payload or {}
            existing = db_session.get(ClassSession, int(session_id))
            if not existing:
                existing = ClassSession(
                    id=int(session_id),
                    title=payload.get('title', 'Untitled Session'),
                    course_code=payload.get('course_code', ''),
                    room=payload.get('room', ''),
                    starts_at=_parse_dt(payload.get('starts_at')) or datetime.now(timezone.utc),
                    ends_at=_parse_dt(payload.get('ends_at')) or datetime.now(timezone.utc),
                    teacher_id=payload.get('teacher_id'),
                )
                db_session.add(existing)
            existing.course_id = payload.get('course_id', existing.course_id)
            existing.course_code = payload.get('course_code', existing.course_code)
            existing.title = payload.get('title', existing.title)
            existing.room = payload.get('room', existing.room)
            existing.section = payload.get('section', getattr(existing, 'section', None))
            existing.teacher_id = payload.get('teacher_id', existing.teacher_id)
            existing.is_active = payload.get('is_active', existing.is_active)
            starts_at = _parse_dt(payload.get('starts_at'))
            ends_at = _parse_dt(payload.get('ends_at'))
            if starts_at:
                existing.starts_at = starts_at
            if ends_at:
                existing.ends_at = ends_at
            existing.location_lat = payload.get('location_lat', existing.location_lat)
            existing.location_lng = payload.get('location_lng', existing.location_lng)
            if payload.get('location_radius_meters') is not None:
                existing.location_radius_meters = payload.get('location_radius_meters')

        db_session.commit()
        logger.info("✅ Firebase reference data synced to SQLite")
    except Exception as exc:
        db_session.rollback()
        logger.error(f"Firebase sync_reference_data_to_sqlite failed: {exc}")

