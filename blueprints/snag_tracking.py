from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify, send_file
from flask_login import login_required, current_user
from functools import wraps
from datetime import datetime, timedelta
import os
import json
import gspread
from google.oauth2.service_account import Credentials
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload
import pandas as pd
from io import BytesIO
import time

snag_bp = Blueprint('snag', __name__, url_prefix='/snag')

# Cache for Google Sheets data
CACHE_DURATION = 3600  # 1 hour
cache = {
    'stores': {'data': [], 'timestamp': 0},
    'categories': {'data': [], 'timestamp': 0},
    'urgency_levels': {'data': [], 'timestamp': 0}
}

# Google Sheets Configuration
SPREADSHEET_URL = 'https://docs.google.com/spreadsheets/d/16BK0uRc5E1y457vEsqZJt9guPEzlYnSyCMLT6gurw_o/'
SPREADSHEET_ID = '16BK0uRc5E1y457vEsqZJt9guPEzlYnSyCMLT6gurw_o'

def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated or current_user.role != 'Admin':
            flash("🚫 Access Denied: Administrator privileges required.")
            return redirect(url_for('dashboard'))
        return f(*args, **kwargs)
    return decorated_function

def get_google_credentials():
    """Get Google API credentials from environment or file"""
    creds_file = os.environ.get('GOOGLE_CREDENTIALS_FILE', 'google_credentials.json')
    
    if not os.path.exists(creds_file):
        return None
    
    try:
        scopes = [
            'https://www.googleapis.com/auth/spreadsheets',
            'https://www.googleapis.com/auth/drive.file'
        ]
        credentials = Credentials.from_service_account_file(creds_file, scopes=scopes)
        return credentials
    except Exception as e:
        print(f"Error loading credentials: {e}")
        return None

def get_gsheet_client():
    """Get authenticated gspread client"""
    credentials = get_google_credentials()
    if not credentials:
        return None
    
    try:
        client = gspread.authorize(credentials)
        return client
    except Exception as e:
        print(f"Error creating gspread client: {e}")
        return None

def get_drive_service():
    """Get authenticated Google Drive service"""
    credentials = get_google_credentials()
    if not credentials:
        return None
    
    try:
        service = build('drive', 'v3', credentials=credentials)
        return service
    except Exception as e:
        print(f"Error creating Drive service: {e}")
        return None

def is_cache_valid(cache_key):
    """Check if cached data is still valid"""
    if cache_key not in cache:
        return False
    
    current_time = time.time()
    cache_age = current_time - cache[cache_key]['timestamp']
    return cache_age < CACHE_DURATION and len(cache[cache_key]['data']) > 0

def get_stores_from_sheet():
    """Fetch store names/addresses from Google Sheet with caching"""
    if is_cache_valid('stores'):
        return cache['stores']['data']
    
    try:
        client = get_gsheet_client()
        if not client:
            return []
        
        sheet = client.open_by_key(SPREADSHEET_ID)
        
        # Try to get from 'Stores' worksheet, or first worksheet
        try:
            worksheet = sheet.worksheet('Stores')
        except:
            worksheet = sheet.get_worksheet(0)
        
        records = worksheet.get_all_records()
        
        stores = []
        for record in records:
            # Handle various column name formats
            store_name = record.get('Store Name') or record.get('store_name') or record.get('Name') or ''
            store_address = record.get('Address') or record.get('address') or ''
            store_code = record.get('Store Code') or record.get('store_code') or record.get('Code') or ''
            
            if store_name:
                full_name = f"{store_name} - {store_address}" if store_address else store_name
                stores.append({
                    'name': store_name,
                    'address': store_address,
                    'full_name': full_name,
                    'code': store_code
                })
        
        # Update cache
        cache['stores']['data'] = stores
        cache['stores']['timestamp'] = time.time()
        
        return stores
    except Exception as e:
        print(f"Error fetching stores from sheet: {e}")
        return []

