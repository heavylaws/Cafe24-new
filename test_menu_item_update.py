#!/usr/bin/env python3
"""
Test script for menu item update functionality
"""
import requests
from typing import Dict, Any, Optional

def test_menu_item_update():
    base_url = "http://127.0.0.1:5000/api/v1"
    
    print("🔧 Testing Menu Item Update...")
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
    
    # Test 1: Get menu items
    print("\n📋 Test 1: Get menu items")
    response: requests.Response = requests.get(f"{base_url}/menu/items", headers=headers)
    if response.status_code == 200:
        menu_items = response.json()
        print(f"✅ Found {len(menu_items)} menu items:")
        for item in menu_items[:3]:  # Show first 3
            print(f"   - {item['name']} (ID: {item['id']}) - ${item['base_price_usd']}")
        
        if menu_items:
            test_item = menu_items[0]
            test_item_id = test_item['id']
            print(f"\n🎯 Using item '{test_item['name']}' (ID: {test_item_id}) for testing")
        else:
            print("❌ No menu items found")
            return
    else:
        print(f"❌ Failed to get menu items: {response.status_code}")
        return
    
    # Test 2: Update menu item
    print(f"\n✏️ Test 2: Update menu item {test_item_id}")
    update_data = {
        "name": f"{test_item['name']} (Updated)",
        "description": "This item was updated for testing",
        "base_price_usd": float(test_item['base_price_usd']) + 1.00,
        "category_id": test_item['category_id']  # Keep the same category
    }
    
    print(f"📝 Update data: {update_data}")
    
    response: requests.Response = requests.put(f"{base_url}/menu/items/{test_item_id}", 
                          json=update_data, 
                          headers=headers)
    
    print(f"📊 Response status: {response.status_code}")
    print(f"📄 Response body: {response.text}")
    
    if response.status_code == 200:
        print("✅ Menu item updated successfully!")
        
        # Test 3: Verify the update
        print(f"\n🔍 Test 3: Verify the update")
        response: requests.Response = requests.get(f"{base_url}/menu/items/{test_item_id}", headers=headers)
        if response.status_code == 200:
            updated_item = response.json()
            print(f"✅ Updated item: {updated_item['name']} - ${updated_item['base_price_usd']}")
            print(f"   Description: {updated_item['description']}")
        else:
            print(f"❌ Failed to verify update: {response.status_code}")
    else:
        print("❌ Menu item update failed!")
        try:
            error_data = response.json()
            print(f"   Error details: {error_data}")
        except:
            print(f"   Raw error: {response.text}")
    
    print("\n🎉 Menu item update test completed!")

if __name__ == "__main__":
    test_menu_item_update() 