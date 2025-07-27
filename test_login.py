#!/usr/bin/env python3
"""
Simple test script to verify login functionality
"""
import requests


def test_login():
    """Test login functionality for all user types."""
    url = "http://127.0.0.1:5000/api/v1/auth/login"

    # Test data
    test_users = [
        {"username": "manager", "password": "password123"},
        {"username": "cashier", "password": "password123"},
        {"username": "barista", "password": "password123"},
        {"username": "courier", "password": "password123"}
    ]

    print("Testing login functionality...")
    print("=" * 50)

    for user_data in test_users:
        try:
            response: requests.Response = requests.post(url, json=user_data, timeout=5)
            print(f"Testing {user_data['username']}:")
            print(f"  Status Code: {response.status_code}")
            print(f"  Response: {response.text}")
            print("-" * 30)
        except Exception as e:
            print(f"Error testing {user_data['username']}: {e}")
            print("-" * 30)

    print("\nLogin testing completed!")


if __name__ == "__main__":
    test_login() 