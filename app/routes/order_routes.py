"""Order management routes for the Cafe24 POS system."""

import datetime
from decimal import Decimal

from flask import Blueprint, current_app, jsonify, request
from flask_jwt_extended import get_jwt_identity, jwt_required

from app.models import (
    Ingredient, MenuItem, MenuItemOptionChoice, Order, OrderItem,
    Recipe, StockAdjustment, SystemSettings, User, db
)
from app.utils.decorators import roles_required
from app.utils.helpers import (
    calculate_lbp_price, generate_customer_number, generate_order_number,
    get_current_exchange_rate
)

order_bp = Blueprint('order_bp', __name__)

def check_and_deduct_stock(order_items_data, user_id):
    """
    Check if ingredients are available for the order items and deduct stock.
    Returns True if successful, raises exception with message if not.
    """
    # First, calculate total ingredient requirements for the entire order
    ingredient_requirements = {}  # ingredient_id -> total_amount_needed
    
    for item_data in order_items_data:
        menu_item_id = item_data['menu_item_id']
        quantity = item_data['quantity']
        
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
            insufficient_ingredients.append({
                'name': ingredient.name,
                'needed': amount_needed,
                'available': ingredient.current_stock,
                'unit': ingredient.unit
            })
    
    if insufficient_ingredients:
        error_msg = "Insufficient stock for: " + ", ".join([
            f"{item['name']} (need {item['needed']}{item['unit']}, have {item['available']}{item['unit']})"
            for item in insufficient_ingredients
        ])
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
            reason=f"Order placement - automatic deduction",
            user_id=user_id
        )
        db.session.add(adjustment)
    
    return True

