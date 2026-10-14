"""
Background scheduler for automated tasks like session generation.
"""
import logging
from datetime import datetime, timedelta, timezone
from zoneinfo import ZoneInfo
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.interval import IntervalTrigger

logger = logging.getLogger(__name__)


def init_scheduler(app, db):
    """
    Initialize the background scheduler for automated tasks.
    
    Tasks:
    - Auto-generate sessions from timetable (every 5 minutes)
    - Auto-close expired sessions (every 2 minutes)
    - Send low attendance alerts (daily at 8 AM)
    """
    scheduler = BackgroundScheduler(daemon=True)
    
    # Import here to avoid circular imports
    from models import ClassSession, Timetable, User, Enrollment, SessionAttendance
    
    def auto_generate_sessions():
        """Generate class sessions from timetable entries"""
        with app.app_context():
            try:
                now = datetime.now(ZoneInfo(app.config['APP_TIMEZONE']))
                current_day = now.weekday()  # 0=Monday, 6=Sunday
                
                # Look ahead 30 minutes
                window_start = now
                window_end = now + timedelta(minutes=30)
                
                # Find timetable entries for today that should have sessions created
                timetable_entries = Timetable.query.filter(
                    Timetable.day_of_week == current_day,
                    Timetable.is_active == True
                ).all()
                
                sessions_created = 0
                
                for entry in timetable_entries:
                    # Combine date and time for session start/end
                    today_date = now.date()
                    starts_at_local = datetime.combine(today_date, entry.start_time)
                    ends_at_local = datetime.combine(today_date, entry.end_time)
                    
                    # Only create if session starts within the next 30 minutes
                    if not (window_start <= starts_at_local <= window_end):
                        continue
                    
                    # Convert to UTC naive for database
                    starts_at_utc = starts_at_local.replace(
                        tzinfo=ZoneInfo(app.config['APP_TIMEZONE'])
                    ).astimezone(timezone.utc).replace(tzinfo=None)
                    
                    ends_at_utc = ends_at_local.replace(
                        tzinfo=ZoneInfo(app.config['APP_TIMEZONE'])
                    ).astimezone(timezone.utc).replace(tzinfo=None)
                    
                    # Check if session already exists
                    existing_session = ClassSession.query.filter(
                        ClassSession.course_id == entry.course_id,
                        ClassSession.teacher_id == entry.teacher_id,
                        ClassSession.section == entry.section,
                        ClassSession.starts_at == starts_at_utc
                    ).first()
                    
                    if not existing_session:
                        # Create new session
                        new_session = ClassSession(
                            title=entry.course.title,
                            course_code=entry.course.code,
                            room=entry.room,
                            course_id=entry.course_id,
                            section=entry.section,
                            starts_at=starts_at_utc,
                            ends_at=ends_at_utc,
                            teacher_id=entry.teacher_id,
                            is_active=False,  # Teacher needs to start it
                            location_lat=None,
                            location_lng=None,
                            location_radius_meters=app.config['SESSION_LOCATION_RADIUS_METERS'],
                        )
                        db.session.add(new_session)
                        sessions_created += 1
                        logger.info(
                            f"Auto-generated session: {entry.course.code} - "
                            f"Section {entry.section} - {entry.get_day_name()} {entry.start_time}"
                        )
                
                if sessions_created > 0:
                    db.session.commit()
                    logger.info(f"Auto-session generation: {sessions_created} sessions created")
                    
            except Exception as e:
                db.session.rollback()
                logger.error(f"Error in auto_generate_sessions: {str(e)}", exc_info=True)
    
    def auto_close_expired_sessions():
        """Close sessions that have ended"""
        with app.app_context():
            try:
                now_utc = datetime.now(timezone.utc).replace(tzinfo=None)
                
                expired_sessions = ClassSession.query.filter(
                    ClassSession.is_active == True,
                    ClassSession.ends_at < now_utc
                ).all()
                
                closed_count = 0
                for session in expired_sessions:
                    session.is_active = False
                    closed_count += 1
                    logger.info(f"Auto-closed session: {session.course_code} - Session ID {session.id}")
                
                if closed_count > 0:
                    db.session.commit()
                    logger.info(f"Auto-closed {closed_count} expired sessions")
                    
            except Exception as e:
                db.session.rollback()
                logger.error(f"Error in auto_close_expired_sessions: {str(e)}", exc_info=True)
    
    def send_low_attendance_alerts():
        """Send daily alerts to students with low attendance"""
        with app.app_context():
            try:
                from email_service import send_low_attendance_alert
                
                # Get all active students
                students = User.query.filter_by(role='student', is_active=True).all()
                
                alerts_sent = 0
                for student in students:
                    # Get enrolled courses
                    enrollments = Enrollment.query.filter_by(
                        student_id=student.id,
                        is_active=True
                    ).all()
                    
                    low_courses = []
                    for enrollment in enrollments:
                        # Calculate attendance percentage
                        total_sessions = ClassSession.query.filter_by(
                            course_id=enrollment.course_id
                        ).count()
                        
                        if total_sessions == 0:
                            continue
                        
                        attended_sessions = SessionAttendance.query.filter_by(
                            student_id=student.id
                        ).join(ClassSession).filter(
                            ClassSession.course_id == enrollment.course_id
                        ).count()
                        
                        percentage = (attended_sessions / total_sessions * 100) if total_sessions > 0 else 0
                        
                        if percentage < 75:  # Below 75% threshold
                            low_courses.append({
                                'course': enrollment.course,
                                'percentage': round(percentage, 2),
                                'attended': attended_sessions,
                                'total': total_sessions
                            })
                    
                    if low_courses and student.email:
                        # Send alert email
                        send_low_attendance_alert(app, student, low_courses)
                        alerts_sent += 1
                
                logger.info(f"Sent {alerts_sent} low attendance alerts")
                
            except Exception as e:
                logger.error(f"Error in send_low_attendance_alerts: {str(e)}", exc_info=True)
    
    # Schedule tasks
    scheduler.add_job(
        func=auto_generate_sessions,
        trigger=IntervalTrigger(minutes=5),
        id='auto_generate_sessions',
        name='Auto-generate sessions from timetable',
        replace_existing=True
    )
    
    scheduler.add_job(
        func=auto_close_expired_sessions,
        trigger=IntervalTrigger(minutes=2),
        id='auto_close_sessions',
        name='Auto-close expired sessions',
        replace_existing=True
    )
    
    scheduler.add_job(
        func=send_low_attendance_alerts,
        trigger='cron',
        hour=8,
        minute=0,
        id='low_attendance_alerts',
        name='Send daily low attendance alerts',
        replace_existing=True
    )
    
    scheduler.start()
    logger.info("Background scheduler started successfully")
    
    return scheduler
