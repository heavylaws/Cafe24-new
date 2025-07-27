#!/usr/bin/env python3
"""
Quick test to check Flask backend health
"""
import requests
from typing import Dict, Any, Optional

def quick_health_check():
    print("🔍 Quick Health Check...")
    
    try:
        response: requests.Response = requests.get("http://127.0.0.1:5000/health", timeout=5)
        if response.status_code == 200:
            print("✅ Flask server is healthy!")
        else:
            print(f"⚠️ Flask server responding but status: {response.status_code}")
    except Exception as e:
        print(f"❌ Flask server not responding: {e}")
        return
    
    # Quick login test
    print("\n🔐 Quick Login Test...")
    login_data = {"username": "manager", "password": "password123"}
    
    try:
        response: requests.Response = requests.post("http://127.0.0.1:5000/api/v1/auth/login", json=login_data, timeout=5)
        if response.status_code == 200:
            print("✅ Login working!")
        else:
            print(f"❌ Login failed: {response.status_code}")
    except Exception as e:
        print(f"❌ Login error: {e}")

if __name__ == "__main__":
    quick_health_check() 