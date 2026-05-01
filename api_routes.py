"""
Enhanced API routes for real-time updates and better user experience.
"""
from flask import Blueprint, jsonify, request
from flask_login import login_required, current_user
from models import (
    db, User, ClassSession, SessionAttendance, Course, 
    Enrollment, AttendanceAttempt
)
from datetime import datetime, timezone, timedelta
from sqlalchemy import func

api_bp = Blueprint('api', __name__, url_prefix='/api')

def now_utc_naive():
    return datetime.now(timezone.utc).replace(tzinfo=None)

@api_bp.route('/student/active_sessions')
@login_required
def student_active_sessions():
    """Get active sessions for the current student with real-time data"""
    if current_user.role != 'student':
        return jsonify({'success': False, 'message': 'Students only'}), 403
    
    now = now_utc_naive()
    
    # Get enrolled course IDs
    course_ids = [
        row[0] for row in db.session.query(Enrollment.course_id)
        .filter(Enrollment.student_id == current_user.id, Enrollment.is_active == True)
        .all()
    ]
    
    if not course_ids:
        return jsonify({'success': True, 'sessions': []})
    
    # Get active sessions
    sessions = ClassSession.query.filter(
        ClassSession.course_id.in_(course_ids),
        ClassSession.is_active == True,
        ClassSession.starts_at <= now,
        ClassSession.ends_at >= now
    ).order_by(ClassSession.ends_at.asc()).all()
    
    # Check which sessions student has already marked
    marked_session_ids = {
        row[0] for row in db.session.query(SessionAttendance.session_id)
        .filter(SessionAttendance.student_id == current_user.id)
        .all()
    }
    
    session_data = []
    for session in sessions:
        session_data.append({
            'id': session.id,
            'course_code': session.course_code,
            'title': session.title,
            'room': session.room,
            'section': session.section,
            'starts_at': session.starts_at.isoformat() if session.starts_at else None,
            'ends_at': session.ends_at.isoformat() if session.ends_at else None,
            'is_active': session.is_active,
            'already_marked': session.id in marked_session_ids,
            'time_remaining_minutes': int((session.ends_at - now).total_seconds() / 60) if session.ends_at > now else 0
        })
    
    return jsonify({
        'success': True,
        'sessions': session_data,
        'count': len(session_data)
    })

@api_bp.route('/student/attendance_stats')
@login_required
def student_attendance_stats():
    """Get comprehensive attendance statistics for student"""
    if current_user.role != 'student':
        return jsonify({'success': False, 'message': 'Students only'}), 403
    
    # Get all enrollments
    enrollments = Enrollment.query.filter_by(
        student_id=current_user.id,
        is_active=True
    ).all()
    
    if not enrollments:
        return jsonify({
            'success': True,
            'total_courses': 0,
            'total_sessions': 0,
            'attended_sessions': 0,
            'overall_percentage': 0,
            'status': 'no_courses',
            'courses': []
        })
    
    course_stats = []
    total_sessions_all = 0
    attended_sessions_all = 0
    
    for enrollment in enrollments:
        course = enrollment.course
        
        # Get total sessions for this course
        total_sessions = ClassSession.query.filter_by(
            course_id=course.id
        ).filter(
            ClassSession.starts_at <= now_utc_naive()
        ).count()
        
        # Get attended sessions
        attended_sessions = SessionAttendance.query.filter_by(
            student_id=current_user.id
        ).join(ClassSession).filter(
            ClassSession.course_id == course.id
        ).count()
        
        percentage = (attended_sessions / total_sessions * 100) if total_sessions > 0 else 0
        
        course_stats.append({
            'course_id': course.id,
            'course_code': course.code,
            'course_title': course.title,
            'total_sessions': total_sessions,
            'attended_sessions': attended_sessions,
            'percentage': round(percentage, 2),
            'status': 'good' if percentage >= 75 else ('warning' if percentage >= 50 else 'critical')
        })
        
        total_sessions_all += total_sessions
        attended_sessions_all += attended_sessions
    
    overall_percentage = (attended_sessions_all / total_sessions_all * 100) if total_sessions_all > 0 else 0
    
    # Determine overall status
    if overall_percentage >= 75:
        status = 'good'
    elif overall_percentage >= 50:
        status = 'warning'
    else:
        status = 'critical'
    
    return jsonify({
        'success': True,
        'total_courses': len(enrollments),
        'total_sessions': total_sessions_all,
        'attended_sessions': attended_sessions_all,
        'overall_percentage': round(overall_percentage, 2),
        'status': status,
        'courses': course_stats
    })