def get_categories_from_sheet():
    """Fetch snag categories from Google Sheet with caching"""
    if is_cache_valid('categories'):
        return cache['categories']['data']
    
    try:
        client = get_gsheet_client()
        if not client:
            return ['Electrical', 'Plumbing', 'Structural', 'HVAC', 'Safety', 'Other']
        
        sheet = client.open_by_key(SPREADSHEET_ID)
        
        # Try to get from 'Categories' worksheet
        try:
            worksheet = sheet.worksheet('Categories')
            records = worksheet.get_all_records()
            categories = [record.get('Category') or record.get('category') or '' for record in records if record.get('Category') or record.get('category')]
        except:
            # Default categories if worksheet not found
            categories = ['Electrical', 'Plumbing', 'Structural', 'HVAC', 'Safety', 'Lighting', 'Flooring', 'Doors/Windows', 'Painting', 'Equipment', 'Other']
        
        # Update cache
        cache['categories']['data'] = categories
        cache['categories']['timestamp'] = time.time()
        
        return categories
    except Exception as e:
        print(f"Error fetching categories from sheet: {e}")
        return ['Electrical', 'Plumbing', 'Structural', 'HVAC', 'Safety', 'Other']

def get_urgency_levels_from_sheet():
    """Fetch urgency levels from Google Sheet with caching"""
    if is_cache_valid('urgency_levels'):
        return cache['urgency_levels']['data']
    
    try:
        client = get_gsheet_client()
        if not client:
            return ['Low', 'Medium', 'High', 'Critical']
        
        sheet = client.open_by_key(SPREADSHEET_ID)
        
        # Try to get from 'Urgency Levels' worksheet
        try:
            worksheet = sheet.worksheet('Urgency Levels')
            records = worksheet.get_all_records()
            levels = [record.get('Level') or record.get('level') or '' for record in records if record.get('Level') or record.get('level')]
        except:
            # Default urgency levels if worksheet not found
            levels = ['Low', 'Medium', 'High', 'Critical']
        
        # Update cache
        cache['urgency_levels']['data'] = levels
        cache['urgency_levels']['timestamp'] = time.time()
        
        return levels
    except Exception as e:
        print(f"Error fetching urgency levels from sheet: {e}")
        return ['Low', 'Medium', 'High', 'Critical']

def upload_to_google_drive(file, filename, snag_id):
    """Upload file to Google Drive and return shareable link"""
    try:
        service = get_drive_service()
        if not service:
            return None
        
        # Create folder structure: Snags/YYYY-MM/Store_SnagID
        today = datetime.now()
        folder_name = f"Snags/{today.strftime('%Y-%m')}"
        
        # Find or create the folder
        folder_id = get_or_create_drive_folder(service, folder_name)
        
        # Save file temporarily
        temp_path = f"/tmp/{filename}"
        file.save(temp_path)
        
        # Upload to Drive
        file_metadata = {
            'name': f"{snag_id}_{filename}",
            'parents': [folder_id] if folder_id else []
        }
        
        media = MediaFileUpload(temp_path, resumable=True)
        uploaded_file = service.files().create(
            body=file_metadata,
            media_body=media,
            fields='id, webViewLink'
        ).execute()
        
        # Make file shareable
        service.permissions().create(
            fileId=uploaded_file['id'],
            body={'type': 'anyone', 'role': 'reader'}
        ).execute()
        
        # Clean up temp file
        os.remove(temp_path)
        
        return uploaded_file.get('webViewLink')
    except Exception as e:
        print(f"Error uploading to Google Drive: {e}")
        return None

def get_or_create_drive_folder(service, folder_path):
    """Get or create a folder in Google Drive"""
    try:
        # Split path and create nested folders
        parts = folder_path.split('/')
        parent_id = None
        
        for part in parts:
            query = f"name='{part}' and mimeType='application/vnd.google-apps.folder'"
            if parent_id:
                query += f" and '{parent_id}' in parents"
            
            results = service.files().list(q=query, fields='files(id, name)').execute()
            files = results.get('files', [])
            
            if files:
                parent_id = files[0]['id']
            else:
                # Create folder
                folder_metadata = {
                    'name': part,
                    'mimeType': 'application/vnd.google-apps.folder'
                }
                if parent_id:
                    folder_metadata['parents'] = [parent_id]
                
                folder = service.files().create(body=folder_metadata, fields='id').execute()
                parent_id = folder['id']
        
        return parent_id
    except Exception as e:
        print(f"Error creating Drive folder: {e}")
        return None

