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
# On Render, use the Secret Key env variable, otherwise use a fallback
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'a-very-long-and-random-secret-key-for-local-development')

# --- DATABASE CONFIGURATION (Hybrid: Local PostgreSQL + Cloud) ---
BASE_DIR = os.path.abspath(os.path.dirname(__file__))

# Check if running on Render (Cloud)
database_url = os.environ.get('DATABASE_URL')

if database_url:
    # Cloud Config (Render)
    if database_url.startswith("postgres://"):
        database_url = database_url.replace("postgres://", "postgresql://", 1)
    app.config['SQLALCHEMY_DATABASE_URI'] = database_url
else:
    # --- LOCAL POSTGRESQL CONFIG ---
    # Replace 'YOUR_PASSWORD' with what you set during installation
    LOCAL_DB_USER = "postgres"
    LOCAL_DB_PASS = "postgres"
    LOCAL_DB_NAME = "logistics_db"
    
    app.config['SQLALCHEMY_DATABASE_URI'] = f'postgresql://{LOCAL_DB_USER}:{LOCAL_DB_PASS}@localhost/{LOCAL_DB_NAME}'

app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)
login_manager = LoginManager(app)
login_manager.login_view = 'login'

# --- CONSTANTS ---
WAREHOUSE_ADDRESS = "ATREOS DC 2 Oba Akran, 5 OBALUFON-LAGERE ROAD, LAGERE JUNCTION, beside CATHOLIC CHURCH, Oba Akran, Ikeja 101233, Lagos"

# --- CONTEXT PROCESSOR ---
@app.context_processor
def inject_datetime():
    return {'datetime': datetime}

# --- PERMISSIONS ---
def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if current_user.role != 'Admin':
            flash("🚫 Access Denied: Administrator privileges required.")
            return redirect(url_for('dashboard'))
        return f(*args, **kwargs)
    return decorated_function

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
    capacity_tons = db.Column(db.Float, nullable=False, default=0.0) # Pallets
    trip_count = db.Column(db.Integer, default=0)
    status = db.Column(db.String(50), default='Active') 
    
    # Dedicated Driver Link
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
    
    # Constraints
    high_dock = db.Column(db.Boolean, default=False)
    small_gate = db.Column(db.Boolean, default=False)
    low_wires = db.Column(db.Boolean, default=False)
    
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)

