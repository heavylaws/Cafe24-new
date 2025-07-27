# app/utils/helpers.py
from decimal import Decimal, ROUND_HALF_UP
from flask import current_app # To access app.config for exchange rate and rounding factor
from datetime import datetime, date
from app.models import Order
from app.models import SystemSettings
import random
import string
import time

def get_system_setting(key, default=None):
    """Get a system setting by key."""
    setting = SystemSettings.query.filter_by(setting_key=key).first()
    return setting.setting_value if setting else default

def get_current_exchange_rate():
    """Get the current USD to LBP exchange rate."""
    rate_str = get_system_setting('USD_TO_LBP_EXCHANGE_RATE', '90000.0')
    return float(rate_str or '90000.0')

def get_lbp_rounding_factor():
    """Get the LBP rounding factor."""
    factor_str = get_system_setting('LBP_ROUNDING_FACTOR', '5000')
    return int(factor_str or '5000')

def calculate_lbp_price(price_usd, exchange_rate=None, rounding_factor=None):
    """Calculate LBP price from USD price."""
    if exchange_rate is None:
        exchange_rate = get_current_exchange_rate()
    if rounding_factor is None:
        rounding_factor = get_lbp_rounding_factor()
    
    lbp_price = float(price_usd) * exchange_rate
    rounded_price = round(lbp_price / rounding_factor) * rounding_factor
    return int(rounded_price)

def generate_order_number():
    """Generate a unique order number."""
    timestamp = str(int(time.time()))[-8:]  # Last 8 digits of timestamp
    random_chars = ''.join(random.choices(string.ascii_uppercase + string.digits, k=4))
    return f"ORD{timestamp}{random_chars}"

def generate_customer_number():
    """Generate a unique customer number."""
    timestamp = str(int(time.time()))[-6:]  # Last 6 digits of timestamp
    random_chars = ''.join(random.choices(string.ascii_uppercase + string.digits, k=3))
    return f"CUST{timestamp}{random_chars}"

# Example usage (primarily for backend logic, not directly in routes for complex objects):
# if __name__ == '__main__':
#     # This part won't run when imported, only if you execute helpers.py directly
#     # and assumes a Flask app context is available if using current_app
#     class MockApp:
#         def __init__(self):
#             self.config = {
#                 'USD_TO_LBP_EXCHANGE_RATE': '90000.0',
#                 'LBP_ROUNDING_FACTOR': '5000'
#             }
#     current_app = MockApp() # Mocking current_app for standalone testing

#     print(f"0.50 USD to LBP: {calculate_lbp_price(0.50)}")      # Expected: 45000
#     print(f"0.66 USD to LBP: {calculate_lbp_price(0.66)}")      # Expected: 60000 (59400 rounds to 60000)
#     print(f"0.75 USD to LBP: {calculate_lbp_price(0.75)}")      # Expected: 70000 (67500 rounds to 70000)
#     print(f"0.72 USD to LBP: {calculate_lbp_price(0.72)}")      # Expected: 65000 (64800 rounds to 65000)
#     print(f"0.01 USD to LBP: {calculate_lbp_price(Decimal('0.01'))}") # Expected: 0 (900 rounds to 0)
#     print(f"0.03 USD to LBP: {calculate_lbp_price(Decimal('0.03'))}") # Expected: 5000 (2700 rounds to 5000)

