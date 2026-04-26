# Security and Privacy

This project applies layered controls for authentication, abuse prevention, and attendance integrity.

## Data Classification

Collected data:
- Account profile data (name, email, role, department)
- Face descriptors (numeric vectors, not raw images)
- Attendance metadata (session, timestamps, location, device hash, IP, user agent)

Sensitive data:
- Password hash (scrypt)
- Face descriptor vectors
- Encrypted credential backup entries (if enabled)

Not stored by design:
- Raw face image archive on server
- Browser audio recordings

## Security Controls in Use

1. Authentication and session security
- Flask-Login for session auth
- Password hashing via werkzeug scrypt method
- Session cookie hardening via config flags

2. Request integrity
- CSRF protection via Flask-WTF
- CSRF token checks on form and API writes

3. Abuse prevention
- Endpoint-level rate limits on login/register/face save/attendance actions

4. Attendance anti-fraud controls
- Single-face validation on client before submit
- Geofence validation on server
- Enrollment and active-session checks
- Duplicate mark protection with DB unique constraints
- AttendanceAttempt audit trail for failed/success attempts

5. Admin hardening
- Admin-only route checks on management endpoints
- Dedicated role-change flow separate from profile edit flow
- Secret credentials route requires second-step secret key

6. Backup hardening
- Optional encrypted backup store using Fernet in separate DB
- Key from env or generated local key file under instance path

## Recommended Production Settings

Required:
- FLASK_ENV=production
- SESSION_COOKIE_SECURE=1
- strong SECRET_KEY
- secure DATABASE_URL

Recommended:
- ADMIN_SECRET_VIEW_KEY configured
- USER_BACKUP_ENCRYPTION_KEY configured explicitly
- HTTPS termination at load balancer/reverse proxy
- periodic DB backups and key backup policy

## Known Risk Areas

- Face recognition models are CDN-loaded in browser flows.
- Advanced anti-spoof (deepfake/3D mask) is not fully implemented.
- Secret credentials feature should be tightly restricted operationally.

## Operational Security Checklist

- Rotate admin credentials and secrets regularly.
- Restrict who can access production logs and backup DB files.
- Monitor repeated AttendanceAttempt failures.
- Audit role-change actions operationally.
- Keep dependencies patched.

## Incident Response Basics

If suspicious behavior is observed:
1. Preserve logs and database snapshot.
2. Disable affected user accounts.
3. Rotate sensitive secrets.
4. Review AttendanceAttempt patterns by user/device/IP.
5. Re-enable access after verification.

## Related Docs

- API.md
- ARCHITECTURE.md
- ../OPERATIONS.md