# pyright: reportGeneralTypeIssues=false
from flask import Blueprint, request, jsonify, current_app
from app.models import db, Ingredient, StockAdjustment, StockInvoice, StockInvoiceItem, Recipe, User, Unit
from flask_jwt_extended import jwt_required, get_jwt_identity
from app.utils.decorators import roles_required
import datetime

stock_bp = Blueprint('stock_bp', __name__)

@stock_bp.route('/adjust', methods=['POST'])
@jwt_required()
@roles_required(['manager'])
def adjust_stock():
    """Adjust stock for an ingredient with required reason."""
    try:
        data = request.get_json()
        if not data or not all(k in data for k in ['ingredient_id', 'quantity_change', 'reason']):
            return jsonify({'message': 'ingredient_id, quantity_change, and reason are required'}), 400
        
        ingredient = Ingredient.query.get_or_404(data['ingredient_id'])
        change_amount = float(data['quantity_change'])
        reason = data['reason'].strip()
        
        if not reason:
            return jsonify({'message': 'Reason cannot be empty'}), 400
        
        # Calculate new stock
        new_stock = ingredient.current_stock + change_amount
        if new_stock < 0:
            return jsonify({'message': 'Adjustment would result in negative stock'}), 400
        
        # Get current user ID from JWT
        current_user_id = get_jwt_identity()
        
        # Create adjustment record
        adjustment = StockAdjustment(
            ingredient_id=ingredient.id,
            change_amount=change_amount,
            reason=reason,
            user_id=current_user_id
        )
        
        # Update ingredient stock
        ingredient.current_stock = new_stock
        ingredient.updated_at = datetime.datetime.utcnow()
        
        db.session.add(adjustment)
        db.session.commit()
        
        return jsonify({
            'message': 'Stock adjusted successfully',
            'ingredient': {
                'id': ingredient.id,
                'name': ingredient.name,
                'current_stock': ingredient.current_stock
            }
        }), 200
        
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Error adjusting stock: {str(e)}")
        return jsonify({'message': 'Could not adjust stock'}), 500

@stock_bp.route('/adjustments', methods=['GET'])
@jwt_required()
@roles_required(['manager'])
def get_stock_adjustments():
    """Get all stock adjustments with ingredient and user details."""
    try:
        # Get all adjustments with related data
        adjustments = db.session.query(
            StockAdjustment,
            Ingredient.name.label('ingredient_name'),
            Unit.abbreviation.label('ingredient_unit'),
            User.full_name.label('user_name')
        ).join(
            Ingredient, StockAdjustment.ingredient_id == Ingredient.id
        ).join(
            Unit, Ingredient.unit_id == Unit.id
        ).join(
            User, StockAdjustment.user_id == User.id
        ).order_by(
            StockAdjustment.created_at.desc()
        ).all()
        
        # Format the response
        result = []
        for adj, ing_name, ing_unit, user_name in adjustments:
            # Determine adjustment type based on reason
            adj_type = 'manual'
            if 'restock' in adj.reason.lower():
                adj_type = 'restock'
            elif 'waste' in adj.reason.lower() or 'loss' in adj.reason.lower():
                adj_type = 'waste'
                
            result.append({
                'id': adj.id,
                'ingredient_id': adj.ingredient_id,
                'ingredient_name': ing_name,
                'ingredient_unit': ing_unit,
                'quantity_change': adj.change_amount,
                'adjustment_type': adj_type,
                'reason': adj.reason,
                'user_id': adj.user_id,
                'user_name': user_name,
                'created_at': adj.created_at.isoformat()
            })
            
        return jsonify(result), 200
        
    except Exception as e:
        current_app.logger.error(f"Error fetching stock adjustments: {str(e)}")
        return jsonify({'message': 'Could not retrieve stock adjustments'}), 500

@stock_bp.route('/invoice', methods=['POST'])
@jwt_required()
@roles_required(['manager'])
def create_stock_invoice():
    """Create a new stock invoice for restocking."""
    try:
        data = request.get_json()
        if not data or 'items' not in data:
            return jsonify({'message': 'Items list is required'}), 400
        
        if not isinstance(data['items'], list) or not data['items']:
            return jsonify({'message': 'Items must be a non-empty list'}), 400
        
        # Get current user ID from JWT
        current_user_id = get_jwt_identity()
        
        # Create invoice
        invoice = StockInvoice(
            supplier=data.get('supplier', '').strip(),
            date=datetime.datetime.strptime(data.get('date', datetime.date.today().isoformat()), '%Y-%m-%d').date(),
            user_id=current_user_id
        )
        
        db.session.add(invoice)
        db.session.flush()  # Get invoice ID
        
        total_cost = 0
        
        # Process invoice items
        for item_data in data['items']:
            if not all(k in item_data for k in ['ingredient_id', 'quantity', 'unit_price']):
                return jsonify({'message': 'Each item must have ingredient_id, quantity, and unit_price'}), 400
            
            ingredient = Ingredient.query.get(item_data['ingredient_id'])
            if not ingredient or not ingredient.is_active:
                return jsonify({'message': f'Ingredient with ID {item_data["ingredient_id"]} not found or inactive'}), 400
            
            quantity = float(item_data['quantity'])
            unit_price = float(item_data['unit_price'])
            
            if quantity <= 0 or unit_price < 0:
                return jsonify({'message': 'Quantity must be positive and unit_price must be non-negative'}), 400
            
            total_price = quantity * unit_price
            total_cost += total_price
            
            # Create invoice item
            invoice_item = StockInvoiceItem(
                invoice_id=invoice.id,
                ingredient_id=ingredient.id,
                quantity=quantity,
                unit_price=unit_price,
                total_price=total_price
            )
            
            # Update ingredient stock
            ingredient.current_stock += quantity
            ingredient.updated_at = datetime.datetime.utcnow()
            
            db.session.add(invoice_item)
        
        db.session.commit()
        
        return jsonify({
            'message': 'Stock invoice created successfully',
            'invoice': {
                'id': invoice.id,
                'supplier': invoice.supplier,
                'date': invoice.date.isoformat(),
                'total_cost': total_cost,
                'items_count': len(data['items'])
            }
        }), 201
        
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Error creating stock invoice: {e}")
        return jsonify({'message': 'Could not create stock invoice.'}), 500

