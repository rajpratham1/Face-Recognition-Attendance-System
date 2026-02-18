import os
import json
import base64
import numpy as np
from datetime import datetime
from flask import Flask, render_template, request, jsonify, redirect, url_for, flash
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from geopy.distance import geodesic

from config import Config
from models import db, User, Attendance

app = Flask(__name__)
app.config.from_object(Config)

db.init_app(app)
login_manager = LoginManager()
login_manager.login_view = 'login'
login_manager.init_app(app)

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

def is_within_invertis(lat, lng):
    if lat is None or lng is None:
        return False
    user_location = (lat, lng)
    invertis_location = (app.config['INVERTIS_LAT'], app.config['INVERTIS_LNG'])
    distance = geodesic(user_location, invertis_location).meters
    return distance <= app.config['ALLOWED_RADIUS_METERS']

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        name = request.form.get('name')
        email = request.form.get('email')
        department = request.form.get('department')
        password = request.form.get('password')
        
        if User.query.filter_by(email=email).first():
            flash('Email already registered', 'danger')
            return redirect(url_for('register'))
            
        new_user = User(
            name=name,
            email=email,
            department=department,
            password_hash=generate_password_hash(password, method='scrypt')
        )
        db.session.add(new_user)
        db.session.commit()
        
        login_user(new_user)
        return redirect(url_for('register_face'))
    
    return render_template('register.html')

@app.route('/register_face')
@login_required
def register_face():
    return render_template('register_face.html')

@app.route('/save_face', methods=['POST'])
@login_required
def save_face():
    data = request.json
    descriptor = data.get('descriptor')
    
    if not descriptor:
        return jsonify({'success': False, 'message': 'No face data received'})
    
    current_user.face_encoding = json.dumps(descriptor)
    current_user.face_registered = True
    db.session.commit()
    
    return jsonify({'success': True})

@app.route('/mark_attendance', methods=['GET', 'POST'])
@login_required
def mark_attendance():
    if not current_user.face_registered:
        flash('Please register your face first!', 'warning')
        return redirect(url_for('register_face'))
        
    if request.method == 'POST':
        data = request.json
        descriptor = data.get('descriptor')
        lat = data.get('lat')
        lng = data.get('lng')
        
        if not is_within_invertis(lat, lng):
            return jsonify({
                'success': False, 
                'message': 'Attendance can only be marked within Invertis University campus!'
            })
            
        today = datetime.utcnow().date()
        existing = Attendance.query.filter_by(user_id=current_user.id, date=today).first()
        if existing:
            return jsonify({'success': False, 'message': 'Attendance already marked for today!'})
            
        if not descriptor:
            return jsonify({'success': False, 'message': 'No face detected!'})
            
        known_encoding = np.array(json.loads(current_user.face_encoding))
        unknown_encoding = np.array(descriptor)
        distance = np.linalg.norm(known_encoding - unknown_encoding)
        
        if distance < 0.6:
            new_attendance = Attendance(
                user_id=current_user.id,
                date=today,
                time=datetime.utcnow().time(),
                latitude=lat,
                longitude=lng
            )
            db.session.add(new_attendance)
            db.session.commit()
            return jsonify({'success': True, 'message': 'Attendance marked successfully!'})
        else:
            return jsonify({'success': False, 'message': f'Face verification failed!'})

    return render_template('mark_attendance.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        user = User.query.filter_by(email=email).first()
        
        if user and check_password_hash(user.password_hash, password):
            login_user(user)
            return redirect(url_for('dashboard'))
        flash('Invalid credentials', 'danger')
        
    return render_template('login.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('index'))

@app.route('/dashboard')
@login_required
def dashboard():
    if current_user.role == 'admin':
        users = User.query.all()
        from datetime import timedelta
        today = datetime.utcnow().date()
        recent_dates = [today - timedelta(days=i) for i in range(7)]
        recent_dates.reverse()

        user_attendance_map = {}
        today_count = 0
        
        for user in users:
            user_attendance_map[user.id] = {}
            for date in recent_dates:
                att = Attendance.query.filter_by(user_id=user.id, date=date).first()
                if att:
                    user_attendance_map[user.id][date.isoformat()] = att.time.strftime('%I:%M %p')
                    if date == today:
                        today_count += 1
                else:
                    user_attendance_map[user.id][date.isoformat()] = None

        return render_template('admin_dashboard.html', 
                             users=users, 
                             recent_dates=recent_dates,
                             user_attendance_map=user_attendance_map,
                             today_count=today_count)
    
    my_attendance = Attendance.query.filter_by(user_id=current_user.id).order_by(Attendance.date.desc()).all()
    return render_template('user_dashboard.html', attendance=my_attendance)

with app.app_context():
    db.create_all()

if __name__ == '__main__':
    app.run(debug=True)
