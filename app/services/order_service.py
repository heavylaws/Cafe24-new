# app/services/order_service.py
from app.models import db, MenuItem, MenuItemOptionChoice, SystemSettings
from app.utils.helpers import calculate_lbp_price, get_current_exchange_rate
from decimal import Decimal

# For v0.1, much of the order creation logic is currently in the order_routes.py for simplicity.
# As the application grows, this service layer would handle more complex business logic
# related to orders, such as:
# - Complex discount application
# - Stock checking and deduction (when stock management is implemented)
# - Loyalty point calculations
# - More intricate price calculations if needed
# - Interacting with potential third-party services (e.g., delivery APIs)

# Example of how price calculation could be refactored here:

def calculate_order_item_details(menu_item_id, quantity, chosen_option_choice_id=None):
    """
    Calculates price details for a single order item.
    Returns a dictionary with price details or raises an error if item/option not found.
    This is a more structured way to handle what's currently in the order_routes.create_order.
    """
    menu_item = MenuItem.query.filter_by(id=menu_item_id, is_active=True).first()
    if not menu_item:
        raise ValueError(f"Menu item ID {menu_item_id} not found or inactive.")

    if not isinstance(quantity, int) or quantity <= 0:
        raise ValueError("Quantity must be a positive integer.")

    unit_price_usd = menu_item.base_price_usd
    actual_chosen_option_name = None # For clarity in return value

    if chosen_option_choice_id is not None:
        option_choice = MenuItemOptionChoice.query.get(chosen_option_choice_id)
        if not option_choice or option_choice.option_type.menu_item_id != menu_item.id:
            raise ValueError(f"Invalid option choice ID {chosen_option_choice_id} for item {menu_item.name}")
        unit_price_usd = option_choice.price_usd
        actual_chosen_option_name = option_choice.choice_name

    exchange_rate = get_current_exchange_rate() # Assumes this helper is available and configured

    unit_price_lbp_rounded = calculate_lbp_price(unit_price_usd, exchange_rate)

    line_total_usd = Decimal(unit_price_usd) * Decimal(quantity)
    # For line_total_lbp_rounded, it's generally better to sum rounded unit prices if that's how display works,
    # or round the total sum of unrounded LBP prices. Let's stick to sum of rounded for consistency with display.
    line_total_lbp_rounded = unit_price_lbp_rounded * quantity

    return {
        "menu_item_id": menu_item.id,
        "menu_item_name": menu_item.name,
        "quantity": quantity,
        "chosen_option_choice_id": chosen_option_choice_id,
        "chosen_option_choice_name": actual_chosen_option_name,
        "unit_price_usd_at_order": Decimal(unit_price_usd),
        "unit_price_lbp_rounded_at_order": unit_price_lbp_rounded,
        "line_total_usd_at_order": line_total_usd,
        "line_total_lbp_rounded_at_order": line_total_lbp_rounded,
        "exchange_rate_at_calculation": exchange_rate # Good to log for auditing
    }

def calculate_final_order_totals(order_items_details_list, exchange_rate=None):
    """
    Calculates the final total for an order based on a list of item details.
    order_items_details_list: A list of dictionaries, each from calculate_order_item_details.
    """
    if exchange_rate is None:
        exchange_rate = get_current_exchange_rate()

    grand_total_usd = Decimal('0.00')
    # For LBP, sum the already calculated line_total_lbp_rounded or sum unrounded USD and round once at the end.
    # The current create_order route rounds the final sum of USD. Let's replicate that for consistency.
    grand_total_lbp_unrounded_from_usd_sum = Decimal('0.00')

    for item_detail in order_items_details_list:
        grand_total_usd += item_detail['line_total_usd_at_order']
        # To be consistent with current order_routes, we sum USD and then convert/round.
        # Alternatively, one could sum `line_total_lbp_rounded_at_order` but that might lead to minor
        # discrepancies compared to summing USD then converting/rounding once.

    final_total_lbp_rounded = calculate_lbp_price(grand_total_usd, exchange_rate)

    return {
        "final_total_usd": grand_total_usd,
        "final_total_lbp_rounded": final_total_lbp_rounded
    }

# For v0.1, this service file can remain minimal or be expanded as logic is refactored
# out of the route handlers. The example functions above show a potential direction.
pass