@order_bp.route('', methods=['POST'])
@jwt_required()
@roles_required('courier', 'manager', 'cashier')
def create_order():
    """Create a new order."""
    try:
        data = request.get_json()
        current_app.logger.info(f"Received order data: {data}")  # Log the received data
        
        if not data or 'items' not in data:
            current_app.logger.error("Missing data or items in request")
            return jsonify({'message': 'Items are required.'}), 400

        if not isinstance(data['items'], list) or not data['items']:
            current_app.logger.error("Items must be a non-empty list")
            return jsonify({'message': 'Items must be a non-empty list.'}), 400

        # Log each item for debugging
        for i, item_data in enumerate(data['items']):
            current_app.logger.info(f"Processing item {i}: {item_data}")
            current_app.logger.info(f"Item {i} types - menu_item_id: {type(item_data.get('menu_item_id'))}, quantity: {type(item_data.get('quantity'))}")

        exchange_rate = get_current_exchange_rate() # From helpers, ultimately from config/DB
        order_total_usd = Decimal('0.00')

        new_order_items_to_commit = [] # To store SQLAlchemy OrderItem objects
        order_items_for_stock = [] # To store data for stock deduction

        try:
            for item_data in data['items']:
                menu_item_id = item_data.get('menu_item_id')
                quantity = item_data.get('quantity', 1)

                current_app.logger.info(f"Validating item - menu_item_id: {menu_item_id} (type: {type(menu_item_id)}), quantity: {quantity} (type: {type(quantity)})")

                if not isinstance(menu_item_id, int) or not isinstance(quantity, int) or quantity <= 0:
                    current_app.logger.error(f"Validation failed - menu_item_id: {menu_item_id} (type: {type(menu_item_id)}), quantity: {quantity} (type: {type(quantity)})")
                    return jsonify({'message': 'Invalid menu_item_id or quantity.'}), 400

                menu_item = MenuItem.query.filter_by(id=menu_item_id, is_active=True).first()
                if not menu_item:
                    current_app.logger.error(f"Menu item ID {menu_item_id} not found or inactive.")
                    return jsonify({'message': f"Menu item ID {menu_item_id} not found or inactive."}), 404

                unit_price_usd = menu_item.base_price_usd
                chosen_option_name = None
                chosen_option_id_val = item_data.get('chosen_option_choice_id') # Can be None

                if chosen_option_id_val is not None:
                    option_choice = MenuItemOptionChoice.query.get(chosen_option_id_val)
                    # Ensure the option choice belongs to an option that belongs to the menu item
                    if not option_choice or option_choice.option_type.menu_item_id != menu_item.id:
                        current_app.logger.error(f"Invalid option choice ID {chosen_option_id_val} for item {menu_item.name}")
                        return jsonify({'message': f"Invalid option choice ID {chosen_option_id_val} for item {menu_item.name}"}), 400
                    unit_price_usd = option_choice.price_usd # Option price is the absolute price for this variant
                    chosen_option_name = option_choice.choice_name

                unit_price_lbp_rounded = calculate_lbp_price(unit_price_usd, exchange_rate)
                if unit_price_lbp_rounded is None:
                    current_app.logger.error(f'Could not calculate LBP price for item {menu_item.name}')
                    return jsonify({'message': f'Could not calculate LBP price for item {menu_item.name}'}), 500
                
                line_total_usd = unit_price_usd * Decimal(quantity)
                line_total_lbp_rounded = unit_price_lbp_rounded * quantity # Sum of rounded unit prices

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
                    line_total_lbp_rounded_at_order=line_total_lbp_rounded
                )
                new_order_items_to_commit.append(db_order_item)
                
                # Store for stock deduction
                order_items_for_stock.append({
                    'menu_item_id': menu_item.id,
                    'quantity': quantity
                })

            # Check and deduct stock before creating the order
            try:
                user_id = get_jwt_identity()
                check_and_deduct_stock(order_items_for_stock, user_id)
            except ValueError as e:
                current_app.logger.error(f"Stock deduction failed: {e}")
                return jsonify({'message': str(e)}), 400

            final_total_lbp_rounded = calculate_lbp_price(order_total_usd, exchange_rate) # Round the final USD sum

            # Auto-generate customer number
            customer_number = generate_customer_number()

            new_order = Order(
                order_number=generate_order_number(),
                courier_id=user_id,
                customer_number=customer_number,
                status='paid_waiting_preparation', # Initial status for v0.1
                subtotal_usd=order_total_usd,  # Before discounts
                subtotal_lbp_rounded=final_total_lbp_rounded,  # Before discounts
                discount_total_usd=Decimal('0.00'),  # No discounts initially
                discount_total_lbp_rounded=0,  # No discounts initially
                final_total_usd=order_total_usd,  # Same as subtotal initially
                final_total_lbp_rounded=final_total_lbp_rounded,  # Same as subtotal initially
                exchange_rate_at_order_time=exchange_rate,
                notes=data.get('notes')
            )

            db.session.add(new_order)
            db.session.flush() # To get new_order.id

            for oi in new_order_items_to_commit:
                oi.order_id = new_order.id
                db.session.add(oi)

            db.session.commit()

            return jsonify({
                'message': 'Order created successfully!',
                'order_id': new_order.id,
                'order_number': new_order.order_number,
                'customer_number': new_order.customer_number,
                'final_total_lbp_rounded': new_order.final_total_lbp_rounded,
                'final_total_usd': float(new_order.final_total_usd)
            }), 201

        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f"Error creating order: {e}")
            return jsonify({'message': f'Could not create order. {str(e)}'}), 500

    except Exception as e:
        current_app.logger.error(f"Error in create_order: {e}")
        return jsonify({'message': f'Could not create order. {str(e)}'}), 500


@order_bp.route('/for-barista', methods=['GET'])
@jwt_required()
@roles_required('barista', 'manager')
def get_orders_for_barista():
    # Force Flask to ignore conditional GET headers
    request.if_modified_since = None
    request.if_none_match = None
    """ Barista/Manager: Get orders that need attention by the barista. """
    try:
        # For v0.1, simple filter. Later, more sophisticated queue logic.
        orders = Order.query.filter(
            Order.status.in_(['paid_waiting_preparation', 'preparing'])
        ).order_by(Order.created_at.asc()).all()

        result = []
        for order in orders:
            items_summary = []
            for item in order.order_items: # Assumes 'items' is the relationship name in Order model
                summary = f"{item.quantity}x {item.menu_item_name}"
                if item.chosen_option_choice_name:
                    summary += f" ({item.chosen_option_choice_name})"
                items_summary.append(summary)

            result.append({
                'order_id': order.id,
                'order_number': order.order_number,
                'customer_number': order.customer_number,
                'status': order.status.value,
                'items_summary': ", ".join(items_summary),
                'created_at': order.created_at.isoformat()
            })
        response = jsonify(result)
        response.headers['Cache-Control'] = 'no-store'
        return response, 200
    except Exception as e:
        current_app.logger.error(f"Error fetching orders for barista: {e}")
        response = jsonify({'message': 'Could not retrieve orders for barista.'})
        response.headers['Cache-Control'] = 'no-store'
        return response, 500