class Schedule(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    start_time = db.Column(db.DateTime, nullable=False)
    end_time = db.Column(db.DateTime, nullable=False)
    load_weight = db.Column(db.Float, nullable=False, default=0.0) # Pallets
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

@login_manager.user_loader
def load_user(user_id):
    return db.session.get(User, int(user_id))

# --- HELPERS ---
def check_compatibility(truck, store):
    if truck.is_low and store.high_dock: return False, f"{truck.name} is too LOW for {store.name}."
    if truck.is_large and store.small_gate: return False, f"{truck.name} is too BIG for {store.name}."
    if truck.is_tall and store.low_wires: return False, f"{truck.name} is too TALL for {store.name}."
    return True, "OK"

# --- AUTH ROUTES ---
@app.route('/')
def index(): return redirect(url_for('login'))

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
def logout(): logout_user(); return redirect(url_for('login'))

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        if User.query.filter_by(username=request.form.get('username')).first():
            flash('Username taken.')
        else:
            role = 'Admin' if User.query.count() == 0 else 'User'
            db.session.add(User(username=request.form.get('username'), password=generate_password_hash(request.form.get('password')), role=role))
            db.session.commit()
            flash(f'Registered as {role}! Please login.')
            return redirect(url_for('login'))
    return render_template('register.html')

# --- DASHBOARD ---
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

# --- JOB UPLOADER ---
@app.route('/download_job_template')
@login_required
def download_job_template():
    stores = Store.query.all()
    data = []
    for s in stores:
        data.append({'Store': s.name, 'Address': s.address, 'Pallets': ''})
    
    df = pd.DataFrame(data)
    output = BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        df.to_excel(writer, index=False)
        worksheet = writer.sheets['Sheet1']
        worksheet.column_dimensions['A'].width = 30
        worksheet.column_dimensions['B'].width = 50
        worksheet.column_dimensions['C'].width = 15
    output.seek(0)
    return send_file(output, download_name="bulk_job_template.xlsx", as_attachment=True)

@app.route('/upload_job_manifest', methods=['POST'])
@login_required
def upload_job_manifest():
    file = request.files.get('file')
    if not file:
        flash("No file selected.")
        return redirect(url_for('schedule_truck'))

    try:
        df = pd.read_excel(file)
        df = df.fillna(0)
        df.columns = df.columns.str.strip().str.lower()
        if 'store' not in df.columns:
            flash("Error: Excel must have a column named 'Store'.")
            return redirect(url_for('schedule_truck'))

        preview_jobs = []
        all_stores = Store.query.all()
        
        for _, row in df.iterrows():
            excel_name = str(row.get('store', '')).strip().lower()
            pallets = 0.0
            if 'pallets' in df.columns: pallets = float(row.get('pallets', 0))
            elif 'load' in df.columns: pallets = float(row.get('load', 0))
            elif 'quantity' in df.columns: pallets = float(row.get('quantity', 0))
            elif 'order' in df.columns: pallets = float(row.get('order', 0))
            
            if pallets <= 0: continue

            match = next((s for s in all_stores if s.name.lower() == excel_name), None)
            if match:
                preview_jobs.append({'store_id': match.id, 'store_name': match.name, 'store_address': match.address, 'volume': int(pallets)})
        
        if not preview_jobs:
            flash("No matching stores found in database. Check spelling.")
            return redirect(url_for('schedule_truck'))

        flash(f"Loaded {len(preview_jobs)} jobs from Excel. Please confirm.")
        
        trucks = Truck.query.filter_by(status='Active').order_by(Truck.trip_count).all()
        stores = Store.query.all()
        active_drivers = Driver.query.filter_by(status='Active').count()
        return render_template('schedule.html', trucks=trucks, stores=stores, drivers=active_drivers, preview_jobs=preview_jobs)

    except Exception as e:
        flash(f"Error processing file: {str(e)}")
        return redirect(url_for('schedule_truck'))

# --- SCHEDULING ---
@app.route('/schedule_truck', methods=['GET', 'POST'])
@login_required
def schedule_truck():
    trucks = Truck.query.filter_by(status='Active').order_by(Truck.trip_count).all()
    stores = Store.query.all()
    active_drivers = Driver.query.filter_by(status='Active').order_by(Driver.trip_count).all()
    
    if request.method == 'POST':
        try:
            schedule_type = request.form.get('schedule_type')
            start_time = datetime.strptime(request.form.get('start_time'), '%Y-%m-%dT%H:%M')

            if schedule_type == 'bulk':
                store_ids = request.form.getlist('store_ids[]')
                volumes = request.form.getlist('volumes[]')
                
                valid_trucks = [t for t in trucks if t.capacity_tons > 0 and t.assigned_driver_id]
                if not valid_trucks: 
                    flash("No active trucks with drivers available.")
                    return redirect(url_for('schedule_truck'))

                orders = []
                for i in range(len(store_ids)):
                    try: s_id, vol = int(store_ids[i]), float(volumes[i])
                    except: continue
                    if vol > 0: orders.append({'store': db.session.get(Store, s_id), 'volume': vol})

                trips_generated = 0
                truck_idx = 0
                partials = []

                # Full Loads
                for order in orders:
                    store = order['store']
                    remaining = order['volume']
                    compatible = [t for t in valid_trucks if check_compatibility(t, store)[0]]
                    if not compatible: flash(f"Skipped {store.name}: No compatible trucks."); continue

                    while remaining > 0:
                        truck = compatible[truck_idx % len(compatible)]
                        driver = truck.assigned_driver
                        if not driver or driver.status != 'Active': truck_idx += 1; continue

                        if remaining >= (truck.capacity_tons * 0.8):
                            load = min(remaining, truck.capacity_tons)
                            travel_hrs = (store.distance_km / 30) + 1
                            db.session.add(Schedule(truck_id=truck.id, store_id=store.id, driver_id=driver.id, load_weight=load, start_time=start_time, end_time=start_time + timedelta(hours=travel_hrs), status='Scheduled', trip_type='Direct'))
                            truck.trip_count += 1; driver.trip_count += 1; truck_idx += 1; trips_generated += 1
                            remaining -= load
                        else:
                            partials.append({'store': store, 'volume': remaining})
                            remaining = 0

                # Partials
                partials.sort(key=lambda x: x['store'].distance_km)
                while partials:
                    base = partials[0]
                    base_compat = [t for t in valid_trucks if check_compatibility(t, base['store'])[0]]
                    if not base_compat: partials.pop(0); continue

                    truck = base_compat[truck_idx % len(base_compat)]
                    driver = truck.assigned_driver
                    truck_idx += 1
                    if not driver or driver.status != 'Active': continue
                    
                    current_load = 0
                    current_orders = []
                    for p in partials[:]:
                        if check_compatibility(truck, p['store'])[0] and (current_load + p['volume'] <= truck.capacity_tons):
                             if abs(p['store'].distance_km - base['store'].distance_km) <= 10:
                                current_orders.append(p); current_load += p['volume']; partials.remove(p)
                    
                    for p in current_orders:
                        travel_hrs = (p['store'].distance_km / 30) + 2
                        db.session.add(Schedule(truck_id=truck.id, store_id=p['store'].id, driver_id=driver.id, load_weight=p['volume'], start_time=start_time, end_time=start_time + timedelta(hours=travel_hrs), status='Scheduled', trip_type='Merged'))
                    
                    truck.trip_count += 1; driver.trip_count += 1; trips_generated += 1

                db.session.commit()
                flash(f'Auto-Plan: {trips_generated} trips generated.')
                return redirect(url_for('dashboard'))

            else:
                store = db.session.get(Store, int(request.form.get('store_id')))
                load = float(request.form.get('load_weight'))
                truck = db.session.get(Truck, int(request.form.get('truck_id')))
                
                if truck.status == 'Maintenance': flash("Truck in Maintenance"); return redirect(url_for('schedule_truck'))
                if not check_compatibility(truck, store)[0]: flash("Constraint Error"); return redirect(url_for('schedule_truck'))
                if load > truck.capacity_tons: flash("Overload!"); return redirect(url_for('schedule_truck'))
                driver = truck.assigned_driver
                if not driver or driver.status != 'Active': flash("Truck has no active driver"); return redirect(url_for('schedule_truck'))

                travel_hrs = (store.distance_km / 30) + 1
                db.session.add(Schedule(truck_id=truck.id, store_id=store.id, driver_id=driver.id, load_weight=load, start_time=start_time, end_time=start_time+timedelta(hours=travel_hrs), status='Scheduled', trip_type='Direct'))
                truck.trip_count += 1; driver.trip_count += 1
                db.session.commit()
                return redirect(url_for('dashboard'))

        except Exception as e: flash(f'Error: {e}')
    return render_template('schedule.html', trucks=trucks, stores=stores)

# --- REPORTS ---
@app.route('/reports')
@login_required
def reports():
    trips = Schedule.query.join(Store).join(Truck).order_by(Store.name.asc(), Schedule.start_time.desc()).all()
    return render_template('reports.html', trips=trips)

@app.route('/export_report')
@login_required
def export_report():
    data = []
    trips = Schedule.query.join(Store).join(Truck).order_by(Store.name.asc(), Schedule.start_time.desc()).all()
    for t in trips:
        hr = t.start_time.hour
        shift = "Morning" if 6 <= hr < 12 else "Afternoon" if 12 <= hr < 18 else "Overtime"
        data.append({'Store': t.store.name, 'Full Address': t.store.address, 'Date': t.start_time.strftime('%Y-%m-%d'), 'Time': t.start_time.strftime('%H:%M'), 'Shift': shift, 'Trip Type': t.trip_type, 'Truck': f"{t.truck.name}", 'Capacity (P)': int(t.truck.capacity_tons), 'Driver': t.driver.name if t.driver else '--', 'Load (P)': int(t.load_weight), 'Status': t.status})
    out = BytesIO(); pd.DataFrame(data).to_excel(out, index=False); out.seek(0)
    return send_file(out, download_name="trip_report.xlsx", as_attachment=True)

# --- API FOR CALENDAR ---
@app.route('/api/get_trips_by_date/<date_str>')
@login_required
def get_trips_by_date(date_str):
    try:
        sd = datetime.strptime(date_str, '%Y-%m-%d').date()
        trips = Schedule.query.join(Truck).filter(db.func.date(Schedule.start_time) == sd).order_by(Schedule.start_time.asc()).all()
        res = []
        for t in trips:
            hr = t.start_time.hour
            shift = "Morning" if 6 <= hr < 12 else "Afternoon" if 12 <= hr < 18 else "Overtime"
            res.append({'id': t.id, 'trip_type': t.trip_type, 'shift': shift, 'truck': f"{t.truck.name} ({int(t.truck.capacity_tons)}P)", 'driver': t.driver.name if t.driver else '--', 'store': f"{t.store.name} - {t.store.address}", 'load': int(t.load_weight), 'status': t.status})
        return jsonify({'status': 'success', 'data': res})
    except Exception as e: return jsonify({'status': 'error', 'message': str(e)})

@app.route('/events')
@login_required
def get_events():
    ev = []
    for s in Schedule.query.filter(Schedule.status != 'Completed').all():
        ev.append({'title': 'Trip', 'start': s.start_time.isoformat(), 'end': s.end_time.isoformat(), 'display': 'background', 'color': '#3788d8'})
    return jsonify(ev)

# --- MAINTENANCE & RESOURCES ---
@app.route('/maintenance', methods=['GET', 'POST'])
@login_required
def maintenance():
    trucks = Truck.query.all()
    if request.method == 'POST':
        db.session.add(Maintenance(truck_id=request.form.get('truck_id'), service_type=request.form.get('service_type'), cost=float(request.form.get('cost')), notes=request.form.get('notes'), date=datetime.strptime(request.form.get('date'), '%Y-%m-%d')))
        db.session.commit(); return redirect(url_for('maintenance'))
    logs = Maintenance.query.join(Truck).order_by(Maintenance.date.desc()).all()
    return render_template('maintenance.html', trucks=trucks, logs=logs)

@app.route('/toggle_truck_status/<int:id>', methods=['POST'])
@login_required
def toggle_truck_status(id):
    t = db.session.get(Truck, id)
    if t: t.status='Maintenance' if t.status=='Active' else 'Active'; db.session.commit()
    return redirect(url_for('maintenance'))

@app.route('/clear_logs')
@login_required
@admin_required
def clear_logs():
    Schedule.query.filter(Schedule.status=='Completed').delete(); db.session.commit()
    return redirect(url_for('reports'))

@app.route('/mark_complete/<int:id>')
@login_required
def mark_complete(id):
    t = db.session.get(Schedule, id)
    if t: t.status='Completed'; db.session.commit()
    return redirect(url_for('reports'))

@app.route('/revert_trip/<int:id>')
@login_required
def revert_trip(id):
    t = db.session.get(Schedule, id)
    if t:
        if t.truck.trip_count > 0: t.truck.trip_count -= 1
        if t.driver.trip_count > 0: t.driver.trip_count -= 1
        db.session.delete(t); db.session.commit()
    return redirect(url_for('reports'))

@app.route('/users', methods=['GET', 'POST'])
@login_required
@admin_required
def users():
    if request.method == 'POST':
        if not User.query.filter_by(username=request.form.get('username')).first():
            db.session.add(User(username=request.form.get('username'), password=generate_password_hash(request.form.get('password')), role=request.form.get('role'))); db.session.commit()
    return render_template('users.html', users=User.query.all())

@app.route('/delete_user/<int:id>', methods=['POST'])
@login_required
@admin_required
def delete_user(id):
    if id!=current_user.id: db.session.delete(db.session.get(User, id)); db.session.commit()
    return redirect(url_for('users'))

@app.route('/drivers', methods=['GET', 'POST'])
@login_required
def drivers():
    trucks = Truck.query.all()
    if request.method == 'POST':
        if 'status_update' in request.form:
            d = db.session.get(Driver, request.form.get('driver_id'))
            if d: d.status=request.form.get('status'); db.session.commit()
        else:
            if current_user.role == 'Admin':
                d = Driver(name=request.form.get('name'), license_number=request.form.get('license_number'), phone=request.form.get('phone'), user_id=current_user.id)
                db.session.add(d); db.session.commit()
                if request.form.get('truck_id'):
                    t = db.session.get(Truck, request.form.get('truck_id'))
                    t.assigned_driver_id = d.id
                    db.session.commit()
    return render_template('drivers.html', drivers=Driver.query.all(), trucks=trucks)

@app.route('/edit_driver/<int:id>', methods=['POST'])
@login_required
@admin_required
def edit_driver(id):
    d = db.session.get(Driver, id)
    if d: 
        d.name = request.form.get('name'); d.phone = request.form.get('phone')
        new_tid = request.form.get('truck_id')
        old = Truck.query.filter_by(assigned_driver_id=d.id).first()
        if old: old.assigned_driver_id = None
        if new_tid:
            new = db.session.get(Truck, new_tid)
            new.assigned_driver_id = d.id
        db.session.commit()
    return redirect(url_for('drivers'))

@app.route('/delete_driver/<int:id>', methods=['POST'])
@login_required
@admin_required
def delete_driver(id):
    d = db.session.get(Driver, id)
    if d: 
        t = Truck.query.filter_by(assigned_driver_id=d.id).first()
        if t: t.assigned_driver_id = None
        for s in Schedule.query.filter_by(driver_id=d.id).all(): s.driver_id = None
        db.session.delete(d); db.session.commit()
    return redirect(url_for('drivers'))

@app.route('/add_truck', methods=['GET', 'POST'])
@login_required
@admin_required
def add_truck():
    if request.method == 'POST':
        db.session.add(Truck(name=request.form.get('name'), capacity_tons=float(request.form.get('capacity')), is_low='is_low' in request.form, is_large='is_large' in request.form, is_tall='is_tall' in request.form, user_id=current_user.id))
        db.session.commit(); return redirect(url_for('add_truck'))
    return render_template('add_truck.html')

@app.route('/import_trucks', methods=['POST'])
@login_required
@admin_required
def import_trucks():
    f = request.files.get('file')
    if f:
        try:
            df = pd.read_excel(f); df.columns = df.columns.str.strip().str.lower()
            for _, r in df.iterrows():
                n = str(r['name'])
                if n!='nan' and not Truck.query.filter_by(name=str(r['name'])).first():
                    cap = float(r.get('capacity', 0) or r.get('capacity_tons', 0))
                    db.session.add(Truck(name=n, capacity_tons=cap, user_id=current_user.id))
            db.session.commit(); flash('Imported.')
        except: flash('Error')
    return redirect(url_for('add_truck'))

@app.route('/export_trucks')
@login_required
def export_trucks():
    df = pd.DataFrame([{'Name': t.name, 'Capacity': t.capacity_tons} for t in Truck.query.all()])
    out = BytesIO(); pd.DataFrame(df).to_excel(out, index=False); out.seek(0)
    return send_file(out, download_name="trucks.xlsx", as_attachment=True)

@app.route('/add_store', methods=['GET', 'POST'])
@login_required
@admin_required
def add_store():
    if request.method == 'POST':
        db.session.add(Store(name=request.form.get('name'), address=request.form.get('address'), distance_km=float(request.form.get('distance') or 10), high_dock='high_dock' in request.form, small_gate='small_gate' in request.form, low_wires='low_wires' in request.form, user_id=current_user.id))
        db.session.commit(); return redirect(url_for('add_store'))
    return render_template('add_store.html')

@app.route('/import_stores', methods=['POST'])
@login_required
@admin_required
def import_stores():
    f = request.files.get('file')
    if f:
        try:
            df = pd.read_excel(f); df.columns = df.columns.str.strip().str.lower()
            for _, r in df.iterrows():
                n = str(r.get('name',''))
                if n and n!='nan' and not Store.query.filter_by(name=str(r.get('name'))).first():
                    def pb(v): return str(v).lower() in ['yes', 'y', 'true', '1']
                    db.session.add(Store(name=n, address=str(r.get('address', '')), distance_km=float(r.get('distance', 10)), high_dock=pb(r.get('high dock', False)), small_gate=pb(r.get('small gate', False)), low_wires=pb(r.get('low wires', False)), user_id=current_user.id))
            db.session.commit(); flash('Imported.')
        except Exception as e: flash(f'Import error: {str(e)}')
    return redirect(url_for('add_store'))

@app.route('/export_stores')
@login_required
def export_stores():
    df = pd.DataFrame([{'Name': s.name, 'Address': s.address} for s in Store.query.all()])
    out = BytesIO(); pd.DataFrame(df).to_excel(out, index=False); out.seek(0)
    return send_file(out, download_name="stores.xlsx", as_attachment=True)

@app.route('/settings')
@login_required
@admin_required
def settings(): return render_template('settings.html')

@app.route('/backup_db')
@login_required
@admin_required
def backup_db():
    if os.path.exists(DB_PATH): return send_file(DB_PATH, as_attachment=True, download_name=f"backup.db")
    return redirect(url_for('settings'))

@app.route('/restore_db', methods=['POST'])
@login_required
@admin_required
def restore_db():
    f = request.files.get('file')
    if f: db.session.remove(); f.save(DB_PATH); flash('Restored')
    return redirect(url_for('settings'))

if __name__ == '__main__':
    # REMOVED: db.create_all() here. It's in server.py now.
    app.run(debug=True, port=8080)