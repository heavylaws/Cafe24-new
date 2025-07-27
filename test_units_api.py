#!/usr/bin/env python3
"""
Test script for unit management API endpoints
"""
import requests


def test_units_api():
    """Test all unit management API endpoints."""
    base_url = "http://127.0.0.1:5000/api/v1"
    
    print("🔧 Testing Units API...")
    print("=" * 50)
    
    # Login as manager first
    login_data = {"username": "manager", "password": "password123"}
    login_response: requests.Response = requests.post(f"{base_url}/auth/login", json=login_data)
    
    if login_response.status_code != 200:
        print("❌ Login failed")
        print(f"Response: {login_response.text}")
        return
    
    token = login_response.json()['access_token']
    headers = {'Authorization': f'Bearer {token}'}
    print("✅ Login successful!")
    
    # Test 1: Get all units
    print("\n📋 Test 1: Get all units")
    response: requests.Response = requests.get(f"{base_url}/units/", headers=headers)
    print(f"Status: {response.status_code}")
    if response.status_code == 200:
        units = response.json()
        print(f"Found {len(units)} units")
        for unit in units:
            print(f"  - {unit['name']} ({unit['abbreviation']})")
    else:
        print(f"Error: {response.text}")
    
    # Test 2: Get specific unit
    print("\n🔍 Test 2: Get specific unit (ID: 1)")
    response: requests.Response = requests.get(f"{base_url}/units/1", headers=headers)
    print(f"Status: {response.status_code}")
    if response.status_code == 200:
        unit = response.json()
        print(f"Unit: {unit['name']} ({unit['abbreviation']})")
    else:
        print(f"Error: {response.text}")
    
    # Test 3: Create new unit
    print("\n➕ Test 3: Create new unit")
    new_unit = {
        "name": "Tablespoons",
        "abbreviation": "tbsp",
        "description": "Tablespoon measurement for cooking"
    }
    response: requests.Response = requests.post(f"{base_url}/units/", json=new_unit, headers=headers)
    print(f"Status: {response.status_code}")
    if response.status_code == 201:
        created_unit = response.json()
        new_unit_id = created_unit['id']
        print(f"✅ Created unit: {created_unit['name']} (ID: {new_unit_id})")
    else:
        print(f"❌ Error: {response.text}")
        return
    
    # Test 4: Update unit
    print(f"\n✏️  Test 4: Update unit (ID: {new_unit_id})")
    update_data = {
        "description": "Updated tablespoon measurement for precise cooking"
    }
    response: requests.Response = requests.put(f"{base_url}/units/{new_unit_id}", json=update_data, headers=headers)
    print(f"Status: {response.status_code}")
    if response.status_code == 200:
        updated_unit = response.json()
        print(f"✅ Updated unit description: {updated_unit['description']}")
    else:
        print(f"❌ Error: {response.text}")
    
    # Test 5: Try to create duplicate unit (should fail)
    print("\n🚫 Test 5: Try to create duplicate unit")
    duplicate_unit = {
        "name": "Tablespoons",  # Same name as above
        "abbreviation": "tbs"   # Different abbreviation
    }
    response: requests.Response = requests.post(f"{base_url}/units/", json=duplicate_unit, headers=headers)
    print(f"Status: {response.status_code}")
    if response.status_code == 400:
        print("✅ Correctly rejected duplicate unit name")
    else:
        print(f"❌ Expected 400, got {response.status_code}: {response.text}")
    
    # Test 6: Test unauthorized access (cashier trying to manage units)
    print("\n🔒 Test 6: Test unauthorized access")
    cashier_login = {"username": "cashier", "password": "password123"}
    cashier_login_response = requests.post(f"{base_url}/auth/login", json=cashier_login)
    
    if cashier_login_response.status_code == 200:
        cashier_token = cashier_login_response.json()['access_token']
        cashier_headers = {'Authorization': f'Bearer {cashier_token}'}
        
        # Cashier should be able to GET units (read-only)
        response: requests.Response = requests.get(f"{base_url}/units/", headers=cashier_headers)
        print(f"Cashier GET units status: {response.status_code} (should be 200)")
        
        # But not CREATE units
        response: requests.Response = requests.post(f"{base_url}/units/", json=new_unit, headers=cashier_headers)
        print(f"Cashier POST units status: {response.status_code} (should be 403)")
    
    print("\n🎉 Units API testing completed!")


if __name__ == "__main__":
    test_units_api() 