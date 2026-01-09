# Snag Tracking System Setup Guide

## Overview

The Snag Tracking System is a comprehensive maintenance issue management system integrated into the LogisticsPro app. It features:

- ✅ Google Sheets integration for data synchronization
- ✅ Google Drive integration for media storage
- ✅ Email notifications to area managers
- ✅ Role-based access control
- ✅ Advanced filtering and search
- ✅ Excel export functionality
- ✅ Real-time status tracking

## Prerequisites

1. Python 3.8+ installed
2. PostgreSQL database (for production) or SQLite (for local development)
3. Google Cloud Platform account
4. Gmail account (or other SMTP email service)

## Installation

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Set Up Google Cloud APIs

#### Step 1: Create a Google Cloud Project

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create a new project or select an existing one
3. Note your Project ID

#### Step 2: Enable Required APIs

Enable the following APIs for your project:
- Google Sheets API
- Google Drive API

1. In Cloud Console, go to "APIs & Services" > "Library"
2. Search for "Google Sheets API" and click "Enable"
3. Search for "Google Drive API" and click "Enable"

#### Step 3: Create Service Account Credentials

1. Go to "APIs & Services" > "Credentials"
2. Click "Create Credentials" > "Service Account"
3. Fill in the service account details:
   - Name: `logisticspro-snag-tracker`
   - Description: `Service account for snag tracking system`
4. Click "Create and Continue"
5. Grant the service account these roles:
   - Editor (or custom role with appropriate permissions)
6. Click "Done"
7. Click on the newly created service account
8. Go to the "Keys" tab
9. Click "Add Key" > "Create new key"
10. Select "JSON" format
11. Click "Create" - this will download a JSON file

#### Step 4: Save Credentials

1. Rename the downloaded JSON file to `google_credentials.json`
2. Place it in the root directory of your project
3. **IMPORTANT**: Never commit this file to version control!

### 3. Configure Google Sheet

#### Step 1: Share the Spreadsheet

