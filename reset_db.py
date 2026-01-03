import os
from app import app, db

db_name = "logistics.db"

# 1. Delete the old database
if os.path.exists(db_name):
    try:
        os.remove(db_name)
        print(f"✅ Deleted old '{db_name}' successfully.")
    except PermissionError:
        print(f"❌ ERROR: '{db_name}' is locked. Please CLOSE your PowerShell or Stop the Server first.")
        exit()
else:
    print(f"ℹ️ '{db_name}' not found. Starting fresh.")

# 2. Create the new database
with app.app_context():
    db.create_all()
    print("✅ New database created! You can now run 'python app.py'")