@order_bp.route('/active', methods=['GET'])
@jwt_required()
@roles_required('cashier', 'courier', 'manager')
def get_active_orders():
    # Force Flask to ignore conditional GET headers
    request.if_modified_since = None
    request.if_none_match = None
    """Get all active (non-completed, non-cancelled) orders for cashier/courier/manager."""
    try:
        active_statuses = ['pending_payment', 'paid_waiting_preparation', 'preparing', 'ready_for_pickup']
        orders = Order.query.filter(Order.status.in_(active_statuses)).order_by(Order.created_at.desc()).all()
        result = []
        for order in orders:
            items_details = []
            for item in order.order_items:
                item_info = {
                    'menu_item_name': item.menu_item_name,
                    'quantity': item.quantity,
                    'chosen_option_choice_name': item.chosen_option_choice_name,
                    'unit_price_usd_at_order': float(item.unit_price_usd_at_order),
                    'unit_price_lbp_rounded_at_order': item.unit_price_lbp_rounded_at_order,
                    'line_total_usd_at_order': float(item.line_total_usd_at_order),
                    'line_total_lbp_rounded_at_order': item.line_total_lbp_rounded_at_order
                }
                items_details.append(item_info)
            result.append({
                'order_id': order.id,
                'order_number': order.order_number,
                'customer_number': order.customer_number,
                'status': order.status.value,
                'subtotal_usd': float(order.subtotal_usd),
                'subtotal_lbp_rounded': order.subtotal_lbp_rounded,
                'discount_total_usd': float(order.discount_total_usd),
                'discount_total_lbp_rounded': order.discount_total_lbp_rounded,
                'final_total_usd': float(order.final_total_usd),
                'final_total_lbp_rounded': order.final_total_lbp_rounded,
                'exchange_rate_at_order_time': float(order.exchange_rate_at_order_time),
                'payment_method': order.payment_method,
                'created_at': order.created_at.isoformat(),
                'items': items_details
            })
        response = jsonify(result)
        response.headers['Cache-Control'] = 'no-store'
        return response, 200
    except Exception as e:
        current_app.logger.error(f"Error fetching active orders: {e}")
        response = jsonify({'message': 'Could not retrieve active orders.'})
        response.headers['Cache-Control'] = 'no-store'
        return response, 500

@order_bp.route('/<int:order_id>/status', methods=['PUT'])
@jwt_required() # Role check specific to status transition
def update_order_status(order_id):
    user_id = get_jwt_identity()
    current_user = User.query.get(user_id)
    data = request.get_json()
    new_status = data.get('status')

    order = Order.query.get_or_404(order_id)

    # Log the details for debugging
    current_app.logger.info(f"Attempting to update order {order_id} from '{order.status.value}' to '{new_status}' by user with role '{current_user.role.value}'.")

    if not new_status:
        return jsonify({'message': 'New status is required'}), 400

    # Define allowed transitions and roles for v0.1
    allowed_transitions = {
        'pending_payment': {
            'paid_waiting_preparation': ['cashier', 'manager'] # Cashier marks as paid
        },
        'paid_waiting_preparation': {
            'preparing': ['barista', 'manager']
        },
        'preparing': {
            'ready_for_pickup': ['barista', 'manager']
        },
        'ready_for_pickup': {
            'completed': ['cashier', 'courier', 'manager'] # Any of these can complete it
        }
        # Add cancellation logic later if needed for v0.1, e.g. manager can cancel
    }

    if order.status.value not in allowed_transitions or \
       new_status not in allowed_transitions[order.status.value] or \
       current_user.role.value not in allowed_transitions[order.status.value][new_status]:
        current_app.logger.error(f"403 Forbidden: Cannot change status from '{order.status.value}' to '{new_status}' by user with role '{current_user.role.value}'.")
        return jsonify({'message': f'Cannot change status from {order.status.value} to {new_status} with role {current_user.role.value}'}), 403

    try:
        order.status = new_status
        if new_status == 'paid_waiting_preparation' and current_user.role.value == 'cashier':
            order.cashier_id = current_user.id
            # For v0.1, if cashier is marking paid, we can set a simulated payment method
            order.payment_method = data.get('payment_method', 'simulated_cash_lbp')
        elif new_status == 'preparing' and current_user.role.value == 'barista':
            order.barista_id = current_user.id # Assign barista when prep starts

        order.updated_at = datetime.datetime.utcnow()
        db.session.commit()
        # Could return the updated order object, simplified for now
        return jsonify({'message': f'Order {order.order_number} status updated to {new_status}'}), 200
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Error updating order status: {e}")
        return jsonify({'message': 'Could not update order status.'}), 500


