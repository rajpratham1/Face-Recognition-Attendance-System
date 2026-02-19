# Project Structure

```
Face-Recognition-Attendance-System/
│
├── .github/                          # GitHub configuration
│   └── copilot-instructions.md      # AI assistant guidelines
│
├── deployment/                       # Deployment & Infrastructure
│   ├── Procfile                     # Heroku deployment config
│   ├── firebase.database.rules.json # Firebase security rules
│   └── firebase.database.indexes.json # Firebase DB indexes
│
├── docs/                             # Documentation
│   ├── requirements/                # Original project requirements
│   │   ├── Face_Recognition_Attendance_SRS.pdf
│   │   └── Jira_Backlog_Face_Recognition_Attendance_System.xlsx
│   ├── API.md                       # API reference documentation
│   ├── ARCHITECTURE.md              # System architecture details
│   └── SECURITY.md                  # Security & privacy documentation
│
├── instance/                         # Runtime instance data
│   └── attendance.db                # SQLite database (dev)
│
├── scripts/                          # Utility scripts
│   └── backup_db.py                 # Database backup utility
│
├── static/                           # Frontend static files
│   └── style.css                    # Application styles
│
├── templates/                        # Jinja2 HTML templates
│   ├── base.html                    # Base template layout
│   ├── index.html                   # Landing page
│   ├── login.html                   # Login page
│   ├── register.html                # User registration
│   ├── register_face.html           # Face registration
│   ├── mark_attendance.html         # Teacher attendance marking
│   ├── student_mark_attendance.html # Student session attendance
│   ├── student_dashboard.html       # Student dashboard
│   ├── teacher_dashboard.html       # Teacher dashboard
│   ├── admin_dashboard.html         # Admin dashboard
│   └── user_dashboard.html          # Generic user dashboard
│
├── tests/                            # Test suite
│   ├── test_basic.py                # Basic functionality tests
│   └── __pycache__/                 # Python cache (ignored)
│
├── .env.example                      # Environment variables template
├── .env.firebase.example            # Firebase config template
├── .gitignore                       # Git ignore rules
│
├── app.py                           # Main Flask application
├── config.py                        # Application configuration
├── create_admin.py                  # Admin user creation script
├── firebase_service.py              # Firebase integration
├── manage.py                        # Flask-Migrate management
├── models.py                        # Database models (SQLAlchemy)
├── wsgi.py                          # WSGI entry point for production
│
├── requirements.txt                 # Python dependencies
│
├── CHANGELOG.md                     # Version history
├── CONTRIBUTING.md                  # Contribution guidelines
├── LICENSE                          # MIT License
├── OPERATIONS.md                    # Operations guide
└── README.md                        # Project overview & setup

```

## Directory Descriptions

### Root Level Files

| File | Purpose |
|------|---------|
| **app.py** | Main Flask application - routes, business logic, controllers |
| **config.py** | Application configuration (database, timezone, geofencing) |
| **models.py** | SQLAlchemy database models (User, Course, Attendance, etc.) |
| **firebase_service.py** | Firebase Realtime Database integration |
| **manage.py** | Flask-Migrate database migration management |
| **wsgi.py** | WSGI entry point for Gunicorn/production servers |
| **create_admin.py** | Utility to create initial admin user |
| **requirements.txt** | Python package dependencies |

### Configuration Files

| File | Purpose |
|------|---------|
| **.env.example** | Template for environment variables |
| **.env.firebase.example** | Template for Firebase configuration |
| **.gitignore** | Git ignore patterns (comprehensive) |
| **OPERATIONS.md** | Quick operations guide (migrations, backups) |

### Documentation Files

| File | Purpose |
|------|---------|
| **README.md** | Main project documentation - setup, usage, features |
| **CHANGELOG.md** | Version history and migration guides |
| **CONTRIBUTING.md** | Developer contribution guidelines |
| **LICENSE** | MIT License |

### Folders

#### `.github/`
GitHub-specific configuration files:
- **copilot-instructions.md**: Guidelines for GitHub Copilot AI assistant

#### `deployment/`
Deployment and infrastructure configuration:
- **Procfile**: Heroku deployment configuration
- **firebase.database.rules.json**: Firebase security rules
- **firebase.database.indexes.json**: Firebase database indexes

