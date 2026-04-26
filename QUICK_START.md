# Quick Start

## 1) Prerequisites

- Python 3.9+
- Git

Check version:

```bash
python --version
git --version
```

## 2) Setup

```bash
# Clone
git clone <your-repo-url>
cd Face-Recognition-Attendance-System

# Create venv
python -m venv venv

# Activate (Windows)
venv\Scripts\activate

# Install deps
pip install -r requirements.txt

# Configure env
copy .env.example .env
```

## 3) Initialize and Run

```bash
# Optional: create admin account
python create_admin.py

# Run app
python app.py
```

Open: http://localhost:5000

## 4) First Login

If you used `create_admin.py`:
- Email: `admin@invertis.org`
- Password: `admin123`

Change this in real deployments.

## 5) Typical Flows

### Student
1. Register
2. Register face
3. Wait for live session
4. Mark attendance

### Teacher
1. Login
2. Create course
3. Enroll student
4. Start live session
5. Close session and review report

### Admin
1. Login
2. Review users and attendance
3. Manage user profile/role actions

## Troubleshooting

- Camera denied: allow browser camera permission
- Location denied: allow GPS permission
- Outside campus: verify geofence values in `.env`
- Import errors: ensure venv is activated
- DB issues: check `instance/attendance.db` exists and is writable

## Next Docs

- Docs index: [docs/README.md](docs/README.md)
- Operations: [OPERATIONS.md](OPERATIONS.md)
- API details: [docs/API.md](docs/API.md)
- Security model: [docs/SECURITY.md](docs/SECURITY.md)