from flask import Flask, render_template, redirect, url_for, flash, request, session, jsonify, send_file
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from functools import wraps
import os
import shutil
from datetime import datetime, timedelta
import urllib.parse
import pandas as pd
from io import BytesIO
import random

app = Flask(__name__)

# --- CONFIGURATION ---
# Use a stable secret key for sessions on Render
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'dev-key-default-12345')

# Security headers for production (Ensures login persists over HTTPS)
app.config.update(
    SESSION_COOKIE_SECURE=True,
    SESSION_COOKIE_HTTPONLY=True,
    SESSION_COOKIE_SAMESITE='Lax',
)

# --- DATABASE CONFIGURATION (SSL Fix for Render) ---
BASE_DIR = os.path.abspath(os.path.dirname(__file__))
database_url = os.environ.get('DATABASE_URL')

if database_url:
    # Fix Render's postgres URL format
    if database_url.startswith("postgres://"):
        database_url = database_url.replace("postgres://", "postgresql://", 1)
    app.config['SQLALCHEMY_DATABASE_URI'] = database_url
    
    # SSL and Connection Pool Fix
    app.config['SQLALCHEMY_ENGINE_OPTIONS'] = {
        "connect_args": {
            "sslmode": "require"
        },
        "pool_pre_ping": True,
    }
else:
    # Local fallback
    DB_NAME = 'logistics_prod.db'
    DB_PATH = os.path.join(BASE_DIR, DB_NAME)
    app.config['SQLALCHEMY_DATABASE_URI'] = f'sqlite:///{DB_PATH}'

app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)
login_manager = LoginManager(app)
login_manager.login_view = 'login'

# --- MODELS ---
class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(150), unique=True, nullable=False)
    password = db.Column(db.String(150), nullable=False)
    role = db.Column(db.String(20), default='User')

class Driver(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    license_number = db.Column(db.String(50), nullable=False)
    phone = db.Column(db.String(20), nullable=True)
    status = db.Column(db.String(50), default='Active') 
    trip_count = db.Column(db.Integer, default=0)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)

class Truck(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    capacity_tons = db.Column(db.Float, nullable=False, default=0.0)
    trip_count = db.Column(db.Integer, default=0)
    status = db.Column(db.String(50), default='Active') 
    assigned_driver_id = db.Column(db.Integer, db.ForeignKey('driver.id'), nullable=True)
    assigned_driver = db.relationship('Driver', backref='trucks')
    is_low = db.Column(db.Boolean, default=False)
    is_large = db.Column(db.Boolean, default=False)
    is_tall = db.Column(db.Boolean, default=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)

class Store(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    address = db.Column(db.String(200), nullable=False)
    distance_km = db.Column(db.Float, default=10.0)
    high_dock = db.Column(db.Boolean, default=False)
    small_gate = db.Column(db.Boolean, default=False)
    low_wires = db.Column(db.Boolean, default=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)

class Schedule(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    start_time = db.Column(db.DateTime, nullable=False)
    end_time = db.Column(db.DateTime, nullable=False)
    load_weight = db.Column(db.Float, nullable=False, default=0.0)
    status = db.Column(db.String(20), default='Scheduled')
    trip_type = db.Column(db.String(50), default='Direct')
    truck_id = db.Column(db.Integer, db.ForeignKey('truck.id'), nullable=False)
    store_id = db.Column(db.Integer, db.ForeignKey('store.id'), nullable=False)
    driver_id = db.Column(db.Integer, db.ForeignKey('driver.id'), nullable=True)
    truck = db.relationship('Truck', backref='schedules')
    store = db.relationship('Store', backref='schedules')
    driver = db.relationship('Driver', backref='schedules')

class Maintenance(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    service_type = db.Column(db.String(100), nullable=False)
    cost = db.Column(db.Float, nullable=False)
    date = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    notes = db.Column(db.String(200), nullable=True)
    truck_id = db.Column(db.Integer, db.ForeignKey('truck.id'), nullable=False)
    truck = db.relationship('Truck', backref='maintenance_logs')

# --- DB INITIALIZATION ---
# This ensures tables are created immediately when the app starts on Render
with app.app_context():
    db.create_all()

@login_manager.user_loader
def load_user(user_id):
    return db.session.get(User, int(user_id))

# --- PERMISSION DECORATOR ---
def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if current_user.role != 'Admin':
            flash("🚫 Access Denied: Administrator privileges required.")
            return redirect(url_for('dashboard'))
        return f(*args, **kwargs)
    return decorated_function

# --- HELPERS ---
def check_compatibility(truck, store):
    if truck.is_low and store.high_dock: return False, f"{truck.name} is too LOW for {store.name}."
    if truck.is_large and store.small_gate: return False, f"{truck.name} is too BIG for {store.name}."
    if truck.is_tall and store.low_wires: return False, f"{truck.name} is too TALL for {store.name}."
    return True, "OK"

# --- AUTH ROUTES ---
@app.route('/')
def index():
    return redirect(url_for('login'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        user = User.query.filter_by(username=request.form.get('username')).first()
        if user and check_password_hash(user.password, request.form.get('password')):
            login_user(user)
            return redirect(url_for('dashboard'))
        flash('Invalid username or password.')
    return render_template('login.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('login'))

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        if User.query.filter_by(username=request.form.get('username')).first():
            flash('Username taken.')
        else:
            role = 'Admin' if User.query.count() == 0 else 'User'
            db.session.add(User(
                username=request.form.get('username'), 
                password=generate_password_hash(request.form.get('password')), 
                role=role
            ))
            db.session.commit()
            flash(f'Registered as {role}! Please login.')
            return redirect(url_for('login'))
    return render_template('register.html')

# --- DASHBOARD & CORE ROUTES ---
@app.route('/dashboard')
@login_required
def dashboard():
    trucks = Truck.query.all()
    stores = Store.query.all()
    stats = {
        'truck_count': len(trucks),
        'available_trucks': Truck.query.filter_by(status='Active').count(),
        'maintenance_trucks': Truck.query.filter_by(status='Maintenance').count(),
        'driver_count': Driver.query.filter_by(status='Active').count(),
        'active_jobs': Schedule.query.filter_by(status='Scheduled').count(),
        'maintenance_cost': sum(log.cost for log in Maintenance.query.all())
    }
    return render_template('dashboard.html', trucks=trucks, stores=stores, stats=stats)

# [ ... All your other logic for Schedule, Reports, Maintenance, Drivers, Stores ... ]
# (Copy the remaining routes from your original script here)

if __name__ == '__main__':
    app.run(debug=True)