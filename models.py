from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from datetime import datetime, timezone, date, timedelta
from sqlalchemy import Index, event
from sqlalchemy.orm import validates

db = SQLAlchemy()


class User(UserMixin, db.Model):
    __tablename__ = 'users'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False, index=True)
    email = db.Column(db.String(120), unique=True, nullable=False, index=True)
    phone = db.Column(db.String(15), unique=True, nullable=True, index=True)  # Phone number for notifications
    department = db.Column(db.String(100), nullable=False, index=True)
    password_hash = db.Column(db.String(256), nullable=False)
    role = db.Column(db.String(20), default='student', index=True)  # student / teacher / admin
    college_id = db.Column(db.String(50), nullable=True, index=True)
    section = db.Column(db.String(10), nullable=True, index=True)
    year = db.Column(db.String(10), nullable=True)
    semester = db.Column(db.String(10), nullable=True)
    assignment_status = db.Column(db.String(20), default='pending', index=True)  # pending / assigned
    face_encoding = db.Column(db.Text, nullable=True)   # JSON of 128-D vector
    face_registered = db.Column(db.Boolean, default=False, index=True)
    registered_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))
    is_active = db.Column(db.Boolean, default=True, index=True)
    last_login = db.Column(db.DateTime, nullable=True)

    attendances = db.relationship('Attendance', backref='user', lazy=True, cascade='all, delete-orphan')
    created_sessions = db.relationship('ClassSession', backref='teacher', lazy=True, foreign_keys='ClassSession.teacher_id', cascade='all, delete-orphan')
    session_attendances = db.relationship('SessionAttendance', backref='student', lazy=True, foreign_keys='SessionAttendance.student_id', cascade='all, delete-orphan')
    teacher_courses = db.relationship('Course', backref='teacher', lazy=True, foreign_keys='Course.teacher_id', cascade='all, delete-orphan')
    enrollments = db.relationship('Enrollment', backref='student', lazy=True, foreign_keys='Enrollment.student_id', cascade='all, delete-orphan')
    attendance_attempts = db.relationship('AttendanceAttempt', backref='attempted_by_student', lazy=True, foreign_keys='AttendanceAttempt.student_id')

    @validates('email')
    def validate_email(self, key, email):
        """Validate email format"""
        if not email or '@' not in email:
            raise ValueError('Invalid email address')
        return email.lower().strip()

    @validates('role')
    def validate_role(self, key, role):
        """Validate role is one of allowed values"""
        allowed_roles = ['student', 'teacher', 'admin']
        if role not in allowed_roles:
            raise ValueError(f'Role must be one of: {", ".join(allowed_roles)}')
        return role

    def update_last_login(self):
        """Update last login timestamp"""
        self.last_login = datetime.now(timezone.utc)
        db.session.commit()

    def get_attendance_percentage(self, start_date=None, end_date=None):
        """Calculate attendance percentage for date range"""
        query = SessionAttendance.query.filter_by(student_id=self.id)
        
        if start_date:
            query = query.filter(SessionAttendance.marked_at >= start_date)
        if end_date:
            query = query.filter(SessionAttendance.marked_at <= end_date)
        
        attended = query.count()
        
        # Get total eligible sessions
        enrolled_courses = [e.course_id for e in self.enrollments]
        if not enrolled_courses:
            return 0.0
        
        total_query = ClassSession.query.filter(
            ClassSession.course_id.in_(enrolled_courses),
            ClassSession.starts_at <= datetime.now(timezone.utc)
        )
        
        if start_date:
            total_query = total_query.filter(ClassSession.starts_at >= start_date)
        if end_date:
            total_query = total_query.filter(ClassSession.starts_at <= end_date)
        
        total = total_query.count()
        
        return round((attended / total * 100), 2) if total > 0 else 0.0

    def has_face_registered(self):
        """Check if user has completed face registration"""
        return self.face_registered and self.face_encoding is not None

    def __repr__(self):
        return f'<User {self.name} ({self.role})>'


