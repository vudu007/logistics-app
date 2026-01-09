# Quick Start Guide - Snag Tracking System

## 🚀 Get Started in 5 Minutes

### Prerequisites Check
- [x] Python 3.8+ installed
- [x] All dependencies installed (`pip install -r requirements.txt`)
- [ ] Google Cloud credentials (optional for full functionality)
- [ ] Email SMTP configured (optional for notifications)

### Step 1: Install Dependencies (Already Done ✅)
```bash
pip install -r requirements.txt
```

### Step 2: Run the Application
```bash
python app.py
```

The app will start on `http://localhost:5000`

### Step 3: Login
- Navigate to `http://localhost:5000/login`
- Use your existing credentials or register a new account
- First user automatically becomes Admin

### Step 4: Access Snag Tracking
Look in the sidebar for:
- **Snag Dashboard** - View and manage all snags
- **Report Snag** - Submit a new maintenance issue

## 🎯 Basic Usage (Without Google APIs)

You can use the snag tracking system immediately without Google API setup. It will use default fallback data for dropdowns.

### Submit a Snag:
1. Click "Report Snag" in sidebar
2. Fill in the form:
   - Area Manager Name and Email
   - Store Name (manual entry or select from defaults)
   - Snag details (title, category, urgency, description)
   - Optionally upload a photo/video (will be stored locally)
3. Click "Submit Snag Report"

### View Snags:
1. Click "Snag Dashboard" in sidebar
2. Use filters to search:
   - Filter by store, category, urgency, status
   - Filter by date range
3. Click on any snag to view details
4. Update status, add notes, or manage costs (admin)

### Export Data:
- Click "Export to Excel" button on the dashboard
- Download a complete report of all snags

## 🔧 Optional: Enable Full Google Integration

For full functionality (Google Sheets sync, Drive uploads):

### Quick Setup:
1. **Get Google Credentials**:
   ```bash
   # Follow instructions in SNAG_TRACKING_SETUP.md
   # Place credentials in: google_credentials.json
   ```

2. **Share the Google Sheet**:
   - Open: https://docs.google.com/spreadsheets/d/16BK0uRc5E1y457vEsqZJt9guPEzlYnSyCMLT6gurw_o/
   - Share with your service account email
   - Grant "Editor" access

3. **Verify Setup**:
   ```bash
   python setup_google_api.py
   ```

4. **Configure Email** (in .env):
   ```env
   MAIL_SERVER=smtp.gmail.com
   MAIL_PORT=587
   MAIL_USE_TLS=True
   MAIL_USERNAME=your-email@gmail.com
   MAIL_PASSWORD=your-app-password
   ```

5. **Restart the app**:
   ```bash
   python app.py
   ```

## 📊 Features Overview

### Available Now (No Setup Required):
- ✅ Submit maintenance snags
- ✅ View snag dashboard
- ✅ Filter and search snags
- ✅ Update status
- ✅ Add notes
- ✅ Manage costs (admin)
- ✅ Export to Excel
- ✅ Role-based access control

### With Google Setup:
- ✅ Dynamic dropdowns from Google Sheet
- ✅ Auto-sync to Google Sheet
- ✅ Upload media to Google Drive
- ✅ Email notifications

## 🎨 User Interface

The snag tracking system features:
- **Modern Dashboard**: Statistics cards, filtering, sortable tables
- **Professional Forms**: Validation, file upload, smart dropdowns
- **Detail Views**: Complete snag information, status tracking, notes
- **Responsive Design**: Works on desktop, tablet, and mobile

## 🔐 Access Control

### User Role:
- Submit snags
- View own snags only
- Update status on own snags
- Add notes to own snags

### Admin Role:
- View ALL snags from all users
- Update cost information
- Delete snags
- Access all management features

## 📝 Common Tasks

### Update Snag Status:
1. Open snag detail page
2. Select new status from dropdown
3. Click "Update Status"
4. Status options: Pending → In Progress → Resolved → Closed

### Add Cost Information (Admin):
1. Open snag detail page
2. Scroll to "Cost Information" card
3. Enter cost amount
4. Select payment status
5. Click "Update Cost"

### Filter Snags:
1. On dashboard, use filter form at top
2. Select filters (store, category, urgency, status, dates)
3. Click "Apply Filters"
4. Click "Clear Filters" to reset

### Export Report:
1. Apply desired filters (optional)
2. Click "Export to Excel"
3. Download opens automatically

## 🆘 Troubleshooting

### Problem: Can't see snag routes
**Solution**: Make sure the blueprint is registered in app.py

### Problem: Forms not loading
**Solution**: Check that templates are in the templates/ folder

### Problem: Database errors
**Solution**: Run `python -c "from app import app, db; app.app_context().push(); db.create_all()"`

### Problem: Google API errors
**Solution**: 
1. Check credentials file exists
2. Run `python setup_google_api.py`
3. Verify sheet is shared with service account

## 📚 Documentation

For detailed information, see:
- **SNAG_TRACKING_SETUP.md** - Complete setup guide
- **SNAG_TRACKING_SUMMARY.md** - Implementation details
- **setup_google_api.py** - Setup verification script

## 🎉 You're Ready!

The snag tracking system is now ready to use. Start by submitting a test snag to familiarize yourself with the interface.

**Happy Tracking! 🚀**
