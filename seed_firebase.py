"""
Firebase Seed Script - Sync existing SQLite data to Firebase
Run this script to populate Firebase with existing database data
"""
import sys
from app import app, db
from models import User, Course, ClassSession, SessionAttendance, Enrollment
from firebase_service import (
    firebase_enabled, 
    sync_user_registration,
    sync_course_creation,
    sync_session_creation,
    sync_session_attendance,
    sync_enrollment,
    get_firebase_status,
    create_firebase_user
)

def seed_firebase():
    """Seed Firebase with existing SQLite data"""
    
    with app.app_context():
        print("=" * 70)
        print("🔥 FIREBASE SEED SCRIPT")
        print("=" * 70)
        
        # Check Firebase status
        status = get_firebase_status(app)
        print(f"\n📊 Firebase Status:")
        print(f"   Available: {status['available']}")
        print(f"   Enabled: {status['enabled']}")
        if status['error']:
            print(f"   Error: {status['error']}")
        
        if not status['enabled']:
            print("\n❌ Firebase is not enabled!")
            print("   Please check your .env file and ensure:")
            print("   - FIREBASE_DATABASE_URL is set")
            print("   - FIREBASE_PROJECT_ID is set")
            print("   - FIREBASE_PRIVATE_KEY is set")
            print("   - FIREBASE_CLIENT_EMAIL is set")
            return
        
        print("\n✅ Firebase is connected!")
        print("\n" + "=" * 70)
        
        # Sync Users to Firebase Auth + Realtime DB
        print("\n👥 Syncing Users to Firebase Auth + Realtime Database...")
        users = User.query.all()
        user_count = 0
        auth_count = 0
        default_password = "TempPass123!"  # Temporary password for existing users
        
        for user in users:
            try:
                # Create Firebase Auth user
                firebase_uid = create_firebase_user(app, user.email, default_password, user.name, user.id)
                if firebase_uid:
                    auth_count += 1
                    print(f"   ✓ Firebase Auth: {user.name} ({user.role}) - {user.email}")
                else:
                    print(f"   ⚠ Firebase Auth exists: {user.email}")
                
                # Sync user data to Realtime Database
                sync_user_registration(app, user)
                user_count += 1
                print(f"   ✓ Realtime DB: {user.name} ({user.role}) - {user.email}")
            except Exception as e:
                print(f"   ✗ Failed: {user.email} - {str(e)}")
        
        print(f"\n✅ Synced {user_count}/{len(users)} users to Realtime DB")
        print(f"✅ Created {auth_count} new Firebase Auth users")
        if auth_count < len(users):
            print(f"⚠️  {len(users) - auth_count} users already exist in Firebase Auth")
        
        # Sync Courses
        print("\n📚 Syncing Courses...")
        courses = Course.query.all()
        course_count = 0
        for course in courses:
            try:
                sync_course_creation(app, course)
                course_count += 1
                print(f"   ✓ {course.code} - {course.title}")
            except Exception as e:
                print(f"   ✗ Failed: {course.code} - {str(e)}")
        
        print(f"\n✅ Synced {course_count}/{len(courses)} courses")
        
        # Sync Sessions
        print("\n🎓 Syncing Class Sessions...")
        sessions = ClassSession.query.all()
        session_count = 0
        for session in sessions:
            try:
                sync_session_creation(app, session)
                session_count += 1
                status_text = "LIVE" if session.is_active else "CLOSED"
                print(f"   ✓ {session.course_code} - {session.title} [{status_text}]")
            except Exception as e:
                print(f"   ✗ Failed: Session {session.id} - {str(e)}")
        
        print(f"\n✅ Synced {session_count}/{len(sessions)} sessions")
        
        # Sync Enrollments
        print("\n📝 Syncing Enrollments...")
        enrollments = Enrollment.query.all()
        enrollment_count = 0
        for enrollment in enrollments:
            try:
                sync_enrollment(app, enrollment)
                enrollment_count += 1
                student = User.query.get(enrollment.student_id)
                course = Course.query.get(enrollment.course_id)
                if student and course:
                    print(f"   ✓ {student.name} → {course.code}")
            except Exception as e:
                print(f"   ✗ Failed: Enrollment {enrollment.id} - {str(e)}")
        
        print(f"\n✅ Synced {enrollment_count}/{len(enrollments)} enrollments")
        
        # Sync Attendance Records
        print("\n✅ Syncing Attendance Records...")
        attendance_records = SessionAttendance.query.all()
        attendance_count = 0
        for record in attendance_records:
            try:
                student = User.query.get(record.student_id)
                session = ClassSession.query.get(record.session_id)
                if student and session:
                    sync_session_attendance(app, record, session, student)
                    attendance_count += 1
                    print(f"   ✓ {student.name} → {session.course_code}")
            except Exception as e:
                print(f"   ✗ Failed: Attendance {record.id} - {str(e)}")
        
        print(f"\n✅ Synced {attendance_count}/{len(attendance_records)} attendance records")
        
        # Summary
        print("\n" + "=" * 70)
        print("📊 SYNC SUMMARY")
        print("=" * 70)
        print(f"   Users (Realtime DB): {user_count}/{len(users)}")
        print(f"   Users (Auth):        {auth_count} new")
        print(f"   Courses:             {course_count}/{len(courses)}")
        print(f"   Sessions:            {session_count}/{len(sessions)}")
        print(f"   Enrollments:         {enrollment_count}/{len(enrollments)}")
        print(f"   Attendance:          {attendance_count}/{len(attendance_records)}")
        print("=" * 70)
        
        if auth_count > 0:
            print("\n⚠️  IMPORTANT: New Firebase Auth users created with temporary password:")
            print(f"   Password: {default_password}")
            print("   Users should reset their password on next login.")
        
        if (user_count == len(users) and 
            course_count == len(courses) and 
            session_count == len(sessions)):
            print("\n🎉 SUCCESS! All data synced to Firebase!")
            print("\n📱 Check your Firebase Console:")
            print(f"   Auth: https://console.firebase.google.com/project/{app.config['FIREBASE_PROJECT_ID']}/authentication")
            print(f"   Database: https://console.firebase.google.com/project/{app.config['FIREBASE_PROJECT_ID']}/database")
        else:
            print("\n⚠️  Some records failed to sync. Check errors above.")
        
        print("\n" + "=" * 70)