#### `docs/`
All project documentation:
- **requirements/**: Original SRS and project planning documents
- **API.md**: Complete API reference with examples
- **ARCHITECTURE.md**: System design, component diagrams, data flow
- **SECURITY.md**: Security measures, threat model, compliance

#### `instance/`
Runtime instance data (not tracked in Git):
- **attendance.db**: SQLite database file (development)
- Flask creates this folder automatically for instance-specific files

#### `scripts/`
Utility scripts for maintenance:
- **backup_db.py**: Database backup script with custom path support

#### `static/`
Frontend static assets:
- **style.css**: Application CSS styles
- **models/**: (Future) Face recognition model files for offline use

#### `templates/`
Jinja2 HTML templates:
- **base.html**: Base layout with navbar, imports
- **Authentication**: login.html, register.html, register_face.html
- **Attendance**: mark_attendance.html, student_mark_attendance.html
- **Dashboards**: student_dashboard.html, teacher_dashboard.html, admin_dashboard.html

#### `tests/`
Test suite:
- **test_basic.py**: Basic functionality tests
- **test_api.py**: (Future) API endpoint tests
- **test_security.py**: (Future) Security tests

## File Import Structure

### How Files Connect

```
wsgi.py
  └── imports app from app.py

app.py
  ├── imports Config from config.py
  ├── imports models from models.py (User, Course, Attendance, etc.)
  ├── imports firebase_service from firebase_service.py
  └── uses templates/ for rendering

manage.py
  ├── imports app from app.py
  └── imports db from models.py

models.py
  └── defines database schema (standalone)

config.py
  └── reads environment variables

firebase_service.py
  └── Firebase Admin SDK integration

create_admin.py
  ├── imports app from app.py
  ├── imports db, User from models.py
  └── creates admin user
```

## Adding New Features

### New Route/Endpoint
1. Add route handler in **app.py**
2. Create template in **templates/**
3. Update **API.md** if API endpoint
4. Add tests in **tests/**

### New Database Model
1. Add model class in **models.py**
2. Create migration: `flask db migrate -m "description"`
3. Apply migration: `flask db upgrade`
4. Update **ARCHITECTURE.md** with schema changes

### New Static Asset
1. Add CSS to **static/style.css**
2. Add JS files to **static/js/** (if needed)
3. Reference in **templates/base.html**

### New Documentation
1. General docs → Update **README.md**
2. API changes → Update **docs/API.md**
3. Architecture changes → Update **docs/ARCHITECTURE.md**
4. Security changes → Update **docs/SECURITY.md**

## Environment Setup

### Development
```bash
# 1. Clone repository
git clone <repo-url>
cd Face-Recognition-Attendance-System

# 2. Create virtual environment
python -m venv venv
source venv/bin/activate  # Linux/Mac
venv\Scripts\activate     # Windows

# 3. Install dependencies
pip install -r requirements.txt

# 4. Setup environment
cp .env.example .env
# Edit .env with your configuration

# 5. Initialize database
flask db upgrade
python create_admin.py

# 6. Run development server
python app.py
```

### Production Deployment
```bash
# 1. Set environment variables (on hosting platform)
#    - SECRET_KEY
#    - DATABASE_URL
#    - FLASK_ENV=production

# 2. Use deployment/Procfile for Heroku
#    or configure Gunicorn manually

# 3. Use deployment/firebase.*.json for Firebase setup
```

## Important Notes

### DO NOT Track These Files
- `.env` (secrets!)
- `instance/*.db` (database)
- `__pycache__/` (Python cache)
- `*.pyc` (compiled Python)
- Firebase service account JSON files

### Always Track These Files
- `.env.example` (template)
- `requirements.txt` (dependencies)
- All `.py` files (source code)
- All documentation (`.md` files)
- Templates and static files

### Database Migrations
- **migrations/** folder tracks schema versions
- Create migration after model changes: `flask db migrate -m "message"`
- Apply migrations: `flask db upgrade`
- Rollback: `flask db downgrade`

## Questions?

See **README.md** for setup instructions or **CONTRIBUTING.md** for development guidelines.

---

**Last Updated**: February 19, 2026  
**Maintainer**: IIOT Group Project Team
