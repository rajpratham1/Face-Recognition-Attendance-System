# 🎓 Face Recognition Attendance System

[![Python](https://img.shields.io/badge/Python-3.9+-blue.svg)](https://www.python.org/downloads/)
[![Flask](https://img.shields.io/badge/Flask-3.0.0-green.svg)](https://flask.palletsprojects.com/)
[![License](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Status](https://img.shields.io/badge/Status-Active-success.svg)]()

A modern, secure, and intelligent attendance management system built for **Invertis University** that uses face recognition technology to eliminate proxy attendance and automate attendance tracking for academic institutions.

---

## 📋 Table of Contents

- [Overview](#-overview)
- [Key Features](#-key-features)
- [Tech Stack](#-tech-stack)
- [System Architecture](#-system-architecture)
- [Quick Start](#-quick-start)
- [Installation](#-installation)
- [Configuration](#-configuration)
- [Usage](#-usage)
- [API Documentation](#-api-documentation)
- [Security](#-security)
- [Contributing](#-contributing)
- [Testing](#-testing)
- [Troubleshooting](#-troubleshooting)
- [License](#-license)

---

## 🎯 Overview

Traditional attendance systems are prone to proxy attendance and manual errors. Our **Face Recognition Attendance System** leverages cutting-edge biometric technology to ensure:

- **100% Authentic Attendance**: Face verification prevents proxy attendance
- **Real-time Session Tracking**: Teachers create live sessions, students mark in real-time
- **Geofencing**: Location verification ensures on-campus attendance
- **Security & Privacy**: Client-side face processing, minimal data storage
- **Role-Based System**: Separate interfaces for Students, Teachers, and Admins

### 🎥 System Demo
```
Student Flow: Register → Scan Face → Enroll in Course → Join Live Session → Mark Attendance
Teacher Flow: Create Course → Enroll Students → Start Session → Monitor Attendance → Generate Reports
Admin Flow: Monitor System → View Analytics → Manage Users → Audit Logs
```

---

## ✨ Key Features

### 👤 For Students
- ✅ **Face Registration**: One-time biometric enrollment using webcam
- ✅ **Live Session View**: Real-time display of active class sessions
- ✅ **One-Click Attendance**: Face + location verification in seconds
- ✅ **Attendance History**: View session-wise and daily attendance records
- ✅ **Dashboard Analytics**: Track enrolled courses and attendance status

### 👨‍🏫 For Teachers
- ✅ **Course Management**: Create courses with sections
- ✅ **Student Enrollment**: Enroll students via email
- ✅ **Live Session Control**: Start sessions with customizable duration (5-120 mins)
- ✅ **Real-time Monitoring**: See attendance marking in real-time
- ✅ **Attendance Reports**: Download session-wise attendance data
- ✅ **Student Analytics**: View enrolled students' attendance patterns

### 👨‍💼 For Admins
- ✅ **System Dashboard**: Overview of all users, sessions, and attendance
- ✅ **User Management**: View and manage all faculty and students
- ✅ **Attendance Analytics**: 7-day attendance trends and statistics
- ✅ **Audit Logs**: Track all attendance attempts (successful and failed)
- ✅ **Fraud Detection**: Device fingerprinting and location tracking

### 🔐 Security Features
- 🛡️ **CSRF Protection**: All forms protected with CSRF tokens
- 🛡️ **Rate Limiting**: Prevents brute force and DoS attacks
- 🛡️ **Geofencing**: 100-meter radius enforcement from campus
- 🛡️ **Device Fingerprinting**: Tracks unique devices per user
- 🛡️ **IP Tracking**: Logs IP addresses for audit trails
- 🛡️ **Multi-Face Prevention**: Blocks attendance with multiple faces in frame
- 🛡️ **Session Security**: HTTPOnly cookies, secure session management

### 🌐 Advanced Features
- 📊 **Firebase Cloud Sync**: Optional real-time cloud backup
- 🗺️ **Geo-location Tracking**: Stores latitude/longitude for verification
- 📱 **Mobile Responsive**: Works on smartphones and tablets
- 🧪 **Liveness Detection**: UI prompts to prevent photo spoofing
- 📈 **Analytics Dashboard**: Visual attendance trends and statistics
- 🔄 **Database Migrations**: Schema versioning with Flask-Migrate

---

## 🛠️ Tech Stack

### Backend
| Technology | Version | Purpose |
|------------|---------|---------|
| **Python** | 3.9+ | Core language |
| **Flask** | 3.0.0 | Web framework |
| **SQLAlchemy** | 3.1.1 | ORM for database |
| **Flask-Login** | 0.6.3 | User session management |
| **Flask-Limiter** | 3.10.1 | Rate limiting |
| **Flask-Migrate** | 4.0.7 | Database migrations |
| **Firebase Admin** | 6.7.0 | Cloud sync (optional) |
| **Werkzeug** | 3.0.1 | WSGI utilities |
| **Geopy** | 2.4.1 | Geolocation distance calculation |
| **NumPy** | Latest | Face descriptor distance calculation |

### Frontend
| Technology | Purpose |
|------------|---------|
| **HTML5/CSS3** | Markup and styling |
| **JavaScript (ES6+)** | Client-side logic |
| **Bootstrap 5** | Responsive UI framework |
| **face-api.js** | Face detection and recognition |
| **Font Awesome** | Icons |

### Database
| Type | Environment | Purpose |
|------|-------------|---------|
| **SQLite** | Development | Local database |
| **PostgreSQL** | Production | Scalable cloud database |

### Deployment
| Service | Purpose |
|---------|---------|
| **Gunicorn** | WSGI server |
| **Heroku/AWS** | Cloud hosting |
| **Firebase Realtime DB** | Cloud backup & audit |

---

## 🏗️ System Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    CLIENT (Browser)                         │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐     │
│  │  Camera API  │  │  face-api.js │  │  Geolocation │     │
│  └──────┬───────┘  └──────┬───────┘  └──────┬───────┘     │
│         │                  │                  │              │
│         └──────────────────┼──────────────────┘              │
│                            │                                 │
│                    ┌───────▼────────┐                       │
│                    │  Fetch API     │                       │
│                    │  (AJAX + CSRF) │                       │
│                    └───────┬────────┘                       │
└────────────────────────────┼──────────────────────────────┘
                             │ HTTPS
┌────────────────────────────▼──────────────────────────────┐
│                    FLASK SERVER                            │
│  ┌──────────────────────────────────────────────────────┐ │
│  │         Application Layer (app.py)                   │ │
│  │  ┌────────────┐  ┌────────────┐  ┌────────────┐    │ │
│  │  │   Routes   │  │ Auth Logic │  │  Business  │    │ │
│  │  │  Handlers  │  │  (Login)   │  │   Logic    │    │ │
│  │  └────────────┘  └────────────┘  └────────────┘    │ │
│  └──────────────────────────────────────────────────────┘ │
│                                                             │
│  ┌──────────────────────────────────────────────────────┐ │
│  │         Security Layer                                │ │
│  │  [CSRF Protection][Rate Limiter][Role Validator]     │ │
│  └──────────────────────────────────────────────────────┘ │
│                                                             │
│  ┌──────────────────────────────────────────────────────┐ │
│  │         Data Layer (models.py)                       │ │
│  │  [User][Course][Enrollment][ClassSession]            │ │
│  │  [SessionAttendance][AttendanceAttempt]              │ │
│  └──────────────────────────────────────────────────────┘ │
│                            │                               │
└────────────────────────────┼───────────────────────────────┘
                             │
                ┌────────────┴────────────┐
                │                         │
        ┌───────▼─────┐         ┌────────▼─────────┐
        │  SQLite/    │         │  Firebase         │
        │  PostgreSQL │         │  Realtime DB      │
        │  (Primary)  │         │  (Audit/Backup)   │
        └─────────────┘         └──────────────────┘
```

### Data Flow - Student Marking Attendance

```
1. Student opens /mark_attendance
2. Browser requests camera + geolocation permissions
3. face-api.js loads models from CDN
4. Student clicks "Verify and Mark Attendance"
5. face-api.js detects face → extracts 128-D descriptor
6. JavaScript checks: single face? geofence OK?
7. Sends POST to /api/session_attendance/mark with:
   - session_id
   - descriptor (128 floats)
   - latitude, longitude
   - device_id (localStorage)
8. Flask validates:
   - Session active?
   - Student enrolled in course?
   - Within 100m of campus?
   - Face matches registered descriptor?
   - Not already marked?
9. If valid: Save to SessionAttendance + AttendanceAttempt
10. Sync to Firebase (optional)
11. Return success → Redirect to dashboard
```

---

## 🚀 Quick Start

### Prerequisites
- Python 3.9 or higher
- pip (Python package manager)
- Webcam (for face registration)
- HTTPS connection (for geolocation API)

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

# Linux/Mac
python3 -m venv venv
source venv/bin/activate
```

### 3. Install Dependencies
```bash
pip install -r requirements.txt
```

### 4. Set Up Environment Variables
```bash
# Create .env file
cp .env.example .env

# Edit .env with your configuration
# Minimum required: SECRET_KEY
```

### 5. Initialize Database
```bash
# Create database and apply migrations
flask --app manage.py db init
flask --app manage.py db migrate -m "Initial schema"
flask --app manage.py db upgrade

# Create admin user
python create_admin.py
```

### 6. Run the Application
```bash
# Development mode
python app.py

# Production mode
gunicorn wsgi:app
```

### 7. Access the System
```
URL: http://localhost:5000
Admin Login: admin@invertis.org / admin123
```

---

## 💻 Installation

### Detailed Installation Steps

#### Step 1: System Requirements
```bash
# Check Python version
python --version  # Should be 3.9 or higher

# Install system dependencies (Ubuntu/Debian)
sudo apt-get update
sudo apt-get install python3-dev libpq-dev build-essential

# For macOS
brew install python@3.9

# For Windows: Download Python from python.org
```

#### Step 2: Clone and Setup
```bash
git clone https://github.com/rajpratham1/Face-Recognition-Attendance-System.git
cd Face-Recognition-Attendance-System

# Create virtual environment
python -m venv venv

# Activate virtual environment
# Windows PowerShell:
venv\Scripts\Activate.ps1
# Windows CMD:
venv\Scripts\activate.bat
# Linux/Mac:
source venv/bin/activate
```

#### Step 3: Install Python Dependencies
```bash
pip install --upgrade pip
pip install -r requirements.txt

# Verify installation
pip list | grep Flask
# Should show: Flask==3.0.0
```

#### Step 4: Database Setup
```bash
# Option A: SQLite (Default - Development)
# No additional setup needed, database auto-created

# Option B: PostgreSQL (Production)
# 1. Install PostgreSQL
sudo apt-get install postgresql postgresql-contrib

# 2. Create database
sudo -u postgres psql
CREATE DATABASE attendance_db;
CREATE USER attendance_user WITH PASSWORD 'your_password';
GRANT ALL PRIVILEGES ON DATABASE attendance_db TO attendance_user;
\q

# 3. Set DATABASE_URL in .env
DATABASE_URL=postgresql://attendance_user:your_password@localhost/attendance_db
```

#### Step 5: Environment Configuration
```bash
# Create .env file
cat > .env << EOF
SECRET_KEY=$(python -c 'import secrets; print(secrets.token_hex(32))')
FLASK_ENV=development
APP_TIMEZONE=Asia/Kolkata
DATABASE_URL=sqlite:///attendance.db
SESSION_COOKIE_SECURE=0
EOF
```

#### Step 6: Initialize Database Schema
```bash
# Initialize Flask-Migrate
flask --app manage.py db init

# Generate migration
flask --app manage.py db migrate -m "Initial schema"

# Apply migration
flask --app manage.py db upgrade

# Create admin user
python create_admin.py
```

#### Step 7: Verify Installation
```bash
# Run tests
pytest tests/

# Start development server
python app.py

# Open browser: http://localhost:5000
```

---

## ⚙️ Configuration

### Environment Variables

Create a `.env` file in the root directory:

```bash
# Required Configuration
SECRET_KEY=your-secret-key-here-generate-with-secrets.token_hex

# Flask Configuration
FLASK_ENV=production  # or 'development'
DEBUG=0               # Set to 1 only in development

# Database Configuration
DATABASE_URL=sqlite:///attendance.db  # or PostgreSQL URL

# Timezone
APP_TIMEZONE=Asia/Kolkata  # Adjust to your timezone

# Security
SESSION_COOKIE_SECURE=1  # Set to 1 in production with HTTPS
SESSION_COOKIE_HTTPONLY=1
SESSION_COOKIE_SAMESITE=Lax

# Rate Limiting
RATELIMIT_STORAGE_URI=memory://  # or redis://localhost:6379

# Firebase (Optional - for cloud sync)
FIREBASE_PROJECT_ID=your-project-id
FIREBASE_DATABASE_URL=https://your-project.firebaseio.com
FIREBASE_SERVICE_ACCOUNT_PATH=path/to/serviceAccountKey.json

# Firebase Web SDK Config (Optional)
FIREBASE_API_KEY=AIzaSyXXXXXXXXXXXXXXXXXXXX
FIREBASE_AUTH_DOMAIN=your-project.firebaseapp.com
FIREBASE_STORAGE_BUCKET=your-project.appspot.com
FIREBASE_MESSAGING_SENDER_ID=123456789
FIREBASE_APP_ID=1:123456789:web:abcdef123456
```

### Campus Location Configuration

Edit `config.py` to set your university coordinates:

```python
# config.py
class Config:
    # Your University Coordinates
    INVERTIS_LAT = 28.325764684367748  # Replace with your campus latitude
    INVERTIS_LNG = 79.46097110207619   # Replace with your campus longitude
    ALLOWED_RADIUS_METERS = 100        # Geofence radius in meters
```

### Face Recognition Threshold

Adjust face matching sensitivity in `app.py`:

```python
# app.py - Line ~307 and ~540
FACE_MATCH_THRESHOLD = 0.6  # Lower = stricter, Higher = lenient
if distance < FACE_MATCH_THRESHOLD:
    # Face matched
```

---

## 📖 Usage

### For Students

#### 1. Register Account
1. Visit `/register`
2. Fill in: Name, Email, Department, Password
3. Select role: **Student**
4. Accept biometric consent
5. Click "Register"

#### 2. Register Face
1. After registration, you'll be redirected to face registration
2. Allow camera access
3. Wait for AI models to load
4. Position face in the circle
5. Click "Scan My Face"
6. Face descriptor saved (128-D vector)

#### 3. View Dashboard
1. Login and go to `/dashboard`
2. See enrolled courses
3. View live sessions
4. Check attendance history

#### 4. Mark Attendance
1. Click "Open Session Attendance"
2. Allow location access
3. Select active session from dropdown
4. Click "Refresh" to update sessions
5. Click "Verify and Mark Session Attendance"
6. Look at camera for face verification
7. Success → Redirected to dashboard

### For Teachers

#### 1. Create Course
1. Login and go to `/dashboard`
2. In "Create Course" section:
   - Code: e.g., "CSE101"
   - Title: e.g., "Data Structures"
   - Section: e.g., "A"
3. Click "Add"

#### 2. Enroll Students
1. In "Enroll Student by Email":
   - Select course from dropdown
   - Enter student email
   - Click "Enroll"
2. Student must be registered with role="student"

#### 3. Create Live Session
1. In "Create Live Class Session":
   - Select course
   - Enter room/lab (e.g., "Lab 301")
   - Select duration (10-45 minutes)
   - Click "Start Session"
2. Session becomes live immediately
3. Students can now mark attendance

#### 4. Monitor Attendance
1. View "Session Attendance Panel"
2. See live vs closed sessions
3. Check "Marked" count per session
4. Close session manually if needed

#### 5. Close Session
1. Find session in "Session Attendance Panel"
2. Click "Close Session" button
3. Students can no longer mark attendance

### For Admins

#### 1. View System Dashboard
1. Login with admin credentials
2. View all users (students, teachers, admins)
3. See 7-day attendance trends
4. Check today's attendance count

#### 2. Print Reports
1. On admin dashboard
2. Click "Print Report" button
3. Browser print dialog opens
4. Save as PDF or print

---

## 🔌 API Documentation

### Authentication Endpoints

#### POST `/register`
Register new user account.

**Form Data:**
```json
{
  "name": "John Doe",
  "email": "john@example.com",
  "department": "Computer Science",
  "password": "securepassword123",
  "role": "student",
  "consent": "yes"
}
```

**Response:** Redirect to `/register_face`

---

#### POST `/login`
Authenticate user and create session.

**Form Data:**
```json
{
  "email": "john@example.com",
  "password": "securepassword123"
}
```

**Response:** Redirect to `/dashboard`

---

### Face Recognition Endpoints

#### POST `/save_face`
Save user's face descriptor after registration.

**Headers:**
```
Content-Type: application/json
X-CSRFToken: <token>
```

**JSON Body:**
```json
{
  "descriptor": [0.1234, 0.5678, ..., 0.9012]  // 128 floats
}
```

**Response:**
```json
{
  "success": true
}
```

---

### Attendance Endpoints

#### GET `/api/active_sessions`
Get list of active class sessions for current student.

**Headers:**
```
Cookie: session=<session_cookie>
```

**Response:**
```json
{
  "sessions": [
    {
      "id": 1,
      "title": "Data Structures",
      "course_code": "CSE101",
      "room": "Lab 301",
      "ends_at": "2026-02-19 03:45 PM"
    }
  ]
}
```

---

#### POST `/api/session_attendance/mark`
Mark attendance for a class session.

**Headers:**
```
Content-Type: application/json
X-CSRFToken: <token>
```

**JSON Body:**
```json
{
  "session_id": 1,
  "descriptor": [0.1234, ..., 0.9012],  // 128 floats
  "lat": 28.325764684367748,
  "lng": 79.46097110207619,
  "device_id": "unique-device-identifier"
}
```

**Success Response (200):**
```json
{
  "success": true,
  "message": "Attendance marked for CSE101 (Data Structures)."
}
```

**Error Response (400/403):**
```json
{
  "success": false,
  "message": "You are not enrolled for this course."
}
```

**Error Reasons:**
- `"Session not found"`
- `"Student not enrolled"`
- `"Session inactive"`
- `"Outside campus"`
- `"Duplicate mark"`
- `"No face descriptor"`
- `"Face mismatch"`

---

### Teacher Endpoints

#### POST `/teacher/courses/create`
Create new course.

**Form Data:**
```json
{
  "code": "CSE101",
  "title": "Data Structures",
  "section": "A"
}
```

---

#### POST `/teacher/courses/<course_id>/enroll`
Enroll student in course.

**Form Data:**
```json
{
  "student_email": "student@example.com"
}
```

---

#### POST `/teacher/sessions/create`
Create live class session.

**Form Data:**
```json
{
  "course_id": 1,
  "room": "Lab 301",
  "duration": 30  // minutes
}
```

---

#### POST `/teacher/sessions/<session_id>/close`
Close active session.

**Response:** Redirect to `/dashboard`

---

## 🔒 Security

### Security Measures Implemented

#### 1. **CSRF Protection**
- All forms protected with Flask-WTF CSRF tokens
- Token validation on every POST request
- Auto-refresh on token expiry

#### 2. **Rate Limiting**
```python
Login: 5 requests per minute
Registration: 20 requests per hour
Face Save: 30 requests per hour
Mark Attendance: 10 requests per minute
```

#### 3. **Geofencing**
- Location verification using geopy
- 100-meter radius from campus center
- Rejects attendance outside boundary

#### 4. **Face Verification**
- Euclidean distance threshold: 0.6
- Multi-face detection prevention
- Client-side processing (privacy)

#### 5. **Device Fingerprinting**
- Unique device ID stored in localStorage
- SHA-256 hashing of device identifier
- Tracks attendance from multiple devices

#### 6. **Audit Logging**
- All attendance attempts logged
- Tracks: success/failure, reason, location, face distance
- IP address and user agent recording

#### 7. **Session Security**
- HTTPOnly cookies prevent XSS
- SameSite=Lax prevents CSRF
- Secure flag in production (HTTPS)

#### 8. **Password Security**
- Scrypt hashing (more secure than bcrypt)
- No plaintext storage
- Password minimum length enforced

### Privacy Considerations

✅ **What We Store:**
- Face descriptors (128 floats - mathematical representation)
- Location coordinates (latitude/longitude)
- Device hash (SHA-256)
- IP address (for audit)

❌ **What We DON'T Store:**
- Face images or videos
- Raw device information
- Biometric templates (only descriptors)

### Security Best Practices for Deployment

1. **Always use HTTPS in production**
2. **Set strong SECRET_KEY** (32+ characters)
3. **Enable SESSION_COOKIE_SECURE=1**
4. **Use PostgreSQL with SSL** (not SQLite)
5. **Set up firewall** (only ports 80/443 open)
6. **Regular backups** (use `scripts/backup_db.py`)
7. **Monitor logs** (check AttendanceAttempt table)
8. **Update dependencies** regularly

---

## 🤝 Contributing

We welcome contributions! Please follow these guidelines:

### Development Workflow

1. **Fork the repository**
2. **Create feature branch**
   ```bash
   git checkout -b feature/your-feature-name
   ```
3. **Make changes**
   - Follow PEP 8 style guide
   - Add docstrings to functions
   - Write unit tests
4. **Test changes**
   ```bash
   pytest tests/
   ```
5. **Commit changes**
   ```bash
   git commit -m "Add: Description of your changes"
   ```
6. **Push to branch**
   ```bash
   git push origin feature/your-feature-name
   ```
7. **Create Pull Request**

### Coding Standards

#### Python
- Use type hints: `def func(param: int) -> str:`
- Follow PEP 8 naming conventions
- Add docstrings for all functions
- Use SQLAlchemy ORM (no raw SQL)

#### JavaScript
- Use ES6+ syntax (const/let, arrow functions)
- Add JSDoc comments for functions
- Use async/await for asynchronous operations

#### Git Commit Messages
```
Add: New feature implementation
Fix: Bug fix description
Update: Changes to existing feature
Refactor: Code refactoring
Docs: Documentation updates
Test: Test additions or modifications
```

See [CONTRIBUTING.md](CONTRIBUTING.md) for detailed guidelines.

---

## 🧪 Testing

### Running Tests

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=app --cov-report=html

# Run specific test file
pytest tests/test_basic.py

# Run with verbose output
pytest -v
```

### Test Structure

```
tests/
├── test_basic.py           # Basic app tests
├── test_auth.py            # Authentication tests
├── test_attendance.py      # Attendance logic tests
├── test_api.py             # API endpoint tests
└── test_security.py        # Security tests
```

### Writing Tests

Example test:
```python
def test_mark_attendance_success(client, auth_student):
    """Test successful attendance marking"""
    # Setup
    session = create_test_session()
    
    # Execute
    response = client.post('/api/session_attendance/mark', json={
        'session_id': session.id,
        'descriptor': [0.1] * 128,
        'lat': 28.325764684367748,
        'lng': 79.46097110207619
    })
    
    # Assert
    assert response.status_code == 200
    assert response.json['success'] == True
```

---

## 🐛 Troubleshooting

### Common Issues

#### Issue: Camera not working
**Solution:**
- Ensure HTTPS connection (required for camera API)
- Check browser permissions (allow camera access)
- Try different browser (Chrome/Firefox recommended)

#### Issue: Face models not loading
**Solution:**
- Check internet connection (models loaded from CDN)
- Clear browser cache
- Host models locally in `/static/models/`

#### Issue: Location access denied
**Solution:**
- Enable location services in browser
- Check device location settings
- Use HTTPS (required for geolocation API)

#### Issue: "Outside campus" error even when on campus
**Solution:**
- Update campus coordinates in `config.py`
- Increase `ALLOWED_RADIUS_METERS`
- Check GPS accuracy on device

#### Issue: Database migration errors
**Solution:**
```bash
# Reset migrations
rm -rf migrations/
flask --app manage.py db init
flask --app manage.py db migrate -m "Initial schema"
flask --app manage.py db upgrade
```

#### Issue: Firebase sync not working
**Solution:**
- Verify `FIREBASE_DATABASE_URL` in `.env`
- Check service account JSON file path
- Ensure Firebase Realtime Database is enabled
- System works without Firebase (optional feature)

#### Issue: Face verification always fails
**Solution:**
- Re-register face in good lighting
- Ensure single face in frame
- Adjust `FACE_MATCH_THRESHOLD` (increase to 0.7)
- Check console for face distance values

### Debug Mode

Enable debug mode for detailed errors:

```bash
# .env
FLASK_ENV=development
DEBUG=1

# Run with debug
python app.py
```

### Logs

Check logs for errors:
```bash
# Application logs
tail -f app.log

# Database queries
# Set in config.py:
SQLALCHEMY_ECHO = True
```

---

## 📊 Performance Optimization

### Database Optimization
- Use indexes on foreign keys (already implemented)
- Implement pagination for large datasets
- Use connection pooling in production

### Face Recognition Optimization
- Use `detectSingleFace()` instead of `detectAllFaces()`
- Cache face descriptors after registration
- Implement throttling for real-time detection

### Caching
```python
# Add Flask-Caching
from flask_caching import Cache
cache = Cache(app, config={'CACHE_TYPE': 'simple'})

@cache.cached(timeout=300)
@app.route('/dashboard')
def dashboard():
    # Expensive operations cached for 5 minutes
    pass
```

---

## 📄 License

This project is licensed under the **MIT License** - see the [LICENSE](LICENSE) file for details.

```
MIT License

Copyright (c) 2026 IIOT Group Project Team

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
```

---

## 👥 Authors & Contributors

- **IIOT Group Project Team** - *Initial work* - [GitHub](https://github.com/rajpratham1)

See also the list of [contributors](https://github.com/rajpratham1/Face-Recognition-Attendance-System/contributors) who participated in this project.

---

## 🙏 Acknowledgments

- **Invertis University** for project support
- **face-api.js** team for the amazing face recognition library
- **Flask** community for excellent documentation
- **Bootstrap** team for the UI framework

---

## 📞 Contact & Support

- **Email**: support@invertis.org
- **Issues**: [GitHub Issues](https://github.com/rajpratham1/Face-Recognition-Attendance-System/issues)
- **Discussions**: [GitHub Discussions](https://github.com/rajpratham1/Face-Recognition-Attendance-System/discussions)

---


**⭐ If you find this project useful, please give it a star on GitHub!**

**Made with ❤️ by IIOT Group Project Team**
