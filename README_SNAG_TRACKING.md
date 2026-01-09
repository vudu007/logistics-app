# 🔧 Maintenance/Snag Tracking System

A comprehensive maintenance issue management system integrated with Google Sheets and Google Drive, built for the LogisticsPro fleet management application.

## 📋 Overview

The Snag Tracking System enables area managers to report and track maintenance issues (snags) at store locations with seamless integration to Google Sheets for centralized data management and Google Drive for media storage.

## ✨ Key Features

### Core Functionality
- 📝 **Submit Snags**: Report maintenance issues with detailed information
- 📊 **Dashboard**: View and manage all snags with advanced filtering
- 🔍 **Search & Filter**: Filter by store, category, urgency, status, date range
- 📈 **Statistics**: Real-time statistics cards (total, pending, critical, costs)
- 📄 **Detail View**: Complete snag information with status tracking
- 💬 **Notes & Comments**: Add timestamped notes to any snag
- 💰 **Cost Tracking**: Track repair costs and payment status
- 📧 **Email Notifications**: Automatic notifications to area managers

### Google Integration
- 📊 **Google Sheets Sync**: Auto-sync snag data to Google Sheets
- 📂 **Google Drive Upload**: Store photos/videos in Google Drive
- 🔄 **Dynamic Dropdowns**: Store names, categories, urgency levels from Google Sheet
- ⚡ **Smart Caching**: 1-hour cache to minimize API calls
- 🔗 **Shareable Links**: Direct links to media files in Drive

### Access Control
- 👤 **User Role**: Submit and manage own snags
- 👨‍💼 **Admin Role**: View all snags, manage costs, delete snags
- 🔒 **Secure**: Role-based permissions enforced at route level

### Export & Reporting
- 📥 **Excel Export**: Export filtered snags to Excel
- 📊 **Comprehensive Data**: All fields included in exports
- 🎯 **Filtered Exports**: Export based on active filters

## 🏗️ Architecture

### Technology Stack
- **Backend**: Flask (Python)
- **Database**: SQLAlchemy (SQLite/PostgreSQL)
- **Authentication**: Flask-Login
- **Email**: Flask-Mail
- **APIs**: Google Sheets API, Google Drive API
- **Frontend**: Tailwind CSS, Bootstrap, TomSelect
- **Export**: pandas, openpyxl

### File Structure
```
├── app.py                          # Main application with Snag model
├── blueprints/
│   └── snag_tracking.py           # Snag tracking routes and logic
├── templates/
│   ├── base.html                   # Navigation with snag links
│   ├── snag_form.html             # Snag submission form
│   ├── snag_dashboard.html        # Dashboard with filtering
│   └── snag_detail.html           # Snag detail view
├── requirements.txt                # Python dependencies
├── .env.example                    # Environment variables template
├── google_credentials.example.json # Google credentials template
├── setup_google_api.py            # Setup verification script
└── docs/
    ├── SNAG_TRACKING_SETUP.md     # Detailed setup guide
    ├── SNAG_TRACKING_SUMMARY.md   # Implementation summary
    └── QUICK_START_SNAG_TRACKING.md # Quick start guide
```

## 🚀 Quick Start

### 1. Install Dependencies
```bash
pip install -r requirements.txt
```

### 2. Run Application
```bash
python app.py
```

### 3. Access Snag Tracking
- Navigate to `http://localhost:5000`
- Login with your credentials
- Click "Snag Dashboard" or "Report Snag" in sidebar

### 4. (Optional) Enable Google Integration
See [SNAG_TRACKING_SETUP.md](SNAG_TRACKING_SETUP.md) for detailed setup instructions.

## 📊 Database Schema

### Snag Model
```python
class Snag(db.Model):
    id                      # Primary key
    snag_id                 # Unique identifier (SNag-YYYYMMDD-####)
    timestamp               # Creation timestamp
    name_of_area_manager    # Area manager name
    email_address           # Area manager email
    store_name_address      # Store location
    store_number_code       # Store code
    date_of_report          # Report date
    snag_title              # Brief title
    snag_category           # Category (Electrical, Plumbing, etc.)
    describe_issue          # Detailed description
    urgency_level           # Low, Medium, High, Critical
    score                   # Calculated priority score
    current_status          # Pending, In Progress, Resolved, Closed
    latest_cost             # Repair cost
    latest_payment_status   # Unpaid, Partial, Paid
    email_sent              # Email notification status
    google_drive_media_link # Link to uploaded media
    user_id                 # User who submitted (FK)
    notes                   # Timestamped notes
    resolved_date           # Resolution timestamp
    resolved_by             # User who resolved
```

## 🔌 API Endpoints

### Public Routes (Authenticated)
- `GET /snag/submit` - Snag submission form
- `POST /snag/submit` - Process snag submission
- `GET /snag/dashboard` - Dashboard with filtering
- `GET /snag/detail/<id>` - View snag details
- `POST /snag/update_status/<id>` - Update snag status
- `POST /snag/add_note/<id>` - Add note to snag
- `GET /snag/export` - Export to Excel

### Admin Routes
- `POST /snag/update_cost/<id>` - Update cost information
- `POST /snag/delete/<id>` - Delete snag
- `POST /snag/api/clear_cache` - Clear Google Sheets cache

