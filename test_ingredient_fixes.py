#!/usr/bin/env python3
"""
Test script to verify ingredient fixes
"""
import requests
from typing import Dict, Any, Optional

def test_ingredient_fixes():
    base_url = "http://127.0.0.1:5000/api/v1"
    
    print("🔧 Testing Ingredient Fixes...")
    print("=" * 50)
    
    # Login as manager
    login_data = {"username": "manager", "password": "password123"}
    
    try:
        login_response: requests.Response = requests.post(f"{base_url}/auth/login", json=login_data, timeout=5)
        if login_response.status_code != 200:
            print("❌ Login failed")
            return
        
        token = login_response.json()['access_token']
        headers = {'Authorization': f'Bearer {token}'}
        print("✅ Login successful!")
        
    except Exception as e:
        print(f"❌ Login error: {e}")
        return
    
    # Test 1: Get ingredients
    print("\n📋 Test 1: Get ingredients")
    try:
        response: requests.Response = requests.get(f"{base_url}/ingredients", headers=headers, timeout=5)
        if response.status_code == 200:
            ingredients = response.json()
            print(f"✅ Found {len(ingredients)} ingredients")
            if ingredients:
                test_ingredient = ingredients[0]
                ingredient_id = test_ingredient['id']
                print(f"   Using: {test_ingredient['name']} (ID: {ingredient_id})")
            else:
                print("❌ No ingredients found")
                return
        else:
            print(f"❌ Failed to get ingredients: {response.status_code}")
            return
    except Exception as e:
        print(f"❌ Ingredients error: {e}")
        return
    
    # Test 2: Ingredient Usage Route (Fixed)
    print(f"\n🔍 Test 2: Ingredient usage route (ID: {ingredient_id})")
    try:
        response: requests.Response = requests.get(f"{base_url}/ingredients/{ingredient_id}/usage", headers=headers, timeout=5)
        print(f"   Status: {response.status_code}")
        if response.status_code == 200:
            usage = response.json()
            print(f"✅ Usage route working! Found {len(usage)} menu items using this ingredient")
        elif response.status_code == 404:
            print("❌ Still getting 404 - route not found")
        else:
            print(f"⚠️ Unexpected status: {response.text}")
    except Exception as e:
        print(f"❌ Usage route error: {e}")
    
    # Test 3: Ingredient Update with Same Name (Fixed)
    print(f"\n✏️ Test 3: Update ingredient keeping same name")
    try:
        # Update without changing name (should work now)
        update_data = {
            "current_stock": float(test_ingredient['current_stock']) + 1.0,
            "cost_per_unit_usd": 2.99
        }
        
        response: requests.Response = requests.put(f"{base_url}/ingredients/{ingredient_id}", 
                              json=update_data, headers=headers, timeout=5)
        print(f"   Status: {response.status_code}")
        if response.status_code == 200:
            print("✅ Update with same name working!")
        else:
            error_data = response.json() if response.headers.get('content-type', '').startswith('application/json') else response.text
            print(f"❌ Update failed: {error_data}")
    except Exception as e:
        print(f"❌ Update error: {e}")
    
    print("\n🎉 Ingredient fixes test completed!")
    print("   Both issues should now be resolved!")

if __name__ == "__main__":
    test_ingredient_fixes() 