def sync_snag_to_sheet(snag):
    """Sync a snag to Google Sheets"""
    try:
        client = get_gsheet_client()
        if not client:
            return False
        
        sheet = client.open_by_key(SPREADSHEET_ID)
        
        # Get or create 'Snags' worksheet
        try:
            worksheet = sheet.worksheet('Snags')
        except:
            worksheet = sheet.add_worksheet(title='Snags', rows=1000, cols=20)
            # Add headers
            headers = [
                'Timestamp', 'Snag ID', 'Area Manager', 'Email', 'Store Name/Address',
                'Store Code', 'Date of Report', 'Snag Title', 'Category', 'Description',
                'Urgency Level', 'Score', 'Status', 'Latest Cost', 'Payment Status',
                'Email Sent', 'Media Link', 'Notes', 'Resolved Date', 'Resolved By'
            ]
            worksheet.append_row(headers)
        
        # Prepare row data
        row = [
            snag.timestamp.strftime('%Y-%m-%d %H:%M:%S'),
            snag.snag_id,
            snag.name_of_area_manager,
            snag.email_address,
            snag.store_name_address,
            snag.store_number_code or '',
            snag.date_of_report.strftime('%Y-%m-%d'),
            snag.snag_title,
            snag.snag_category,
            snag.describe_issue,
            snag.urgency_level,
            snag.score,
            snag.current_status,
            snag.latest_cost,
            snag.latest_payment_status,
            'Yes' if snag.email_sent else 'No',
            snag.google_drive_media_link or '',
            snag.notes or '',
            snag.resolved_date.strftime('%Y-%m-%d %H:%M:%S') if snag.resolved_date else '',
            snag.resolved_by or ''
        ]
        
        worksheet.append_row(row)
        return True
    except Exception as e:
        print(f"Error syncing snag to sheet: {e}")
        return False

def send_snag_notification(snag, app):
    """Send email notification for new snag"""
    try:
        from flask_mail import Mail, Message
        
        mail = Mail(app)
        
        subject = f"New Snag Reported: {snag.snag_title} [{snag.snag_id}]"
        
        body = f"""
        Dear {snag.name_of_area_manager},
        
        A new maintenance snag has been reported:
        
        Snag ID: {snag.snag_id}
        Store: {snag.store_name_address}
        Category: {snag.snag_category}
        Urgency: {snag.urgency_level}
        
        Title: {snag.snag_title}
        
        Description:
        {snag.describe_issue}
        
        Date of Report: {snag.date_of_report.strftime('%d %B %Y')}
        
        {'Media Link: ' + snag.google_drive_media_link if snag.google_drive_media_link else ''}
        
        Please review and take appropriate action.
        
        Best regards,
        LogisticsPro Maintenance System
        """
        
        msg = Message(
            subject=subject,
            sender=app.config.get('MAIL_DEFAULT_SENDER', 'noreply@logisticspro.com'),
            recipients=[snag.email_address],
            body=body
        )
        
        mail.send(msg)
        return True
    except Exception as e:
        print(f"Error sending email notification: {e}")
        return False

@snag_bp.route('/submit', methods=['GET', 'POST'])
@login_required
def submit_snag():
    """Snag submission form"""
    from app import db, Snag, app as flask_app
    
    if request.method == 'POST':
        try:
            # Generate unique snag ID
            snag_id = f"SNag-{datetime.now().strftime('%Y%m%d')}-{str(Snag.query.count() + 1).zfill(4)}"
            
            # Handle file upload
            media_link = None
            if 'media_file' in request.files:
                file = request.files['media_file']
                if file and file.filename:
                    media_link = upload_to_google_drive(file, file.filename, snag_id)
            
            # Calculate score based on urgency
            urgency_scores = {'Low': 1, 'Medium': 2, 'High': 3, 'Critical': 4}
            score = urgency_scores.get(request.form.get('urgency_level'), 0)
            
            # Create snag record
            snag = Snag(
                snag_id=snag_id,
                name_of_area_manager=request.form.get('name_of_area_manager'),
                email_address=request.form.get('email_address'),
                store_name_address=request.form.get('store_name_address'),
                store_number_code=request.form.get('store_number_code'),
                date_of_report=datetime.strptime(request.form.get('date_of_report'), '%Y-%m-%d').date(),
                snag_title=request.form.get('snag_title'),
                snag_category=request.form.get('snag_category'),
                describe_issue=request.form.get('describe_issue'),
                urgency_level=request.form.get('urgency_level'),
                score=score,
                google_drive_media_link=media_link,
                user_id=current_user.id
            )
            
            db.session.add(snag)
            db.session.commit()
            
            # Sync to Google Sheets
            sync_success = sync_snag_to_sheet(snag)
            
            # Send email notification
            email_sent = send_snag_notification(snag, flask_app)
            if email_sent:
                snag.email_sent = True
                db.session.commit()
            
            flash(f'✅ Snag submitted successfully! ID: {snag_id}' + (' (Synced to Google Sheets)' if sync_success else ''))
            return redirect(url_for('snag.dashboard'))
        except Exception as e:
            db.session.rollback()
            flash(f'❌ Error submitting snag: {str(e)}')
    
    # Get dropdown data from Google Sheets
    stores = get_stores_from_sheet()
    categories = get_categories_from_sheet()
    urgency_levels = get_urgency_levels_from_sheet()
    
    return render_template('snag_form.html', 
                         stores=stores, 
                         categories=categories, 
                         urgency_levels=urgency_levels)

