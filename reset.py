import os
from app import app, db

# Delete old file
if os.path.exists("trucks.db"):
    os.remove("trucks.db")
    print("Old database deleted.")

# Create new tables
with app.app_context():
    db.create_all()
    print("New database created successfully!")