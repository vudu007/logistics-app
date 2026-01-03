from flask_sqlalchemy import SQLAlchemy
db = SQLAlchemy()

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(150), unique=True, nullable=False, index=True) # Indexed
    password = db.Column(db.String(150), nullable=False)

class Truck(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    # Index user_id because we frequently search for trucks by user
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False, index=True)

class Schedule(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    job_description = db.Column(db.String(200), nullable=False)
    start_time = db.Column(db.DateTime, nullable=False, index=True) # Indexed for calendar lookups
    end_time = db.Column(db.DateTime, nullable=False)
    # Index truck_id to quickly find conflicts
    truck_id = db.Column(db.Integer, db.ForeignKey('truck.id'), nullable=False, index=True)