@api_bp.route('/student/attendance_alert')
@login_required
def student_attendance_alert():
    """Check if student has low attendance and return alert data"""
    if current_user.role != 'student':
        return jsonify({'success': False, 'message': 'Students only'}), 403
    
    enrollments = Enrollment.query.filter_by(
        student_id=current_user.id,
        is_active=True
    ).all()
    
    low_courses = []
    threshold = 75
    
    for enrollment in enrollments:
        course = enrollment.course
        
        total_sessions = ClassSession.query.filter_by(
            course_id=course.id
        ).filter(
            ClassSession.starts_at <= now_utc_naive()
        ).count()
        
        if total_sessions == 0:
            continue
        
        attended_sessions = SessionAttendance.query.filter_by(
            student_id=current_user.id
        ).join(ClassSession).filter(
            ClassSession.course_id == course.id
        ).count()
        
        percentage = (attended_sessions / total_sessions * 100)
        
        if percentage < threshold:
            required = max(0, int((threshold * total_sessions / 100) - attended_sessions))
            
            low_courses.append({
                'course_id': course.id,
                'course_code': course.code,
                'course_title': course.title,
                'percentage': round(percentage, 2),
                'attended': attended_sessions,
                'total': total_sessions,
                'required': required
            })
    
    return jsonify({
        'success': True,
        'alert': len(low_courses) > 0,
        'threshold': threshold,
        'low_courses': low_courses
    })

@api_bp.route('/teacher/session/<int:session_id>/stats')
@login_required
def teacher_session_stats(session_id):
    """Get real-time statistics for a session"""
    if current_user.role != 'teacher':
        return jsonify({'success': False, 'message': 'Teachers only'}), 403
    
    session = ClassSession.query.filter_by(
        id=session_id,
        teacher_id=current_user.id
    ).first()
    
    if not session:
        return jsonify({'success': False, 'message': 'Session not found'}), 404
    
    # Get enrolled students count
    enrolled_count = 0
    if session.course_id:
        query = Enrollment.query.filter_by(course_id=session.course_id, is_active=True)
        if session.section:
            query = query.join(User).filter(User.section == session.section)
        enrolled_count = query.count()
    
    # Get attendance count
    attendance_count = SessionAttendance.query.filter_by(session_id=session_id).count()
    
    # Get failed attempts count
    failed_attempts = AttendanceAttempt.query.filter_by(
        session_id=session_id,
        success=False
    ).count()
    
    # Calculate percentage
    percentage = (attendance_count / enrolled_count * 100) if enrolled_count > 0 else 0
    
    # Time remaining
    now = now_utc_naive()
    time_remaining = 0
    if session.ends_at > now:
        time_remaining = int((session.ends_at - now).total_seconds() / 60)
    
    return jsonify({
        'success': True,
        'session_id': session_id,
        'enrolled': enrolled_count,
        'marked': attendance_count,
        'failed': failed_attempts,
        'pending': enrolled_count - attendance_count,
        'percentage': round(percentage, 2),
        'is_active': session.is_active and session.ends_at >= now,
        'time_remaining_minutes': time_remaining
    })


