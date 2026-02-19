# Changelog

All notable changes to the Face Recognition Attendance System will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Planned for v2.0
- Mobile application (React Native)
- Attendance percentage calculator per course
- Email/SMS notifications for low attendance
- Leave request management system
- Excel/PDF report generation
- Interactive analytics dashboard
- Multi-campus support with multiple geofence zones
- QR code fallback for attendance marking
- LMS integration (Moodle, Canvas, Blackboard)
- API documentation with Swagger/OpenAPI
- Attendance prediction using ML

### Planned for v1.1
- Admin fraud detection UI for AttendanceAttempt logs
- Manual attendance override for teachers
- Bulk student enrollment (CSV upload)
- Face re-registration capability
- Attendance reports download (CSV/PDF)
- Session attendance percentage view
- Enhanced mobile responsiveness
- Real-time session updates (WebSocket)

---

## [1.0.0] - 2026-02-19

### Initial Release

#### Added

**Core Features**
- User registration with role-based access (Student, Teacher, Admin)
- Face registration using face-api.js (client-side biometric processing)
- Session-based attendance marking with live class sessions
- Geofencing (100-meter radius from Invertis University campus)
- Face verification with configurable threshold (0.6 Euclidean distance)
- Device fingerprinting for fraud detection
- IP address and user agent tracking

**Authentication & Authorization**
- Flask-Login session management
- Scrypt password hashing
- Role-based access control (RBAC)
- Biometric consent during registration

**Security Features**
- CSRF protection on all forms
- Rate limiting on sensitive endpoints:
  - Login: 5 requests/minute
  - Registration: 20 requests/hour
  - Face save: 30 requests/hour
  - Attendance marking: 10 requests/minute
- HTTPOnly cookies
- SameSite cookie protection
- Multi-face detection prevention
- Audit logging for all attendance attempts

**Course Management**
- Course creation with code, title, and section
- Student enrollment by email
- Course-student-teacher relationships
- Unique constraints to prevent duplicates

**Session Management**
- Live session creation with customizable duration (5-120 minutes)
- Auto-expiry based on time bounds
- Manual session closing by teacher
- Real-time active session detection
- Room/lab tracking

**Attendance System**
- Session-based attendance recording
- Dual attendance models:
  - SessionAttendance: Class-specific for students
  - Attendance: Daily check-in for teachers
- AttendanceAttempt audit log for fraud detection
- Duplicate prevention (one mark per session per student)
- Location coordinate storage
- Face distance recording

**Dashboards**
- Student Dashboard:
  - Enrolled courses view
  - Active sessions display
  - Session attendance history
  - Daily attendance records
- Teacher Dashboard:
  - Course creation and management
  - Student enrollment interface
  - Live session creation and control
  - Enrolled students view with 7-day attendance
  - Course enrollment count
  - Session attendance statistics
- Admin Dashboard:
  - All users view (students, teachers, admins)
  - 7-day attendance grid for all users
  - Today's attendance count
  - System-wide statistics

**Firebase Integration (Optional)**
- Firebase Realtime Database sync for cloud backup
- Attendance record synchronization
- Attendance attempt logging to Firebase
- Graceful fallback when Firebase unavailable

**Database**
- SQLite support for development
- PostgreSQL support for production
- Flask-Migrate for schema version control
- Proper foreign key relationships
- Unique constraints on critical fields
- Cascade delete for related records

**API Endpoints**
- `/api/active_sessions` - Get active sessions for student
- `/api/session_attendance/mark` - Mark attendance with face + location
- RESTful JSON responses
- Proper HTTP status codes
- Detailed error messages

**Developer Tools**
- Database migration scripts
- Admin user creation script (`create_admin.py`)
- Backup script (`scripts/backup_db.py`)
- Environment variable configuration
- Development and production configs

**Documentation**
- README.md with comprehensive setup guide
- ARCHITECTURE.md with system design documentation
- CONTRIBUTING.md with contribution guidelines
- GitHub Copilot instructions for AI assistance
- API documentation
- Code comments and docstrings

