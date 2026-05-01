#!/usr/bin/env python3
"""
Data Migration Script - Phase 1
Migrates existing courses to new TeacherAssignment structure
Run this ONCE after deploying Phase 1 changes
"""

from app import app, db
from models import Course, TeacherAssignment, User
from datetime import datetime, timezone

def migrate_courses():
    """Migrate existing courses with teacher_id to TeacherAssignment table"""
    print("\n" + "=" * 70)
    print("COURSE MIGRATION SCRIPT - Phase 1")
    print("=" * 70 + "\n")
    
    with app.app_context():
        # Get or create admin user
        admin = User.query.filter_by(role='admin').first()
        if not admin:
            print("❌ No admin user found!")
            print("Creating default admin user...")
            from werkzeug.security import generate_password_hash
            
            admin = User(
                name="System Admin",
                email="admin@system.local",
                department="Administration",
                role="admin",
                password_hash=generate_password_hash("admin123", method="scrypt")
            )
            db.session.add(admin)
            db.session.commit()
            print(f"✅ Created admin user: {admin.email} (password: admin123)")
            print("⚠️  CHANGE THIS PASSWORD IMMEDIATELY!\n")
        
        # Find courses with teacher_id but no TeacherAssignment
        courses_with_teachers = Course.query.filter(
            Course.teacher_id.isnot(None)
        ).all()
        
        if not courses_with_teachers:
            print("✅ No courses to migrate. All done!")
            return
        
        print(f"Found {len(courses_with_teachers)} courses to migrate\n")
        
        migrated = 0
        skipped = 0
        errors = []
        
        for course in courses_with_teachers:
            try:
                # Check if teacher exists
                teacher = User.query.get(course.teacher_id)
                if not teacher:
                    errors.append(f"Course {course.code}: Teacher ID {course.teacher_id} not found")
                    skipped += 1
                    continue
                
                # Check if assignment already exists
                existing = TeacherAssignment.query.filter_by(
                    teacher_id=course.teacher_id,
                    course_id=course.id
                ).first()
                
                if existing:
                    print(f"⏭️  Skipped: {course.code} - Assignment already exists")
                    skipped += 1
                    continue
                
                # Determine section (use existing or default to "A")
                section = getattr(course, 'section', None) or "A"
                
                # Create TeacherAssignment
                assignment = TeacherAssignment(
                    teacher_id=course.teacher_id,
                    course_id=course.id,
                    section=section,
                    assigned_by_admin_id=admin.id,
                    assigned_at=datetime.now(timezone.utc)
                )
                db.session.add(assignment)
                
                # Update course with default values if missing
                if not course.department:
                    course.department = teacher.department or "General"
                if not course.academic_year:
                    course.academic_year = "2025-26"
                if not course.semester:
                    course.semester = "1"
                if not course.credits:
                    course.credits = 3
                if not course.created_by_admin_id:
                    course.created_by_admin_id = admin.id
                
                migrated += 1
                print(f"✅ Migrated: {course.code} - {course.title}")
                print(f"   Teacher: {teacher.name} → Section: {section}")
                
            except Exception as e:
                errors.append(f"Course {course.code}: {str(e)}")
                skipped += 1
                continue
        
        # Commit all changes
        try:
            db.session.commit()
            print("\n" + "=" * 70)
            print("MIGRATION COMPLETE")
            print("=" * 70)
            print(f"✅ Successfully migrated: {migrated} courses")
            print(f"⏭️  Skipped: {skipped} courses")
            
            if errors:
                print(f"\n⚠️  Errors encountered: {len(errors)}")
                for error in errors:
                    print(f"   - {error}")
            
            print("\n📋 Next Steps:")
            print("1. Verify assignments in admin dashboard")
            print("2. Update frontend templates")
            print("3. Test teacher login and course access")
            print("4. Backup database before production deployment")
            
        except Exception as e:
            db.session.rollback()
            print(f"\n❌ Migration failed: {str(e)}")
            print("Database rolled back. No changes made.")
            return False
    
    return True


def verify_migration():
    """Verify migration was successful"""
    print("\n" + "=" * 70)
    print("VERIFICATION")
    print("=" * 70 + "\n")
    
    with app.app_context():
        total_courses = Course.query.count()
        courses_with_teachers = Course.query.filter(Course.teacher_id.isnot(None)).count()
        total_assignments = TeacherAssignment.query.filter_by(is_active=True).count()
        
        print(f"Total Courses: {total_courses}")
        print(f"Courses with teacher_id: {courses_with_teachers}")
        print(f"Active TeacherAssignments: {total_assignments}")
        
        if courses_with_teachers == total_assignments:
            print("\n✅ Migration verified successfully!")
            print("All courses with teachers have corresponding assignments.")
        else:
            print(f"\n⚠️  Warning: Mismatch detected!")
            print(f"Expected {courses_with_teachers} assignments, found {total_assignments}")
            print("Some courses may not have been migrated correctly.")
        
        # Show sample assignments
        print("\n📋 Sample Assignments:")
        assignments = TeacherAssignment.query.limit(5).all()
        for a in assignments:
            teacher = User.query.get(a.teacher_id)
            course = Course.query.get(a.course_id)
            print(f"   {teacher.name} → {course.code} Section {a.section}")


if __name__ == "__main__":
    print("\n⚠️  WARNING: This script will modify your database!")
    print("Make sure you have a backup before proceeding.\n")
    
    response = input("Do you want to continue? (yes/no): ").strip().lower()
    
    if response != 'yes':
        print("Migration cancelled.")
        exit(0)
    
    success = migrate_courses()
    
    if success:
        verify_migration()
        print("\n✅ Migration completed successfully!\n")
        exit(0)
    else:
        print("\n❌ Migration failed!\n")
        exit(1)
