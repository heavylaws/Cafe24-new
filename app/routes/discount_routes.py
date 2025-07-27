from flask import Blueprint, request, jsonify, current_app
from app.models import db, Discount, Order, OrderItem, OrderDiscount, OrderItemDiscount
from app.utils.decorators import roles_required
from flask_jwt_extended import jwt_required, get_jwt_identity
from app.utils.helpers import calculate_lbp_price, get_current_exchange_rate
from decimal import Decimal
import datetime

discount_bp = Blueprint('discount_bp', __name__)

@discount_bp.route('/discounts', methods=['GET'])
@jwt_required()
@roles_required('manager', 'cashier')
def get_discounts():
    """Get all active discounts available for application."""
    try:
        discounts = Discount.query.filter_by(is_active=True).order_by(Discount.name).all()
        result = []
        for discount in discounts:
            result.append({
                'id': discount.id,
                'name': discount.name,
                'description': discount.description,
                'discount_type': discount.discount_type.value,
                'discount_value': float(discount.discount_value),
                'applies_to': discount.applies_to.value,
                'is_active': discount.is_active
            })
        return jsonify(result), 200
    except Exception as e:
        current_app.logger.error(f"Error fetching discounts: {e}")
        return jsonify({'message': 'Could not retrieve discounts.'}), 500

@discount_bp.route('/discounts', methods=['POST'])
@jwt_required()
@roles_required('manager')
def create_discount():
    """Manager: Create a new discount."""
    data = request.get_json()
    required_fields = ['name', 'discount_type', 'discount_value', 'applies_to']
    if not all(field in data for field in required_fields):
        return jsonify({'message': f'Missing required fields: {", ".join(required_fields)}'}), 400

    if data['discount_type'] not in ['percentage', 'fixed_amount']:
        return jsonify({'message': 'discount_type must be "percentage" or "fixed_amount"'}), 400
    
    if data['applies_to'] not in ['order', 'item']:
        return jsonify({'message': 'applies_to must be "order" or "item"'}), 400

    try:
        discount_value = Decimal(str(data['discount_value']))
        if discount_value <= 0:
            return jsonify({'message': 'discount_value must be positive'}), 400
        
        if data['discount_type'] == 'percentage' and discount_value > 100:
            return jsonify({'message': 'percentage discount cannot exceed 100%'}), 400

        new_discount = Discount(  # type: ignore
            name=data['name'],  # type: ignore[arg-type]
            description=data.get('description', ''),  # type: ignore[arg-type]
            discount_type=data['discount_type'],  # type: ignore[arg-type]
            discount_value=discount_value,  # type: ignore[arg-type]
            applies_to=data['applies_to'],  # type: ignore[arg-type]
            is_active=data.get('is_active', True)  # type: ignore[arg-type]
        )
        
        db.session.add(new_discount)
        db.session.commit()
        
        return jsonify({
            'id': new_discount.id,
            'name': new_discount.name,
            'discount_type': new_discount.discount_type,
            'discount_value': float(new_discount.discount_value),
            'applies_to': new_discount.applies_to
        }), 201
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Error creating discount: {e}")
        return jsonify({'message': 'Could not create discount.'}), 500

@discount_bp.route('/discounts/<int:discount_id>', methods=['PUT'])
@jwt_required()
@roles_required('manager')
def update_discount(discount_id):
    """Manager: Update a discount."""
    data = request.get_json()
    if not data:
        return jsonify({'message': 'No data provided'}), 400

    discount = Discount.query.get_or_404(discount_id)
    
    try:
        if 'name' in data:
            discount.name = data['name']
        if 'description' in data:
            discount.description = data['description']
        if 'discount_type' in data:
            if data['discount_type'] not in ['percentage', 'fixed_amount']:
                return jsonify({'message': 'discount_type must be "percentage" or "fixed_amount"'}), 400
            discount.discount_type = data['discount_type']
        if 'discount_value' in data:
            discount_value = Decimal(str(data['discount_value']))
            if discount_value <= 0:
                return jsonify({'message': 'discount_value must be positive'}), 400
            if discount.discount_type == 'percentage' and discount_value > 100:
                return jsonify({'message': 'percentage discount cannot exceed 100%'}), 400
            discount.discount_value = discount_value
        if 'applies_to' in data:
            if data['applies_to'] not in ['order', 'item']:
                return jsonify({'message': 'applies_to must be "order" or "item"'}), 400
            discount.applies_to = data['applies_to']
        if 'is_active' in data:
            discount.is_active = bool(data['is_active'])
        
        discount.updated_at = datetime.datetime.utcnow()
        db.session.commit()
        
        return jsonify({
            'id': discount.id,
            'name': discount.name,
            'discount_type': discount.discount_type,
            'discount_value': float(discount.discount_value),
            'applies_to': discount.applies_to,
            'is_active': discount.is_active
        }), 200
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Error updating discount: {e}")
        return jsonify({'message': 'Could not update discount.'}), 500