@stock_bp.route('/invoices', methods=['GET'])
@jwt_required()
@roles_required(['manager'])
def get_stock_invoices():
    """Get all stock invoices with optional filtering."""
    try:
        days = request.args.get('days', type=int, default=30)
        
        # Get current user ID from JWT
        current_user_id = get_jwt_identity()
        
        # Filter by date range
        cutoff_date = datetime.datetime.utcnow() - datetime.timedelta(days=days)
        invoices = StockInvoice.query.filter(
            StockInvoice.created_at >= cutoff_date
        ).order_by(StockInvoice.created_at.desc()).all()
        
        result = []
        for invoice in invoices:
            total_cost = sum(item.total_price for item in invoice.items)
            result.append({
                'id': invoice.id,
                'supplier': invoice.supplier,
                'date': invoice.date.isoformat(),
                'total_cost': float(total_cost),
                'items_count': len(invoice.items),
                'created_at': invoice.created_at.isoformat()
            })
        
        return jsonify(result), 200
        
    except Exception as e:
        current_app.logger.error(f"Error fetching stock invoices: {e}")
        return jsonify({'message': 'Could not retrieve stock invoices.'}), 500

@stock_bp.route('/invoice/<int:invoice_id>', methods=['GET'])
@jwt_required()
@roles_required(['manager'])
def get_stock_invoice_details(invoice_id):
    """Get detailed information about a specific stock invoice."""
    try:
        invoice = StockInvoice.query.get_or_404(invoice_id)
        
        items = []
        total_cost = 0
        for item in invoice.items:
            items.append({
                'ingredient_id': item.ingredient_id,
                'ingredient_name': item.ingredient.name,
                'unit': item.ingredient.unit,
                'quantity': item.quantity,
                'unit_price': float(item.unit_price),
                'total_price': float(item.total_price)
            })
            total_cost += item.total_price
        
        result = {
            'id': invoice.id,
            'supplier': invoice.supplier,
            'date': invoice.date.isoformat(),
            'total_cost': float(total_cost),
            'created_at': invoice.created_at.isoformat(),
            'items': items
        }
        
        return jsonify(result), 200
        
    except Exception as e:
        current_app.logger.error(f"Error fetching stock invoice details: {e}")
        return jsonify({'message': 'Could not retrieve stock invoice details.'}), 500

@stock_bp.route('/decrement', methods=['POST'])
@jwt_required()
@roles_required(['system'])
def decrement_stock_for_order():
    """Decrement ingredient stock based on order items and recipes."""
    try:
        data = request.get_json()
        if not data or 'order_items' not in data:
            return jsonify({'message': 'Order items are required'}), 400
        
        insufficient_stock = []
        
        # First, check if all items have sufficient stock
        for order_item in data['order_items']:
            menu_item_id = order_item['menu_item_id']
            quantity = order_item['quantity']
            
            recipes = Recipe.query.filter_by(menu_item_id=menu_item_id).all()
            
            for recipe in recipes:
                required_amount = recipe.amount * quantity
                if recipe.ingredient.current_stock < required_amount:
                    insufficient_stock.append({
                        'menu_item_id': menu_item_id,
                        'ingredient_name': recipe.ingredient.name,
                        'required': required_amount,
                        'available': recipe.ingredient.current_stock,
                        'unit': recipe.ingredient.unit
                    })
        
        if insufficient_stock:
            return jsonify({
                'success': False,
                'message': 'Insufficient stock for order',
                'insufficient_stock': insufficient_stock
            }), 400
        
        # If all items have sufficient stock, proceed with decrementing
        for order_item in data['order_items']:
            menu_item_id = order_item['menu_item_id']
            quantity = order_item['quantity']
            
            recipes = Recipe.query.filter_by(menu_item_id=menu_item_id).all()
            
            for recipe in recipes:
                required_amount = recipe.amount * quantity
                recipe.ingredient.current_stock -= required_amount
                recipe.ingredient.updated_at = datetime.datetime.utcnow()
        
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'Stock decremented successfully'
        }), 200
        
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Error decrementing stock: {e}")
        return jsonify({'message': 'Could not decrement stock.'}), 500
