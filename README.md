# Face Recognition Attendance System

A role-based attendance platform with face verification, geofence checks, and session-based classroom tracking.

## Why This Project

This system is built to reduce proxy attendance and manual entry errors by combining:
- Face descriptor matching
- Campus geofence validation
- Course enrollment validation
- Session-level attendance records with audit logs

## Core Features

### Student
- Register account and face
- View active class sessions
- Mark attendance with face + location checks
- View session and daily attendance history

### Teacher
- Create courses
- Enroll students by email
- Start and close live class sessions
- View attendance counts and course reports
- Export attendance CSV

### Admin
- View system-wide user and attendance overview
- Clear face data
- Delete users
- Edit limited user profile fields
- Change user role via dedicated admin action

## Security Highlights

- Password hashing with scrypt
- CSRF protection on forms and APIs
- Rate limits on sensitive endpoints
- Geofence enforcement with configurable radius
- Single-face checks during attendance marking
- Attendance attempt audit logs (reason, device hash, IP, user-agent)
- Optional encrypted credentials backup in separate instance DB
- Optional second-step secret key route for protected credential view

## Tech Stack

- Python 3.9+
- Flask
- SQLAlchemy
- Flask-Login
- Flask-WTF
- Flask-Limiter
- NumPy
- Geopy
- face-api.js (browser side)

## Quick Start

See [QUICK_START.md](QUICK_START.md) for setup in minutes.

## Configuration

Use [.env.example](.env.example) as the base for your local `.env`.

Important variables:
- `SECRET_KEY`
- `DATABASE_URL`
- `APP_TIMEZONE`
- `GEOFENCE_ENFORCED`
- `INVERTIS_LAT`, `INVERTIS_LNG`, `ALLOWED_RADIUS_METERS`
- `SESSION_LOCATION_RADIUS_METERS`
- `ADMIN_SECRET_VIEW_KEY`
- `USER_BACKUP_DB_PATH`, `USER_BACKUP_ENCRYPTION_KEY`, `USER_BACKUP_KEY_PATH`

## Documentation Map

- [docs/README.md](docs/README.md): Documentation index and reading paths
- [QUICK_START.md](QUICK_START.md): Fast local setup and first run
- [OPERATIONS.md](OPERATIONS.md): Backup, run, and maintenance commands
- [docs/API.md](docs/API.md): Endpoint-level reference
- [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md): System design and data flow
- [docs/SECURITY.md](docs/SECURITY.md): Security and privacy model
- [CONTRIBUTING.md](CONTRIBUTING.md): Contribution workflow
- [CHANGELOG.md](CHANGELOG.md): Release history

## Development Notes

- Primary dev DB path: `instance/attendance.db`
- Encrypted backup DB path (default): `instance/userbackup.db`
- Backup encryption key path (default): `instance/userbackup.key`

## License

This project is licensed under the MIT License. See [LICENSE](LICENSE).