@snag_bp.route('/dashboard')
@login_required
def dashboard():
    """Snag management dashboard with filtering"""
    from app import Snag
    
    # Build query based on user role
    query = Snag.query
    if current_user.role != 'Admin':
        query = query.filter_by(user_id=current_user.id)
    
    # Apply filters
    store_filter = request.args.get('store')
    category_filter = request.args.get('category')
    urgency_filter = request.args.get('urgency')
    status_filter = request.args.get('status')
    date_from = request.args.get('date_from')
    date_to = request.args.get('date_to')
    
    if store_filter:
        query = query.filter(Snag.store_name_address.contains(store_filter))
    if category_filter:
        query = query.filter_by(snag_category=category_filter)
    if urgency_filter:
        query = query.filter_by(urgency_level=urgency_filter)
    if status_filter:
        query = query.filter_by(current_status=status_filter)
    if date_from:
        query = query.filter(Snag.date_of_report >= datetime.strptime(date_from, '%Y-%m-%d').date())
    if date_to:
        query = query.filter(Snag.date_of_report <= datetime.strptime(date_to, '%Y-%m-%d').date())
    
    # Sort by timestamp descending
    snags = query.order_by(Snag.timestamp.desc()).all()
    
    # Get unique values for filter dropdowns
    all_snags = Snag.query.all() if current_user.role == 'Admin' else Snag.query.filter_by(user_id=current_user.id).all()
    stores = list(set([s.store_name_address for s in all_snags]))
    categories = list(set([s.snag_category for s in all_snags]))
    urgency_levels = ['Low', 'Medium', 'High', 'Critical']
    statuses = ['Pending', 'In Progress', 'Resolved', 'Closed']
    
    # Calculate statistics
    stats = {
        'total': len(all_snags),
        'pending': len([s for s in all_snags if s.current_status == 'Pending']),
        'in_progress': len([s for s in all_snags if s.current_status == 'In Progress']),
        'resolved': len([s for s in all_snags if s.current_status == 'Resolved']),
        'critical': len([s for s in all_snags if s.urgency_level == 'Critical']),
        'total_cost': sum([s.latest_cost for s in all_snags])
    }
    
    return render_template('snag_dashboard.html', 
                         snags=snags,
                         stores=stores,
                         categories=categories,
                         urgency_levels=urgency_levels,
                         statuses=statuses,
                         stats=stats)

@snag_bp.route('/detail/<int:id>')
@login_required
def detail(id):
    """View snag details"""
    from app import Snag
    
    snag = Snag.query.get_or_404(id)
    
    # Check access permission
    if current_user.role != 'Admin' and snag.user_id != current_user.id:
        flash('Access denied.')
        return redirect(url_for('snag.dashboard'))
    
    return render_template('snag_detail.html', snag=snag)

