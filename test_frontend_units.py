#!/usr/bin/env python3
"""
Test script for frontend units integration
"""
import requests
from typing import Dict, Any, Optional

def test_frontend_units():
    base_url = "http://127.0.0.1:5000/api/v1"
    
    print("🔧 Testing Frontend Units Integration...")
    print("=" * 50)
    
    # Login as manager
    login_data = {"username": "manager", "password": "password123"}
    
    try:
        login_response: requests.Response = requests.post(f"{base_url}/auth/login", json=login_data)
        if login_response.status_code != 200:
            print("❌ Login failed")
            return
        
        token = login_response.json()['access_token']
        headers = {'Authorization': f'Bearer {token}'}
        print("✅ Login successful!")
        
    except Exception as e:
        print(f"❌ Login error: {e}")
        return
    
    # Test 1: Get units (for dropdown)
    print("\n📋 Test 1: Get units for dropdown")
    response: requests.Response = requests.get(f"{base_url}/units/", headers=headers)
    if response.status_code == 200:
        units = response.json()['data']
        print(f"✅ Found {len(units)} units for dropdown:")
        for unit in units[:5]:  # Show first 5
            print(f"   - {unit['name']} ({unit['abbreviation']}) - ID: {unit['id']}")
    else:
        print(f"❌ Failed to get units: {response.status_code}")
        units = []  # Initialize empty list if failed
    
    # Test 2: Get ingredients with units
    print("\n🥘 Test 2: Get ingredients with units")
    response: requests.Response = requests.get(f"{base_url}/ingredients", headers=headers)
    if response.status_code == 200:
        ingredients = response.json()
        print(f"✅ Found {len(ingredients)} ingredients:")
        for ingredient in ingredients:
            print(f"   - {ingredient['name']}: {ingredient['current_stock']} {ingredient['unit']}")
    else:
        print(f"❌ Failed to get ingredients: {response.status_code}")
    
    # Test 3: Create ingredient with unit_id
    print("\n➕ Test 3: Create ingredient with unit_id")
    kg_unit = next((u for u in units if u['abbreviation'] == 'kg'), None)
    if kg_unit:
        new_ingredient = {
            "name": "Test Sugar",
            "unit_id": kg_unit['id'],
            "current_stock": 5.0,
            "cost_per_unit_usd": 2.50,
            "reorder_level": 1.0
        }
        
        response: requests.Response = requests.post(f"{base_url}/ingredients", json=new_ingredient, headers=headers)
        if response.status_code == 201:
            print("✅ Successfully created ingredient with unit_id")
        else:
            print(f"❌ Failed to create ingredient: {response.status_code}")
            print(response.text)
    else:
        print("❌ Could not find kg unit for test")
    
    print("\n🎉 Frontend units integration test completed!")

if __name__ == "__main__":
    test_frontend_units() 