class Attendance(db.Model):
    __tablename__ = 'attendance'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False, index=True)
    date = db.Column(db.Date, nullable=False, index=True)
    time = db.Column(db.Time, nullable=False)
    status = db.Column(db.String(20), default='present', index=True)
    latitude = db.Column(db.Float, nullable=True)
    longitude = db.Column(db.Float, nullable=True)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))

    __table_args__ = (
        db.UniqueConstraint('user_id', 'date', name='unique_attendance_per_day'),
        Index('idx_user_date', 'user_id', 'date'),
        Index('idx_date_status', 'date', 'status'),
    )

    @validates('status')
    def validate_status(self, key, status):
        """Validate status is one of allowed values"""
        allowed_statuses = ['present', 'absent', 'late', 'excused']
        if status not in allowed_statuses:
            raise ValueError(f'Status must be one of: {", ".join(allowed_statuses)}')
        return status

    def is_today(self):
        """Check if attendance is for today"""
        return self.date == date.today()

    def __repr__(self):
        return f'<Attendance {self.user_id} - {self.date} ({self.status})>'


class ClassSession(db.Model):
    __tablename__ = 'class_sessions'

    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(120), nullable=False)
    course_code = db.Column(db.String(40), nullable=False, index=True)
    room = db.Column(db.String(80), nullable=False)
    course_id = db.Column(db.Integer, db.ForeignKey('courses.id'), nullable=True, index=True)
    section = db.Column(db.String(10), nullable=True, index=True)  # Section for this session
    starts_at = db.Column(db.DateTime, nullable=False, index=True)
    ends_at = db.Column(db.DateTime, nullable=False, index=True)
    is_active = db.Column(db.Boolean, default=True, index=True)
    location_lat = db.Column(db.Float, nullable=True)
    location_lng = db.Column(db.Float, nullable=True)
    location_radius_meters = db.Column(db.Integer, nullable=False, default=50)
    teacher_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False, index=True)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

    session_attendances = db.relationship('SessionAttendance', backref='session', lazy=True, cascade='all, delete-orphan')

    __table_args__ = (
        Index('idx_teacher_active', 'teacher_id', 'is_active'),
        Index('idx_course_starts', 'course_id', 'starts_at'),
        Index('idx_active_time', 'is_active', 'starts_at', 'ends_at'),
        Index('idx_course_section', 'course_id', 'section'),
    )

    def is_currently_active(self):
        """Check if session is currently active"""
        now = datetime.now(timezone.utc)
        return self.is_active and self.starts_at <= now <= self.ends_at

    def get_attendance_count(self):
        """Get number of students who marked attendance"""
        return SessionAttendance.query.filter_by(session_id=self.id).count()

    def get_enrolled_count(self):
        """Get number of enrolled students for this session's course"""
        if not self.course_id:
            return 0
        return Enrollment.query.filter_by(course_id=self.course_id).count()

    def get_attendance_percentage(self):
        """Calculate attendance percentage for this session"""
        enrolled = self.get_enrolled_count()
        if enrolled == 0:
            return 0.0
        attended = self.get_attendance_count()
        return round((attended / enrolled * 100), 2)

    def duration_minutes(self):
        """Get session duration in minutes"""
        if self.starts_at and self.ends_at:
            delta = self.ends_at - self.starts_at
            return int(delta.total_seconds() / 60)
        return 0

    def __repr__(self):
        return f'<ClassSession {self.course_code} {self.title} ({self.starts_at})>'