@snag_bp.route('/update_status/<int:id>', methods=['POST'])
@login_required
def update_status(id):
    """Update snag status"""
    from app import db, Snag
    
    snag = Snag.query.get_or_404(id)
    
    # Check access permission
    if current_user.role != 'Admin' and snag.user_id != current_user.id:
        flash('Access denied.')
        return redirect(url_for('snag.dashboard'))
    
    snag.current_status = request.form.get('status')
    
    if snag.current_status == 'Resolved':
        snag.resolved_date = datetime.now()
        snag.resolved_by = current_user.username
    
    db.session.commit()
    
    # Sync to Google Sheets
    sync_snag_to_sheet(snag)
    
    flash('Status updated successfully!')
    return redirect(url_for('snag.detail', id=id))

@snag_bp.route('/update_cost/<int:id>', methods=['POST'])
@login_required
@admin_required
def update_cost(id):
    """Update snag cost and payment status"""
    from app import db, Snag
    
    snag = Snag.query.get_or_404(id)
    
    snag.latest_cost = float(request.form.get('cost', 0))
    snag.latest_payment_status = request.form.get('payment_status', 'Unpaid')
    
    db.session.commit()
    
    # Sync to Google Sheets
    sync_snag_to_sheet(snag)
    
    flash('Cost updated successfully!')
    return redirect(url_for('snag.detail', id=id))

@snag_bp.route('/add_note/<int:id>', methods=['POST'])
@login_required
def add_note(id):
    """Add note to snag"""
    from app import db, Snag
    
    snag = Snag.query.get_or_404(id)
    
    # Check access permission
    if current_user.role != 'Admin' and snag.user_id != current_user.id:
        flash('Access denied.')
        return redirect(url_for('snag.dashboard'))
    
    new_note = request.form.get('note')
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M')
    
    if snag.notes:
        snag.notes += f"\n\n[{timestamp}] {current_user.username}: {new_note}"
    else:
        snag.notes = f"[{timestamp}] {current_user.username}: {new_note}"
    
    db.session.commit()
    
    flash('Note added successfully!')
    return redirect(url_for('snag.detail', id=id))

@snag_bp.route('/delete/<int:id>', methods=['POST'])
@login_required
@admin_required
def delete_snag(id):
    """Delete a snag (admin only)"""
    from app import db, Snag
    
    snag = Snag.query.get_or_404(id)
    db.session.delete(snag)
    db.session.commit()
    
    flash('Snag deleted successfully!')
    return redirect(url_for('snag.dashboard'))

@snag_bp.route('/export')
@login_required
def export_snags():
    """Export snags to Excel"""
    from app import Snag
    
    # Build query based on user role
    query = Snag.query
    if current_user.role != 'Admin':
        query = query.filter_by(user_id=current_user.id)
    
    snags = query.order_by(Snag.timestamp.desc()).all()
    
    data = []
    for s in snags:
        data.append({
            'Snag ID': s.snag_id,
            'Timestamp': s.timestamp.strftime('%Y-%m-%d %H:%M:%S'),
            'Area Manager': s.name_of_area_manager,
            'Email': s.email_address,
            'Store': s.store_name_address,
            'Store Code': s.store_number_code or '',
            'Date of Report': s.date_of_report.strftime('%Y-%m-%d'),
            'Title': s.snag_title,
            'Category': s.snag_category,
            'Description': s.describe_issue,
            'Urgency': s.urgency_level,
            'Score': s.score,
            'Status': s.current_status,
            'Cost': s.latest_cost,
            'Payment Status': s.latest_payment_status,
            'Media Link': s.google_drive_media_link or '',
            'Notes': s.notes or '',
            'Resolved Date': s.resolved_date.strftime('%Y-%m-%d %H:%M:%S') if s.resolved_date else '',
            'Resolved By': s.resolved_by or ''
        })
    
    df = pd.DataFrame(data)
    output = BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        df.to_excel(writer, index=False, sheet_name='Snags')
    output.seek(0)
    
    return send_file(output, download_name=f"snags_export_{datetime.now().strftime('%Y%m%d')}.xlsx", as_attachment=True)

@snag_bp.route('/api/clear_cache', methods=['POST'])
@login_required
@admin_required
def clear_cache():
    """Clear the Google Sheets data cache"""
    global cache
    cache = {
        'stores': {'data': [], 'timestamp': 0},
        'categories': {'data': [], 'timestamp': 0},
        'urgency_levels': {'data': [], 'timestamp': 0}
    }
    return jsonify({'status': 'success', 'message': 'Cache cleared'})
