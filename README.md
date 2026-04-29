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
    <img src="https://readme-typing-svg.herokuapp.com?font=Outfit&weight=600&size=24&pause=1000&color=2563EB&center=true&vCenter=true&width=600&lines=Zero+Proxy+Attendance.;AI+Face+Verification.;Strict+Campus+Geofencing.;Lightning+Fast+Processing." alt="Typing SVG" />
  </p>
</div>

---

<br>

## 🌌 Overview

This system drastically reduces proxy attendance and manual entry errors by utilizing advanced face verification, strict campus geofencing, and real-time session tracking. It features a modern, premium **Glassmorphism UI** that provides a beautiful, animated, and intuitive experience for students, teachers, and administrators.

<br>

## ✨ Core Features

<table>
  <tr>
    <td width="50%">
      <h3 align="center">🎨 Modern UI & UX</h3>
      <ul>
        <li><strong>Glassmorphism Design:</strong> Beautiful, responsive UI with sleek animations and deep dark themes.</li>
        <li><strong>AJAX Contact Form:</strong> Built-in support form that sends messages directly to admin email seamlessly.</li>
        <li><strong>Spam Protection:</strong> Mathematical CAPTCHA integrated into the contact system.</li>
        <li><strong>Legal & About Pages:</strong> Dynamic and beautifully crafted policy and terms pages.</li>
      </ul>
    </td>
    <td width="50%">
      <h3 align="center">👨‍🎓 Student Portal</h3>
      <ul>
        <li>Securely map facial vectors (128-dimensional descriptor, <b>no photos stored</b>).</li>
        <li>View active class sessions in real-time.</li>
        <li>Mark attendance using <strong>Face Verification</strong> + <strong>Location Checks</strong>.</li>
        <li>View session and daily attendance history.</li>
      </ul>
    </td>
  </tr>
  <tr>
    <td width="50%">
      <h3 align="center">👩‍🏫 Teacher Dashboard</h3>
      <ul>
        <li>Create and manage courses instantly.</li>
        <li>Enroll students securely via email.</li>
        <li>Start and close live class sessions with a single click.</li>
        <li>View real-time attendance counts and export CSV reports.</li>
      </ul>
    </td>
    <td width="50%">
      <h3 align="center">🛡️ Admin Panel</h3>
      <ul>
        <li>System-wide user and attendance overview.</li>
        <li>Manage Data: Clear face data, delete users, edit profiles.</li>
        <li>Role management and system configuration.</li>
      </ul>
    </td>
  </tr>
</table>

<br>

## 🔐 Security Highlights

| Feature | Description |
| :--- | :--- |
| **Strict Geofencing** | Users can only mark attendance if their GPS coordinates fall strictly within the configurable campus radius (e.g., 100 meters). |
| **Edge Biometrics** | The system runs purely on edge devices for privacy. Facial descriptors cannot be reverse-engineered into photographs. |
| **Single-Face Checks** | Advanced AI ensures only *one* face is in the camera frame during attendance. |
| **Audit Logging** | Every attendance attempt is logged securely with IP, user-agent, and device hashes. |
| **API Defense** | Protected via **scrypt password hashing**, **CSRF tokens**, and strict **Rate Limiting**. |

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

---

<div align="center">
  <p><b>An Advance AI Group Project developed with ❤️ by Team AstraTech</b></p>
  <p>&copy; 2026 Team AstraTech - Invertis University</p>
</div>
