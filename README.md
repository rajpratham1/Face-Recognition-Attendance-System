# 🎓 Face Recognition Attendance System

[![Python](https://img.shields.io/badge/Python-3.9+-blue.svg)](https://www.python.org/downloads/)
[![Flask](https://img.shields.io/badge/Flask-3.0.0-green.svg)](https://flask.palletsprojects.com/)
[![License](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Status](https://img.shields.io/badge/Status-Active-success.svg)]()

A modern, secure, and intelligent attendance management system built for **Invertis University, Bareilly** that uses face recognition technology to eliminate proxy attendance and automate academic attendance tracking.

---

## 📋 Table of Contents

- [Overview](#-overview)
- [Key Features](#-key-features)
- [Project File Structure](#-project-file-structure)
- [Tech Stack](#-tech-stack)
- [System Architecture](#-system-architecture)
- [Quick Start](#-quick-start)
- [Installation](#-installation)
- [Configuration](#-configuration)
- [Usage Guide](#-usage-guide)
- [API Documentation](#-api-documentation)
- [Security](#-security)
- [Troubleshooting](#-troubleshooting)
- [Contributing](#-contributing)
- [License](#-license)

---

## 🎯 Overview

Traditional attendance systems are prone to proxy attendance and manual errors. This **Face Recognition Attendance System** leverages client-side biometric technology to ensure:

- **100% Authentic Attendance** — Face verification prevents proxy attendance
- **Cross-Role Face Uniqueness** — One face can only be linked to one account globally (no same person as student + teacher)
- **Real-time Session Tracking** — Teachers create live sessions; students mark in real-time
- **Geofencing** — Location verification ensures on-campus attendance (100m radius)
- **Dual Attendance Records** — Session-based + daily attendance both tracked
- **Privacy-First** — All face processing happens client-side; only 128-D math vectors stored

### System Demo Flow
```
Student: Register → Scan Face → Enroll in Course → Join Live Session → Mark Attendance
Teacher: Create Course → Enroll Students → Start Session → Monitor → Close Session
Admin:   Monitor System → View Analytics → Manage Users → Audit Logs
```

---

## ✨ Key Features

### 👤 For Students
| Feature | Description |
|---|---|
| **Face Registration** | One-time biometric enrollment; 5 frames silently averaged for accuracy |
| **Face Uniqueness Enforcement** | Cannot register a face already linked to any other account (any role) |
| **Live Session View** | Real-time display of active class sessions |
| **One-Click Attendance** | Face + GPS location verified in seconds |
| **Session Attendance History** | View per-session records with date, time, course |
| **Daily Attendance Records** | Auto-populated whenever a session attendance is marked |
| **Attendance Percentage** | Real-time % based on sessions attended vs sessions held |
| **Enrolled Courses Panel** | View all courses you are enrolled in |

### 👨‍🏫 For Teachers
| Feature | Description |
|---|---|
| **Course Management** | Create courses with code, title, and section |
| **Student Enrollment** | Enroll students into courses by email |
| **Live Session Control** | Start sessions with room + duration (5–120 minutes) |
| **Real-time Monitoring** | Session attendance count shown on dashboard |
| **Close Sessions** | Manually end a session before it auto-expires |
| **Student Analytics** | 7-day attendance pattern for each enrolled student |
| **Own Attendance Record** | Teachers can also view their personal daily attendance |

### 👨‍💼 For Admins
| Feature | Description |
|---|---|
| **System Dashboard** | Overview of all users and 7-day attendance grid |
| **User Management** | See all students, teachers, and admins |
| **Attendance Analytics** | Today's count + recent history per user |
| **Print Reports** | Browser-based print/PDF of attendance reports |
| **Audit Log** | All attempts (success + failure) tracked in `AttendanceAttempt` table |

### 🔐 Security Features
| Feature | Detail |
|---|---|
| **CSRF Protection** | Every POST request protected with Flask-WTF tokens |
| **Rate Limiting** | Login: 5/min · Register: 20/hr · Mark: 10/min · Save Face: 30/hr |
| **Geofencing** | 100-meter radius around Invertis University (lat/lng in `config.py`) |
| **Face Uniqueness** | Euclidean distance check vs ALL registered users before saving |
| **Spoofing Detection** | Distance > 0.8 logged as possible photo/spoof attack |
| **Device Fingerprinting** | SHA-256 hash of device ID stored per attendance record |
| **IP + User-Agent Logging** | Recorded for every attendance attempt |
| **Session Security** | HTTPOnly + SameSite=Lax cookies; Secure flag in production |
| **Password Security** | Scrypt hashing (stronger than bcrypt) |

### 🌐 Advanced Features
- 📊 **Firebase Cloud Sync** — Optional real-time cloud backup for attendance & attempts
- 🔄 **Startup Backfill** — On first launch after update, auto-creates daily attendance from existing session records
- 📧 **Email Notifications** — Sends attendance confirmation email on mark (configurable)
- 🗺️ **Location Storage** — Lat/lng saved per record for audit
- 📱 **Mobile Responsive** — Works on phones and tablets via Bootstrap

---

## 📁 Project File Structure

```
Face-Recognition-Attendance-System/
│
├── app.py                          # Main Flask app — all routes, business logic
│   ├── /register                   #   Account registration (student/teacher)
│   ├── /register_face              #   Face ID registration page
│   ├── /save_face                  #   API: save face descriptor + uniqueness check
│   ├── /login  /logout             #   Auth routes
│   ├── /dashboard                  #   Role-based dashboard (student/teacher/admin)
│   ├── /mark_attendance            #   Student attendance page + teacher daily
│   ├── /api/active_sessions        #   API: list live sessions for student
│   ├── /api/session_attendance/mark #  API: verify face+GPS, mark session attendance
│   ├── /teacher/courses/create     #   Create a course
│   ├── /teacher/courses/<id>/enroll #  Enroll student by email
│   ├── /teacher/sessions/create    #   Start a live class session
│   └── /teacher/sessions/<id>/close #  Close a session
│
├── models.py                       # SQLAlchemy database models
│   ├── User                        #   id, name, email, role, face_encoding, face_registered
│   ├── Attendance                  #   Daily attendance record (date + time)
│   ├── ClassSession                #   Live class session (course, room, start/end)
│   ├── SessionAttendance           #   Per-session attendance record per student
│   ├── Course                      #   Course (code, title, section, teacher)
│   ├── Enrollment                  #   Student ↔ Course link
│   └── AttendanceAttempt           #   Audit log of every attendance attempt
│
├── config.py                       # App configuration
│   ├── DB, secret key, timezone    #   Loaded from .env
│   ├── INVERTIS_LAT / INVERTIS_LNG #   Campus coordinates (Bareilly, UP)
│   ├── ALLOWED_RADIUS_METERS = 100 #   Geofence radius
│   └── Firebase / Email settings   #   Optional integrations
│
├── email_service.py                # Sends attendance confirmation emails via SMTP
├── firebase_service.py             # Optional Firebase Realtime DB sync
├── create_admin.py                 # One-time script to create admin account
├── manage.py                       # Flask-Migrate wrapper for DB migrations
├── wsgi.py                         # WSGI entry point for production (Gunicorn)
│
├── templates/                      # Jinja2 HTML templates
│   ├── base.html                   #   Base layout (navbar, footer, CSRF helper)
│   ├── index.html                  #   Landing page
│   ├── register.html               #   Registration form
│   ├── login.html                  #   Login form
│   ├── register_face.html          #   Face scan UI (silent 5-sample capture)
│   ├── student_dashboard.html      #   Student: courses, sessions, attendance %
│   ├── teacher_dashboard.html      #   Teacher: courses, sessions, student analytics
│   ├── admin_dashboard.html        #   Admin: all users, 7-day attendance grid
│   ├── mark_attendance.html        #   Teacher daily attendance page
│   ├── student_mark_attendance.html #  Student session attendance + face cam
│   └── user_dashboard.html         #  Generic profile dashboard
│
├── static/
│   ├── style.css                   #   Global styles (glassmorphism, dark theme)
│   ├── logo.svg                    #   App logo
│   └── favicon.svg                 #   Browser tab icon
│
├── scripts/
│   └── backup_db.py                #   Database backup utility script
│
├── deployment/
│   └── firebase.database.indexes.json  # Firebase Realtime DB index rules
│
├── tests/                          # Pytest test suite
│   ├── test_basic.py
│   ├── test_auth.py
│   ├── test_attendance.py
│   ├── test_api.py
│   └── test_security.py
│
├── instance/
│   └── attendance.db               # SQLite database (auto-created, gitignored)
│
├── requirements.txt                # Python dependencies
├── .env.example                    # Environment variable template
├── .env.firebase.example           # Firebase config template
├── .gitignore
├── README.md
├── LICENSE
├── CHANGELOG.md
└── CONTRIBUTING.md
```

---

## 🛠️ Tech Stack

### Backend
| Technology | Version | Purpose |
|------------|---------|---------|
| **Python** | 3.9+ | Core language |
| **Flask** | 3.0.0 | Web framework |
| **SQLAlchemy** | 3.1.1 | ORM for database |
| **Flask-Login** | 0.6.3 | User session management |
| **Flask-WTF** | Latest | CSRF protection |
| **Flask-Limiter** | 3.10.1 | Rate limiting |
| **Flask-Migrate** | 4.0.7 | Database migrations |
| **Firebase Admin** | 6.7.0 | Cloud sync (optional) |
| **Geopy** | 2.4.1 | Geodesic distance for geofencing |
| **NumPy** | Latest | Euclidean distance for face matching |

### Frontend
| Technology | Purpose |
|------------|---------|
| **HTML5 / CSS3** | Structure and styling |
| **JavaScript ES6+** | Client-side logic |
| **Bootstrap 5** | Responsive grid and components |
| **face-api.js 0.22.2** | Browser-side face detection and 128-D descriptor extraction |

### Database
| Type | Environment |
|------|-------------|
| **SQLite** | Development (auto-created at `instance/attendance.db`) |
| **PostgreSQL** | Production (set `DATABASE_URL` in `.env`) |

---

## 🏗️ System Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    CLIENT (Browser)                         │
│  [Camera API]  [face-api.js]  [Geolocation API]             │
│         ↓            ↓               ↓                      │
│              Fetch API (AJAX + CSRF Token)                   │
└──────────────────────┬──────────────────────────────────────┘
                       │ HTTPS POST
┌──────────────────────▼──────────────────────────────────────┐
│                  FLASK SERVER (app.py)                       │
│  [CSRF Check] → [Rate Limiter] → [Login Required]           │
│  [Role Validator] → [Business Logic] → [Face Uniqueness]    │
│                       ↓                                      │
│              models.py (SQLAlchemy ORM)                     │
│  User | Course | Enrollment | ClassSession                  │
│  SessionAttendance | Attendance | AttendanceAttempt         │
└──────────────┬───────────────────────────┬──────────────────┘
               ↓                           ↓
        SQLite / PostgreSQL         Firebase Realtime DB
         (Primary DB)               (Audit / Cloud Backup)
```

### Attendance Marking Flow (Student)
```
1. Student opens /mark_attendance
2. Browser loads face-api.js models from CDN
3. Camera starts → GPS location acquired
4. Student clicks "Verify and Mark Session Attendance"
5. face-api.js silently captures 5 frames → averages → 128-D vector
6. JavaScript validates: single face? inside geofence?
7. POST /api/session_attendance/mark  {session_id, descriptor, lat, lng, device_id}
8. Flask checks:
   ├── Session active and within time window?
   ├── Student enrolled in that course?
   ├── Within 100m of campus?
   ├── Face distance < 0.6 (Euclidean)?
   └── Not already marked for this session?
9. ✅ Save SessionAttendance + upsert daily Attendance record
10. Sync to Firebase (if configured)
11. Send email notification (if configured)
12. Return success → Student redirected to dashboard
```

### Face Registration Flow
```
1. Camera starts → face-api.js models load
2. User clicks "Scan My Face"
3. 5 face frames silently captured (500ms apart)
4. All 5 descriptors averaged → single robust 128-D vector
5. POST /save_face {descriptor: [128 floats]}
6. Server checks:
   ├── Valid 128-D vector with finite values?
   └── Distance vs ALL registered users < 0.50?  → 409 Conflict if match found
7. ✅ Save face_encoding + face_registered=True
8. Redirect to dashboard
```

---

## 🚀 Quick Start

### Prerequisites
- Python 3.9+
- pip
- Webcam
- HTTPS or localhost (required for camera + geolocation API)

### 1. Clone the Repository
```bash
git clone https://github.com/rajpratham1/Face-Recognition-Attendance-System.git
cd Face-Recognition-Attendance-System
```

### 2. Create Virtual Environment
```bash
# Windows
python -m venv venv
venv\Scripts\activate

# Linux / macOS
python3 -m venv venv
source venv/bin/activate
```

### 3. Install Dependencies
```bash
pip install -r requirements.txt
```

### 4. Set Up Environment Variables
```bash
cp .env.example .env
# Edit .env — minimum required: SECRET_KEY
```

### 5. Create Admin Account
```bash
python create_admin.py
```

### 6. Run the Application
```bash
# Development
python app.py

# Production
gunicorn wsgi:app
```

### 7. Open Browser
```
URL: http://localhost:5000
```

> **Note:** The database (`instance/attendance.db`) and all tables are auto-created on first run via `ensure_schema_compatibility()`.

---

## 💻 Installation

### Detailed Steps

#### Step 1: System Requirements
```bash
python --version   # Must be 3.9+

# Ubuntu/Debian
sudo apt-get install python3-dev libpq-dev build-essential

# Windows: Download from python.org
```

#### Step 2: Clone & Setup
```bash
git clone https://github.com/rajpratham1/Face-Recognition-Attendance-System.git
cd Face-Recognition-Attendance-System
python -m venv venv

# Windows PowerShell:
venv\Scripts\Activate.ps1
# Linux/Mac:
source venv/bin/activate
```

#### Step 3: Install Dependencies
```bash
pip install --upgrade pip
pip install -r requirements.txt
```

#### Step 4: Configure Environment
```bash
# Minimum .env config:
SECRET_KEY=your-random-32-char-secret-here
FLASK_ENV=development
APP_TIMEZONE=Asia/Kolkata
DATABASE_URL=sqlite:///attendance.db
SESSION_COOKIE_SECURE=0
```

#### Step 5: Create Admin
```bash
python create_admin.py
# Follow prompts to set admin email + password
```

#### Step 6: Run
```bash
python app.py
# Server starts at http://127.0.0.1:5000
```

---

## ⚙️ Configuration

### Environment Variables (`.env`)

```bash
# ── Required ────────────────────────────────────────────────
SECRET_KEY=your-secret-key-min-32-chars

# ── Flask ───────────────────────────────────────────────────
FLASK_ENV=production        # or development
APP_TIMEZONE=Asia/Kolkata   # Your timezone

# ── Database ────────────────────────────────────────────────
DATABASE_URL=sqlite:///attendance.db   # or PostgreSQL URL

# ── Security ────────────────────────────────────────────────
SESSION_COOKIE_SECURE=1     # Set 1 in production (HTTPS only)

# ── Email Notifications (Optional) ──────────────────────────
MAIL_SERVER=smtp.gmail.com
MAIL_PORT=587
MAIL_USERNAME=yourapp@gmail.com
MAIL_PASSWORD=your-16-char-app-password   # Gmail App Password
MAIL_FROM_NAME=Attendance System

# ── Firebase (Optional) ─────────────────────────────────────
FIREBASE_PROJECT_ID=your-project-id
FIREBASE_DATABASE_URL=https://your-project.firebaseio.com
FIREBASE_SERVICE_ACCOUNT_PATH=path/to/serviceAccountKey.json
FIREBASE_API_KEY=AIzaSy...
FIREBASE_AUTH_DOMAIN=your-project.firebaseapp.com
```

### Campus Location (`config.py`)

```python
# Invertis University, Bareilly, UP (default)
INVERTIS_LAT = 28.325764684367748
INVERTIS_LNG = 79.46097110207619
ALLOWED_RADIUS_METERS = 100   # 100-meter geofence
```

Change these values if deploying for a different institution.

### Face Matching Thresholds (`app.py`)

| Threshold | Value | Purpose |
|---|---|---|
| `FACE_DUPLICATE_THRESHOLD` | `0.50` | Block duplicate face registration |
| Face attendance match | `0.60` | Face must match within this distance |
| Spoofing alert | `0.80` | Distance > 0.8 flagged as possible photo attack |

---

## 📖 Usage Guide

### For Students

#### Register Account
1. Go to `/register`
2. Fill: Name, Email, Department, Password
3. Select role: **Student**
4. Accept biometric consent → Click **Register**

#### Register Face
1. Auto-redirected to `/register_face` after registration
2. Allow camera access
3. Wait for "AI models loaded" message
4. Look straight at the camera → Click **Scan My Face**
5. App silently captures and processes your face
6. ✅ Redirected to dashboard on success
7. ⛔ If face already registered to another account → shown a clear error

#### Mark Session Attendance
1. Go to `/mark_attendance`
2. Allow location access
3. Select active session from dropdown
4. Click **Verify and Mark Session Attendance**
5. Look at camera → verified → ✅ attendance marked
6. Both **session record** and **daily record** auto-updated

#### View Dashboard
- **My Enrolled Courses** — all courses you're in
- **Live Classes Available** — sessions active right now
- **My Session Attendance** — per-session history
- **My Daily Attendance Records** — daily log + percentage

---

### For Teachers

#### Create a Course
1. Dashboard → "Create Course" section
2. Enter: Code (`BCS23`), Title (`Data Structures`), Section (`A`)
3. Click **Add**

#### Enroll Students
1. Dashboard → "Enroll Student by Email"
2. Select course → Enter student email → Click **Enroll**

#### Start a Live Session
1. Dashboard → "Create Live Class Session"
2. Select course → Enter room (e.g., `Lab 301`) → Set duration
3. Click **Start Session** → Session goes live immediately

#### Close a Session
1. Find session in dashboard
2. Click **Close Session** → students can no longer mark attendance

---

### For Admins

1. Login with admin credentials
2. View all users with 7-day attendance grid
3. Check today's attendance count
4. Click **Print Report** to export as PDF

---

## 🔌 API Documentation

### `POST /save_face`
Save 128-D face descriptor after registration. Checks uniqueness across all users.

**Request:**
```json
{
  "descriptor": [0.123, 0.456, ..., 0.789]  // exactly 128 floats
}
```
**Success `200`:** `{"success": true}`
**Duplicate `409`:** `{"success": false, "message": "⚠ This face is already registered to another Student account."}`

---

### `POST /api/session_attendance/mark`
Mark attendance for a live class session.

**Request:**
```json
{
  "session_id": 1,
  "descriptor": [0.123, ..., 0.789],
  "lat": 28.325764,
  "lng": 79.460971,
  "device_id": "unique-device-string"
}
```
**Success `200`:**
```json
{"success": true, "message": "Attendance marked for BCS23 (hii)."}
```
**Failure reasons:** `Session not found` · `Student not enrolled` · `Session inactive` · `Outside campus` · `Duplicate mark` · `No face descriptor` · `Unknown face detected`

---

### `GET /api/active_sessions`
Get live sessions for the current student.

**Response:**
```json
{
  "sessions": [
    {"id": 1, "title": "Data Structures", "course_code": "CSE101", "room": "Lab 301", "ends_at": "14 Apr 2026 11:30 PM"}
  ]
}
```

---

### `POST /teacher/courses/create`
```
code=CSE101 & title=Data+Structures & section=A
```

### `POST /teacher/courses/<id>/enroll`
```
student_email=student@example.com
```

### `POST /teacher/sessions/create`
```
course_id=1 & room=Lab+301 & duration=30
```

### `POST /teacher/sessions/<id>/close`
Closes an active session.

---

## 🔒 Security

### All Protections at a Glance

| Layer | Implementation |
|---|---|
| CSRF | `Flask-WTF` token on every form + AJAX header |
| Rate Limiting | Per-route limits via `Flask-Limiter` |
| Authentication | `Flask-Login` session management |
| Password Hashing | `werkzeug` scrypt |
| Face Duplicates | Euclidean distance < 0.50 → block |
| Geofencing | `geopy.geodesic` < 100m |
| Audit Trail | `AttendanceAttempt` table logs every attempt |
| Session Cookies | HTTPOnly + SameSite=Lax + Secure (prod) |
| Device Tracking | SHA-256 device fingerprint per record |

### Privacy
- ✅ Stores: 128-float math descriptor, location, device hash, IP
- ❌ Does NOT store: face images, videos, raw biometric data

---

## 🐛 Troubleshooting

| Problem | Solution |
|---|---|
| Camera not working | Use HTTPS (required by browser security) or `localhost` |
| Face models not loading | Check internet · clear cache · models load from CDN |
| Location denied | Enable location in browser settings · use HTTPS |
| "Outside campus" error | Update `INVERTIS_LAT/LNG` in `config.py` · increase radius |
| Face registration blocked (409) | Same person already has an account — use existing login |
| Daily attendance shows 0 | Restart server — backfill runs automatically on startup |
| Firebase sync failing | Check `FIREBASE_DATABASE_URL` in `.env` · system works without it |
| Face verification always fails | Re-register face in good lighting · adjust threshold to `0.65` |

### Enable Debug Mode
```bash
# .env
FLASK_ENV=development

# Run
python app.py
```

---

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch: `git checkout -b feature/your-feature`
3. Follow PEP 8 (Python) and ES6+ (JavaScript)
4. Write tests in `tests/`
5. Commit: `git commit -m "feat: description"`
6. Push: `git push origin feature/your-feature`
7. Open a Pull Request

See [CONTRIBUTING.md](CONTRIBUTING.md) for full guidelines.

---

## 🧪 Testing

```bash
# Run all tests
pytest tests/

# With coverage report
pytest --cov=app --cov-report=html

# Specific file
pytest tests/test_auth.py -v
```

---

## 📊 Performance Tips

- Use PostgreSQL (not SQLite) in production for concurrent access
- Host face-api.js model weights locally in `static/models/` to avoid CDN dependency
- Use Redis for `RATELIMIT_STORAGE_URI` instead of `memory://` in multi-worker setups

---

## 📄 License

This project is licensed under the **MIT License** — see [LICENSE](LICENSE) for details.

---

## 👥 Authors & Contributors

- **Pratham Raj** — [GitHub @rajpratham1](https://github.com/rajpratham1)

---

## 🙏 Acknowledgments

- **Invertis University, Bareilly** — for project support
- **[face-api.js](https://github.com/justadudewhohacks/face-api.js)** — browser face recognition library
- **Flask** community — excellent framework and documentation
- **Bootstrap** team — responsive UI components

---

## 📞 Contact & Support

- **Email**: rajpratham40@gmail.com
- **Issues**: [GitHub Issues](https://github.com/rajpratham1/Face-Recognition-Attendance-System/issues)
- **Discussions**: [GitHub Discussions](https://github.com/rajpratham1/Face-Recognition-Attendance-System/discussions)

---

**⭐ If you find this project useful, please give it a star on GitHub!**

**Made with ❤️ by Pratham Raj**