@order_bp.route('/by-number/<string:order_number>', methods=['GET'])
@jwt_required()
@roles_required('cashier', 'manager', 'courier') # Courier might want to check status too
def get_order_by_number(order_number):
    """ Cashier/Manager/Courier: Get a specific order by its number. """
    try:
        order = Order.query.filter_by(order_number=order_number).first_or_404()

        items_details = []
        for item in order.items:
            items_details.append({
                'menu_item_name': item.menu_item_name,
                'quantity': item.quantity,
                'chosen_option_choice_name': item.chosen_option_choice_name,
                'unit_price_lbp_rounded_at_order': item.unit_price_lbp_rounded_at_order,
                'line_total_lbp_rounded_at_order': item.line_total_lbp_rounded_at_order,
                'unit_price_usd_at_order': float(item.unit_price_usd_at_order),
                'line_total_usd_at_order': float(item.line_total_usd_at_order),
            })

        return jsonify({
            'order_id': order.id,
            'order_number': order.order_number,
            'customer_number': order.customer_number,
            'status': order.status,
            'subtotal_usd': float(order.subtotal_usd),
            'subtotal_lbp_rounded': order.subtotal_lbp_rounded,
            'discount_total_usd': float(order.discount_total_usd),
            'discount_total_lbp_rounded': order.discount_total_lbp_rounded,
            'final_total_usd': float(order.final_total_usd),
            'final_total_lbp_rounded': order.final_total_lbp_rounded,
            'exchange_rate_at_order_time': float(order.exchange_rate_at_order_time),
            'payment_method': order.payment_method,
            'notes': order.notes,
            'created_at': order.created_at.isoformat(),
            'updated_at': order.updated_at.isoformat(),
            'items': items_details,
            'courier_id': order.courier_id,
            'cashier_id': order.cashier_id,
            'barista_id': order.barista_id
        }), 200
    except Exception as e:
        # Catch specific exception if model not found by first_or_404 if needed
        current_app.logger.error(f"Error fetching order by number: {e}")
        return jsonify({'message': 'Could not retrieve order.'}), 500

@order_bp.route('/completed', methods=['GET'])
@jwt_required()
@roles_required('cashier', 'courier', 'manager')
def get_completed_orders():
    """Get all completed orders for cashier/courier/manager."""
    try:
        orders = Order.query.filter(Order.status == 'completed').order_by(Order.created_at.desc()).all()
        result = []
        for order in orders:
            items_details = []
            for item in order.items:
                item_info = {
                    'menu_item_name': item.menu_item_name,
                    'quantity': item.quantity,
                    'chosen_option_choice_name': item.chosen_option_choice_name,
                    'unit_price_usd_at_order': float(item.unit_price_usd_at_order),
                    'unit_price_lbp_rounded_at_order': item.unit_price_lbp_rounded_at_order,
                    'line_total_usd_at_order': float(item.line_total_usd_at_order),
                    'line_total_lbp_rounded_at_order': item.line_total_lbp_rounded_at_order
                }
                items_details.append(item_info)
            result.append({
                'order_id': order.id,
                'order_number': order.order_number,
                'customer_number': order.customer_number,
                'status': order.status,
                'subtotal_usd': float(order.subtotal_usd),
                'subtotal_lbp_rounded': order.subtotal_lbp_rounded,
                'discount_total_usd': float(order.discount_total_usd),
                'discount_total_lbp_rounded': order.discount_total_lbp_rounded,
                'final_total_usd': float(order.final_total_usd),
                'final_total_lbp_rounded': order.final_total_lbp_rounded,
                'exchange_rate_at_order_time': float(order.exchange_rate_at_order_time),
                'payment_method': order.payment_method,
                'created_at': order.created_at.isoformat(),
                'items': items_details
            })
        return jsonify(result), 200
    except Exception as e:
        current_app.logger.error(f"Error fetching completed orders: {e}")
        return jsonify({'message': 'Could not retrieve completed orders.'}), 500
