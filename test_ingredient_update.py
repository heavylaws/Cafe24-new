#!/usr/bin/env python3
"""
Test script for ingredient update functionality  
"""
import requests
from typing import Dict, Any, Optional

def test_ingredient_update():
    base_url = "http://127.0.0.1:5000/api/v1"
    
    print("🔧 Testing Ingredient Update and Usage...")
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
    
    # Test 1: Get ingredients
    print("\n📋 Test 1: Get ingredients")
    try:
        response: requests.Response = requests.get(f"{base_url}/ingredients", headers=headers)
        if response.status_code == 200:
            ingredients = response.json()
            print(f"✅ Found {len(ingredients)} ingredients:")
            for ingredient in ingredients:
                print(f"   - {ingredient['name']} (ID: {ingredient['id']}) - {ingredient['current_stock']} {ingredient['unit']}")
            
            if ingredients:
                test_ingredient = ingredients[0]
                test_ingredient_id = test_ingredient['id']
                print(f"\n🎯 Using ingredient '{test_ingredient['name']}' (ID: {test_ingredient_id}) for testing")
            else:
                print("❌ No ingredients found")
                return
        else:
            print(f"❌ Failed to get ingredients: {response.status_code}")
            return
    except Exception as e:
        print(f"❌ Failed to get ingredients: {e}")
        return
    
    # Test 2: Get ingredient usage
    print(f"\n🔍 Test 2: Get ingredient usage for {test_ingredient_id}")
    try:
        response: requests.Response = requests.get(f"{base_url}/ingredients/{test_ingredient_id}/usage", headers=headers)
        print(f"📊 Usage response status: {response.status_code}")
        if response.status_code == 200:
            usage = response.json()
            print(f"✅ Usage data: {usage}")
        else:
            print(f"❌ Failed to get usage: {response.text}")
    except Exception as e:
        print(f"❌ Failed to get usage: {e}")
        return
    
    # Test 3: Update ingredient
    print(f"\n✏️ Test 3: Update ingredient {test_ingredient_id}")
    try:
        update_data = {
            "name": f"{test_ingredient['name']} (Updated)",
            "current_stock": float(test_ingredient['current_stock']) + 5.0,
            "cost_per_unit_usd": 1.50
        }
        
        print(f"📝 Update data: {update_data}")
        
        response: requests.Response = requests.put(f"{base_url}/ingredients/{test_ingredient_id}", 
                                              json=update_data, 
                                              headers=headers)
        
        print(f"📊 Response status: {response.status_code}")
        print(f"📄 Response body: {response.text}")
        
        if response.status_code == 200:
            print("✅ Ingredient updated successfully!")
        else:
            print("❌ Ingredient update failed!")
    except Exception as e:
        print(f"❌ Failed to update ingredient: {e}")
        return
    
    print("\n🎉 Ingredient update test completed!")

if __name__ == "__main__":
    test_ingredient_update() 