@api_bp.route('/teacher/dashboard_stats')
@login_required
def teacher_dashboard_stats():
    """Get comprehensive dashboard statistics for teacher"""
    if current_user.role != 'teacher':
        return jsonify({'success': False, 'message': 'Teachers only'}), 403
    
    from models import TeacherAssignment
    
    # Get assigned courses
    assignments = TeacherAssignment.query.filter_by(
        teacher_id=current_user.id,
        is_active=True
    ).all()
    
    course_ids = list(set([a.course_id for a in assignments]))
    
    # Get unique students across all courses
    if course_ids:
        students = User.query.join(Enrollment).filter(
            Enrollment.course_id.in_(course_ids),
            Enrollment.is_active == True,
            User.role == 'student'
        ).distinct().all()
    else:
        students = []
    
    # Get active sessions count
    now = now_utc_naive()
    active_sessions = ClassSession.query.filter(
        ClassSession.teacher_id == current_user.id,
        ClassSession.is_active == True,
        ClassSession.starts_at <= now,
        ClassSession.ends_at >= now
    ).count()
    
    # Get today's sessions
    from zoneinfo import ZoneInfo
    from flask import current_app
    
    local_now = datetime.now(ZoneInfo(current_app.config['APP_TIMEZONE']))
    today_start = local_now.replace(hour=0, minute=0, second=0, microsecond=0)
    today_end = today_start + timedelta(days=1)
    
    today_start_utc = today_start.astimezone(timezone.utc).replace(tzinfo=None)
    today_end_utc = today_end.astimezone(timezone.utc).replace(tzinfo=None)
    
    today_sessions = ClassSession.query.filter(
        ClassSession.teacher_id == current_user.id,
        ClassSession.starts_at >= today_start_utc,
        ClassSession.starts_at < today_end_utc
    ).count()
    
    return jsonify({
        'success': True,
        'total_courses': len(course_ids),
        'total_students': len(students),
        'active_sessions': active_sessions,
        'today_sessions': today_sessions,
        'total_assignments': len(assignments)
    })


@api_bp.route('/admin/dashboard_stats')
@login_required
def admin_dashboard_stats():
    """Get comprehensive dashboard statistics for admin"""
    if current_user.role != 'admin':
        return jsonify({'success': False, 'message': 'Admins only'}), 403
    
    # Total users by role
    total_students = User.query.filter_by(role='student', is_active=True).count()
    total_teachers = User.query.filter_by(role='teacher', is_active=True).count()
    total_admins = User.query.filter_by(role='admin', is_active=True).count()
    
    # Pending section assignments
    pending_assignments = User.query.filter_by(
        role='student',
        assignment_status='pending',
        is_active=True
    ).count()
    
    # Total courses
    total_courses = Course.query.filter_by(is_active=True).count()
    
    # Active sessions right now
    now = now_utc_naive()
    active_sessions = ClassSession.query.filter(
        ClassSession.is_active == True,
        ClassSession.starts_at <= now,
        ClassSession.ends_at >= now
    ).count()
    
    # Today's attendance count
    from zoneinfo import ZoneInfo
    from flask import current_app
    
    local_now = datetime.now(ZoneInfo(current_app.config['APP_TIMEZONE']))
    today_date = local_now.date()
    
    from models import Attendance
    today_attendance = Attendance.query.filter_by(date=today_date).count()
    
    # Students with low attendance (< 75%)
    low_attendance_students = []
    students = User.query.filter_by(role='student', is_active=True).limit(100).all()
    
    for student in students:
        enrollments = Enrollment.query.filter_by(student_id=student.id, is_active=True).all()
        
        if not enrollments:
            continue
        
        total_sessions = 0
        attended_sessions = 0
        
        for enrollment in enrollments:
            course_sessions = ClassSession.query.filter_by(course_id=enrollment.course_id).count()
            course_attended = SessionAttendance.query.filter_by(
                student_id=student.id
            ).join(ClassSession).filter(
                ClassSession.course_id == enrollment.course_id
            ).count()
            
            total_sessions += course_sessions
            attended_sessions += course_attended
        
        if total_sessions > 0:
            percentage = (attended_sessions / total_sessions * 100)
            if percentage < 75:
                low_attendance_students.append(student.id)
    
    return jsonify({
        'success': True,
        'total_students': total_students,
        'total_teachers': total_teachers,
        'total_admins': total_admins,
        'pending_assignments': pending_assignments,
        'total_courses': total_courses,
        'active_sessions': active_sessions,
        'today_attendance': today_attendance,
        'low_attendance_count': len(low_attendance_students)
    })
