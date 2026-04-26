# Architecture

This document describes the current application architecture used in the repository.

## High-Level Design

The system uses a server-rendered Flask app with browser-side face descriptor extraction.

1. Presentation layer
- Jinja templates in templates/
- Shared styling in static/style.css
- Browser APIs: camera + geolocation

2. Application layer
- app.py route handlers and business logic
- Role-based authorization checks (student/teacher/admin)
- Attendance and session validation logic

3. Data layer
- SQLAlchemy models in models.py
- Primary DB: SQLite (dev) or configured DB URL
- Optional Firebase sync for audit/backup paths

4. Auxiliary secure store
- Encrypted credentials backup service in user_backup_service.py
- Separate DB path default: instance/userbackup.db

## Main Modules

- app.py: routes, validation, attendance logic, dashboards
- models.py: User, Course, Enrollment, ClassSession, SessionAttendance, Attendance, AttendanceAttempt
- config.py: environment-driven configuration
- firebase_service.py: optional Firebase integration
- user_backup_service.py: encrypted credential backup/read utilities
- email_service.py: attendance email notifications

## Role-Based Access

Student:
- Mark attendance
- View own attendance data
- Reset own face

Teacher:
- Manage courses and enrollments
- Start/close sessions
- View reports and export CSV

Admin:
- View system dashboard
- Edit limited user profile fields
- Change user role (student/teacher)
- Clear face data and delete users
- Access secret credentials page (with second step key)

## Attendance Marking Flow

1. Student opens attendance screen.
2. Browser obtains camera descriptor and location.
3. Client submits session_id + descriptor + coordinates.
4. Server validates:
- user role and login
- active session and enrollment
- geofence
- face distance threshold
- duplicate attendance constraints
5. Server writes SessionAttendance and AttendanceAttempt.
6. Optional sync to Firebase and optional email path.

## Data Integrity and Constraints

- Unique user email in users table
- Unique attendance per user per day in Attendance
- Unique attendance per student per session in SessionAttendance
- Unique course enrollment per student/course pair

## Runtime Notes

- Startup includes schema compatibility helper for SQLite.
- Expired sessions are auto-closed on request cycle.
- Database backfill logic can generate missing daily attendance from session attendance.

## Deployment Shape

- WSGI entry: wsgi.py
- Typical prod command: gunicorn wsgi:app
- Env values loaded from .env via dotenv

## Related Docs

- API.md
- SECURITY.md
- ../OPERATIONS.md