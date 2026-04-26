# API Documentation

This document covers the current HTTP routes and JSON APIs exposed by the application.

## Base URL

- Local: http://localhost:5000
- Production: your deployed domain

## Authentication Model

- Session-cookie based authentication via Flask-Login.
- Most write actions require CSRF token.
- API requests from browser should include X-CSRFToken.

## Route Groups

### Public

- GET /
- GET, POST /register
- GET, POST /login

### Authenticated (role-aware)

- GET /dashboard
- GET /logout
- GET /register_face
- POST /save_face
- GET, POST /mark_attendance

### Student APIs

- GET /api/active_sessions
- POST /api/session_attendance/mark
- GET /api/my_course_attendance
- POST /student/reset_face

### Teacher Actions/APIs

- POST /teacher/courses/create
- POST /teacher/courses/<course_id>/enroll
- POST /teacher/sessions/create
- POST /teacher/sessions/<session_id>/close
- GET /teacher/sessions/<session_id>/roster
- GET /teacher/attendance/export
- GET /teacher/courses/<course_id>/report
- POST /teacher/courses/<course_id>/unenroll/<student_id>
- POST /teacher/courses/<course_id>/delete
- GET /api/session_counts

### Admin Actions

- GET, POST /admin/users/<user_id>/edit
- GET, POST /admin/users/<user_id>/change_role
- POST /admin/users/<user_id>/delete
- POST /admin/users/<user_id>/clear_face
- GET, POST /admin/secret_credentials

## JSON API Details

## GET /api/active_sessions

Purpose:
- Returns active sessions for logged-in student.

Success response:

```json
{
  "sessions": [
    {
      "id": 12,
      "title": "Data Structures",
      "course_code": "CSE201",
      "room": "Lab-2",
      "ends_at": "03:45 PM"
    }
  ]
}
```

Notes:
- Non-student users receive an empty list.

## POST /api/session_attendance/mark

Purpose:
- Marks attendance for a session after enrollment, geofence, and face checks.

Behavior notes:
- Teacher session creation captures the classroom location.
- Students must be within the live session classroom radius to mark attendance.
- If a student is outside the allowed classroom area, the API returns a clear "Go to the classroom" style message.

Request body:

```json
{
  "session_id": 12,
  "descriptor": [0.1, 0.2, 0.3],
  "lat": 28.2923,
  "lng": 79.4930,
  "device_id": "local-device-id"
}
```

Typical success:

```json
{
  "success": true,
  "message": "Attendance marked successfully"
}
```

Common failure messages:
- Session not active or not found
- Not enrolled in course
- Outside allowed campus radius
- Face mismatch or multiple-face detection
- Duplicate marking attempt

## GET /api/session_counts

Purpose:
- Teacher polling endpoint for attendance counts per session.

Success response:

```json
{
  "12": 23,
  "14": 19
}
```

## GET /api/my_course_attendance

Purpose:
- Student course-wise attendance percentages.

Success response:

```json
[
  {
    "course_code": "CSE201",
    "course_title": "Data Structures",
    "section": "A",
    "attended": 7,
    "total": 9,
    "percentage": 77.8,
    "low": false
  }
]
```

## POST /save_face

Purpose:
- Saves user face descriptor after registration.

Body:

```json
{
  "descriptor": [0.1, 0.2, 0.3]
}
```

Checks:
- Descriptor shape and numeric validity
- Cross-user duplicate face prevention

## Security Expectations for Clients

- Always send CSRF token for POST/PUT/DELETE style requests.
- Keep browser permissions enabled for camera and location on attendance screens.
- Do not call admin routes without admin session.

## Related Docs

- ../README.md
- ARCHITECTURE.md
- SECURITY.md
