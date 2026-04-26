# Changelog

All notable changes to this project are documented in this file.

## Unreleased

### Added
- Separate encrypted backup service for credentials in user_backup_service.py
- Optional backup configuration keys:
  - USER_BACKUP_DB_PATH
  - USER_BACKUP_ENCRYPTION_KEY
  - USER_BACKUP_KEY_PATH
- Admin secret-key gated credentials page: /admin/secret_credentials
- Admin user management improvements:
  - limited profile edit action
  - dedicated role-change action (student/teacher)
- Seed utility script under seed_users/test.py for test account creation
- Dashboard UI refresh across student, teacher, and admin pages
- Home page redesign with clearer role-based action hierarchy

### Changed
- Admin user edit authority reduced to safer fields only
- Navigation made role-aware to reduce feature confusion
- Documentation consolidated and cleaned to remove outdated overlap

### Removed
- PROJECT_STRUCTURE.md (redundant doc removed)

## 1.0.0 - 2026-02-19

### Initial public release
- Role-based attendance system with face verification
- Geofence checks and session attendance
- Teacher course/session management
- Admin monitoring dashboard