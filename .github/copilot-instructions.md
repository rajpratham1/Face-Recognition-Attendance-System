# GitHub Copilot Instructions - Face Recognition Attendance System

## Project Context
This is an **Academic Face Recognition Attendance System** for Invertis University, built with Flask (Python) backend and vanilla JavaScript frontend with face-api.js for biometric verification.

## Architecture Overview
- **Backend**: Flask (Python 3.9+) with SQLAlchemy ORM
- **Frontend**: Jinja2 templates + Bootstrap 5 + face-api.js
- **Database**: SQLite (dev) / PostgreSQL (production)
- **Authentication**: Flask-Login with role-based access control
- **Face Recognition**: face-api.js (client-side) with 128-D face descriptors
- **Security**: CSRF protection, rate limiting, geofencing, device fingerprinting

## Key Design Patterns

### 1. Role-Based Architecture
```python
# Three distinct user roles with different workflows:
- Admin: System-wide management and analytics
- Teacher: Course creation, session management, attendance reports
- Student: Face registration, session attendance marking
```

### 2. Dual Attendance Models (IMPORTANT)
```python
# Attendance (Legacy) - Generic daily check-in for staff/teachers
class Attendance:
    user_id, date, time, status, latitude, longitude

# SessionAttendance (Primary) - Class session-based for students
class SessionAttendance:
    session_id, student_id, marked_at, face_distance, device_hash, ip_address
    
# AttendanceAttempt - Fraud detection audit log
class AttendanceAttempt:
    session_id, student_id, success, reason, latitude, longitude, face_distance
```

### 3. Security-First Approach
- All face verification happens client-side (privacy)
- Server validates face distance threshold (< 0.6)
- Geofencing enforced (100m radius from Invertis University)
- Rate limiting on all auth and attendance endpoints
- Device fingerprinting to track duplicate attempts
- CSRF tokens on all forms

## Coding Standards

### Python (Backend)
```python
# Follow these conventions:
- Use type hints for function parameters and returns
- All database queries should use SQLAlchemy ORM (no raw SQL unless necessary)
- UTC timestamps in database, convert to Asia/Kolkata for display
- Error handling: try-except with flash messages for user-facing errors
- Rate limiting: Use @limiter.limit() decorator on sensitive endpoints
- Validation: Check user role, enrollment status, session active status before operations
```

### JavaScript (Frontend)
```javascript
// Follow these conventions:
- Use async/await for face-api.js operations
- Always check face detection before sending to server
- Use fetch() with CSRF token from window.getCsrfToken()
- Handle camera permissions gracefully with user-friendly errors
- Implement proper loading states during face processing
```

### Database Migrations
```bash
# Always use Flask-Migrate for schema changes:
flask db migrate -m "descriptive message"
flask db upgrade
# Never modify models.py without creating migration
```

## Common Patterns to Follow

### 1. Creating New Routes
```python
@app.route("/teacher/new-feature", methods=["GET", "POST"])
@login_required
@limiter.limit("20 per hour")  # Add rate limiting
def new_feature():
    # 1. Check user role
    if current_user.role != "teacher":
        flash("Access denied", "danger")
        return redirect(url_for("dashboard"))
    
    # 2. Handle POST request
    if request.method == "POST":
        # Validate CSRF (automatic with Flask-WTF)
        # Validate input
        # Perform operation
        # Flash success message
        # Redirect
        pass
    
    # 3. Render template with context
    return render_template("new_feature.html")
```

### 2. Face Verification Pattern
```javascript
// Client-side face verification template
const detections = await faceapi.detectAllFaces(video)
    .withFaceLandmarks()
    .withFaceDescriptors();

// Check for single face
if (!detections || detections.length !== 1) {
    statusText.innerText = 'Exactly one face required';
    return;
}

// Send to server
const response = await fetch('/api/endpoint', {
    method: 'POST',
    headers: {
        'Content-Type': 'application/json',
        'X-CSRFToken': csrfToken
    },
    body: JSON.stringify({
        descriptor: Array.from(detections[0].descriptor),
        lat: userCoords.lat,
        lng: userCoords.lng,
        device_id: deviceId
    })
});
```

### 3. Attendance Recording Pattern
```python
def record_attendance_with_fraud_check(session_id, student_id, descriptor, lat, lng, device_hash):
    # 1. Validate session is active
    session = ClassSession.query.filter_by(id=session_id).first()
    if not session or not session.is_active:
        record_attempt(session_id, student_id, False, "Session inactive", lat, lng)
        return {"success": False, "message": "Session not active"}
    
    # 2. Check geofencing
    if not is_within_invertis(lat, lng):
        record_attempt(session_id, student_id, False, "Outside campus", lat, lng)
        return {"success": False, "message": "Outside campus boundary"}
    
    # 3. Check duplicate
    if SessionAttendance.query.filter_by(session_id=session_id, student_id=student_id).first():
        record_attempt(session_id, student_id, False, "Duplicate", lat, lng)
        return {"success": False, "message": "Already marked"}
    
    # 4. Verify face
    known = np.array(json.loads(student.face_encoding))
    unknown = np.array(descriptor)
    distance = float(np.linalg.norm(known - unknown))
    
    if distance >= 0.6:
        record_attempt(session_id, student_id, False, "Face mismatch", lat, lng, distance, device_hash)
        return {"success": False, "message": "Face verification failed"}
    
    # 5. Record attendance
    attendance = SessionAttendance(...)
    db.session.add(attendance)
    record_attempt(session_id, student_id, True, "Success", lat, lng, distance, device_hash)
    db.session.commit()
    
    return {"success": True}
```

