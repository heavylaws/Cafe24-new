#!/usr/bin/env python3
"""
Direct test script to verify login functionality using Flask app context
"""
from app import create_app, db
from app.models import User
from werkzeug.security import check_password_hash

def test_login_direct():
    app = create_app()
    
    with app.app_context():
        print("Testing login functionality directly...")
        print("=" * 50)
        
        # Test users
        test_users = [
            {"username": "manager", "password": "password123"},
            {"username": "cashier", "password": "password123"},
            {"username": "barista", "password": "password123"},
            {"username": "courier", "password": "password123"}
        ]
        
        for user_data in test_users:
            username = user_data['username']
            password = user_data['password']
            
            print(f"Testing {username}:")
            
            # Find user in database
            user = User.query.filter_by(username=username).first()
            
            if user:
                print(f"  User found: {user.username} ({user.role.value})")
                print(f"  Is active: {user.is_active}")
                print(f"  Password check: {user.check_password(password)}")
                
                if user.check_password(password):
                    print(f"  ✅ Login successful for {username}")
                else:
                    print(f"  ❌ Password incorrect for {username}")
            else:
                print(f"  ❌ User {username} not found in database")
            
            print("-" * 30)

if __name__ == "__main__":
    test_login_direct() 