@discount_bp.route('/apply-order-discount', methods=['POST'])
@jwt_required()
@roles_required('cashier', 'manager')
def apply_order_discount():
    user_id = get_jwt_identity()
    """Cashier/Manager: Apply a discount to an order."""
    data = request.get_json()
    required_fields = ['order_id', 'discount_id']
    if not all(field in data for field in required_fields):
        return jsonify({'message': f'Missing required fields: {", ".join(required_fields)}'}), 400

    try:
        order = Order.query.get_or_404(data['order_id'])
        discount = Discount.query.get_or_404(data['discount_id'])
        
        if not discount.is_active:
            return jsonify({'message': 'Discount is not active'}), 400
        
        if discount.applies_to != 'order':
            return jsonify({'message': 'This discount can only be applied to individual items'}), 400
        
        # Check if discount already applied to this order
        existing_discount = OrderDiscount.query.filter_by(
            order_id=order.id, 
            discount_id=discount.id
        ).first()
        if existing_discount:
            return jsonify({'message': 'Discount already applied to this order'}), 400

        # Calculate discount amount
        if discount.discount_type == 'percentage':
            discount_amount_usd = order.subtotal_usd * (discount.discount_value / 100)
        else:  # fixed_amount
            discount_amount_usd = min(discount.discount_value, order.subtotal_usd)
        
        discount_amount_lbp = calculate_lbp_price(discount_amount_usd, order.exchange_rate_at_order_time)
        
        # Create discount record
        order_discount = OrderDiscount(  # type: ignore
            order_id=order.id,  # type: ignore[arg-type]
            discount_id=discount.id,  # type: ignore[arg-type]
            discount_name=discount.name,  # type: ignore[arg-type]
            discount_amount_usd=discount_amount_usd,  # type: ignore[arg-type]
            discount_amount_lbp=discount_amount_lbp,  # type: ignore[arg-type]
            applied_by_user_id=user_id  # type: ignore[arg-type]
        )
        
        # Update order totals
        order.discount_total_usd += discount_amount_usd
        order.discount_total_lbp_rounded += discount_amount_lbp
        order.final_total_usd = order.subtotal_usd - order.discount_total_usd
        order.final_total_lbp_rounded = order.subtotal_lbp_rounded - order.discount_total_lbp_rounded
        order.updated_at = datetime.datetime.utcnow()
        
        db.session.add(order_discount)
        db.session.commit()
        
        return jsonify({
            'message': 'Discount applied successfully',
            'discount_amount_usd': float(discount_amount_usd),
            'discount_amount_lbp': discount_amount_lbp,
            'new_final_total_usd': float(order.final_total_usd),
            'new_final_total_lbp_rounded': order.final_total_lbp_rounded
        }), 200
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Error applying order discount: {e}")
        return jsonify({'message': 'Could not apply discount.'}), 500


@discount_bp.route('/apply-item-discount', methods=['POST'])
@jwt_required()
@roles_required('cashier', 'manager')
def apply_item_discount():
    user_id = get_jwt_identity()
    """Cashier/Manager: Apply a discount to an order item."""
    data = request.get_json()
    required_fields = ['order_item_id', 'discount_id']
    if not all(field in data for field in required_fields):
        return jsonify({'message': f'Missing required fields: {", ".join(required_fields)}'}), 400

    try:
        order_item = OrderItem.query.get_or_404(data['order_item_id'])
        discount = Discount.query.get_or_404(data['discount_id'])
        
        if not discount.is_active:
            return jsonify({'message': 'Discount is not active'}), 400
        
        if discount.applies_to != 'item':
            return jsonify({'message': 'This discount can only be applied to entire orders'}), 400
        
        # Check if discount already applied to this item
        existing_discount = OrderItemDiscount.query.filter_by(
            order_item_id=order_item.id, 
            discount_id=discount.id
        ).first()
        if existing_discount:
            return jsonify({'message': 'Discount already applied to this item'}), 400

        # Calculate discount amount
        if discount.discount_type == 'percentage':
            discount_amount_usd = order_item.line_total_usd_at_order * (discount.discount_value / 100)
        else:  # fixed_amount
            discount_amount_usd = min(discount.discount_value, order_item.line_total_usd_at_order)
        
        discount_amount_lbp = calculate_lbp_price(discount_amount_usd, order_item.order.exchange_rate_at_order_time)
        
        # Create discount record
        item_discount = OrderItemDiscount(  # type: ignore
            order_item_id=order_item.id,  # type: ignore[arg-type]
            discount_id=discount.id,  # type: ignore[arg-type]
            discount_name=discount.name,  # type: ignore[arg-type]
            discount_amount_usd=discount_amount_usd,  # type: ignore[arg-type]
            discount_amount_lbp=discount_amount_lbp,  # type: ignore[arg-type]
            applied_by_user_id=user_id  # type: ignore[arg-type]
        )
        
        # Update item discount amounts
        order_item.discount_amount_usd += discount_amount_usd
        order_item.discount_amount_lbp += discount_amount_lbp
        
        # Update order totals
        order = order_item.order
        order.discount_total_usd += discount_amount_usd
        order.discount_total_lbp_rounded += discount_amount_lbp
        order.final_total_usd = order.subtotal_usd - order.discount_total_usd
        order.final_total_lbp_rounded = order.subtotal_lbp_rounded - order.discount_total_lbp_rounded
        order.updated_at = datetime.datetime.utcnow()
        
        db.session.add(item_discount)
        db.session.commit()
        
        return jsonify({
            'message': 'Item discount applied successfully',
            'discount_amount_usd': float(discount_amount_usd),
            'discount_amount_lbp': discount_amount_lbp,
            'new_order_total_usd': float(order.final_total_usd),
            'new_order_total_lbp_rounded': order.final_total_lbp_rounded
        }), 200
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Error applying item discount: {e}")
        return jsonify({'message': 'Could not apply discount.'}), 500 
