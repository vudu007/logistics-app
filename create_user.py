from app import app, db, User
from werkzeug.security import generate_password_hash

# This allows us to access the database configured in app.py
with app.app_context():
    # Check if the 'admin' user already exists
    existing_user = User.query.filter_by(username='admin').first()
    
    if existing_user:
        print("User 'admin' already exists!")
    else:
        # Create the user
        hashed_pw = generate_password_hash('123') # The password will be '123'
        new_user = User(username='admin', password=hashed_pw)
        
        db.session.add(new_user)
        db.session.commit()
        print("Success! User 'admin' created with password '123'")