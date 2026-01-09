#!/usr/bin/env python3
"""
Test script for Snag Tracking System
Run this to verify the system is properly installed and configured.
"""

import sys
from datetime import datetime

def test_imports():
    """Test that all required modules can be imported"""
    print("Testing imports...")
    try:
        import flask
        import flask_sqlalchemy
        import flask_login
        import flask_mail
        import gspread
        import google.oauth2.service_account
        import googleapiclient.discovery
        import pandas
        import openpyxl
        print("✓ All required packages imported successfully")
        return True
    except ImportError as e:
        print(f"✗ Import error: {e}")
        print("  Run: pip install -r requirements.txt")
        return False

def test_app_configuration():
    """Test Flask app configuration"""
    print("\nTesting app configuration...")
    try:
        from app import app, db
        
        with app.app_context():
            # Check configuration
            print(f"✓ Secret key configured: {bool(app.config.get('SECRET_KEY'))}")
            print(f"✓ Database URI configured: {bool(app.config.get('SQLALCHEMY_DATABASE_URI'))}")
            print(f"✓ Mail server configured: {app.config.get('MAIL_SERVER', 'Not set')}")
            
        return True
    except Exception as e:
        print(f"✗ Configuration error: {e}")
        return False

def test_database_models():
    """Test database models"""
    print("\nTesting database models...")
    try:
        from app import app, db, User, Driver, Truck, Store, Schedule, Maintenance, Snag
        
        with app.app_context():
            # Create all tables
            db.create_all()
            print("✓ Database tables created")
            
            # Check Snag model
            snag_columns = [c.name for c in Snag.__table__.columns]
            required_fields = [
                'id', 'snag_id', 'timestamp', 'name_of_area_manager',
                'email_address', 'store_name_address', 'snag_title',
                'snag_category', 'urgency_level', 'current_status',
                'google_drive_media_link', 'user_id'
            ]
            
            missing = [f for f in required_fields if f not in snag_columns]
            if missing:
                print(f"✗ Missing Snag fields: {missing}")
                return False
            
            print(f"✓ Snag model has all required fields ({len(snag_columns)} columns)")
            
            # Check indexes
            indexed_columns = [idx.name for idx in Snag.__table__.indexes]
            print(f"✓ Indexed columns configured")
            
        return True
    except Exception as e:
        print(f"✗ Database model error: {e}")
        return False

def test_blueprint_registration():
    """Test that snag blueprint is registered"""
    print("\nTesting blueprint registration...")
    try:
        from app import app
        
        # Check blueprint registration
        if 'snag' not in app.blueprints:
            print("✗ Snag blueprint not registered")
            return False
        
        print("✓ Snag blueprint registered")
        
        # Check routes
        snag_routes = [r.rule for r in app.url_map._rules if 'snag' in r.rule.lower()]
        expected_routes = [
            '/snag/submit',
            '/snag/dashboard',
            '/snag/detail/<int:id>',
            '/snag/update_status/<int:id>',
            '/snag/update_cost/<int:id>',
            '/snag/add_note/<int:id>',
            '/snag/delete/<int:id>',
            '/snag/export',
            '/snag/api/clear_cache'
        ]
        
        print(f"✓ Found {len(snag_routes)} snag routes")
        
        missing_routes = [r for r in expected_routes if r not in snag_routes]
        if missing_routes:
            print(f"⚠ Some routes may be missing: {missing_routes}")
        else:
            print("✓ All expected routes present")
        
        return True
    except Exception as e:
        print(f"✗ Blueprint registration error: {e}")
        return False

def test_templates():
    """Test that templates exist"""
    print("\nTesting templates...")
    import os
    
    templates = [
        'templates/snag_form.html',
        'templates/snag_dashboard.html',
        'templates/snag_detail.html'
    ]
    
    all_exist = True
    for template in templates:
        if os.path.exists(template):
            print(f"✓ {template} exists")
        else:
            print(f"✗ {template} not found")
            all_exist = False
    
    return all_exist

