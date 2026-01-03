from flask import Blueprint, jsonify
from flask_login import login_required, current_user
from ..models import Schedule, Truck

api_bp = Blueprint('api', __name__)

@api_bp.route('/events')
@login_required
def get_events():
    """Return JSON data for the Calendar"""
    schedules = Schedule.query.join(Truck).filter(Truck.user_id == current_user.id).all()
    events = []
    
    for s in schedules:
        events.append({
            'title': f"{s.truck.name}: {s.job_description}",
            'start': s.start_time.isoformat(),
            'end': s.end_time.isoformat(),
            'backgroundColor': '#3788d8' # You can color code trucks later
        })
    
    return jsonify(events)