# Security & Privacy Documentation

## Overview

Face Recognition Attendance System implements multi-layered security measures to protect user data, prevent fraud, and ensure privacy compliance.

## Data We Collect

### Biometric Data
- **Face Descriptors**: 128-dimensional numerical vectors (NOT images)
- **Storage Format**: JSON array in database
- **Purpose**: Identity verification for attendance

### Location Data
- **Coordinates**: Latitude and longitude
- **Purpose**: Geofencing (ensure on-campus attendance)
- **Retention**: Stored with each attendance record

### Device Information
- **Device ID**: SHA-256 hash of browser identifier
- **Purpose**: Fraud detection (track multiple devices per user)
- **User Agent**: Browser and OS information
- **IP Address**: Network identifier

### Account Information
- **Name**: Full name
- **Email**: Unique identifier (login credential)
- **Department**: Organizational unit
- **Password**: Scrypt-hashed (never stored in plaintext)
- **Role**: Student, Teacher, or Admin

## Data We DON'T Collect

❌ Face images or videos  
❌ Audio recordings  
❌ Browsing history  
❌ Third-party tracking cookies  
❌ Unnecessary personal information  
❌ Financial information  

## Privacy Principles

### 1. Data Minimization
We only collect data necessary for attendance tracking.

### 2. Purpose Limitation
Data is used ONLY for:
- Attendance verification
- Fraud prevention
- System administration
- Legal compliance

### 3. Client-Side Processing
Face detection and descriptor extraction happen **in the browser**, not on servers. This means:
- No face images sent to server
- Faster processing
- Better privacy

### 4. User Consent
- Explicit biometric consent required during registration
- Users can view what data is collected
- Clear privacy policy

### 5. Data Security
- Encrypted HTTPS transmission
- Secure password hashing (Scrypt)
- Session security (HTTPOnly cookies)
- Rate limiting (prevent abuse)

## Security Measures

### Authentication Security

#### Password Protection
```
Plaintext Password → Scrypt Hashing → Database Storage
                     (with salt)
```

Features:
- Scrypt algorithm (stronger than bcrypt)
- Automatic salt generation
- Configurable work factor
- No password recovery (only reset)

#### Session Management
- Session cookies with HTTPOnly flag (prevent XSS)
- SameSite=Lax (prevent CSRF)
- Secure flag in production (HTTPS only)
- Automatic session expiry

### CSRF Protection

All state-changing requests require CSRF token:

```html
<form method="POST">
    <input type="hidden" name="csrf_token" value="{{ csrf_token() }}">
    <!-- form fields -->
</form>
```

JavaScript:
```javascript
fetch('/api/endpoint', {
    headers: {
        'X-CSRFToken': csrfToken
    }
})
```

### Rate Limiting

Prevents brute force attacks and abuse:

| Endpoint | Limit | Window |
|----------|-------|--------|
| Login | 5 requests | 1 minute |
| Registration | 20 requests | 1 hour |
| Face Save | 30 requests | 1 hour |
| Attendance | 10 requests | 1 minute |

### Geofencing

Prevents remote attendance marking:

```python
# Campus center coordinates
INVERTIS_LAT = 28.325764684367748
INVERTIS_LNG = 79.46097110207619

# Maximum distance allowed (meters)
ALLOWED_RADIUS_METERS = 100

# Validation
def is_within_invertis(lat, lng):
    distance = geodesic(
        (lat, lng),
        (INVERTIS_LAT, INVERTIS_LNG)
    ).meters
    return distance <= ALLOWED_RADIUS_METERS
```

### Face Verification Security

#### Threshold-Based Matching
```python
# Extract face descriptors
known_encoding = np.array(json.loads(user.face_encoding))
unknown_encoding = np.array(descriptor)

# Calculate Euclidean distance
distance = float(np.linalg.norm(known_encoding - unknown_encoding))

# Verify match
if distance < 0.6:  # Threshold
    # Face matched
    mark_attendance()
else:
    # Face mismatch
    log_failed_attempt()
```

#### Multi-Face Prevention
System rejects attendance if multiple faces detected:

```javascript
const faces = await faceapi.detectAllFaces(video);

if (faces.length !== 1) {
    alert('Exactly one face required');
    return;
}
```

#### Liveness Detection (UI-Based)
- User sees real-time camera feed
- Must position face in circle overlay
- Prevents photo/video spoofing (basic level)

**Note**: Advanced liveness detection (blink detection, head movement) planned for v2.0

### Device Fingerprinting

Tracks unique devices per user:

