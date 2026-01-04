from waitress import serve
from app import app, db
import webbrowser
from threading import Timer
import os
import shutil
from datetime import datetime

# --- CONFIGURATION ---
DB_FILENAME = 'logistics_final_v2.db' # Match the new DB name
BACKUP_FOLDER = 'backups'

def create_backup(event_type):
    if not os.path.exists(BACKUP_FOLDER):
        os.makedirs(BACKUP_FOLDER)
    if os.path.exists(DB_FILENAME):
        timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        destination = os.path.join(os.path.abspath(os.path.dirname(__file__)), BACKUP_FOLDER, f"logistics_{event_type}_{timestamp}.db")
        try:
            shutil.copy2(DB_FILENAME, destination)
            print(f"[{event_type}] Backup successful.")
        except Exception as e:
            print(f"[{event_type}] Backup FAILED: {e}")

def open_browser():
    webbrowser.open_new("http://localhost:8080")

if __name__ == '__main__':
    # CRITICAL: Create tables here, inside the app context
    with app.app_context():
        db.create_all()

    print("-" * 50)
    print(" PRODUCTION SERVER INITIALIZING")
    print("-" * 50)

    # Perform Startup Backup
    create_backup("STARTUP")

    print("-" * 50)
    print(" SERVER RUNNING")
    print(" Access: http://localhost:8080")
    print(" Stop:   Press CTRL + C")
    print("-" * 50)
    
    Timer(1.5, open_browser).start()
    
    try:
        serve(app, host='0.0.0.0', port=8080, threads=8)
    except KeyboardInterrupt:
        print("\nStopping server...")
    finally:
        # Perform Shutdown Backup
        create_backup("SHUTDOWN")
        print("Goodbye!")