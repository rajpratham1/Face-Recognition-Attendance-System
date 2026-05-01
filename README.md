<div align="center">
  <br />
  <img src="https://raw.githubusercontent.com/rajpratham1/Face-Recognition-Attendance-System/main/static/logo.svg" alt="AstraTech Logo" width="100" onerror="this.src='https://cdn-icons-png.flaticon.com/512/8206/8206846.png'" />
  
  <h1 align="center">Face Recognition Attendance System</h1>
  
  <p align="center">
    <strong>An Advance AI Group Project by Team AstraTech</strong><br>
    Built exclusively for Invertis University
  </p>
  
  <p align="center">
    <a href="https://github.com/rajpratham1/Face-Recognition-Attendance-System"><img src="https://img.shields.io/badge/Developed_by-Team_AstraTech-0f172a?style=for-the-badge&logo=rocket" alt="Team AstraTech" /></a>
    <a href="https://github.com/rajpratham1/Face-Recognition-Attendance-System"><img src="https://img.shields.io/github/repo-size/rajpratham1/Face-Recognition-Attendance-System?style=for-the-badge&color=2563eb" alt="Repo Size" /></a>
    <a href="https://github.com/rajpratham1/Face-Recognition-Attendance-System"><img src="https://img.shields.io/github/license/rajpratham1/Face-Recognition-Attendance-System?style=for-the-badge&color=10b981" alt="License" /></a>
  </p>

  <p align="center">
    <img src="https://readme-typing-svg.herokuapp.com?font=Outfit&weight=600&size=24&pause=1000&color=2563EB&center=true&vCenter=true&width=600&lines=Zero+Proxy+Attendance.;AI+Face+Verification.;Smart+Attendance+Predictions.;Real-Time+Dashboard+Updates.;Strict+Campus+Geofencing.;Lightning+Fast+Processing." alt="Typing SVG" />
  </p>
</div>

---

<br>

## 🌌 Overview

This system drastically reduces proxy attendance and manual entry errors by utilizing advanced face verification, strict campus geofencing, and real-time session tracking. It features a modern, premium **Glassmorphism UI** that provides a beautiful, animated, and intuitive experience for students, teachers, and administrators.

**New in Latest Version:**
- 🧠 **Smart Attendance Predictions** - AI tells students exactly how many classes they need to attend to reach 75%
- 🔥 **Streak Tracking** - Gamified attendance streaks to motivate students
- ⚡ **Real-Time Updates** - All dashboards auto-refresh with live data (no page reload needed)
- 📊 **Enhanced Analytics** - Comprehensive insights for students, teachers, and admins
- 🎯 **Status Indicators** - Color-coded attendance status (Good/Warning/Critical)
- 🔄 **Automated Sessions** - Auto-generate class sessions from timetable entries

<br>

## ✨ Core Features