class SessionAttendance(db.Model):
    __tablename__ = 'session_attendance'

    id = db.Column(db.Integer, primary_key=True)
    session_id = db.Column(db.Integer, db.ForeignKey('class_sessions.id'), nullable=False, index=True)
    student_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False, index=True)
    marked_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc), index=True)
    latitude = db.Column(db.Float, nullable=True)
    longitude = db.Column(db.Float, nullable=True)
    face_distance = db.Column(db.Float, nullable=True)
    device_hash = db.Column(db.String(128), nullable=True, index=True)
    ip_address = db.Column(db.String(64), nullable=True)
    user_agent = db.Column(db.String(255), nullable=True)
    is_late = db.Column(db.Boolean, default=False, index=True)  # Marked >10 min after start
    is_locked = db.Column(db.Boolean, default=False, index=True)  # Teacher locked attendance

    __table_args__ = (
        db.UniqueConstraint('session_id', 'student_id', name='unique_student_per_session'),
        Index('idx_student_marked', 'student_id', 'marked_at'),
        Index('idx_session_marked', 'session_id', 'marked_at'),
        Index('idx_late', 'is_late'),
    )

    def is_on_time(self):
        """Check if attendance was marked on time (within session time)"""
        if not self.marked_at:
            return False
        session = ClassSession.query.get(self.session_id)
        if not session:
            return False
        return session.starts_at <= self.marked_at <= session.ends_at

    def is_late_marking(self):
        """Check if attendance was marked late (after session start + grace period)"""
        if not self.marked_at:
            return False
        session = ClassSession.query.get(self.session_id)
        if not session:
            return False
        # Consider late if marked more than 10 minutes after start
        late_threshold = session.starts_at.replace(tzinfo=timezone.utc) + timedelta(minutes=10)
        marked_utc = self.marked_at.replace(tzinfo=timezone.utc) if self.marked_at.tzinfo is None else self.marked_at
        return marked_utc > late_threshold

    def __repr__(self):
        return f'<SessionAttendance s{self.session_id} u{self.student_id} at {self.marked_at}>'


class Course(db.Model):
    __tablename__ = 'courses'

    id = db.Column(db.Integer, primary_key=True)
    code = db.Column(db.String(40), nullable=False, index=True)
    title = db.Column(db.String(120), nullable=False)
    department = db.Column(db.String(100), nullable=False, index=True)
    academic_year = db.Column(db.String(20), nullable=False, index=True)  # "2025-26"
    semester = db.Column(db.String(10), nullable=False, index=True)  # "1", "2", "3", etc.
    credits = db.Column(db.Integer, default=3)
    
    # DEPRECATED: teacher_id (kept for backward compatibility, will be removed in future)
    # Use TeacherAssignment table instead for many-to-many relationship
    teacher_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True, index=True)
    
    created_by_admin_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True, index=True)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))
    is_active = db.Column(db.Boolean, default=True, index=True)

    sessions = db.relationship('ClassSession', backref='course', lazy=True, cascade='all, delete-orphan')
    enrollments = db.relationship('Enrollment', backref='course', lazy=True, cascade='all, delete-orphan')
    teacher_assignments = db.relationship('TeacherAssignment', backref='course', lazy=True, cascade='all, delete-orphan')

    __table_args__ = (
        db.UniqueConstraint('code', 'department', 'academic_year', 'semester', name='unique_course_per_semester'),
        Index('idx_dept_year_sem', 'department', 'academic_year', 'semester'),
        Index('idx_active', 'is_active'),
    )

    def get_enrollment_count(self):
        """Get number of enrolled students"""
        return Enrollment.query.filter_by(course_id=self.id).count()

    def get_session_count(self):
        """Get total number of sessions"""
        return ClassSession.query.filter_by(course_id=self.id).count()

    def get_active_session_count(self):
        """Get number of currently active sessions"""
        now = datetime.now(timezone.utc)
        return ClassSession.query.filter(
            ClassSession.course_id == self.id,
            ClassSession.is_active == True,
            ClassSession.starts_at <= now,
            ClassSession.ends_at >= now
        ).count()

    def get_average_attendance(self):
        """Calculate average attendance percentage across all sessions"""
        sessions = ClassSession.query.filter_by(course_id=self.id).all()
        if not sessions:
            return 0.0
        
        total_percentage = sum(session.get_attendance_percentage() for session in sessions)
        return round(total_percentage / len(sessions), 2)

    def get_assigned_teachers(self):
        """Get all teachers assigned to teach this course"""
        assignments = TeacherAssignment.query.filter_by(course_id=self.id, is_active=True).all()
        teacher_ids = [a.teacher_id for a in assignments]
        return User.query.filter(User.id.in_(teacher_ids)).all() if teacher_ids else []

    def __repr__(self):
        return f'<Course {self.code} ({self.academic_year} Sem {self.semester})>'


