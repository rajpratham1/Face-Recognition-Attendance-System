# API Documentation

Complete API reference for the Face Recognition Attendance System.

## Base URL

```
Development: http://localhost:5000
Production: https://your-domain.com
```

## Authentication

Most API endpoints require authentication via Flask session cookies. User must be logged in.

### Headers

```http
Content-Type: application/json
X-CSRFToken: <csrf_token>
Cookie: session=<session_cookie>
```

---

## Table of Contents

- [Authentication APIs](#authentication-apis)
- [Face Recognition APIs](#face-recognition-apis)
- [Student APIs](#student-apis)
- [Teacher APIs](#teacher-apis)
- [Admin APIs](#admin-apis)
- [Error Responses](#error-responses)

---

## Authentication APIs

### POST /register

Register a new user account.

**Authentication**: Not required

**Request**:
```http
POST /register
Content-Type: application/x-www-form-urlencoded
X-CSRFToken: <token>

name=John+Doe&email=john@example.com&department=Computer+Science&password=SecurePass123&role=student&consent=yes
```

**Form Parameters**:
| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| name | string | Yes | Full name of user |
| email | string | Yes | Email address (must be unique) |
| department | string | Yes | Department/Faculty name |
| password | string | Yes | Password (minimum 8 characters recommended) |
| role | string | Yes | Either "student" or "teacher" |
| consent | string | Yes | Must be "yes" for biometric consent |

**Success Response**:
```http
HTTP/1.1 302 Found
Location: /register_face
Set-Cookie: session=...
```

**Error Responses**:
- `400 Bad Request` - Invalid role selected
- `400 Bad Request` - Email already registered
- `400 Bad Request` - Biometric consent not provided

---

### POST /login

Authenticate user and create session.

**Authentication**: Not required

**Rate Limit**: 5 requests per minute

**Request**:
```http
POST /login
Content-Type: application/x-www-form-urlencoded
X-CSRFToken: <token>

email=john@example.com&password=SecurePass123
```

**Form Parameters**:
| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| email | string | Yes | Registered email address |
| password | string | Yes | User password |

**Success Response**:
```http
HTTP/1.1 302 Found
Location: /dashboard
Set-Cookie: session=...
```

**Error Response**:
```http
HTTP/1.1 302 Found
Location: /login
Flash: "Invalid credentials"
```

---

### GET /logout

Logout user and destroy session.

**Authentication**: Required

**Request**:
```http
GET /logout
Cookie: session=<session_cookie>
```

**Response**:
```http
HTTP/1.1 302 Found
Location: /
Set-Cookie: session=; Expires=Thu, 01 Jan 1970 00:00:00 GMT
```

---

## Face Recognition APIs

### POST /save_face

Save user's face descriptor after registration.

**Authentication**: Required  
**Rate Limit**: 30 requests per hour

**Request**:
```http
POST /save_face
Content-Type: application/json
X-CSRFToken: <token>
Cookie: session=<session_cookie>

{
  "descriptor": [0.123, 0.456, ..., 0.789]
}
```

**Body Parameters**:
| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| descriptor | array[float] | Yes | Face descriptor (128 floats) from face-api.js |

**Success Response**:
```json
HTTP/1.1 200 OK
Content-Type: application/json

{
  "success": true
}
```

**Error Responses**:

Missing descriptor:
```json
HTTP/1.1 400 Bad Request
{
  "success": false,
  "message": "No face data received"
}
```

---

## Student APIs

### GET /api/active_sessions

Get list of active class sessions for the current student.

**Authentication**: Required (student role)

**Request**:
```http
GET /api/active_sessions
Cookie: session=<session_cookie>
```

**Success Response**:
```json
HTTP/1.1 200 OK
Content-Type: application/json

{
  "sessions": [
    {
      "id": 1,
      "title": "Data Structures",
      "course_code": "CSE101",
      "room": "Lab 301",
      "ends_at": "2026-02-19 03:45 PM"
    },
    {
      "id": 2,
      "title": "Algorithms",
      "course_code": "CSE201",
      "room": "Room 205",
      "ends_at": "2026-02-19 05:00 PM"
    }
  ]
}
```

**Response Fields**:
| Field | Type | Description |
|-------|------|-------------|
| sessions | array | List of active session objects |
| sessions[].id | integer | Session unique identifier |
| sessions[].title | string | Course title |
| sessions[].course_code | string | Course code |
| sessions[].room | string | Room/Lab location |
| sessions[].ends_at | string | Session end time (formatted) |

**Empty Response** (no active sessions):
```json
{
  "sessions": []
}
```

**Non-Student Response**:
```json
{
  "sessions": []
}
```

---

### POST /api/session_attendance/mark

Mark attendance for a class session.

**Authentication**: Required (student role)  
**Rate Limit**: 10 requests per minute

**Request**:
```http
POST /api/session_attendance/mark
Content-Type: application/json
X-CSRFToken: <token>
Cookie: session=<session_cookie>

{
  "session_id": 1,
  "descriptor": [0.123, 0.456, ..., 0.789],
  "lat": 28.325764684367748,
  "lng": 79.46097110207619,
  "device_id": "1234567890-abcdef"
}
```

**Body Parameters**:
| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| session_id | integer | Yes | ID of the class session |
| descriptor | array[float] | Yes | Face descriptor (128 floats) |
| lat | float | Yes | Latitude coordinate |
| lng | float | Yes | Longitude coordinate |
| device_id | string | Yes | Unique device identifier |

**Success Response**:
```json
HTTP/1.1 200 OK
Content-Type: application/json

{
  "success": true,
  "message": "Attendance marked for CSE101 (Data Structures)."
}
```

**Error Responses**:

Face not registered:
```json
HTTP/1.1 400 Bad Request
{
  "success": false,
  "message": "Face registration is required before marking attendance."
}
```

Session not found:
```json
HTTP/1.1 400 Bad Request
{
  "success": false,
  "message": "Session not found."
}
```

Not enrolled in course:
```json
HTTP/1.1 403 Forbidden
{
  "success": false,
  "message": "You are not enrolled for this course."
}
```

Session not active:
```json
HTTP/1.1 400 Bad Request
{
  "success": false,
  "message": "This session is not active now."
}
```

Outside campus:
```json
HTTP/1.1 400 Bad Request
{
  "success": false,
  "message": "Attendance can only be marked within Invertis University campus."
}
```

Already marked:
```json
HTTP/1.1 400 Bad Request
{
  "success": false,
  "message": "Attendance already marked for this class session."
}
```

No face detected:
```json
HTTP/1.1 400 Bad Request
{
  "success": false,
  "message": "No face detected!"
}
```

Face verification failed:
```json
HTTP/1.1 400 Bad Request
{
  "success": false,
  "message": "Face verification failed. Please try again."
}
```

---

### GET /mark_attendance

Get UI page for marking session attendance.

**Authentication**: Required (student role)

**Request**:
```http
GET /mark_attendance
Cookie: session=<session_cookie>
```

**Response**: HTML page with active sessions list

---

## Teacher APIs

### POST /teacher/courses/create

Create a new course.

**Authentication**: Required (teacher role)

**Request**:
```http
POST /teacher/courses/create
Content-Type: application/x-www-form-urlencoded
X-CSRFToken: <token>
Cookie: session=<session_cookie>

code=CSE101&title=Data+Structures&section=A
```

**Form Parameters**:
| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| code | string | Yes | Course code (e.g., "CSE101") |
| title | string | Yes | Course title |
| section | string | Yes | Section identifier (e.g., "A") |

**Success Response**:
```http
HTTP/1.1 302 Found
Location: /dashboard
Flash: "Course created successfully."
```

**Error Responses**:

Missing fields:
```http
HTTP/1.1 302 Found
Location: /dashboard
Flash: "All course fields are required."
```

Course already exists:
```http
HTTP/1.1 302 Found
Location: /dashboard
Flash: "Course already exists for this section."
```

---

### POST /teacher/courses/<course_id>/enroll

Enroll a student in a course.

**Authentication**: Required (teacher role)

**Request**:
```http
POST /teacher/courses/5/enroll
Content-Type: application/x-www-form-urlencoded
X-CSRFToken: <token>
Cookie: session=<session_cookie>

student_email=student@example.com
```

**URL Parameters**:
| Parameter | Type | Description |
|-----------|------|-------------|
| course_id | integer | ID of the course |

**Form Parameters**:
| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| student_email | string | Yes | Email of student to enroll |

**Success Response**:
```http
HTTP/1.1 302 Found
Location: /dashboard
Flash: "Student enrolled successfully."
```

**Error Responses**:

Student not found:
```http
HTTP/1.1 302 Found
Location: /dashboard
Flash: "Student not found with this email."
```

Already enrolled:
```http
HTTP/1.1 302 Found
Location: /dashboard
Flash: "Student already enrolled in this course."
```

---

### POST /teacher/sessions/create

Create a live class session.

**Authentication**: Required (teacher role)

**Request**:
```http
POST /teacher/sessions/create
Content-Type: application/x-www-form-urlencoded
X-CSRFToken: <token>
Cookie: session=<session_cookie>

course_id=5&room=Lab+301&duration=30
```

**Form Parameters**:
| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| course_id | integer | Yes | ID of the course |
| room | string | Yes | Room/Lab location |
| duration | integer | Yes | Session duration in minutes (5-120) |

**Success Response**:
```http
HTTP/1.1 302 Found
Location: /dashboard
Flash: "Class session created and is now live for enrolled students."
```

**Error Responses**:

Invalid course:
```http
HTTP/1.1 302 Found
Location: /dashboard
Flash: "Course not found for this teacher."
```

Missing room:
```http
HTTP/1.1 302 Found
Location: /dashboard
Flash: "Room/Lab is required."
```

---

### POST /teacher/sessions/<session_id>/close

Close an active class session.

**Authentication**: Required (teacher role)

**Request**:
```http
POST /teacher/sessions/12/close
Content-Type: application/x-www-form-urlencoded
X-CSRFToken: <token>
Cookie: session=<session_cookie>
```

**URL Parameters**:
| Parameter | Type | Description |
|-----------|------|-------------|
| session_id | integer | ID of the session to close |

**Success Response**:
```http
HTTP/1.1 302 Found
Location: /dashboard
Flash: "Class session closed."
```

**Error Response**:
```http
HTTP/1.1 404 Not Found
```

---

## Admin APIs

### GET /dashboard

Get role-specific dashboard view.

**Authentication**: Required (any role)

**Request**:
```http
GET /dashboard
Cookie: session=<session_cookie>
```

**Response**: HTML page based on user role:
- Admin → `admin_dashboard.html`
- Teacher → `teacher_dashboard.html`
- Student → `student_dashboard.html`

---

## Error Responses

### Standard Error Format

```json
{
  "success": false,
  "message": "Human-readable error message"
}
```

### HTTP Status Codes

| Code | Meaning | Usage |
|------|---------|-------|
| 200 | OK | Successful request |
| 302 | Found | Redirect (for form submissions) |
| 400 | Bad Request | Invalid input or business logic error |
| 401 | Unauthorized | Not authenticated |
| 403 | Forbidden | Not authorized (wrong role) |
| 404 | Not Found | Resource doesn't exist |
| 429 | Too Many Requests | Rate limit exceeded |
| 500 | Internal Server Error | Server-side error |

### Rate Limit Response

When rate limit is exceeded:

```http
HTTP/1.1 429 Too Many Requests
Content-Type: application/json

{
  "error": "ratelimit exceeded",
  "message": "X per Y"
}
```

Rate limit headers are included in all responses:
```http
X-RateLimit-Limit: 10
X-RateLimit-Remaining: 7
X-RateLimit-Reset: 1645275840
```

---

## Code Examples

### JavaScript - Mark Attendance

```javascript
async function markAttendance(sessionId, faceDescriptor, latitude, longitude) {
    const csrfToken = document.querySelector('meta[name="csrf-token"]').content;
    const deviceId = localStorage.getItem('device_id') || generateDeviceId();
    
    try {
        const response = await fetch('/api/session_attendance/mark', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': csrfToken
            },
            body: JSON.stringify({
                session_id: sessionId,
                descriptor: Array.from(faceDescriptor),
                lat: latitude,
                lng: longitude,
                device_id: deviceId
            })
        });
        
        const result = await response.json();
        
        if (result.success) {
            console.log('Success:', result.message);
            window.location.href = '/dashboard';
        } else {
            console.error('Error:', result.message);
            alert(result.message);
        }
    } catch (error) {
        console.error('Network error:', error);
        alert('Connection error. Please try again.');
    }
}
```

### Python - Call API Internally

```python
from flask import session
from app import app

# Within application context
with app.test_client() as client:
    # Login first
    client.post('/login', data={
        'email': 'student@example.com',
        'password': 'password'
    })
    
    # Call API with session cookie
    response = client.get('/api/active_sessions')
    data = response.get_json()
    
    sessions = data['sessions']
    for sess in sessions:
        print(f"Session: {sess['course_code']} in {sess['room']}")
```

### cURL Examples

Get active sessions:
```bash
curl -X GET http://localhost:5000/api/active_sessions \
  -H "Cookie: session=your_session_cookie" \
  -H "Content-Type: application/json"
```

Mark attendance:
```bash
curl -X POST http://localhost:5000/api/session_attendance/mark \
  -H "Cookie: session=your_session_cookie" \
  -H "X-CSRFToken: your_csrf_token" \
  -H "Content-Type: application/json" \
  -d '{
    "session_id": 1,
    "descriptor": [0.1, 0.2, ..., 0.9],
    "lat": 28.325764684367748,
    "lng": 79.46097110207619,
    "device_id": "unique-device-id"
  }'
```

---

## Webhooks (Future Feature)

Planned webhook support for real-time notifications:

### POST <your_webhook_url>

When student marks attendance:
```json
{
  "event": "attendance.marked",
  "timestamp": "2026-02-19T10:30:00Z",
  "data": {
    "student_id": 42,
    "student_name": "John Doe",
    "session_id": 5,
    "course_code": "CSE101",
    "marked_at": "2026-02-19T10:30:00Z"
  }
}
```

When session closes:
```json
{
  "event": "session.closed",
  "timestamp": "2026-02-19T11:00:00Z",
  "data": {
    "session_id": 5,
    "course_code": "CSE101",
    "total_enrolled": 50,
    "total_present": 47
  }
}
```

---

## API Versioning (Future)

Planned API versioning for backward compatibility:

```
v1: /api/v1/session_attendance/mark
v2: /api/v2/session_attendance/mark
```

Version 2 will include:
- Pagination for list endpoints
- Filtering and sorting
- Batch operations
- GraphQL endpoint

---

## Rate Limits Summary

| Endpoint | Limit | Window |
|----------|-------|--------|
| POST /login | 5 | 1 minute |
| POST /register | 20 | 1 hour |
| POST /save_face | 30 | 1 hour |
| POST /api/session_attendance/mark | 10 | 1 minute |
| POST /mark_attendance | 20 | 1 minute |
| Global default | 200 | 1 day |
| Global default | 60 | 1 hour |

---

## Security Notes

1. **CSRF Tokens**: All POST/PUT/DELETE requests require valid CSRF token
2. **Session Cookies**: HttpOnly, SameSite=Lax, Secure (in production)
3. **Rate Limiting**: Prevents brute force and DoS attacks
4. **Input Validation**: All inputs validated server-side
5. **Face Data**: Never sent to logs or error messages (privacy)
6. **Geolocation**: Required for attendance marking (geofencing)

---

## Testing APIs

Use the provided test fixtures for API testing:

```python
pytest tests/test_api.py -v
```

Or use Postman:
1. Import `postman_collection.json` (if provided)
2. Set environment variables (base_url, csrf_token, session_cookie)
3. Run collection tests

---

**API Version**: 1.0  
**Last Updated**: February 19, 2026  
**Maintainer**: IIOT Group Project Team
