import os
import shutil
import time
from datetime import datetime
from waitress import serve
from app import app, db
import webbrowser
from threading import Timer

# --- CONFIGURATION ---
DB_FILENAME = 'logistics_prod.db'
BACKUP_FOLDER = 'backups'

def create_backup(event_type):
    """
    Creates a backup of the database file.
    event_type: 'STARTUP' or 'SHUTDOWN'
    """
    # 1. Create backup folder if it doesn't exist
    if not os.path.exists(BACKUP_FOLDER):
        os.makedirs(BACKUP_FOLDER)

    # 2. Check if DB exists
    if os.path.exists(DB_FILENAME):
        # 3. Create formatted filename (e.g., logistics_STARTUP_2025-01-03_14-30.db)
        timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        backup_name = f"logistics_{event_type}_{timestamp}.db"
        destination = os.path.join(BACKUP_FOLDER, backup_name)

        try:
            shutil.copy2(DB_FILENAME, destination)
            print(f"[{event_type}] Backup successful: {backup_name}")
        except Exception as e:
            print(f"[{event_type}] Backup FAILED: {e}")
    else:
        print(f"[{event_type}] No database found to back up yet.")

def open_browser():
    """Opens the default web browser"""
    print("Launching Browser...")
    webbrowser.open_new("http://localhost:8080")

if __name__ == '__main__':
    # Ensure Database Exists before starting
    with app.app_context():
        db.create_all()

    print("-------------------------------------------------------")
    print(" PRODUCTION SERVER INITIALIZING")
    print("-------------------------------------------------------")

    # --- 1. PERFORM STARTUP BACKUP ---
    create_backup("STARTUP")

    print("-------------------------------------------------------")
    print(" SERVER RUNNING")
    print(" Access: http://localhost:8080")
    print(" Stop:   Press CTRL + C")
    print("-------------------------------------------------------")
    
    # Auto-open browser after 1.5 seconds
    Timer(1.5, open_browser).start()
    
    try:
        # Start the Waitress Server
        serve(app, host='0.0.0.0', port=8080, threads=6)
    except KeyboardInterrupt:
        # This catches CTRL+C
        print("\nStopping server...")
    finally:
        # --- 2. PERFORM SHUTDOWN BACKUP ---
        print("Performing safety backup...")
        create_backup("SHUTDOWN")
        print("Goodbye!")