class TeacherAssignment(db.Model):
    """Maps teachers to specific course sections they can teach"""
    __tablename__ = 'teacher_assignments'
    
    id = db.Column(db.Integer, primary_key=True)
    teacher_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False, index=True)
    course_id = db.Column(db.Integer, db.ForeignKey('courses.id'), nullable=False, index=True)
    section = db.Column(db.String(10), nullable=False, index=True)  # "A", "B", "C", etc.
    assigned_by_admin_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    assigned_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    is_active = db.Column(db.Boolean, default=True, index=True)
    
    # Relationships
    teacher = db.relationship('User', foreign_keys=[teacher_id], backref='teaching_assignments')
    assigned_by = db.relationship('User', foreign_keys=[assigned_by_admin_id])
    
    __table_args__ = (
        db.UniqueConstraint('teacher_id', 'course_id', 'section', name='unique_teacher_course_section'),
        Index('idx_teacher_active', 'teacher_id', 'is_active'),
        Index('idx_course_section', 'course_id', 'section'),
    )
    
    def get_enrolled_students(self):
        """Get students enrolled in this specific section"""
        return (
            User.query.join(Enrollment, Enrollment.student_id == User.id)
            .filter(
                Enrollment.course_id == self.course_id,
                User.section == self.section,
                User.role == 'student'
            )
            .order_by(User.name.asc())
            .all()
        )
    
    def __repr__(self):
        return f'<TeacherAssignment teacher_id={self.teacher_id} course_id={self.course_id} section={self.section}>'


class BulkEnrollment(db.Model):
    """Track bulk student enrollment operations"""
    __tablename__ = 'bulk_enrollments'
    
    id = db.Column(db.Integer, primary_key=True)
    uploaded_by_admin_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False, index=True)
    filename = db.Column(db.String(255), nullable=False)
    total_rows = db.Column(db.Integer, default=0)
    successful = db.Column(db.Integer, default=0)
    failed = db.Column(db.Integer, default=0)
    error_log = db.Column(db.Text, nullable=True)  # JSON array of errors
    uploaded_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc), index=True)
    
    uploaded_by = db.relationship('User', foreign_keys=[uploaded_by_admin_id])
    
    def __repr__(self):
        return f'<BulkEnrollment {self.filename} ({self.successful}/{self.total_rows} success)>'


class Enrollment(db.Model):
    __tablename__ = 'enrollments'

    id = db.Column(db.Integer, primary_key=True)
    course_id = db.Column(db.Integer, db.ForeignKey('courses.id'), nullable=False, index=True)
    student_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False, index=True)
    enrolled_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    is_active = db.Column(db.Boolean, default=True, index=True)

    __table_args__ = (
        db.UniqueConstraint('course_id', 'student_id', name='unique_course_student'),
        Index('idx_student_active', 'student_id', 'is_active'),
        Index('idx_course_active', 'course_id', 'is_active'),
    )

    def get_attendance_percentage(self):
        """Calculate attendance percentage for this enrollment"""
        sessions = ClassSession.query.filter_by(course_id=self.course_id).all()
        if not sessions:
            return 0.0
        
        session_ids = [s.id for s in sessions]
        attended = SessionAttendance.query.filter(
            SessionAttendance.student_id == self.student_id,
            SessionAttendance.session_id.in_(session_ids)
        ).count()
        
        return round((attended / len(sessions) * 100), 2)

    def __repr__(self):
        return f'<Enrollment c{self.course_id} s{self.student_id}>'


