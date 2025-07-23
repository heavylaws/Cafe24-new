# app/utils/helpers.py
from decimal import Decimal, ROUND_HALF_UP
from flask import current_app # To access app.config for exchange rate and rounding factor
from datetime import datetime, date
from app.models import Order

def get_system_setting(key, default=None):
    """
    Helper function to get a system setting from the database.
    For v0.1, we might hardcode or get from config, but this is for future use.
    """
    from app.models import SystemSettings # Local import to avoid circular dependency
    setting = SystemSettings.query.filter_by(setting_key=key).first()
    return setting.setting_value if setting else default

def get_current_exchange_rate():
    """
    Retrieves the current USD to LBP exchange rate.
    First tries to get from database, falls back to config.
    """
    try:
        # Try to get from database first
        rate_setting = get_system_setting('usd_to_lbp_exchange_rate')
        if rate_setting:
            return Decimal(rate_setting)
    except Exception:
        pass
    
    # Fall back to config
    return Decimal(current_app.config.get('USD_TO_LBP_EXCHANGE_RATE', '90000.0'))

def get_lbp_rounding_factor():
    """
    Retrieves the LBP rounding factor (e.g., 5000).
    """
    return int(current_app.config.get('LBP_ROUNDING_FACTOR', '5000'))

def calculate_lbp_price(price_usd, exchange_rate=None, rounding_factor=None):
    """
    Converts a USD price to LBP and rounds it according to the system's rounding factor.
    """
    if price_usd is None:
        return None

    if exchange_rate is None:
        exchange_rate = get_current_exchange_rate()

    if rounding_factor is None:
        rounding_factor = get_lbp_rounding_factor()

    price_usd_decimal = Decimal(str(price_usd)) # Ensure it's a Decimal
    lbp_unrounded = price_usd_decimal * exchange_rate

    # Round to the nearest multiple of rounding_factor
    # (Value / Factor) -> Round -> * Factor
    if rounding_factor == 0: # Avoid division by zero if factor is misconfigured
        return int(lbp_unrounded.to_integral_value(rounding=ROUND_HALF_UP))

    rounded_lbp = (lbp_unrounded / Decimal(rounding_factor)).to_integral_value(rounding=ROUND_HALF_UP) * Decimal(rounding_factor)
    return int(rounded_lbp)

def generate_order_number():
    """
    Generates a unique order number.
    For v0.1, a simple timestamp-based number. Can be made more robust.
    """
    import datetime
    import random
    now = datetime.datetime.utcnow()
    return f"ORD-{now.strftime('%Y%m%d%H%M%S')}-{random.randint(1000, 9999)}"

def generate_customer_number():
    """
    Generates a unique customer number based on date + incremental counter.
    Format: YYYYMMDD-XXX where XXX is a 3-digit counter that resets daily at midnight.
    Example: 20241201-001, 20241201-002, etc.
    """
    today = date.today()
    today_str = today.strftime('%Y%m%d')
    
    # Find the highest customer number for today
    today_pattern = f"{today_str}-%"
    highest_customer = Order.query.filter(
        Order.customer_number.like(today_pattern)
    ).order_by(Order.customer_number.desc()).first()
    
    if highest_customer:
        # Extract the counter from the highest number
        try:
            counter_part = highest_customer.customer_number.split('-')[1]
            next_counter = int(counter_part) + 1
        except (IndexError, ValueError):
            next_counter = 1
    else:
        next_counter = 1
    
    # Format as YYYYMMDD-XXX (3-digit counter with leading zeros)
    return f"{today_str}-{next_counter:03d}"

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