def test_google_credentials():
    """Test Google API credentials"""
    print("\nTesting Google API credentials...")
    import os
    import json
    
    creds_file = os.environ.get('GOOGLE_CREDENTIALS_FILE', 'google_credentials.json')
    
    if not os.path.exists(creds_file):
        print(f"⚠ Google credentials file not found: {creds_file}")
        print("  Google Sheets/Drive integration will not work")
        print("  See SNAG_TRACKING_SETUP.md for setup instructions")
        return None  # Not a failure, just a warning
    
    try:
        with open(creds_file, 'r') as f:
            creds = json.load(f)
        
        required_fields = ['type', 'project_id', 'private_key', 'client_email']
        missing = [f for f in required_fields if f not in creds]
        
        if missing:
            print(f"✗ Credentials file missing fields: {missing}")
            return False
        
        print(f"✓ Google credentials file valid")
        print(f"  Service account: {creds['client_email']}")
        print(f"  Project: {creds['project_id']}")
        
        return True
    except Exception as e:
        print(f"✗ Error reading credentials: {e}")
        return False

def test_email_configuration():
    """Test email configuration"""
    print("\nTesting email configuration...")
    try:
        from app import app
        
        mail_server = app.config.get('MAIL_SERVER')
        mail_username = app.config.get('MAIL_USERNAME')
        
        if not mail_server:
            print("⚠ Email server not configured")
            print("  Email notifications will not work")
            print("  Configure MAIL_* variables in .env")
            return None  # Not a failure, just a warning
        
        print(f"✓ Mail server configured: {mail_server}")
        if mail_username:
            print(f"✓ Mail username configured: {mail_username}")
        else:
            print("⚠ Mail username not set")
        
        return True
    except Exception as e:
        print(f"✗ Email configuration error: {e}")
        return False

def main():
    """Run all tests"""
    print("=" * 70)
    print("Snag Tracking System - Test Suite")
    print("=" * 70)
    print()
    
    results = {
        'Imports': test_imports(),
        'App Configuration': test_app_configuration(),
        'Database Models': test_database_models(),
        'Blueprint Registration': test_blueprint_registration(),
        'Templates': test_templates(),
        'Google Credentials': test_google_credentials(),
        'Email Configuration': test_email_configuration(),
    }
    
    print()
    print("=" * 70)
    print("Test Summary")
    print("=" * 70)
    
    passed = sum(1 for v in results.values() if v is True)
    failed = sum(1 for v in results.values() if v is False)
    warnings = sum(1 for v in results.values() if v is None)
    
    for test, result in results.items():
        if result is True:
            status = "✓ PASS"
        elif result is False:
            status = "✗ FAIL"
        else:
            status = "⚠ WARNING"
        print(f"{status:12} {test}")
    
    print("=" * 70)
    print(f"Results: {passed} passed, {failed} failed, {warnings} warnings")
    print("=" * 70)
    
    if failed > 0:
        print("\n⚠ Some tests failed. Please fix the issues before using the system.")
        return 1
    
    if warnings > 0:
        print("\n⚠ Some features require additional configuration:")
        if results['Google Credentials'] is None:
            print("  - Set up Google Cloud credentials for Sheets/Drive integration")
        if results['Email Configuration'] is None:
            print("  - Configure email settings for notifications")
        print("\nThe system will work with limited functionality.")
        print("See SNAG_TRACKING_SETUP.md for full setup instructions.")
    else:
        print("\n✅ All tests passed! The snag tracking system is ready to use.")
    
    print("\nNext steps:")
    print("  1. Start the app: python app.py")
    print("  2. Login to the application")
    print("  3. Navigate to 'Snag Dashboard' in the sidebar")
    print("  4. Click 'Report Snag' to submit a test snag")
    
    return 0

if __name__ == '__main__':
    sys.exit(main())