<table>
  <tr>
    <td width="50%">
      <h3 align="center">🎨 Modern UI & UX</h3>
      <ul>
        <li><strong>Glassmorphism Design:</strong> Beautiful, responsive UI with sleek animations and deep dark themes.</li>
        <li><strong>Real-Time Updates:</strong> Auto-refreshing dashboards with live attendance counts and session status.</li>
        <li><strong>AJAX Contact Form:</strong> Built-in support form that sends messages directly to admin email seamlessly.</li>
        <li><strong>Spam Protection:</strong> Mathematical CAPTCHA integrated into the contact system.</li>
        <li><strong>Legal & About Pages:</strong> Dynamic and beautifully crafted policy and terms pages.</li>
      </ul>
    </td>
    <td width="50%">
      <h3 align="center">👨‍🎓 Student Portal</h3>
      <ul>
        <li>Securely map facial vectors (128-dimensional descriptor, <b>no photos stored</b>).</li>
        <li><strong>Smart Attendance Insights:</strong> AI-powered predictions showing exactly how many classes needed to reach 75%.</li>
        <li><strong>Attendance Streak Tracking:</strong> Gamified streak counter to motivate consistent attendance.</li>
        <li>View active class sessions in real-time with countdown timers.</li>
        <li>Mark attendance using <strong>Face Verification</strong> + <strong>Location Checks</strong>.</li>
        <li>Course-wise attendance breakdown with status indicators (Good/Warning/Critical).</li>
        <li>View session and daily attendance history with calendar view.</li>
      </ul>
    </td>
  </tr>
  <tr>
    <td width="50%">
      <h3 align="center">👩‍🏫 Teacher Dashboard</h3>
      <ul>
        <li>Create and manage courses with section-wise assignments.</li>
        <li>Enroll students securely via email or bulk CSV upload.</li>
        <li>Start and close live class sessions with GPS-based classroom location.</li>
        <li><strong>Real-Time Session Monitoring:</strong> Live attendance counts with auto-refresh every 30 seconds.</li>
        <li>Enhanced session cards showing marked, failed, and pending students.</li>
        <li>Kiosk mode for hands-free attendance marking.</li>
        <li>Export detailed CSV reports with timestamps and student details.</li>
        <li><strong>Automated Timetable Integration:</strong> Auto-generate sessions from timetable entries.</li>
      </ul>
    </td>
    <td width="50%">
      <h3 align="center">🛡️ Admin Panel</h3>
      <ul>
        <li>System-wide user and attendance overview with real-time stats.</li>
        <li><strong>Comprehensive Dashboard:</strong> Track total students, teachers, courses, active sessions, and low attendance alerts.</li>
        <li>Bulk operations: CSV import for students, section assignments, and course enrollments.</li>
        <li>Department-wise registration statistics with progress tracking.</li>
        <li>7-day attendance heat grid for visual attendance patterns.</li>
        <li>Manage Data: Clear face data, delete users, edit profiles, change roles.</li>
        <li>Role management and system configuration.</li>
        <li><strong>Auto-refresh:</strong> Dashboard stats update every 60 seconds.</li>
      </ul>
    </td>
  </tr>
</table>

<br>

## 🔐 Security Highlights

| Feature | Description |
| :--- | :--- |
| **Liveness Detection** | Advanced anti-spoofing with blink detection, head movement tracking, and texture analysis to prevent photo/video attacks. |
| **Strict Geofencing** | Users can only mark attendance if their GPS coordinates fall strictly within the configurable campus radius (e.g., 100 meters). |
| **Edge Biometrics** | The system runs purely on edge devices for privacy. Facial descriptors cannot be reverse-engineered into photographs. |
| **Single-Face Checks** | Advanced AI ensures only *one* face is in the camera frame during attendance. |
| **Audit Logging** | Every attendance attempt is logged securely with IP, user-agent, and device hashes. |
| **API Defense** | Protected via **scrypt password hashing**, **CSRF tokens**, and strict **Rate Limiting**. |

<br>

## 🚀 New Features & Enhancements

### 📊 Smart Attendance Insights
- **Predictive Analytics**: Students see exactly how many classes they need to attend to reach 75% attendance
- **Attendance Forecasting**: Real-time calculations based on current attendance trends
- **Course-wise Breakdown**: Detailed attendance percentage for each enrolled course
- **Status Indicators**: Visual color-coded status (Good ≥75%, Warning ≥65%, Critical <65%)

### 🔥 Gamification
- **Streak Tracking**: Consecutive days attendance counter with fire emoji
- **Motivational Messages**: Encouraging feedback based on attendance performance
- **Progress Bars**: Visual representation of attendance progress

### ⚡ Real-Time Dashboard Updates
- **Auto-Refresh**: Student dashboard updates every 30 seconds
- **Teacher Dashboard**: Live session stats refresh every 30 seconds
- **Admin Dashboard**: System-wide stats update every 60 seconds
- **No Page Reload**: Seamless updates using AJAX calls

### 🎯 Enhanced Teacher Features
- **Live Session Monitoring**: Real-time attendance counts during active sessions
- **Session Cards**: Enhanced UI showing marked, failed, and pending students
- **Kiosk Mode**: Hands-free attendance marking for classroom deployment
- **Bulk Operations**: Mark multiple students present/absent at once
- **Automated Timetable**: Auto-generate sessions from timetable entries

