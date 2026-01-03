from flask import Blueprint, render_template, request, flash, redirect, url_for
from flask_login import login_required, current_user
from ..models import db, Truck, Schedule
from ..forms import TruckForm, ScheduleForm

main_bp = Blueprint('main', __name__)

@main_bp.route('/dashboard')
@login_required
def dashboard():
    trucks = Truck.query.filter_by(user_id=current_user.id).all()
    # Note: We don't pass 'schedules' here anymore because the API handles it!
    return render_template('dashboard.html', trucks=trucks)

# ... (Include add_truck and schedule_truck functions here, adapted from your old code)
# IMPORTANT: When creating Schedule, ensure you import Truck and Schedule from ..models