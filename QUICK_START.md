# Quick Start Guide

## 🚀 5-Minute Setup

### Prerequisites Check
```bash
python --version  # Must be 3.9+
git --version
```

### Installation
```bash
# 1. Clone & Navigate
git clone https://github.com/rajpratham1/Face-Recognition-Attendance-System.git
cd Face-Recognition-Attendance-System

# 2. Virtual Environment
python -m venv venv
venv\Scripts\activate  # Windows
# source venv/bin/activate  # Linux/Mac

# 3. Install Dependencies
pip install -r requirements.txt

# 4. Configure Environment
copy .env.example .env
# Edit .env: Set SECRET_KEY

# 5. Initialize Database
flask db upgrade
python create_admin.py

# 6. Run Application
python app.py
```

### Access Application
```
URL: http://localhost:5000
Admin: admin@invertis.org / admin123
```

---

## 📁 Project Structure Overview

```
Face-Recognition-Attendance-System/
├── 📄 Main Application Files
│   ├── app.py                 # Flask application (routes & controllers)
│   ├── models.py              # Database models
│   ├── config.py              # Configuration
│   └── firebase_service.py    # Firebase integration
│
├── 📂 deployment/             # Deployment configs
│   ├── Procfile              # Heroku
│   └── firebase.*.json       # Firebase setup
│
├── 📂 docs/                   # Documentation
│   ├── requirements/         # SRS & Jira backlog
│   ├── API.md               # API reference
│   ├── ARCHITECTURE.md      # System design
│   └── SECURITY.md          # Security guide
│
├── 📂 templates/              # HTML templates
├── 📂 static/                 # CSS, JS, images
├── 📂 tests/                  # Test suite
├── 📂 scripts/                # Utility scripts
│
└── 📄 Documentation
    ├── README.md             # Main documentation
    ├── CONTRIBUTING.md       # Developer guide
    ├── CHANGELOG.md          # Version history
    ├── OPERATIONS.md         # Operations guide
    └── PROJECT_STRUCTURE.md  # This file
```

---

## 🎯 Common Tasks

### Database Operations
```bash
# Create migration after model changes
flask db migrate -m "Add new column"

# Apply migrations
flask db upgrade

# Rollback one migration
flask db downgrade

# View migration history
flask db history

# Backup database
python scripts/backup_db.py
```

### User Management
```bash
# Create admin user
python create_admin.py

# In Python shell:
from app import app, db, User
from werkzeug.security import generate_password_hash

with app.app_context():
    # Create teacher
    teacher = User(
        name="John Doe",
        email="john@example.com",
        department="CS",
        role="teacher",
        password_hash=generate_password_hash("password")
    )
    db.session.add(teacher)
    db.session.commit()
```

### Running Tests
```bash
# All tests
pytest

# Specific test file
pytest tests/test_basic.py

# With coverage
pytest --cov=app --cov-report=html

# View coverage report
start htmlcov/index.html  # Windows
```

### Development Server
```bash
# Development mode (auto-reload)
python app.py

# Production mode (Gunicorn)
gunicorn wsgi:app

# With specific port
gunicorn wsgi:app --bind 0.0.0.0:8000
```

---

## 🔧 Configuration

### Environment Variables (.env)
```bash
# Required
SECRET_KEY=generate-with-secrets-module

# Database
DATABASE_URL=sqlite:///attendance.db

# Optional
FIREBASE_PROJECT_ID=your-project
FIREBASE_DATABASE_URL=https://...
```

### Campus Location (config.py)
```python
INVERTIS_LAT = 28.325764684367748
INVERTIS_LNG = 79.46097110207619
ALLOWED_RADIUS_METERS = 100
```

---

## 📝 Workflows

### Student Workflow
1. Register → `/register`
2. Register Face → `/register_face`
3. Login → `/login`
4. View Dashboard → `/dashboard`
5. Mark Attendance → `/mark_attendance`

### Teacher Workflow
1. Login → `/login`
2. Create Course → Dashboard → "Create Course"
3. Enroll Students → Dashboard → "Enroll Student by Email"
4. Start Live Session → Dashboard → "Create Live Class Session"
5. Monitor Attendance → Dashboard → "Session Attendance Panel"
6. Close Session → Click "Close Session" button

### Admin Workflow
1. Login → `/login`
2. View All Users → Dashboard → Users table
3. Check Attendance → Dashboard → 7-day attendance grid
4. Review Logs → (UI planned for v1.1)

---

## 🐛 Troubleshooting

### Common Issues

**Camera not working**
```
Solution: Use HTTPS or localhost, enable camera permissions
```

**Face models not loading**
```
Solution: Check internet connection (models from CDN)
```

**Database locked error**
```
Solution: Close all connections, restart server
```

**"Outside campus" error**
```
Solution: Update campus coordinates in config.py
```

**Import errors**
```
Solution: Activate virtual environment, reinstall requirements
```

### Debug Mode
```bash
# Enable in .env
FLASK_ENV=development
DEBUG=1

# Run with Flask debugger
flask run --debug
```

---

## 📚 Documentation Links

| Document | Purpose |
|----------|---------|
| [README.md](../README.md) | Main documentation & setup |
| [API.md](docs/API.md) | API reference |
| [ARCHITECTURE.md](docs/ARCHITECTURE.md) | System design |
| [SECURITY.md](docs/SECURITY.md) | Security guide |
| [CONTRIBUTING.md](../CONTRIBUTING.md) | Developer guide |
| [CHANGELOG.md](../CHANGELOG.md) | Version history |
| [OPERATIONS.md](../OPERATIONS.md) | Operations guide |

---

## 🔗 Useful Commands

### Git
```bash
# Check status
git status

# Check ignored files
git status --ignored

# Add all changes
git add .

# Commit
git commit -m "Description"

# Push
git push origin main
```

### Python Package Management
```bash
# Install package
pip install package-name

# Update requirements.txt
pip freeze > requirements.txt

# Install from requirements
pip install -r requirements.txt

# Update all packages
pip list --outdated
pip install --upgrade package-name
```

### Virtual Environment
```bash
# Create
python -m venv venv

# Activate
venv\Scripts\activate          # Windows PowerShell
venv\Scripts\activate.bat      # Windows CMD
source venv/bin/activate       # Linux/Mac

# Deactivate
deactivate

# Remove
rm -rf venv  # Linux/Mac
rmdir /s venv  # Windows
```

---

## 💡 Tips

### Development
- Use `pytest -s` to see print statements during tests
- Use `flask shell` for interactive Python console with app context
- Use browser DevTools (F12) to debug JavaScript face detection
- Check `app.log` for error messages

### Production
- Always use PostgreSQL, not SQLite
- Set `SECRET_KEY` to strong random value
- Enable `SESSION_COOKIE_SECURE=1` with HTTPS
- Use Redis for rate limiting: `RATELIMIT_STORAGE_URI=redis://...`
- Set up automated database backups

### Security
- Never commit `.env` file
- Keep dependencies updated: `pip list --outdated`
- Review `AttendanceAttempt` table regularly for fraud
- Monitor failed login attempts
- Use strong passwords for admin accounts

---

## 📞 Support

- **Issues**: GitHub Issues
- **Email**: support@invertis.org
- **Documentation**: See docs/ folder

---

**Last Updated**: February 19, 2026  
**Version**: 1.0.0
