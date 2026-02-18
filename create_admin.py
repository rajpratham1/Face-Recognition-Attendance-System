from app import app, db, User
from werkzeug.security import generate_password_hash

def create_admin():
    with app.app_context():
        admin = User.query.filter_by(email='admin@invertis.org').first()
        if not admin:
            admin = User(
                name='Invertis Admin',
                email='admin@invertis.org',
                department='Administration',
                password_hash=generate_password_hash('admin123', method='scrypt'),
                role='admin',
                face_registered=True
            )
            db.session.add(admin)
            db.session.commit()
            print("Admin created: email: admin@invertis.org, password: admin123")
        else:
            print("Admin already exists.")

if __name__ == '__main__':
    create_admin()