class AttendanceAttempt(db.Model):
    __tablename__ = 'attendance_attempts'

    id = db.Column(db.Integer, primary_key=True)
    session_id = db.Column(db.Integer, db.ForeignKey('class_sessions.id'), nullable=True, index=True)
    student_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True, index=True)
    success = db.Column(db.Boolean, nullable=False, default=False, index=True)
    reason = db.Column(db.String(255), nullable=False, index=True)
    latitude = db.Column(db.Float, nullable=True)
    longitude = db.Column(db.Float, nullable=True)
    face_distance = db.Column(db.Float, nullable=True)
    device_hash = db.Column(db.String(128), nullable=True, index=True)
    ip_address = db.Column(db.String(64), nullable=True)
    user_agent = db.Column(db.String(255), nullable=True)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc), index=True)

    __table_args__ = (
        Index('idx_student_success', 'student_id', 'success'),
        Index('idx_session_created', 'session_id', 'created_at'),
        Index('idx_created_success', 'created_at', 'success'),
    )

    def is_security_concern(self):
        """Check if this attempt indicates a security concern"""
        security_reasons = [
            'Unknown person detected',
            'Multiple faces detected',
            'Face verification failed',
            'Outside classroom radius',
            'Possible spoofing attempt'
        ]
        return any(reason in self.reason for reason in security_reasons)

    def __repr__(self):
        return f'<AttendanceAttempt s{self.session_id} u{self.student_id} ok={self.success}>'


class Timetable(db.Model):
    """Weekly timetable entries for automatic session generation"""
    __tablename__ = 'timetables'
    
    id = db.Column(db.Integer, primary_key=True)
    course_id = db.Column(db.Integer, db.ForeignKey('courses.id'), nullable=False, index=True)
    teacher_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False, index=True)
    section = db.Column(db.String(10), nullable=False, index=True)
    day_of_week = db.Column(db.Integer, nullable=False, index=True)  # 0=Monday, 6=Sunday
    start_time = db.Column(db.Time, nullable=False)
    end_time = db.Column(db.Time, nullable=False)
    room = db.Column(db.String(80), nullable=False)
    class_type = db.Column(db.String(20), default='Lecture')  # Lecture, Lab, Tutorial
    is_active = db.Column(db.Boolean, default=True, index=True)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))
    
    # Relationships
    course = db.relationship('Course', backref='timetable_entries')
    teacher = db.relationship('User', foreign_keys=[teacher_id], backref='timetable_entries')
    
    __table_args__ = (
        db.UniqueConstraint('course_id', 'section', 'day_of_week', 'start_time', name='unique_timetable_slot'),
        Index('idx_day_time', 'day_of_week', 'start_time'),
        Index('idx_teacher_day', 'teacher_id', 'day_of_week'),
        Index('idx_section_day', 'section', 'day_of_week'),
    )
    
    def get_day_name(self):
        """Get day name from day_of_week number"""
        days = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
        return days[self.day_of_week] if 0 <= self.day_of_week <= 6 else 'Unknown'
    
    def duration_minutes(self):
        """Calculate duration in minutes"""
        if self.start_time and self.end_time:
            start = datetime.combine(date.today(), self.start_time)
            end = datetime.combine(date.today(), self.end_time)
            return int((end - start).total_seconds() / 60)
        return 0
    
    def __repr__(self):
        return f'<Timetable {self.get_day_name()} {self.start_time} - {self.course.code if self.course else "?"} Sec {self.section}>'


# Event listeners for automatic timestamp updates
@event.listens_for(User, 'before_update')
def receive_before_update_user(mapper, connection, target):
    """Update updated_at timestamp before user update"""
    target.updated_at = datetime.now(timezone.utc)


@event.listens_for(ClassSession, 'before_update')
def receive_before_update_session(mapper, connection, target):
    """Update updated_at timestamp before session update"""
    target.updated_at = datetime.now(timezone.utc)


@event.listens_for(Course, 'before_update')
def receive_before_update_course(mapper, connection, target):
    """Update updated_at timestamp before course update"""
    target.updated_at = datetime.now(timezone.utc)
