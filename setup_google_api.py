#!/usr/bin/env python3
"""
Google API Setup Helper Script
This script helps you set up and verify Google Sheets and Drive API integration.
"""

import os
import sys
import json

def main():
    print("=" * 80)
    print("Google API Setup Helper for LogisticsPro Snag Tracking System")
    print("=" * 80)
    print()
    
    # Check if credentials file exists
    creds_file = os.environ.get('GOOGLE_CREDENTIALS_FILE', 'google_credentials.json')
    
    if not os.path.exists(creds_file):
        print(f"❌ Credentials file not found: {creds_file}")
        print()
        print("To set up Google API integration:")
        print()
        print("1. Go to Google Cloud Console:")
        print("   https://console.cloud.google.com/")
        print()
        print("2. Create a new project or select an existing one")
        print()
        print("3. Enable the following APIs:")
        print("   - Google Sheets API")
        print("   - Google Drive API")
        print()
        print("4. Create Service Account credentials:")
        print("   - Go to 'APIs & Services' > 'Credentials'")
        print("   - Click 'Create Credentials' > 'Service Account'")
        print("   - Fill in the details and create")
        print("   - Click on the created service account")
        print("   - Go to 'Keys' tab")
        print("   - Click 'Add Key' > 'Create new key' > 'JSON'")
        print("   - Download the JSON file")
        print()
        print(f"5. Save the downloaded JSON file as: {creds_file}")
        print()
        print("6. Share your Google Sheet and Drive folder with the service account email")
        print("   (You'll find the email in the JSON file)")
        print()
        sys.exit(1)
    
    print(f"✅ Credentials file found: {creds_file}")
    print()
    
    # Load and validate credentials
    try:
        with open(creds_file, 'r') as f:
            creds_data = json.load(f)
        
        print("📋 Service Account Information:")
        print(f"   Email: {creds_data.get('client_email', 'N/A')}")
        print(f"   Project ID: {creds_data.get('project_id', 'N/A')}")
        print()
        
        print("✅ Credentials file is valid JSON")
        print()
        
        # Check required fields
        required_fields = ['type', 'project_id', 'private_key_id', 'private_key', 
                          'client_email', 'client_id', 'auth_uri', 'token_uri']
        missing_fields = [field for field in required_fields if field not in creds_data]
        
        if missing_fields:
            print(f"⚠️  Warning: Missing fields in credentials: {', '.join(missing_fields)}")
            print()
        else:
            print("✅ All required credential fields present")
            print()
        
    except json.JSONDecodeError:
        print("❌ Error: Credentials file is not valid JSON")
        sys.exit(1)
    except Exception as e:
        print(f"❌ Error reading credentials file: {e}")
        sys.exit(1)
    
    # Test Google Sheets API
    print("Testing Google Sheets API connection...")
    try:
        import gspread
        from google.oauth2.service_account import Credentials
        
        scopes = [
            'https://www.googleapis.com/auth/spreadsheets',
            'https://www.googleapis.com/auth/drive.file'
        ]
        
        credentials = Credentials.from_service_account_file(creds_file, scopes=scopes)
        client = gspread.authorize(credentials)
        
        print("✅ Successfully authenticated with Google Sheets API")
        print()
        
        # Test access to the specific spreadsheet
        spreadsheet_id = '16BK0uRc5E1y457vEsqZJt9guPEzlYnSyCMLT6gurw_o'
        print(f"Testing access to spreadsheet: {spreadsheet_id}")
        
        try:
            sheet = client.open_by_key(spreadsheet_id)
            print(f"✅ Successfully accessed spreadsheet: {sheet.title}")
            print()
            
            print("📊 Available worksheets:")
            for worksheet in sheet.worksheets():
                print(f"   - {worksheet.title} ({worksheet.row_count} rows, {worksheet.col_count} cols)")
            print()
            
        except gspread.exceptions.SpreadsheetNotFound:
            print("❌ Spreadsheet not found or service account doesn't have access")
            print()
            print("Please share the Google Sheet with the service account email:")
            print(f"   {creds_data.get('client_email', 'N/A')}")
            print()
            print("Share with 'Editor' permissions")
            print()
        except Exception as e:
            print(f"❌ Error accessing spreadsheet: {e}")
            print()
        
    except ImportError:
        print("❌ Required packages not installed")
        print("   Run: pip install gspread google-auth")
        print()
    except Exception as e:
        print(f"❌ Error testing Google Sheets API: {e}")
        print()
    
    # Test Google Drive API
    print("Testing Google Drive API connection...")
    try:
        from googleapiclient.discovery import build
        from google.oauth2.service_account import Credentials
        
        scopes = [
            'https://www.googleapis.com/auth/spreadsheets',
            'https://www.googleapis.com/auth/drive.file'
        ]
        
        credentials = Credentials.from_service_account_file(creds_file, scopes=scopes)
        service = build('drive', 'v3', credentials=credentials)
        
        # Test by listing files (limited to 5)
        results = service.files().list(pageSize=5, fields="files(id, name)").execute()
        files = results.get('files', [])
        
        print("✅ Successfully authenticated with Google Drive API")
        print()
        
        if files:
            print("📁 Sample files accessible:")
            for file in files[:5]:
                print(f"   - {file['name']} (ID: {file['id']})")
            print()
        else:
            print("ℹ️  No files found (this is normal for new service accounts)")
            print()
        
    except ImportError:
        print("❌ Required packages not installed")
        print("   Run: pip install google-api-python-client google-auth")
        print()
    except Exception as e:
        print(f"❌ Error testing Google Drive API: {e}")
        print()
    
    print("=" * 80)
    print("Setup verification complete!")
    print()
    print("Next steps:")
    print("1. Ensure the Google Sheet is shared with the service account")
    print("2. Set up environment variables in .env file")
    print("3. Configure Flask-Mail settings for email notifications")
    print("4. Run the Flask app and test snag submission")
    print()
    print("=" * 80)

if __name__ == '__main__':
    main()
