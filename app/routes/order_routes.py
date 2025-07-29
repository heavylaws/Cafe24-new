import datetime
from decimal import Decimal

from flask import Blueprint, current_app, jsonify, request
from flask_jwt_extended import get_jwt_identity, jwt_required

from app.models import (
    Ingredient,
    MenuItem,
    MenuItemOptionChoice,
    Order,
    OrderItem,
    Recipe,
    StockAdjustment,
    SystemSettings,
    User,
    db,
)
from app.utils.decorators import roles_required
from app.utils.helpers import (
    calculate_lbp_price,
    generate_customer_number,
    generate_order_number,
    get_current_exchange_rate,
)

order_bp = Blueprint("order_bp", __name__)


def check_and_deduct_stock(order_items_data, user_id):
    """
    Check if ingredients are available for the order items and deduct stock.
    Returns True if successful, raises exception with message if not.
    """
    # First, calculate total ingredient requirements for the entire order
    ingredient_requirements = {}  # ingredient_id -> total_amount_needed

    for item_data in order_items_data:
        menu_item_id = item_data["menu_item_id"]
        quantity = item_data["quantity"]

        # Get recipes for this menu item
        recipes = Recipe.query.filter_by(menu_item_id=menu_item_id).all()

        for recipe in recipes:
            ingredient_id = recipe.ingredient_id
            amount_needed = recipe.amount * quantity

            if ingredient_id in ingredient_requirements:
                ingredient_requirements[ingredient_id] += amount_needed
            else:
                ingredient_requirements[ingredient_id] = amount_needed

    # Check if all ingredients are available
    insufficient_ingredients = []
    for ingredient_id, amount_needed in ingredient_requirements.items():
        ingredient = Ingredient.query.get(ingredient_id)
        if not ingredient or not ingredient.is_active:
            continue  # Skip inactive ingredients

        if ingredient.current_stock < amount_needed:
            insufficient_ingredients.append(
                {
                    "name": ingredient.name,
                    "needed": amount_needed,
                    "available": ingredient.current_stock,
                    "unit": ingredient.unit,
                }
            )

    if insufficient_ingredients:
        error_msg = "Insufficient stock for: " + ", ".join(
            [
                f"{item['name']} (need {item['needed']}{item['unit']}, have {item['available']}{item['unit']})"
                for item in insufficient_ingredients
            ]
        )
        raise ValueError(error_msg)

    # Deduct stock and create adjustment records
    for ingredient_id, amount_needed in ingredient_requirements.items():
        ingredient = Ingredient.query.get(ingredient_id)
        if not ingredient or not ingredient.is_active:
            continue

        # Deduct stock
        ingredient.current_stock -= amount_needed

        # Create stock adjustment record
        adjustment = StockAdjustment(
            ingredient_id=ingredient_id,
            change_amount=-amount_needed,  # Negative for deduction
            reason="Order placement - automatic deduction",
            user_id=user_id,
        )
        db.session.add(adjustment)

    return True


