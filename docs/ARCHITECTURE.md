# System Architecture Documentation

## Table of Contents

- [System Overview](#system-overview)
- [Architecture Pattern](#architecture-pattern)
- [Component Diagram](#component-diagram)
- [Database Schema](#database-schema)
- [Security Architecture](#security-architecture)
- [Data Flow](#data-flow)
- [Technology Stack](#technology-stack)
- [Deployment Architecture](#deployment-architecture)

---

## System Overview

The Face Recognition Attendance System is a web-based biometric attendance solution built on a **three-tier architecture** with client-side face processing for privacy and security.

### High-Level Architecture

```
┌───────────────────────────────────────────────────────────────┐
│                     Presentation Layer                        │
│  ┌─────────────┐  ┌─────────────┐  ┌──────────────┐         │
│  │  HTML/CSS   │  │  JavaScript │  │  face-api.js │         │
│  │  Bootstrap  │  │   (ES6+)    │  │  (biometric) │         │
│  └─────────────┘  └─────────────┘  └──────────────┘         │
└───────────────────────────────────────────────────────────────┘
                            ▲ HTTP/HTTPS
                            │
┌───────────────────────────▼───────────────────────────────────┐
│                     Application Layer                         │
│  ┌──────────────────────────────────────────────────────┐    │
│  │              Flask Web Framework                     │    │
│  │  ┌────────┐  ┌─────────┐  ┌──────────┐  ┌────────┐ │    │
│  │  │ Routes │  │  Auth   │  │ Business │  │ Utils  │ │    │
│  │  │Handler │  │ Manager │  │  Logic   │  │Helpers │ │    │
│  │  └────────┘  └─────────┘  └──────────┘  └────────┘ │    │
│  └──────────────────────────────────────────────────────┘    │
│                                                                │
│  ┌──────────────────────────────────────────────────────┐    │
│  │           Security & Middleware Layer                 │    │
│  │  [CSRF Protection][Rate Limiter][Role Validator]     │    │
│  └──────────────────────────────────────────────────────┘    │
└────────────────────────────────────────────────────────────────┘
                            ▲ ORM (SQLAlchemy)
                            │
┌───────────────────────────▼───────────────────────────────────┐
│                       Data Layer                              │
│  ┌────────────────┐           ┌───────────────────────┐      │
│  │  SQLite/       │           │  Firebase Realtime    │      │
│  │  PostgreSQL    │           │  Database (Optional)  │      │
│  │  (Primary)     │           │  (Audit/Cloud Sync)   │      │
│  └────────────────┘           └───────────────────────┘      │
└───────────────────────────────────────────────────────────────┘
```

---

## Architecture Pattern

### Model-View-Controller (MVC) Pattern

#### Model (`models.py`)
- **User**: User accounts (students, teachers, admins)
- **Course**: Academic courses with sections
- **Enrollment**: Student-course relationships
- **ClassSession**: Live class sessions
- **SessionAttendance**: Attendance records per session
- **Attendance**: Legacy daily attendance (teachers)
- **AttendanceAttempt**: Audit log for fraud detection

#### View (`templates/`)
- Jinja2 templates for server-side rendering
- Role-specific dashboards:
  - `student_dashboard.html`
  - `teacher_dashboard.html`
  - `admin_dashboard.html`
- Attendance interfaces:
  - `register_face.html`
  - `student_mark_attendance.html`

#### Controller (`app.py`)
- Route handlers for HTTP requests
- Business logic for attendance processing
- Authentication and authorization
- API endpoints for AJAX requests

---

## Component Diagram

### Detailed Component Structure

```
┌─────────────────────────────────────────────────────────────┐
│                     Browser (Client)                        │
│                                                              │
│  ┌──────────────────────────────────────────────────────┐  │
│  │               User Interface Components               │  │
│  │                                                        │  │
│  │  ┌──────────┐  ┌──────────┐  ┌──────────┐           │  │
│  │  │ Camera   │  │ Location │  │ Form     │           │  │
│  │  │ Capture  │  │ Service  │  │ Handler  │           │  │
│  │  └──────────┘  └──────────┘  └──────────┘           │  │
│  └──────────────────────────────────────────────────────┘  │
│                                                              │
│  ┌──────────────────────────────────────────────────────┐  │
│  │            Face Recognition Module                    │  │
│  │                                                        │  │
│  │  ┌────────────────┐  ┌────────────────────────┐     │  │
│  │  │ Face Detection │  │ Descriptor Extraction  │     │  │
│  │  │ (SSD MobileNet)│  │ (FaceRecognitionNet)   │     │  │
│  │  └────────────────┘  └────────────────────────┘     │  │
│  │                                                        │  │
│  │  ┌────────────────┐                                   │  │
│  │  │ Landmark       │                                   │  │
│  │  │ Detection      │                                   │  │
│  │  └────────────────┘                                   │  │
│  └──────────────────────────────────────────────────────┘  │
│                                                              │
│  ┌──────────────────────────────────────────────────────┐  │
│  │              Communication Layer                      │  │
│  │  Fetch API + CSRF Token + JSON Serialization        │  │
│  └──────────────────────────────────────────────────────┘  │
└──────────────────────┬───────────────────────────────────────┘
                       │ HTTPS POST/GET
                       ▼
┌─────────────────────────────────────────────────────────────┐
│                   Flask Application Server                  │
│                                                              │
│  ┌──────────────────────────────────────────────────────┐  │
│  │                 Request Pipeline                      │  │
│  │                                                        │  │
│  │  Request → CSRF Check → Rate Limit → Auth Check →   │  │
│  │  Route Handler → Response                             │  │
│  └──────────────────────────────────────────────────────┘  │
│                                                              │
│  ┌──────────────────────────────────────────────────────┐  │
│  │              Authentication Module                    │  │
│  │                                                        │  │
│  │  ┌──────────────┐  ┌──────────────────────┐         │  │
│  │  │ Flask-Login  │  │ Password Hashing     │         │  │
│  │  │ (Sessions)   │  │ (Scrypt)             │         │  │
│  │  └──────────────┘  └──────────────────────┘         │  │
│  └──────────────────────────────────────────────────────┘  │
│                                                              │
│  ┌──────────────────────────────────────────────────────┐  │
│  │            Attendance Processing Module               │  │
│  │                                                        │  │
│  │  ┌────────────────┐  ┌────────────────────────┐     │  │
│  │  │ Geofencing     │  │ Face Verification      │     │  │
│  │  │ (Geopy)        │  │ (NumPy Distance)       │     │  │
│  │  └────────────────┘  └────────────────────────┘     │  │
│  │                                                        │  │
│  │  ┌────────────────┐  ┌────────────────────────┐     │  │
│  │  │ Session        │  │ Enrollment             │     │  │
│  │  │ Validation     │  │ Verification           │     │  │
│  │  └────────────────┘  └────────────────────────┘     │  │
│  │                                                        │  │
│  │  ┌────────────────┐  ┌────────────────────────┐     │  │
│  │  │ Duplicate      │  │ Fraud Logging          │     │  │
│  │  │ Check          │  │ (AttendanceAttempt)    │     │  │
│  │  └────────────────┘  └────────────────────────┘     │  │
│  └──────────────────────────────────────────────────────┘  │
│                                                              │
│  ┌──────────────────────────────────────────────────────┐  │
│  │              Course Management Module                 │  │
│  │  [Create Course][Enroll Students][Session Control]   │  │
│  └──────────────────────────────────────────────────────┘  │
│                                                              │
│  ┌──────────────────────────────────────────────────────┐  │
│  │              Reporting Module (Planned)               │  │
│  │  [Generate Reports][Calculate Percentage][Export]    │  │
│  └──────────────────────────────────────────────────────┘  │
└──────────────────────┬───────────────────────────────────────┘
                       │ SQLAlchemy ORM
                       ▼
┌─────────────────────────────────────────────────────────────┐
│                     Database Layer                          │
│                                                              │
│  ┌────────────────┐           ┌───────────────────────┐    │
│  │  Primary DB    │           │  Firebase Realtime    │    │
│  │  (SQLite/      │           │  Database             │    │
│  │   PostgreSQL)  │           │                       │    │
│  │                │           │  ┌─────────────────┐  │    │
│  │  schema:       │           │  │ /attendance/    │  │    │
│  │  - users       │           │  │   {student_id}/ │  │    │
│  │  - courses     │           │  │   {session_id}  │  │    │
│  │  - enrollments │           │  └─────────────────┘  │    │
│  │  - class_      │           │                       │    │
│  │    sessions    │           │  ┌─────────────────┐  │    │
│  │  - session_    │           │  │ /attendance_    │  │    │
│  │    attendance  │           │  │  attempts/      │  │    │
│  │  - attendance_ │           │  │  {date}/        │  │    │
│  │    attempts    │           │  │  {attempt_id}   │  │    │
│  └────────────────┘           │  └─────────────────┘  │    │
│                                └───────────────────────┘    │
└─────────────────────────────────────────────────────────────┘
```

---

## Database Schema

### Entity-Relationship Diagram

```
┌──────────────────────┐
│       User           │
├──────────────────────┤
│ PK id                │
│    name              │
│    email (UNIQUE)    │
│    department        │
│    password_hash     │
│    role              │◄──────────────┐
│    face_encoding     │               │
│    face_registered   │               │
│    registered_at     │               │
└──────────────────────┘               │
         │ 1                            │
         │                              │
         │ 1:N                          │ N:1
         ▼                              │
┌──────────────────────┐          ┌────┴──────────────┐
│   Enrollment         │          │     Course        │
├──────────────────────┤          ├───────────────────┤
│ PK id                │  N:1     │ PK id             │
│ FK course_id         ├──────────► code             │
│ FK student_id        │          │    title          │
│    enrolled_at       │          │    section        │
└──────────────────────┘          │ FK teacher_id     │
         │                        │    created_at     │
         │                        └───────────────────┘
         │                               │ 1
         │                               │
         │                               │ 1:N
         │                               ▼
         │                        ┌───────────────────┐
         │                        │  ClassSession     │
         │                        ├───────────────────┤
         │                        │ PK id             │
         │                        │    title          │
         │                        │    course_code    │
         │                        │    room           │
         │                        │ FK course_id      │
         │                        │ FK teacher_id     │
         │                        │    starts_at      │
         │                        │    ends_at        │
         │                        │    is_active      │
         │                        │    created_at     │
         │                        └───────────────────┘
         │                               │ 1
         │                               │
         │                               │ 1:N
         │                               ▼
         │         ┌────────────────────────────────────┐
         └─────────►  SessionAttendance                 │
                   ├────────────────────────────────────┤
                   │ PK id                              │
                   │ FK session_id                      │
                   │ FK student_id                      │
                   │    marked_at                       │
                   │    latitude                        │
                   │    longitude                       │
                   │    face_distance                   │
                   │    device_hash                     │
                   │    ip_address                      │
                   │    user_agent                      │
                   │                                    │
                   │ UNIQUE(session_id, student_id)    │
                   └────────────────────────────────────┘

┌──────────────────────────────────┐
│       AttendanceAttempt          │
├──────────────────────────────────┤
│ PK id                            │
│ FK session_id                    │
│ FK student_id                    │
│    success (BOOLEAN)             │
│    reason                        │
│    latitude                      │
│    longitude                     │
│    face_distance                 │
│    device_hash                   │
│    ip_address                    │
│    user_agent                    │
│    created_at                    │
└──────────────────────────────────┘
        (Audit log - no constraints)

┌──────────────────────┐
│     Attendance       │  (Legacy - Teachers only)
├──────────────────────┤
│ PK id                │
│ FK user_id           │
│    date              │
│    time              │
│    status            │
│    latitude          │
│    longitude         │
│                      │
│ UNIQUE(user_id, date)│
└──────────────────────┘
```

### Database Constraints

#### Primary Keys
- All tables have auto-incrementing integer primary keys

#### Foreign Keys
- `Enrollment.course_id` → `Course.id`
- `Enrollment.student_id` → `User.id`
- `Course.teacher_id` → `User.id`
- `ClassSession.course_id` → `Course.id`
- `ClassSession.teacher_id` → `User.id`
- `SessionAttendance.session_id` → `ClassSession.id`
- `SessionAttendance.student_id` → `User.id`
- `AttendanceAttempt.session_id` → `ClassSession.id`
- `AttendanceAttempt.student_id` → `User.id`

#### Unique Constraints
- `User.email` - UNIQUE
- `Course(code, section, teacher_id)` - UNIQUE
- `Enrollment(course_id, student_id)` - UNIQUE
- `SessionAttendance(session_id, student_id)` - UNIQUE
- `Attendance(user_id, date)` - UNIQUE

#### Cascade Rules
- `Course.enrollments` - CASCADE DELETE (when course deleted, enrollments deleted)
- `ClassSession.session_attendances` - CASCADE DELETE (when session deleted, attendance records deleted)

---

## Security Architecture

### Multi-Layer Security Model

```
┌─────────────────────────────────────────────────────────┐
│              Layer 1: Network Security                  │
│  - HTTPS Encryption (TLS 1.2+)                         │
│  - Firewall Rules (Ports 80/443 only)                  │
│  - DDoS Protection                                      │
└─────────────────────────────────────────────────────────┘
                         ▼
┌─────────────────────────────────────────────────────────┐
│           Layer 2: Application Security                 │
│  ┌─────────────────────────────────────────────────┐   │
│  │ CSRF Protection (Flask-WTF)                     │   │
│  │  - Token generation on every form               │   │
│  │  - Validation on POST/PUT/DELETE                │   │
│  └─────────────────────────────────────────────────┘   │
│                                                          │
│  ┌─────────────────────────────────────────────────┐   │
│  │ Rate Limiting (Flask-Limiter)                   │   │
│  │  - Login: 5 requests/minute                     │   │
│  │  - Registration: 20 requests/hour               │   │
│  │  - Attendance: 10 requests/minute               │   │
│  └─────────────────────────────────────────────────┘   │
│                                                          │
│  ┌─────────────────────────────────────────────────┐   │
│  │ Session Security                                 │   │
│  │  - HTTPOnly cookies (prevent XSS)               │   │
│  │  - SameSite=Lax (prevent CSRF)                  │   │
│  │  - Secure flag in production (HTTPS only)       │   │
│  └─────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────┘
                         ▼
┌─────────────────────────────────────────────────────────┐
│         Layer 3: Authentication & Authorization         │
│  ┌─────────────────────────────────────────────────┐   │
│  │ Password Security                                │   │
│  │  - Scrypt hashing (stronger than bcrypt)       │   │
│  │  - Salt per password (automatic)                │   │
│  │  - No plaintext storage                         │   │
│  └─────────────────────────────────────────────────┘   │
│                                                          │
│  ┌─────────────────────────────────────────────────┐   │
│  │ Role-Based Access Control (RBAC)                │   │
│  │  - Student: Attendance marking only             │   │
│  │  - Teacher: Course + session management         │   │
│  │  - Admin: Full system access                    │   │
│  └─────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────┘
                         ▼
┌─────────────────────────────────────────────────────────┐
│          Layer 4: Biometric Security                    │
│  ┌─────────────────────────────────────────────────┐   │
│  │ Face Verification                                │   │
│  │  - Client-side processing (privacy)             │   │
│  │  - Euclidean distance threshold: 0.6            │   │
│  │  - Multi-face prevention                        │   │
│  │  - Liveness detection (UI prompt)               │   │
│  └─────────────────────────────────────────────────┘   │
│                                                          │
│  ┌─────────────────────────────────────────────────┐   │
│  │ Geofencing                                       │   │
│  │  - 100-meter radius enforcement                 │   │
│  │  - GPS coordinate validation                    │   │
│  │  - Geodesic distance calculation                │   │
│  └─────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────┘
                         ▼
┌─────────────────────────────────────────────────────────┐
│           Layer 5: Fraud Detection                      │
│  ┌─────────────────────────────────────────────────┐   │
│  │ Device Fingerprinting                            │   │
│  │  - Unique device ID (localStorage)              │   │
│  │  - SHA-256 hashing                              │   │
│  │  - Track devices per user                       │   │
│  └─────────────────────────────────────────────────┘   │
│                                                          │
│  ┌─────────────────────────────────────────────────┐   │
│  │ Audit Logging (AttendanceAttempt)                │   │
│  │  - Log all attempts (success + failure)         │   │
│  │  - Track reasons, locations, face distance      │   │
│  │  - IP address and user agent                    │   │
│  └─────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────┘
                         ▼
┌─────────────────────────────────────────────────────────┐
│            Layer 6: Data Security                       │
│  - Input validation (all user inputs)                   │
│  - Output escaping (prevent XSS)                        │
│  - SQL injection prevention (ORM)                       │
│  - No sensitive data in logs                            │
│  - Database backups encryption (planned)                │
└─────────────────────────────────────────────────────────┘
```

### Security Checklist

#### ✅ Implemented
- [x] CSRF protection on all forms
- [x] Rate limiting on sensitive endpoints
- [x] HTTPOnly + SameSite cookies
- [x] Secure password hashing (Scrypt)
- [x] Role-based authorization
- [x] Face verification (distance threshold)
- [x] Geofencing (100m radius)
- [x] Device fingerprinting
- [x] Audit logging (AttendanceAttempt)
- [x] Input validation
- [x] SQL injection prevention (ORM)
- [x] XSS prevention (template escaping)

#### ⚠️ Partially Implemented
- [ ] Secure flag on cookies (dev mode disabled)
- [ ] HTTPS enforcement (deployment-specific)
- [ ] Face encoding encryption at rest
- [ ] Session timeout configuration

#### ❌ Not Implemented (Future)
- [ ] Two-factor authentication (2FA)
- [ ] Security headers (CSP, HSTS, X-Frame-Options)
- [ ] Data encryption at rest
- [ ] Automated security scanning
- [ ] Intrusion detection system
- [ ] API authentication (JWT tokens)

---

## Data Flow

### Student Attendance Marking Flow

```
┌─────────────┐
│   Student   │
│   Browser   │
└──────┬──────┘
       │ 1. Navigate to /mark_attendance
       ▼
┌─────────────┐
│    Flask    │
│   Server    │
└──────┬──────┘
       │ 2. Render student_mark_attendance.html
       ▼
┌─────────────┐
│   Browser   │
│             │
│ 3. Request camera + location permissions
│ 4. Load face-api.js models from CDN
│ 5. Fetch active sessions via AJAX
└──────┬──────┘
       │ GET /api/active_sessions
       ▼
┌─────────────┐
│    Flask    │
│             │
│ 6. Query enrolled sessions
│ 7. Filter active sessions (starts_at ≤ now ≤ ends_at)
└──────┬──────┘
       │ 8. Return JSON: sessions[]
       ▼
┌─────────────┐
│   Browser   │
│             │
│ 9. Display sessions in dropdown
│10. User selects session
│11. User clicks "Verify and Mark Attendance"
│12. face-api.js detectAllFaces(video)
│13. Extract 128-D face descriptor
└──────┬──────┘
       │ 14. POST /api/session_attendance/mark
       │     {session_id, descriptor[], lat, lng, device_id}
       ▼
┌─────────────┐
│    Flask    │
│             │
│ Validation Pipeline:
│ ├─ 15. Check user authenticated
│ ├─ 16. Check user is student
│ ├─ 17. Check face registered
│ ├─ 18. Validate session ID
│ ├─ 19. Check session exists
│ ├─ 20. Check student enrolled in course
│ ├─ 21. Check session active (is_active + time bounds)
│ ├─ 22. Check within geofence (100m radius)
│ ├─ 23. Check not already marked (duplicate)
│ ├─ 24. Verify face descriptor
│ │      - Load known_encoding from database
│ │      - Calculate Euclidean distance
│ │      - Compare with threshold (0.6)
│ └─ 25. All checks passed!
│
│26. Create SessionAttendance record
│27. Create successful AttendanceAttempt log
│28. Save to database
│29. Sync to Firebase (if enabled)
└──────┬──────┘
       │ 30. Return JSON: {success: true, message: "..."}
       ▼
┌─────────────┐
│   Browser   │
│             │
│31. Display success message
│32. Redirect to /dashboard
└─────────────┘
```

### Validation Failure Points

If any validation fails, the flow short-circuits:

```
Failure Point           → Record AttendanceAttempt   → Return Error JSON
─────────────────────────────────────────────────────────────────────────
Session not found       → reason: "Session not found" → 400 Bad Request
Not enrolled            → reason: "Not enrolled"      → 403 Forbidden
Session inactive        → reason: "Session inactive"  → 400 Bad Request
Outside campus          → reason: "Outside campus"    → 400 Bad Request
Already marked          → reason: "Duplicate mark"    → 400 Bad Request
No face descriptor      → reason: "No face"           → 400 Bad Request
Face mismatch           → reason: "Face mismatch"     → 400 Bad Request
```

---

## Technology Stack

### Backend Technologies

| Component | Technology | Version | Purpose |
|-----------|-----------|---------|---------|
| **Language** | Python | 3.9+ | Core programming language |
| **Web Framework** | Flask | 3.0.0 | Web application framework |
| **ORM** | SQLAlchemy | 3.1.1 | Database abstraction layer |
| **Authentication** | Flask-Login | 0.6.3 | User session management |
| **Security - CSRF** | Flask-WTF | 1.2.1 | CSRF protection |
| **Security - Rate Limiting** | Flask-Limiter | 3.10.1 | API rate limiting |
| **Database Migrations** | Flask-Migrate | 4.0.7 | Schema version control |
| **Password Hashing** | Werkzeug | 3.0.1 | Scrypt password hashing |
| **Geolocation** | Geopy | 2.4.1 | Distance calculation |
| **Math Operations** | NumPy | Latest | Face descriptor distance |
| **Cloud Sync** | Firebase Admin | 6.7.0 | Optional cloud backup |
| **WSGI Server** | Gunicorn | 21.2.0 | Production server |
| **Environment** | python-dotenv | 1.0.0 | Environment variables |
| **Testing** | Pytest | 8.3.5 | Unit and integration tests |

### Frontend Technologies

| Component | Technology | Version | Purpose |
|-----------|-----------|---------|---------|
| **Markup** | HTML5 | - | Semantic structure |
| **Styling** | CSS3 + Bootstrap | 5.3+ | Responsive UI |
| **Scripting** | JavaScript | ES6+ | Client-side logic |
| **Face Recognition** | face-api.js | 0.22.2 | Biometric processing |
| **Icons** | Font Awesome | 6.x | UI icons |
| **Template Engine** | Jinja2 | - | Server-side rendering |

### Database Technologies

| Environment | Database | Purpose |
|-------------|----------|---------|
| **Development** | SQLite | Local file-based DB |
| **Production** | PostgreSQL | Scalable relational DB |
| **Cloud Sync** | Firebase Realtime DB | Audit trail backup |

### DevOps & Deployment

| Component | Technology | Purpose |
|-----------|-----------|---------|
| **Version Control** | Git | Source code management |
| **CI/CD** | GitHub Actions | Automated testing & deployment |
| **Hosting** | Heroku / AWS | Cloud infrastructure |
| **Domain** | Custom domain | Production URL |
| **SSL** | Let's Encrypt | HTTPS certificates |

---

## Deployment Architecture

### Development Environment

```
┌──────────────────────────────────────┐
│      Developer Workstation           │
│                                      │
│  ┌────────────────────────────────┐ │
│  │  Python Virtual Environment    │ │
│  │  (venv)                        │ │
│  │                                │ │
│  │  Flask Development Server      │ │
│  │  Port: 5000                    │ │
│  │  Debug: ON                     │ │
│  │  Reload: ON                    │ │
│  └────────────────────────────────┘ │
│                                      │
│  ┌────────────────────────────────┐ │
│  │  SQLite Database               │ │
│  │  File: instance/attendance.db  │ │
│  └────────────────────────────────┘ │
└──────────────────────────────────────┘
```

### Production Environment (Cloud Deployment)

```
┌───────────────────────────────────────────────────────────┐
│                    Internet (Users)                       │
└────────────────────────┬──────────────────────────────────┘
                         │ HTTPS
                         ▼
┌───────────────────────────────────────────────────────────┐
│                  Load Balancer / CDN                      │
│              (Cloudflare / AWS CloudFront)                │
└────────────────────────┬──────────────────────────────────┘
                         │
                         ▼
┌───────────────────────────────────────────────────────────┐
│                   Application Server                      │
│                  (Heroku Dyno / AWS EC2)                  │
│                                                            │
│  ┌──────────────────────────────────────────────────┐    │
│  │           Gunicorn WSGI Server                   │    │
│  │           Workers: 4 (CPU cores * 2)             │    │
│  │           Threads: 2                              │    │
│  │           Port: 8000                              │    │
│  └──────────────────────────────────────────────────┘    │
│                                                            │
│  ┌──────────────────────────────────────────────────┐    │
│  │              Flask Application                    │    │
│  │              (Production Config)                  │    │
│  │              - DEBUG: OFF                         │    │
│  │              - SECRET_KEY: from env               │    │
│  │              - SESSION_COOKIE_SECURE: ON          │    │
│  └──────────────────────────────────────────────────┘    │
└────────────────────────┬──────────────────────────────────┘
                         │
          ┌──────────────┴──────────────┐
          │                             │
          ▼                             ▼
┌─────────────────────┐      ┌──────────────────────┐
│  PostgreSQL         │      │  Firebase Realtime   │
│  Database           │      │  Database            │
│  (AWS RDS /         │      │  (Cloud Backup)      │
│   Heroku Postgres)  │      │                      │
│                     │      │  - Attendance logs   │
│  - Primary data     │      │  - Audit trail       │
│  - ACID compliance  │      │  - Real-time sync    │
│  - Automated backups│      └──────────────────────┘
│  - Connection pool  │
└─────────────────────┘
```

### Scaling Strategy

#### Horizontal Scaling
```
Load Balancer
     │
     ├───► App Server 1 (Gunicorn)
     ├───► App Server 2 (Gunicorn)
     ├───► App Server 3 (Gunicorn)
     └───► App Server N (Gunicorn)
            │
            └───► Shared PostgreSQL Database
```

#### Caching Layer (Future Enhancement)
```
Client Request
     │
     ▼
Load Balancer
     │
     ▼
Redis Cache ──► Cache Hit → Return Cached Response
     │
     └──► Cache Miss
            │
            ▼
      App Server
            │
            ▼
     PostgreSQL DB
```

---

## Performance Considerations

### Bottlenecks

1. **Face Processing**: Client-side, depends on user's device CPU
2. **Database Queries**: N+1 query problem in dashboard views
3. **Model Loading**: face-api.js models loaded from CDN

### Optimization Strategies

#### Database Optimization
```python
# Use eager loading to avoid N+1 queries
students = (
    User.query
    .options(joinedload(User.enrollments).joinedload(Enrollment.course))
    .filter(User.role == 'student')
    .all()
)

# Use pagination for large datasets
students = User.query.paginate(page=1, per_page=50)

# Index frequently queried columns (already implemented)
# - email (unique index)
# - role
# - Foreign keys (automatic)
```

#### Caching Strategy
```python
# Cache expensive dashboard queries
@cache.memoize(timeout=300)  # 5 minutes
def get_attendance_stats(teacher_id):
    # Expensive aggregation query
    pass
```

#### CDN for Static Assets
```
# Serve face-api.js models from local server
/static/models/
    ssdMobilenetv1/
    faceLandmark68Net/
    faceRecognitionNet/
```

---

## Monitoring & Logging

### Application Logging
```python
import logging

# Configure logging
logging.basicConfig(
    filename='app.log',
    level=logging.INFO,
    format='%(asctime)s %(levelname)s: %(message)s'
)

# Log important events
app.logger.info(f"User {user.id} logged in")
app.logger.warning(f"Failed login attempt for {email}")
app.logger.error(f"Database error: {str(e)}")
```

### Performance Monitoring
- Database query time tracking
- Response time per endpoint
- Error rate monitoring
- User activity metrics

### Security Monitoring
- Failed login attempts per IP
- Unusual attendance patterns
- Multiple device usage per user
- Geofence violations

---

## Future Architecture Enhancements

### Version 2.0 Roadmap

1. **Microservices Architecture**
   - Separate face recognition service
   - Notification service (email/SMS)
   - Reporting service (PDF generation)

2. **Mobile App**
   - React Native mobile client
   - Push notifications
   - Offline capability

3. **API Gateway**
   - RESTful API with JWT authentication
   - Rate limiting per API key
   - API versioning

4. **Real-time Features**
   - WebSocket for live attendance updates
   - Teacher dashboard auto-refresh
   - Notification system

5. **Advanced Analytics**
   - Machine learning for fraud detection
   - Attendance prediction models
   - Trend analysis

---

**Document Version**: 1.0  
**Last Updated**: February 19, 2026  
**Maintainer**: IIOT Group Project Team