```javascript
const deviceId = (() => {
    const key = 'attendance_device_id';
    let id = localStorage.getItem(key);
    
    if (!id) {
        id = `${Date.now()}-${Math.random().toString(36)}`;
        localStorage.setItem(key, id);
    }
    
    return id;
})();

// SHA-256 hash on server
device_hash = hashlib.sha256(device_id.encode()).hexdigest()
```

Benefits:
- Detect attendance from multiple devices
- Identify suspicious patterns
- Audit trail for investigations

### Fraud Detection & Audit Logging

Every attendance attempt is logged in `AttendanceAttempt` table:

```python
class AttendanceAttempt(db.Model):
    session_id = ...
    student_id = ...
    success = Boolean  # True/False
    reason = String    # "Success", "Face mismatch", "Outside campus", etc.
    latitude = Float
    longitude = Float
    face_distance = Float
    device_hash = String
    ip_address = String
    user_agent = String
    created_at = DateTime
```

This enables:
- Identify repeated failed attempts
- Detect location spoofing
- Track device switching
- Investigate fraud complaints

## Threat Model

### Threats We Protect Against

#### ✅ Proxy Attendance
**Attack**: Friend marks attendance on behalf of absent student  
**Mitigation**: Face verification + geofencing + device tracking

#### ✅ Photo Spoofing (Basic)
**Attack**: Hold printed photo to camera  
**Mitigation**: UI-based liveness check (user sees real-time feed)

#### ✅ Location Spoofing
**Attack**: Fake GPS coordinates  
**Mitigation**: 
- Cross-reference with IP geolocation (future)
- Device tracking (multiple locations flagged)
- Manual teacher review

#### ✅ Brute Force
**Attack**: Repeatedly try different face descriptors  
**Mitigation**: Rate limiting + account lockout (planned)

#### ✅ Session Hijacking
**Attack**: Steal session cookie  
**Mitigation**: HTTPOnly cookies + SameSite=Lax + IP tracking

#### ✅ CSRF Attacks
**Attack**: Trick user into making unwanted requests  
**Mitigation**: CSRF tokens on all forms

#### ✅ XSS Attacks
**Attack**: Inject malicious JavaScript  
**Mitigation**: Template auto-escaping + CSP headers (planned)

#### ✅ SQL Injection
**Attack**: Inject SQL code via inputs  
**Mitigation**: SQLAlchemy ORM (parameterized queries)

### Threats We DON'T Fully Protect Against

#### ⚠️ Advanced Face Spoofing
**Attack**: Deepfake video, 3D mask  
**Status**: Not protected (requires specialized hardware)  
**Future**: Add blink detection, head movement analysis

#### ⚠️ Compromised Device
**Attack**: Malware on user's device modifies face descriptor  
**Status**: Limited protection  
**Mitigation**: Some protection via server-side validation

#### ⚠️ Database Breach
**Attack**: Attacker gains database access  
**Status**: Partial protection  
**Current**: Passwords hashed, but face descriptors not encrypted  
**Future**: Encrypt face descriptors at rest

#### ⚠️ Man-in-the-Middle
**Attack**: Intercept network traffic  
**Status**: Protected in production (HTTPS)  
**Current**: Development uses HTTP (local only)

## Compliance

### GDPR Compliance (EU)

**Right to Access**: Users can view their data via dashboard  
**Right to Erasure**: Admin can delete user accounts (planned)  
**Right to Portability**: Export data feature (planned)  
**Consent**: Explicit biometric consent required  
**Data Minimization**: Only necessary data collected  
**Purpose Limitation**: Data used only for attendance  

**To-Do for GDPR**:
- [ ] Privacy policy page
- [ ] Data export functionality
- [ ] Account deletion with data removal
- [ ] Data retention policy
- [ ] Data processing agreement

### CCPA Compliance (California)

**Disclosure**: System discloses data collected  
**Opt-Out**: Users can refuse biometric enrollment  
**Non-Discrimination**: Service works without biometric (manual attendance)  
**Access**: Users can request data access  

### India IT Act 2000 / SPDI Rules

**Consent**: Obtained before biometric collection  
**Security**: Reasonable security measures implemented  
**Sensitivity**: Biometric data treated as sensitive  
**Disclosure**: Users informed of data usage  

**Institution Responsibilities**:
- Obtain written consent from users
- Publish privacy policy
- Appoint data protection officer
- Conduct security audits
- Report data breaches

## Best Practices for Deployment

### For Administrators