@order_bp.route("", methods=["POST"])
@jwt_required()
@roles_required("courier", "manager", "cashier")
def create_order():
    """Create a new order."""
    try:
        data = request.get_json()
        current_app.logger.info(f"Received order data: {data}")  # Log the received data

        if not data or "items" not in data:
            current_app.logger.error("Missing data or items in request")
            return jsonify({"message": "Items are required."}), 400

        if not isinstance(data["items"], list) or not data["items"]:
            current_app.logger.error("Items must be a non-empty list")
            return jsonify({"message": "Items must be a non-empty list."}), 400

        # Log each item for debugging
        for i, item_data in enumerate(data["items"]):
            current_app.logger.info(f"Processing item {i}: {item_data}")
            current_app.logger.info(
                f"Item {i} types - menu_item_id: {type(item_data.get('menu_item_id'))}, quantity: {type(item_data.get('quantity'))}"
            )

        exchange_rate = get_current_exchange_rate()
        order_total_usd = Decimal("0.00")

        new_order_items_to_commit = []  # To store SQLAlchemy OrderItem objects
        order_items_for_stock = []  # To store data for stock deduction

        try:
            for item_data in data["items"]:
                menu_item_id = item_data.get("menu_item_id")
                quantity = item_data.get("quantity", 1)

                current_app.logger.info(
                    f"Validating item - menu_item_id: {menu_item_id} (type: {type(menu_item_id)}), quantity: {quantity} (type: {type(quantity)})"
                )

                if (
                    not isinstance(menu_item_id, int)
                    or not isinstance(quantity, int)
                    or quantity <= 0
                ):
                    current_app.logger.error(
                        f"Validation failed - menu_item_id: {menu_item_id} (type: {type(menu_item_id)}), quantity: {quantity} (type: {type(quantity)})"
                    )
                    return (
                        jsonify({"message": "Invalid menu_item_id or quantity."}),
                        400,
                    )

                menu_item = MenuItem.query.filter_by(
                    id=menu_item_id, is_active=True
                ).first()
                if not menu_item:
                    current_app.logger.error(
                        f"Menu item ID {menu_item_id} not found or inactive."
                    )
                    return (
                        jsonify(
                            {
                                "message": f"Menu item ID {menu_item_id} not found or inactive."
                            }
                        ),
                        404,
                    )

                unit_price_usd = menu_item.base_price_usd
                chosen_option_name = None
                chosen_option_id_val = item_data.get("chosen_option_choice_id")  # Can be None

                if chosen_option_id_val is not None:
                    option_choice = MenuItemOptionChoice.query.get(chosen_option_id_val)
                    # Ensure the option choice belongs to an option that belongs to the menu item
                    if (
                        not option_choice
                        or option_choice.option_type.menu_item_id != menu_item.id
                    ):
                        current_app.logger.error(
                            f"Invalid option choice ID {chosen_option_id_val} for item {menu_item.name}"
                        )
                        return (
                            jsonify(
                                {
                                    "message": f"Invalid option choice ID {chosen_option_id_val} for item {menu_item.name}"
                                }
                            ),
                            400,
                        )
                    unit_price_usd = option_choice.price_usd  # Option price is the absolute price for this variant
                    chosen_option_name = option_choice.choice_name

                unit_price_lbp_rounded = calculate_lbp_price(unit_price_usd, exchange_rate)
                if unit_price_lbp_rounded is None:
                    current_app.logger.error(
                        f"Could not calculate LBP price for item {menu_item.name}"
                    )
                    return (
                        jsonify(
                            {
                                "message": f"Could not calculate LBP price for item {menu_item.name}"
                            }
                        ),
                        500,
                    )

                line_total_usd = unit_price_usd * Decimal(quantity)
                line_total_lbp_rounded = unit_price_lbp_rounded * quantity  # Sum of rounded unit prices

                order_total_usd += line_total_usd

                db_order_item = OrderItem(
                    menu_item_id=menu_item.id,
                    menu_item_name=menu_item.name,
                    quantity=quantity,
                    chosen_option_choice_id=chosen_option_id_val,
                    chosen_option_choice_name=chosen_option_name,
                    unit_price_usd_at_order=unit_price_usd,
                    unit_price_lbp_rounded_at_order=unit_price_lbp_rounded,
                    line_total_usd_at_order=line_total_usd,
                    line_total_lbp_rounded_at_order=line_total_lbp_rounded,
                )
                new_order_items_to_commit.append(db_order_item)

                # Store for stock deduction
                order_items_for_stock.append(
                    {"menu_item_id": menu_item.id, "quantity": quantity}
                )

            # Check and deduct stock before creating the order
            try:
                user_id = get_jwt_identity()
                check_and_deduct_stock(order_items_for_stock, user_id)
            except ValueError as e:
                current_app.logger.error(f"Stock deduction failed: {e}")
                return jsonify({"message": str(e)}), 400

            final_total_lbp_rounded = calculate_lbp_price(order_total_usd, exchange_rate)

            # Auto-generate customer number
            customer_number = generate_customer_number()

            new_order = Order(
                order_number=generate_order_number(),
                courier_id=user_id,
                customer_number=customer_number,
                status="paid_waiting_preparation",  # Initial status for v0.1
                subtotal_usd=order_total_usd,  # Before discounts
                subtotal_lbp_rounded=final_total_lbp_rounded,  # Before discounts
                discount_total_usd=Decimal("0.00"),  # No discounts initially
                discount_total_lbp_rounded=0,  # No discounts initially
                final_total_usd=order_total_usd,  # Same as subtotal initially
                final_total_lbp_rounded=final_total_lbp_rounded,  # Same as subtotal initially
                exchange_rate_at_order_time=exchange_rate,
                notes=data.get("notes"),
            )

            db.session.add(new_order)
            db.session.flush()  # To get new_order.id

            for oi in new_order_items_to_commit:
                oi.order_id = new_order.id
                db.session.add(oi)

            db.session.commit()

            # Emit real-time notification for new order
            try:
                from app.routes.realtime_routes import emit_new_order
                emit_new_order(new_order.id)
            except Exception as emit_error:
                current_app.logger.warning(f"Failed to emit real-time update for new order: {emit_error}")

            return jsonify({
                "message": "Order created successfully!",
                "order_id": new_order.id,
                "order_number": new_order.order_number,
                "customer_number": new_order.customer_number,
                "final_total_lbp_rounded": new_order.final_total_lbp_rounded,
                "final_total_usd": float(new_order.final_total_usd),
            }), 201

        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f"Error creating order: {e}")
            return jsonify({"message": f"Could not create order. {str(e)}"}), 500

    except Exception as e:
        current_app.logger.error(f"Error in create_order: {e}")
        return jsonify({"message": f"Could not create order. {str(e)}"}), 500

# ... (rest of your routes remain unchanged)