#### Technical Specifications

**Backend**
- Python 3.9+
- Flask 3.0.0
- SQLAlchemy 3.1.1 ORM
- Flask-Login 0.6.3
- Flask-WTF 1.2.1 (CSRF)
- Flask-Limiter 3.10.1 (Rate limiting)
- Flask-Migrate 4.0.7 (DB migrations)
- Firebase Admin SDK 6.7.0
- Geopy 2.4.1 (Distance calculation)
- NumPy (Face descriptor math)

**Frontend**
- HTML5/CSS3
- JavaScript (ES6+)
- Bootstrap 5
- face-api.js 0.22.2
- Font Awesome icons

**Database Schema**
- Users table with biometric storage
- Courses with teacher assignments
- Enrollments (many-to-many)
- Class sessions with time bounds
- Session attendance with security metadata
- Attendance attempts audit log
- Legacy daily attendance table

**Security**
- Scrypt password hashing
- CSRF tokens on all state-changing requests
- Rate limiting per endpoint
- HTTPOnly + SameSite=Lax cookies
- Session security
- Input validation
- Output escaping (XSS prevention)
- SQL injection prevention (ORM)

#### Known Limitations

- Face models loaded from CDN (requires internet)
- Single geofence location (hardcoded in config.py)
- No face re-registration capability
- No attendance percentage calculation
- No report generation
- No email notifications
- Admin cannot view detailed fraud detection logs
- No manual attendance override for teachers
- Attendance history not paginated (performance issue with large datasets)
- Firebase sync errors not surfaced to admin UI

---

## [0.1.0] - 2026-01-15

### Development Preview

#### Added
- Basic Flask application structure
- User model with authentication
- Simple login/logout functionality
- Face registration prototype
- Basic geolocation tracking
- SQLite database setup

#### Changed
- Migrated from plain password storage to hashed passwords
- Updated from Flask 2.x to Flask 3.0

#### Security
- Added CSRF protection
- Implemented rate limiting on auth endpoints

---

## Version Numbering

This project uses [Semantic Versioning](https://semver.org/):

- **MAJOR** version (X.0.0): Incompatible API changes or major architectural changes
- **MINOR** version (0.X.0): New features in a backwards-compatible manner
- **PATCH** version (0.0.X): Backwards-compatible bug fixes

### Release Schedule

- **Patch releases**: As needed for bug fixes (typically 2-4 weeks)
- **Minor releases**: Every 2-3 months with new features
- **Major releases**: Annually or when significant changes are made

---

## Migration Guide

### Upgrading from 0.1.0 to 1.0.0

**Breaking Changes:**
- Database schema changed significantly
- Environment variable names updated
- API endpoint paths changed

**Migration Steps:**

1. **Backup your database**
   ```bash
   python scripts/backup_db.py
   ```

2. **Update dependencies**
   ```bash
   pip install -r requirements.txt
   ```

3. **Update environment variables**
   - Rename `.env` to `.env.old`
   - Copy `.env.example` to `.env`
   - Transfer values from `.env.old` to `.env`

4. **Run database migrations**
   ```bash
   flask --app manage.py db upgrade
   ```

5. **Recreate admin user**
   ```bash
   python create_admin.py
   ```

6. **Test the application**
   ```bash
   pytest tests/
   ```

---

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md) for how to contribute changes to this project.

---

## Credits

### Core Team
- IIOT Group Project Team, Invertis University

### Contributors
- (List will be updated as contributors join)

### Special Thanks
- Face-api.js team for face recognition library
- Flask community for documentation and support
- Open source community for third-party libraries

---

## Links

- **Homepage**: https://github.com/rajpratham1/Face-Recognition-Attendance-System
- **Documentation**: See README.md
- **Bug Reports**: https://github.com/rajpratham1/Face-Recognition-Attendance-System/issues
- **Source Code**: https://github.com/rajpratham1/Face-Recognition-Attendance-System

---

**Note**: Dates use ISO 8601 format (YYYY-MM-DD)
