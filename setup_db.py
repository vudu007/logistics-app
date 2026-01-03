import os
from app import app, db

db_file = "trucks.db"

# Force delete the old database file
if os.path.exists(db_file):
    try:
        os.remove(db_file)
        print(f"Old '{db_file}' deleted successfully.")
    except PermissionError:
        print(f"Error: Could not delete '{db_file}'. Please STOP the server (CTRL+C) and try again.")
        exit()
else:
    print(f"'{db_file}' not found (clean slate).")

# Create the new database tables
with app.app_context():
    db.create_all()
    print("New database created successfully with 'Store' and 'capacity' columns!")
    print("You may now run 'python app.py'")