1. **Enable HTTPS**: Always use HTTPS in production
2. **Strong Secrets**: Use cryptographically secure SECRET_KEY
3. **Regular Backups**: Automated daily backups
4. **Update Dependencies**: Keep libraries up-to-date
5. **Monitor Logs**: Review AttendanceAttempt for suspicious patterns
6. **User Training**: Educate users on security best practices
7. **Incident Response Plan**: Have plan for data breaches
8. **Access Control**: Limit admin access to trusted personnel
9. **Network Security**: Use firewall, VPN for admin access
10. **Compliance**: Ensure legal compliance in your jurisdiction

### For Developers

1. **Code Reviews**: Security review for all changes
2. **Input Validation**: Never trust user input
3. **Output Escaping**: Prevent XSS attacks
4. **Parameterized Queries**: Use ORM, avoid raw SQL
5. **Secrets Management**: Never commit secrets to Git
6. **Error Handling**: Don't expose sensitive info in errors
7. **Logging**: Log security events, not sensitive data
8. **Testing**: Security test cases for all features
9. **Documentation**: Document security assumptions
10. **Updates**: Monitor CVEs for dependencies

### For Users

1. **Strong Passwords**: Use unique, complex passwords
2. **Device Security**: Keep devices updated and secure
3. **Camera Privacy**: Be aware when camera is active
4. **Public Networks**: Avoid marking attendance on public WiFi
5. **Logout**: Always logout on shared devices
6. **Suspicious Activity**: Report unusual login attempts
7. **Consent**: Understand what data is collected
8. **Privacy Settings**: Review and adjust settings

## Incident Response

### Data Breach Response Plan

1. **Identify**: Detect breach via logs, user reports, monitoring
2. **Contain**: Disable affected accounts, revoke sessions
3. **Assess**: Determine scope (what data, how many users)
4. **Notify**: 
   - Inform affected users within 72 hours
   - Report to authorities if required
   - Public disclosure if necessary
5. **Remediate**: 
   - Patch vulnerability
   - Reset passwords
   - Update security measures
6. **Review**: 
   - Conduct post-mortem
   - Update security policies
   - Implement preventive measures

### Contact for Security Issues

**Email**: security@invertis.org  
**Response Time**: 24-48 hours  
**PGP Key**: Available on request  

**Please DO NOT** publicly disclose security vulnerabilities. Report privately first.

## Encryption

### Data in Transit
- HTTPS/TLS 1.2+ in production
- Encrypted WebSocket (WSS) planned for real-time features

### Data at Rest
**Currently Encrypted**:
- Passwords (Scrypt hashing)
- Session cookies (encrypted by Flask)

**NOT Encrypted** (planned for v2.0):
- Face descriptors in database
- Attendance records
- User personal information

**Why Not Encrypted Now?**
- Performance considerations for SQLite
- Complexity of key management
- Focus on MVP features first

**Future**: Implement transparent data encryption (TDE) or application-level encryption.

## Responsible Disclosure

If you discover a security vulnerability:

1. **Email**: security@invertis.org
2. **Include**:
   - Description of vulnerability
   - Steps to reproduce
   - Potential impact
   - Suggested fix (optional)
3. **Wait**: Give us 90 days to fix before public disclosure
4. **Credit**: We'll credit you in security advisory (if you want)

**Bug Bounty**: Not currently available, but may be added in future.

## Security Checklist

### Pre-Production
- [ ] Change default SECRET_KEY
- [ ] Enable HTTPS
- [ ] Set SESSION_COOKIE_SECURE=1
- [ ] Use PostgreSQL (not SQLite)
- [ ] Enable rate limiting with Redis
- [ ] Configure firewall
- [ ] Set up monitoring and alerts
- [ ] Conduct security audit
- [ ] Penetration testing
- [ ] Legal review (privacy policy, terms)

### Post-Production
- [ ] Monitor logs daily
- [ ] Review failed login attempts
- [ ] Check AttendanceAttempt for patterns
- [ ] Update dependencies monthly
- [ ] Security patches within 48 hours
- [ ] Backup verification weekly
- [ ] Access log review
- [ ] User feedback monitoring

## Resources

### Security Guidelines
- [OWASP Top 10](https://owasp.org/Top10/)
- [Flask Security Best Practices](https://flask.palletsprojects.com/en/latest/security/)
- [GDPR Guidelines](https://gdpr.eu/)
- [NIST Cybersecurity Framework](https://www.nist.gov/cyberframework)

### Tools
- **Dependency Scanning**: `safety check`
- **Code Analysis**: `bandit` for Python
- **Secrets Detection**: `git-secrets`, `truffleHog`
- **Penetration Testing**: `OWASP ZAP`, `Burp Suite`

---

**Document Version**: 1.0  
**Last Updated**: February 19, 2026  
**Maintainer**: IIOT Group Project Team  
**Review Cycle**: Quarterly
