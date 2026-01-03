import os
from app import app, db

# 1. Define the database file name
db_file = "trucks.db"

# 2. Delete the old file
if os.path.exists(db_file):
    try:
        os.remove(db_file)
        print(f"SUCCESS: Deleted old '{db_file}'")
    except PermissionError:
        print("ERROR: File is locked. Please STOP the flask server (CTRL+C) first!")
        exit()
else:
    print("Old database not found (already clean).")

# 3. Create the new database with the correct columns
with app.app_context():
    db.create_all()
    print("SUCCESS: Created new database with 'capacity' column.")
    print("You may now run 'python app.py'.")