def clear_firebase():
    """Clear all Firebase data (use with caution!)"""
    
    with app.app_context():
        if not firebase_enabled(app):
            print("❌ Firebase is not enabled!")
            return
        
        print("\n⚠️  WARNING: This will delete ALL data from Firebase!")
        confirm = input("Type 'DELETE' to confirm: ")
        
        if confirm != "DELETE":
            print("❌ Cancelled")
            return
        
        try:
            from firebase_admin import db as firebase_db
            
            # Delete all data
            firebase_db.reference('/').delete()
            print("✅ Firebase data cleared!")
            
        except Exception as e:
            print(f"❌ Error: {str(e)}")


def show_firebase_stats():
    """Show Firebase statistics"""
    
    with app.app_context():
        if not firebase_enabled(app):
            print("❌ Firebase is not enabled!")
            return
        
        try:
            from firebase_admin import db as firebase_db
            
            print("\n" + "=" * 70)
            print("📊 FIREBASE STATISTICS")
            print("=" * 70)
            
            # Count users
            users_ref = firebase_db.reference('users')
            users_data = users_ref.get()
            user_count = len(users_data) if users_data else 0
            
            # Count courses
            courses_ref = firebase_db.reference('courses')
            courses_data = courses_ref.get()
            course_count = len(courses_data) if courses_data else 0
            
            # Count sessions
            sessions_ref = firebase_db.reference('sessions')
            sessions_data = sessions_ref.get()
            session_count = len(sessions_data) if sessions_data else 0
            
            # Count enrollments
            enrollments_ref = firebase_db.reference('enrollments')
            enrollments_data = enrollments_ref.get()
            enrollment_count = len(enrollments_data) if enrollments_data else 0
            
            # Count attendance
            attendance_ref = firebase_db.reference('attendance/students')
            attendance_data = attendance_ref.get()
            attendance_count = 0
            if attendance_data:
                for student_data in attendance_data.values():
                    if student_data:
                        attendance_count += len(student_data)
            
            print(f"\n   Users:       {user_count}")
            print(f"   Courses:     {course_count}")
            print(f"   Sessions:    {session_count}")
            print(f"   Enrollments: {enrollment_count}")
            print(f"   Attendance:  {attendance_count}")
            
            print("\n" + "=" * 70)
            print(f"\n📱 Firebase Console:")
            print(f"   Auth: https://console.firebase.google.com/project/{app.config['FIREBASE_PROJECT_ID']}/authentication")
            print(f"   Database: https://console.firebase.google.com/project/{app.config['FIREBASE_PROJECT_ID']}/database")
            print("=" * 70 + "\n")
            
        except Exception as e:
            print(f"❌ Error: {str(e)}")


if __name__ == "__main__":
    if len(sys.argv) > 1:
        command = sys.argv[1]
        
        if command == "seed":
            seed_firebase()
        elif command == "clear":
            clear_firebase()
        elif command == "stats":
            show_firebase_stats()
        else:
            print("❌ Unknown command!")
            print("\nUsage:")
            print("  python seed_firebase.py seed   - Sync SQLite data to Firebase")
            print("  python seed_firebase.py stats  - Show Firebase statistics")
            print("  python seed_firebase.py clear  - Clear all Firebase data")
    else:
        # Default: run seed
        seed_firebase()