### 🛡️ Admin Enhancements
- **Comprehensive Stats**: Total students, teachers, courses, active sessions, low attendance alerts
- **Department Analytics**: Registration statistics by department with progress tracking
- **7-Day Heat Grid**: Visual attendance patterns across the week
- **Bulk Import**: CSV upload for students, sections, and enrollments
- **Real-Time Monitoring**: Live system health and usage statistics

<br>

## ⚙️ Tech Stack

<div align="center">
  <code><img height="40" src="https://raw.githubusercontent.com/devicons/devicon/master/icons/python/python-original.svg" alt="Python"></code>
  <code><img height="40" src="https://raw.githubusercontent.com/devicons/devicon/master/icons/flask/flask-original.svg" alt="Flask"></code>
  <code><img height="40" src="https://raw.githubusercontent.com/devicons/devicon/master/icons/html5/html5-original.svg" alt="HTML5"></code>
  <code><img height="40" src="https://raw.githubusercontent.com/devicons/devicon/master/icons/css3/css3-original.svg" alt="CSS3"></code>
  <code><img height="40" src="https://raw.githubusercontent.com/devicons/devicon/master/icons/bootstrap/bootstrap-original.svg" alt="Bootstrap"></code>
  <code><img height="40" src="https://raw.githubusercontent.com/devicons/devicon/master/icons/javascript/javascript-original.svg" alt="JavaScript"></code>
</div>

<br>

## 🚀 Quick Start Guide

### 1. Clone the Repository
```bash
git clone https://github.com/rajpratham1/Face-Recognition-Attendance-System.git
cd Face-Recognition-Attendance-System
```

### 2. Install Dependencies
Ensure you have Python 3.9 or higher installed.
```bash
pip install -r requirements.txt
```

### 3. Configure Environment Variables
Copy the example environment file and configure it:
```bash
cp .env.example .env
```
Open `.env` and fill in the required variables. **Crucial variables include:**
- `SECRET_KEY`: Set to a long, random string.
- `INVERTIS_LAT` & `INVERTIS_LNG`: Your campus coordinates.
- `ALLOWED_RADIUS_METERS`: Maximum distance (in meters) for marking attendance.
- `GEOFENCE_ENFORCED`: Set to `1` for production, `0` to disable location blocking during local testing.

### 4. Run the Application
```bash
python app.py
```
The server will start on `http://127.0.0.1:5000`. 

<br>

## 📝 Development Notes

- **Database Path:** The primary SQLite database is stored at `instance/attendance.db`.
- **Firebase Deployment:** The `deployment/` folder contains configuration rules (`firebase.json`, `firestore.rules`, etc.) if you wish to adapt this project for Firebase hosting or backend synchronization.

<br>

## 🔌 API Endpoints

The system provides RESTful API endpoints for real-time data access:

### Student APIs
- `GET /api/student/attendance_stats` - Comprehensive attendance statistics
- `GET /api/student/attendance_insights` - Smart predictions and required classes
- `GET /api/student/attendance_alert` - Low attendance warnings
- `GET /api/student/active_sessions` - Real-time active sessions list

### Teacher APIs
- `GET /api/teacher/dashboard_stats` - Dashboard overview metrics
- `GET /api/teacher/session/<id>/stats` - Real-time session statistics

### Admin APIs
- `GET /api/admin/dashboard_stats` - System-wide statistics
- `GET /api/admin/courses` - All courses list
- `GET /api/admin/course_sections/<id>` - Available sections for a course
- `POST /api/admin/generate_sessions` - Auto-generate sessions from timetable

### General APIs
- `GET /api/session_counts` - Session counts by status
- `GET /api/my_course_attendance` - User's course attendance data
- `GET /api/my_attendance_calendar` - Calendar view data

<br>

---

<div align="center">
  <p><b>An Advance AI Group Project developed with ❤️ by Team AstraTech</b></p>
  <p>&copy; 2026 Team AstraTech - Invertis University</p>
</div>
