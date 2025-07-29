"""Helper utility functions for the Cafe24 POS application.

This module contains utility functions for currency conversion, order numbering, etc.
"""
import datetime
import random
from decimal import Decimal, ROUND_HALF_UP
from datetime import date
from flask import current_app
from app.models import Order


def get_system_setting(key, default=None):
    """Get a system setting from the database.
    
    For v0.1, we might hardcode or get from config, but this is for future use.
    
    Args:
        key (str): The setting key to retrieve.
        default: Default value if setting not found.
        
    Returns:
        str: The setting value or default.
    """
    # Local import to avoid circular dependency
    from app.models import SystemSettings
    setting = SystemSettings.query.filter_by(setting_key=key).first()
    return setting.setting_value if setting else default


def get_current_exchange_rate():
    """Retrieve the current USD to LBP exchange rate.
    
    First tries to get from database, falls back to config.
    
    Returns:
        Decimal: The current exchange rate.
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
    """Retrieve the LBP rounding factor (e.g., 5000).
    
    Returns:
        int: The rounding factor.
    """
    return int(current_app.config.get('LBP_ROUNDING_FACTOR', '5000'))


def calculate_lbp_price(price_usd, exchange_rate=None, rounding_factor=None):
    """Convert a USD price to LBP and round it according to the system's rounding factor.
    
    Args:
        price_usd: Price in USD to convert.
        exchange_rate: Exchange rate to use (optional).
        rounding_factor: Rounding factor to use (optional).
        
    Returns:
        int: The price in LBP, rounded.
    """
    if price_usd is None:
        return None

    if exchange_rate is None:
        exchange_rate = get_current_exchange_rate()

    if rounding_factor is None:
        rounding_factor = get_lbp_rounding_factor()

    price_usd_decimal = Decimal(str(price_usd))  # Ensure it's a Decimal
    lbp_unrounded = price_usd_decimal * exchange_rate

    # Round to the nearest multiple of rounding_factor
    # (Value / Factor) -> Round -> * Factor
    if rounding_factor == 0:  # Avoid division by zero if factor is misconfigured
        return int(lbp_unrounded.to_integral_value(rounding=ROUND_HALF_UP))

    rounded_lbp = (lbp_unrounded / Decimal(rounding_factor)).to_integral_value(
        rounding=ROUND_HALF_UP) * Decimal(rounding_factor)
    return int(rounded_lbp)


def generate_order_number():
    """Generate a unique order number.
    
    For v0.1, a simple timestamp-based number. Can be made more robust.
    
    Returns:
        str: A unique order number.
    """
    now = datetime.datetime.utcnow()
    return f"ORD-{now.strftime('%Y%m%d%H%M%S')}-{random.randint(1000, 9999)}"


def generate_customer_number():
    """Generate a unique customer number based on date + incremental counter.
    
    Format: YYYYMMDD-XXX where XXX is a 3-digit counter that resets daily at midnight.
    Example: 20241201-001, 20241201-002, etc.
    
    Returns:
        str: A unique customer number.
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