1. Open the Google Sheet: [https://docs.google.com/spreadsheets/d/16BK0uRc5E1y457vEsqZJt9guPEzlYnSyCMLT6gurw_o/](https://docs.google.com/spreadsheets/d/16BK0uRc5E1y457vEsqZJt9guPEzlYnSyCMLT6gurw_o/)
2. Click "Share" button
3. Add the service account email (found in `google_credentials.json` as `client_email`)
4. Grant "Editor" permissions
5. Uncheck "Notify people"
6. Click "Share"

#### Step 2: Sheet Structure

The Google Sheet should have the following worksheets:

**Stores Worksheet:**
| Store Name | Address | Store Code |
|------------|---------|------------|
| Store 1    | Address 1 | S001     |

**Categories Worksheet:**
| Category |
|----------|
| Electrical |
| Plumbing |
| Structural |

**Urgency Levels Worksheet:**
| Level |
|-------|
| Low |
| Medium |
| High |
| Critical |

**Snags Worksheet** (auto-created by the system):
This worksheet will be automatically created when the first snag is submitted.

### 4. Configure Email Settings

#### For Gmail:

1. Enable 2-Factor Authentication on your Gmail account
2. Generate an App Password:
   - Go to Google Account settings
   - Security > 2-Step Verification > App passwords
   - Generate a new app password for "Mail"
   - Copy the 16-character password

3. Update `.env` file with your email settings

### 5. Environment Configuration

Create a `.env` file in the project root:

```bash
cp .env.example .env
```

Edit `.env` and fill in your configuration:

```env
# Flask Configuration
SECRET_KEY=your-super-secret-key-change-this

# Database (use PostgreSQL for production)
DATABASE_URL=postgresql://user:password@localhost/dbname

# Email Configuration
MAIL_SERVER=smtp.gmail.com
MAIL_PORT=587
MAIL_USE_TLS=True
MAIL_USERNAME=your-email@gmail.com
MAIL_PASSWORD=your-16-char-app-password
MAIL_DEFAULT_SENDER=noreply@logisticspro.com

# Google API Configuration
GOOGLE_CREDENTIALS_FILE=google_credentials.json
```

### 6. Verify Setup

Run the setup verification script:

```bash
python setup_google_api.py
```

This script will:
- ✅ Check if credentials file exists
- ✅ Validate JSON structure
- ✅ Test Google Sheets API connection
- ✅ Test Google Drive API connection
- ✅ Verify access to the specified spreadsheet

### 7. Initialize Database

Run database migrations:

```bash
python setup_db.py
```

Or if using Flask-Migrate:

```bash
flask db upgrade
```

## Usage

### Starting the Application

```bash
python app.py
```

Or for production:

```bash
gunicorn app:app
```

### Accessing the Snag Tracking System

1. Log in to the application
2. Navigate to "Snag Dashboard" in the sidebar
3. Click "Report Snag" to submit a new maintenance issue

### Submitting a Snag

1. Fill in area manager information
2. Select store from dropdown (populated from Google Sheet)
3. Enter snag details:
   - Date of report
   - Title
   - Category (from Google Sheet)
   - Urgency level (from Google Sheet)
   - Description
4. Upload photos/videos (optional)
5. Submit

The system will:
- ✅ Create a unique Snag ID
- ✅ Store in local database
- ✅ Upload media to Google Drive
- ✅ Sync to Google Sheet
- ✅ Send email notification to area manager

### Managing Snags

**Dashboard Features:**
- View all snags with statistics
- Filter by store, category, urgency, status, date range
- Sort and search
- Export to Excel
- View individual snag details

**Snag Detail Page:**
- View full snag information
- Update status (Pending → In Progress → Resolved → Closed)
- Add notes and comments
- Update cost and payment status (Admin only)
- View media attachments

### Role-Based Access

**Users:**
- Submit new snags
- View their own snags
- Update status on their snags
- Add notes to their snags

**Admins:**
- View all snags from all users
- Update cost and payment information
- Delete snags
- Access all management features

## API Endpoints

### Snag Routes

- `GET /snag/submit` - Display snag submission form
- `POST /snag/submit` - Submit new snag
- `GET /snag/dashboard` - View snag dashboard
- `GET /snag/detail/<id>` - View snag details
- `POST /snag/update_status/<id>` - Update snag status
- `POST /snag/update_cost/<id>` - Update cost (Admin only)
- `POST /snag/add_note/<id>` - Add note to snag
- `POST /snag/delete/<id>` - Delete snag (Admin only)
- `GET /snag/export` - Export snags to Excel
- `POST /snag/api/clear_cache` - Clear Google Sheets cache (Admin only)

## Data Flow

### New Snag Submission

```
User submits form
    ↓
Media uploaded to Google Drive (if any)
    ↓
Snag saved to local database
    ↓
Synced to Google Sheet
    ↓
Email notification sent
    ↓
User redirected to dashboard
```

### Google Sheets Sync

- Data is cached for 1 hour to minimize API calls
- Cache is automatically refreshed after expiration
- Admins can manually clear cache if needed
- Each new snag is immediately synced to the sheet

## Troubleshooting

### Issue: "Spreadsheet not found"

**Solution:**
- Verify the spreadsheet ID in `blueprints/snag_tracking.py`
- Ensure the service account email has access to the sheet
- Check that the sheet is not deleted

### Issue: "Permission denied" when uploading to Drive

**Solution:**
- Verify Google Drive API is enabled
- Check service account permissions
- Ensure credentials file is valid

### Issue: Email not sending

**Solution:**
- Verify MAIL_USERNAME and MAIL_PASSWORD in .env
- Check if 2FA is enabled and app password is generated
- Test SMTP settings with a simple test script
- Check firewall/network settings

### Issue: Dropdown data not loading

**Solution:**
- Run `python setup_google_api.py` to verify connection
- Check worksheet names in the spreadsheet
- Clear cache: POST to `/snag/api/clear_cache`
- Verify column names match expected format

### Issue: Import errors

**Solution:**
```bash
pip install --upgrade -r requirements.txt
```

## Security Considerations

1. **Never commit credentials**:
   - Add `google_credentials.json` to `.gitignore`
   - Add `.env` to `.gitignore`

2. **Use environment variables**:
   - Store all secrets in `.env` file
   - Use different credentials for dev/staging/production

3. **Service account permissions**:
   - Grant minimum required permissions
   - Use separate service accounts for different environments

4. **Database security**:
   - Use strong passwords
   - Enable SSL for database connections in production
   - Regular backups

## Maintenance

### Regular Tasks

1. **Monitor Google API quotas**:
   - Check usage in Google Cloud Console
   - Adjust caching if hitting limits

2. **Database backups**:
   - Regular automated backups
   - Test restore procedures

3. **Update dependencies**:
   ```bash
   pip install --upgrade -r requirements.txt
   ```

4. **Clear old snags** (optional):
   - Archive or delete resolved snags older than X months
   - Export to Excel before deletion

## Support

For issues or questions:
1. Check this documentation
2. Run the setup verification script
3. Check application logs
4. Review Google Cloud Console for API errors

## Additional Resources

- [Google Sheets API Documentation](https://developers.google.com/sheets/api)
- [Google Drive API Documentation](https://developers.google.com/drive/api)
- [Flask-Mail Documentation](https://pythonhosted.org/Flask-Mail/)
- [gspread Documentation](https://docs.gspread.org/)
