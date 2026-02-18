# Operations Quick Guide

## Database Migrations

1. Install dependencies:
   - `python -m pip install -r requirements.txt`
2. Initialize migrations once:
   - `flask --app manage.py db init`
3. Create migration after model changes:
   - `flask --app manage.py db migrate -m "schema update"`
4. Apply migrations:
   - `flask --app manage.py db upgrade`

## Backups

Create backup:
- `python scripts/backup_db.py`

Optional custom paths:
- `python scripts/backup_db.py --db instance/attendance.db --out backups`

## Production Run

- Set env vars from `.env.example`.
- Keep `FLASK_ENV=production`.
- Use: `gunicorn wsgi:app`

## Firebase Setup

1. Copy `.env.firebase.example` to `.env` and fill all Firebase values.
2. Add service account path in `FIREBASE_SERVICE_ACCOUNT_PATH`.
3. In Firebase Realtime Database, paste rules from `firebase.database.rules.json`.
4. Add indexes from `firebase.database.indexes.json`.
