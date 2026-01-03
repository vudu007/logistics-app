from waitress import serve
from app import app, db
import webbrowser
from threading import Timer
import os
import shutil
from datetime import datetime

# --- CONFIGURATION ---
DB_FILENAME = 'logistics_prod.db' # Ensure this matches app.py
BACKUP_FOLDER = 'backups'

def create_backup(event_type):
    """Creates a backup of the database file."""
    if not os.path.exists(BACKUP_FOLDER):
        os.makedirs(BACKUP_FOLDER)
    if os.path.exists(DB_FILENAME):
        timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        destination = os.path.join(os.path.abspath(os.path.dirname(__file__)), BACKUP_FOLDER, f"logistics_{event_type}_{timestamp}.db")
        try:
            shutil.copy2(DB_FILENAME, destination)
            print(f"[{event_type}] Backup successful: {os.path.basename(destination)}")
        except Exception as e:
            print(f"[{event_type}] Backup FAILED: {e}")

def open_browser():
    webbrowser.open_new("http://localhost:8080")

if __name__ == '__main__':
    # CRITICAL: Create tables INSIDE the app context, here.
    with app.app_context():
        db.create_all()

    print("-------------------------------------------------------")
    print(" PRODUCTION SERVER INITIALIZING")
    print("-------------------------------------------------------")

    # Perform Startup Backup
    create_backup("STARTUP")

    print("-------------------------------------------------------")
    print(" SERVER RUNNING")
    print(" Access: http://localhost:8080")
    print(" Stop:   Press CTRL + C")
    print("-------------------------------------------------------")
    
    # Auto-open browser
    Timer(1.5, open_browser).start()
    
    try:
        serve(app, host='0.0.0.0', port=8080, threads=6)
    except KeyboardInterrupt:
        print("\nStopping server...")
    finally:
        # Perform Shutdown Backup
        create_backup("SHUTDOWN")
        print("Goodbye!")