## File Organization Rules

### Templates Structure
```
templates/
├── base.html                    # Base layout with navbar, imports
├── index.html                   # Landing page
├── login.html / register.html   # Auth pages
├── register_face.html           # Face registration flow
├── mark_attendance.html         # Generic attendance (teachers)
├── student_mark_attendance.html # Session attendance (students)
├── student_dashboard.html       # Student view
├── teacher_dashboard.html       # Teacher view
├── admin_dashboard.html         # Admin view
└── user_dashboard.html          # Generic user view
```

### Routes Naming Convention
```python
# Public routes
@app.route("/")               # Landing page
@app.route("/register")       # User registration
@app.route("/login")          # Login

# Student routes
@app.route("/mark_attendance")                    # Session attendance UI
@app.route("/api/session_attendance/mark")        # Session attendance API
@app.route("/api/active_sessions")                # Get active sessions

# Teacher routes
@app.route("/teacher/courses/create")             # Create course
@app.route("/teacher/courses/<id>/enroll")        # Enroll student
@app.route("/teacher/sessions/create")            # Create session
@app.route("/teacher/sessions/<id>/close")        # Close session

# Admin routes
@app.route("/admin/users")                        # User management
@app.route("/admin/analytics")                    # System analytics

# Common
@app.route("/dashboard")       # Role-based dashboard dispatcher
@app.route("/logout")          # Logout
```

## Important Constraints

### Geofencing
```python
# Invertis University, Bareilly, UP
INVERTIS_LAT = 28.325764684367748
INVERTIS_LNG = 79.46097110207619
ALLOWED_RADIUS_METERS = 100

# When adding new locations, consider multi-location support
# Future: Store locations in database, not config
```

### Face Recognition Thresholds
```python
# Current threshold for face matching
FACE_MATCH_THRESHOLD = 0.6  # Euclidean distance

# Tips for Copilot:
# - Lower threshold (e.g., 0.4) = stricter, fewer false positives
# - Higher threshold (e.g., 0.7) = lenient, more false positives
# - Current 0.6 is industry standard for face-api.js
```

### Timezone Handling
```python
# ALWAYS use UTC in database
# Convert to Asia/Kolkata for display using filters:
{{ timestamp|localdtfmt('%d %b %Y %I:%M %p') }}

# In Python:
from datetime import timezone
from zoneinfo import ZoneInfo

now_utc = datetime.now(timezone.utc).replace(tzinfo=None)  # For DB
now_local = datetime.now(ZoneInfo("Asia/Kolkata"))         # For display
```

## Testing Guidelines

### When Adding Features
```python
# 1. Unit test the core logic
def test_face_distance_calculation():
    known = np.random.rand(128)
    unknown = known + 0.01  # Similar face
    distance = float(np.linalg.norm(known - unknown))
    assert distance < 0.6

# 2. Integration test the endpoint
def test_mark_attendance_endpoint(client, auth_student, active_session):
    response = client.post('/api/session_attendance/mark', json={
        'session_id': active_session.id,
        'descriptor': [0.1] * 128,
        'lat': 28.325764684367748,
        'lng': 79.46097110207619
    })
    assert response.status_code == 200

# 3. Security test
def test_attendance_outside_campus(client, auth_student):
    response = client.post('/api/session_attendance/mark', json={
        'lat': 0.0,  # Not in Invertis
        'lng': 0.0
    })
    assert response.status_code == 400
    assert b'campus' in response.data
```

## Common Pitfalls to Avoid

### ❌ Don't Do This
```python
# Don't store face images/videos
user.face_image = image_bytes  # PRIVACY VIOLATION

# Don't use synchronous face detection on server
face = face_recognition.compare_faces(...)  # SERVER-SIDE PROCESSING

# Don't hardcode credentials
FIREBASE_KEY = "AIzaSyABC123..."  # USE ENVIRONMENT VARIABLES

# Don't skip enrollment check
SessionAttendance(session_id=s, student_id=u)  # CHECK IF ENROLLED FIRST

# Don't use raw SQL without parameterization
db.execute(f"SELECT * FROM users WHERE email = '{email}'")  # SQL INJECTION
```

### ✅ Do This
```python
# Store only face descriptors (128 floats)
user.face_encoding = json.dumps(descriptor)  # PRIVACY-SAFE

# Use client-side face detection
// JavaScript: faceapi.detectSingleFace(video)

# Use environment variables
FIREBASE_KEY = os.environ.get('FIREBASE_API_KEY')

# Always validate enrollment
enrolled = Enrollment.query.filter_by(course_id=c.id, student_id=u.id).first()
if not enrolled:
    return error_response("Not enrolled")

# Use SQLAlchemy ORM
User.query.filter_by(email=email).first()  # PARAMETERIZED
```