## 🎨 User Interface

### Dashboard
![Dashboard features statistics cards, filtering, and sortable table]
- **Statistics Cards**: Total, Pending, In Progress, Resolved, Critical, Total Cost
- **Filter Bar**: Store, Category, Urgency, Status, Date Range
- **Actions**: View details, View media, Delete (admin)
- **Export**: Download filtered data to Excel

### Snag Form
![Professional form with dynamic dropdowns and file upload]
- **Area Manager Info**: Name and email
- **Store Selection**: Dropdown from Google Sheet
- **Snag Details**: Title, category, urgency, description
- **Media Upload**: Photos/videos with preview
- **Validation**: Client-side validation with helpful messages

### Detail View
![Complete snag information with status tracking and notes]
- **Information Cards**: Basic info, snag details, notes
- **Status Management**: Update status with tracking
- **Cost Management**: Track costs and payments (admin)
- **Notes Section**: Add timestamped comments

## 🔐 Security

### Credentials Management
- Service account credentials in `google_credentials.json`
- Environment variables in `.env`
- Never committed to version control
- `.gitignore` properly configured

### Access Control
- Flask-Login authentication required
- Role-based route protection
- User isolation (see own snags only)
- Admin verification for sensitive operations

### API Security
- Service account with minimal permissions
- Scoped API access
- Rate limiting via caching
- Error handling for API failures

## 📧 Email Notifications

### Configuration
Set in `.env`:
```env
MAIL_SERVER=smtp.gmail.com
MAIL_PORT=587
MAIL_USE_TLS=True
MAIL_USERNAME=your-email@gmail.com
MAIL_PASSWORD=your-app-password
```

### Email Content
- Snag ID and title
- Store location
- Category and urgency
- Description
- Media link (if available)
- Professional template

## 🌐 Google Integration

### Google Sheets
**Spreadsheet ID**: `16BK0uRc5E1y457vEsqZJt9guPEzlYnSyCMLT6gurw_o`

**Expected Worksheets**:
- **Stores**: Store Name, Address, Store Code
- **Categories**: Category
- **Urgency Levels**: Level
- **Snags**: Auto-created, synced data

### Google Drive
**Folder Structure**: `Snags/YYYY-MM/SnagID_filename`
- Organized by year and month
- Automatic folder creation
- Public shareable links
- Editor permissions for service account

## 📈 Workflow

### Snag Lifecycle
```
Submit → Pending → In Progress → Resolved → Closed
              ↓         ↓            ↓
            Notes    Cost Added   Verified
```

### Automatic Actions
1. **On Submit**:
   - Generate unique Snag ID
   - Upload media to Drive (if any)
   - Save to database
   - Sync to Google Sheet
   - Send email notification

2. **On Status Update**:
   - Update database
   - Re-sync to Google Sheet
   - Track resolution date/user

3. **On Export**:
   - Apply active filters
   - Generate Excel with all fields
   - Download to user

## 🛠️ Maintenance

### Regular Tasks
- Monitor Google API quota usage
- Review and archive old snags
- Update categories/urgency levels in Google Sheet
- Check email delivery logs
- Database backups

### Cache Management
- Default: 1-hour cache duration
- Manual clear: Admin can clear cache
- Auto-refresh: After cache expiration
- Per-worksheet: Separate cache for stores, categories, urgency

## 📊 Statistics & Analytics

The dashboard provides real-time statistics:
- **Total Snags**: All snags in system
- **Pending**: Awaiting action
- **In Progress**: Being worked on
- **Resolved**: Fixed but not closed
- **Critical**: High-priority urgent snags
- **Total Cost**: Sum of all snag repair costs

## 🐛 Troubleshooting

### Common Issues

**Google API errors**:
```bash
python setup_google_api.py  # Verify setup
```

**Email not sending**:
- Check SMTP credentials
- Enable app passwords (Gmail)
- Check firewall settings

**Dropdown data not loading**:
- Verify spreadsheet access
- Check worksheet names
- Clear cache: POST `/snag/api/clear_cache`

**Database errors**:
```bash
python -c "from app import app, db; app.app_context().push(); db.create_all()"
```

## 📚 Documentation

- **[SNAG_TRACKING_SETUP.md](SNAG_TRACKING_SETUP.md)** - Complete setup guide with Google Cloud configuration
- **[SNAG_TRACKING_SUMMARY.md](SNAG_TRACKING_SUMMARY.md)** - Implementation details and file structure
- **[QUICK_START_SNAG_TRACKING.md](QUICK_START_SNAG_TRACKING.md)** - Get started in 5 minutes

## 🤝 Support

For issues or questions:
1. Check documentation files
2. Run setup verification: `python setup_google_api.py`
3. Review application logs
4. Check Google Cloud Console for API errors

## 📝 License

Part of LogisticsPro Fleet Management System

## 🎉 Acknowledgments

Built with:
- Flask ecosystem
- Google Cloud APIs
- Tailwind CSS
- TomSelect
- pandas & openpyxl

---

**Version**: 1.0.0  
**Last Updated**: 2024  
**Status**: ✅ Production Ready
