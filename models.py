from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from datetime import datetime

db = SQLAlchemy()


class User(UserMixin, db.Model):
    __tablename__ = 'users'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    department = db.Column(db.String(100), nullable=False)
    password_hash = db.Column(db.String(256), nullable=False)
    role = db.Column(db.String(20), default='student')  # student / teacher / admin
    face_encoding = db.Column(db.Text, nullable=True)   # JSON of 128-D vector
    face_registered = db.Column(db.Boolean, default=False)
    registered_at = db.Column(db.DateTime, default=datetime.utcnow)

    attendances = db.relationship('Attendance', backref='user', lazy=True)
    created_sessions = db.relationship('ClassSession', backref='teacher', lazy=True, foreign_keys='ClassSession.teacher_id')
    session_attendances = db.relationship('SessionAttendance', backref='student', lazy=True, foreign_keys='SessionAttendance.student_id')
    teacher_courses = db.relationship('Course', backref='teacher', lazy=True, foreign_keys='Course.teacher_id')
    enrollments = db.relationship('Enrollment', backref='student', lazy=True, foreign_keys='Enrollment.student_id')

    def __repr__(self):
        return f'<User {self.name}>'


class Attendance(db.Model):
    __tablename__ = 'attendance'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    date = db.Column(db.Date, nullable=False)
    time = db.Column(db.Time, nullable=False)
    status = db.Column(db.String(20), default='present')
    latitude = db.Column(db.Float, nullable=True)
    longitude = db.Column(db.Float, nullable=True)

    __table_args__ = (
        db.UniqueConstraint('user_id', 'date', name='unique_attendance_per_day'),
    )

    def __repr__(self):
        return f'<Attendance {self.user_id} - {self.date}>'


class ClassSession(db.Model):
    __tablename__ = 'class_sessions'

    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(120), nullable=False)
    course_code = db.Column(db.String(40), nullable=False)
    room = db.Column(db.String(80), nullable=False)
    course_id = db.Column(db.Integer, db.ForeignKey('courses.id'), nullable=True)
    starts_at = db.Column(db.DateTime, nullable=False)
    ends_at = db.Column(db.DateTime, nullable=False)
    is_active = db.Column(db.Boolean, default=True)
    teacher_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    session_attendances = db.relationship('SessionAttendance', backref='session', lazy=True, cascade='all, delete-orphan')

    def __repr__(self):
        return f'<ClassSession {self.course_code} {self.title}>'


class SessionAttendance(db.Model):
    __tablename__ = 'session_attendance'

    id = db.Column(db.Integer, primary_key=True)
    session_id = db.Column(db.Integer, db.ForeignKey('class_sessions.id'), nullable=False)
    student_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    marked_at = db.Column(db.DateTime, default=datetime.utcnow)
    latitude = db.Column(db.Float, nullable=True)
    longitude = db.Column(db.Float, nullable=True)
    face_distance = db.Column(db.Float, nullable=False)
    device_hash = db.Column(db.String(128), nullable=True)
    ip_address = db.Column(db.String(64), nullable=True)
    user_agent = db.Column(db.String(255), nullable=True)

    __table_args__ = (
        db.UniqueConstraint('session_id', 'student_id', name='unique_student_per_session'),
    )

    def __repr__(self):
        return f'<SessionAttendance s{self.session_id} u{self.student_id}>'


class Course(db.Model):
    __tablename__ = 'courses'

    id = db.Column(db.Integer, primary_key=True)
    code = db.Column(db.String(40), nullable=False)
    title = db.Column(db.String(120), nullable=False)
    section = db.Column(db.String(40), nullable=False)
    teacher_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    sessions = db.relationship('ClassSession', backref='course', lazy=True)
    enrollments = db.relationship('Enrollment', backref='course', lazy=True, cascade='all, delete-orphan')

    __table_args__ = (
        db.UniqueConstraint('code', 'section', 'teacher_id', name='unique_teacher_course_section'),
    )

    def __repr__(self):
        return f'<Course {self.code} {self.section}>'


class Enrollment(db.Model):
    __tablename__ = 'enrollments'

    id = db.Column(db.Integer, primary_key=True)
    course_id = db.Column(db.Integer, db.ForeignKey('courses.id'), nullable=False)
    student_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    enrolled_at = db.Column(db.DateTime, default=datetime.utcnow)

    __table_args__ = (
        db.UniqueConstraint('course_id', 'student_id', name='unique_course_student'),
    )

    def __repr__(self):
        return f'<Enrollment c{self.course_id} s{self.student_id}>'


class AttendanceAttempt(db.Model):
    __tablename__ = 'attendance_attempts'

    id = db.Column(db.Integer, primary_key=True)
    session_id = db.Column(db.Integer, db.ForeignKey('class_sessions.id'), nullable=True)
    student_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    success = db.Column(db.Boolean, nullable=False, default=False)
    reason = db.Column(db.String(255), nullable=False)
    latitude = db.Column(db.Float, nullable=True)
    longitude = db.Column(db.Float, nullable=True)
    face_distance = db.Column(db.Float, nullable=True)
    device_hash = db.Column(db.String(128), nullable=True)
    ip_address = db.Column(db.String(64), nullable=True)
    user_agent = db.Column(db.String(255), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f'<AttendanceAttempt s{self.session_id} u{self.student_id} ok={self.success}>'