## Firebase Integration Notes

```python
# Firebase is OPTIONAL for cloud sync/audit
# System works without it (local SQLite storage)

# When implementing Firebase features:
if firebase_enabled(app):
    sync_session_attendance(app, entry, session, student)
# Always wrap in conditional - never break app if Firebase down
```

## Performance Considerations

```python
# Face processing is CPU-intensive on client
# Tips for optimization:
- Use detectSingleFace() instead of detectAllFaces() when possible
- Set detectionParams for faster processing
- Implement throttling for real-time face detection
- Cache face descriptors after successful registration

# Database optimization:
- Use indexes on foreign keys (already set in models)
- Use .first() instead of .all()[0]
- Use join queries instead of N+1 queries
- Implement pagination for large datasets (TODO)
```

## When Generating Code...

### For New Features
1. **Check role authorization** - Who can access this?
2. **Add rate limiting** - Prevent abuse
3. **Validate all inputs** - Never trust user input
4. **Handle edge cases** - What if session ended? Student not enrolled?
5. **Add flash messages** - Give user feedback
6. **Log security events** - Use AttendanceAttempt pattern
7. **Update documentation** - Add to this file if needed

### For Bug Fixes
1. **Understand root cause** - Don't patch symptoms
2. **Check if it affects other roles** - Student/Teacher/Admin
3. **Add test case** - Prevent regression
4. **Consider backward compatibility** - Existing data structure
5. **Update migration if needed** - Schema changes require migration

### For Refactoring
1. **Maintain API contracts** - Don't break frontend
2. **Test thoroughly** - All three dashboards
3. **Update type hints** - Keep code documented
4. **Check Firebase sync** - If modifying attendance models
5. **Update rate limits** - If changing request patterns

## Quick Reference

### Environment Variables Required
```bash
SECRET_KEY=            # Flask secret key (required in production)
DATABASE_URL=          # PostgreSQL URL (optional, defaults to SQLite)
APP_TIMEZONE=          # Timezone (default: Asia/Kolkata)
FIREBASE_PROJECT_ID=   # Firebase project ID (optional)
FIREBASE_DATABASE_URL= # Firebase Realtime DB URL (optional)
FIREBASE_SERVICE_ACCOUNT_PATH=  # Path to service account JSON (optional)
FIREBASE_API_KEY=      # Firebase Web API key (optional)
```

### Face-api.js Model Files
```javascript
// Required models (loaded from CDN):
1. ssdMobilenetv1 - Face detection
2. faceLandmark68Net - Facial landmark detection
3. faceRecognitionNet - Face descriptor extraction (128-D)

// Fallback strategy recommended:
- Host models locally in /static/models/
- Add CDN fallback in templates
```

### Database Schema Quick Ref
```
users (id, name, email, department, password_hash, role, face_encoding, face_registered)
  ├─ attendances (daily check-in - legacy)
  ├─ session_attendances (class attendance - primary)
  ├─ attendance_attempts (audit log)
  ├─ enrollments (course enrollment)
  └─ created_sessions (if teacher)

courses (id, code, title, section, teacher_id)
  ├─ enrollments
  └─ class_sessions

class_sessions (id, title, course_code, room, course_id, starts_at, ends_at, is_active, teacher_id)
  └─ session_attendances

enrollments (id, course_id, student_id)

attendance_attempts (id, session_id, student_id, success, reason, latitude, longitude, face_distance, device_hash, ip_address, user_agent, created_at)
```

## AI Assistant Specific Guidance

When I (GitHub Copilot) am asked to:

- **Add a feature**: Follow the route creation pattern, check role authorization
- **Fix a bug**: Identify which role is affected, check both frontend and backend
- **Optimize code**: Focus on database queries and face detection performance
- **Add security**: Use the AttendanceAttempt logging pattern
- **Write tests**: Cover happy path + edge cases + security scenarios
- **Generate SQL**: Use SQLAlchemy ORM, not raw SQL
- **Handle dates**: Use UTC in DB, convert to Asia/Kolkata for display
- **Process faces**: Keep processing client-side, validate distance server-side

## Project-Specific Vocabulary

- **Session**: Class session (not Flask session)
- **Mark attendance**: Record attendance for a session
- **Live session**: Currently active class session (between starts_at and ends_at)
- **Geofence**: Geographic boundary check (100m from Invertis)
- **Face distance**: Euclidean distance between face descriptors
- **Descriptor**: 128-dimensional face encoding vector
- **Enrollment**: Student registered for a course
- **Device hash**: SHA-256 hash of device identifier (fraud prevention)
- **Attendance attempt**: Audit log entry (successful or failed)

---

**Last Updated**: February 19, 2026  
**Project Version**: 1.0.0  
**Maintainer**: IIOT Group Project Team
