"""
Menu management routes for the Cafe24 POS system.

This module handles all menu-related API endpoints including menu items,
categories, options, and system settings management.
"""
import datetime

from flask import Blueprint, request, jsonify, current_app
from flask_jwt_extended import jwt_required
from marshmallow import ValidationError
from sqlalchemy.orm import joinedload

from app.models import (
    db, MenuItem, Category, MenuItemOption, SystemSettings
)
from app.schemas import MenuItemSchema, CreateMenuItemSchema
from app.utils.decorators import roles_required

menu_bp = Blueprint('menu_bp', __name__)


@menu_bp.route('/system-settings', methods=['GET'])
@jwt_required()
@roles_required(['manager', 'cashier', 'courier'])
def get_system_settings():
    """Get system settings for dual currency support."""
    try:
        settings = SystemSettings.query.all()
        settings_dict = {s.setting_key: s.setting_value for s in settings}
        return jsonify(settings_dict)
    except Exception as exc:
        current_app.logger.error(f"Error fetching system settings: {exc}")
        return jsonify({'message': 'Failed to fetch system settings'}), 500


@menu_bp.route('/system-settings', methods=['PUT'])
@jwt_required()
@roles_required(['manager'])
def update_system_settings():
    """Manager: Update system settings."""
    try:
        data = request.get_json()
        if not data:
            return jsonify({'message': 'No data provided'}), 400

        for key, value in data.items():
            setting = SystemSettings.query.filter_by(setting_key=key).first()
            if setting:
                setting.setting_value = str(value)
                setting.updated_at = datetime.datetime.utcnow()
            else:
                # Create new setting if it doesn't exist
                new_setting = SystemSettings(setting_key=key, setting_value=str(value))
                db.session.add(new_setting)

        db.session.commit()
        return jsonify({'message': 'Settings updated successfully'}), 200
    except Exception as exc:
        db.session.rollback()
        current_app.logger.error(f"Error updating system settings: {exc}")
        return jsonify({'message': 'Failed to update settings'}), 500


@menu_bp.route('/active', methods=['GET'])
@jwt_required()
@roles_required(['manager', 'cashier', 'courier'])
def get_active_menu():
    """Returns a structured menu with active items and categories."""
    try:
        all_categories = Category.query.order_by(Category.name).all()

        memo = {}
        def get_path(cat_id):
            if cat_id in memo:
                return memo[cat_id]
            if cat_id is None:
                return ""

            category = next((c for c in all_categories if c.id == cat_id), None)
            if not category:
                return ""

            parent_path = get_path(category.parent_id)
            path = f"{parent_path} > {category.name}" if parent_path else category.name
            memo[cat_id] = path
            return path

        categories_with_paths = [{
            "id": c.id,
            "name": c.name,
            "path": get_path(c.id)
        } for c in all_categories]

        active_items = MenuItem.query.options(
            joinedload(MenuItem.options).joinedload(MenuItemOption.choices)
        ).filter_by(is_active=True).all()
        items_schema = MenuItemSchema(many=True)
        items_data = items_schema.dump(active_items)

        settings = SystemSettings.query.filter_by(
            setting_key='usd_to_lbp_exchange_rate'
        ).first()
        settings_data = {
            'current_exchange_rate': settings.setting_value if settings else '90000'
        }

        return jsonify({
            'menu_items': items_data,
            'categories': categories_with_paths,
            'settings': settings_data
        })
    except Exception as exc:
        current_app.logger.error(f"Error fetching active menu: {exc}", exc_info=True)
        return jsonify({"message": "An error occurred while fetching the menu."}), 500


@menu_bp.route('/active-for-courier', methods=['GET'])
@jwt_required()
def get_active_menu_for_courier():
    """Returns a simplified, flattened menu structure for couriers/cashiers."""
    return get_active_menu()


@menu_bp.route('/items', methods=['POST'])
@jwt_required()
@roles_required(['manager'])
def create_menu_item():
    """Create a new menu item."""
    try:
        data = request.get_json()
        if not data:
            return jsonify({'message': 'No input data provided'}), 400

        current_app.logger.info(f"Received menu item data: {data}")

        # Manually validate required fields first
        required_fields = ['name', 'category_id', 'base_price_usd']
        missing_fields = [field for field in required_fields if field not in data]
        if missing_fields:
            return jsonify({
                'message': 'Missing required fields',
                'missing_fields': missing_fields
            }), 400

        # Convert base_price_usd to float if it's a string
        if isinstance(data.get('base_price_usd'), str):
            try:
                data['base_price_usd'] = float(data['base_price_usd'])
            except (ValueError, TypeError):
                return jsonify({
                    'message': 'Invalid price format. Must be a number.',
                    'field': 'base_price_usd',
                    'value': data.get('base_price_usd')
                }), 400

        # Validate input using CreateMenuItemSchema
        try:
            validated_data = CreateMenuItemSchema().load(data)
        except ValidationError as err:
            return jsonify({
                'message': 'Validation failed',
                'errors': err.messages
            }), 400

        # Check if category exists
        category = Category.query.get(validated_data['category_id'])
        if not category:
            return jsonify({
                'message': 'Invalid category_id',
                'category_id': validated_data['category_id']
            }), 400

        # Check for duplicate name in same category
        existing_item = MenuItem.query.filter_by(
            name=validated_data['name'],
            category_id=validated_data['category_id']
        ).first()
        if existing_item:
            return jsonify({
                'message': 'Menu item with this name already exists in this category',
                'existing_item_id': existing_item.id
            }), 400

        # Create the menu item
        menu_item = MenuItem(**validated_data)
        db.session.add(menu_item)
        db.session.commit()

        # Return the created item
        item_schema = MenuItemSchema()
        result = item_schema.dump(menu_item)
        return jsonify(result), 201

    except Exception as exc:
        db.session.rollback()
        current_app.logger.error(f"Error creating menu item: {exc}", exc_info=True)
        return jsonify({'message': 'Failed to create menu item'}), 500


@menu_bp.route('/items', methods=['GET'])
@jwt_required()
@roles_required(['manager'])
def list_menu_items():
    """List all menu items for management."""
    try:
        items = MenuItem.query.options(
            joinedload(MenuItem.category),
            joinedload(MenuItem.options).joinedload(MenuItemOption.choices)
        ).all()
        items_schema = MenuItemSchema(many=True)
        result = items_schema.dump(items)
        return jsonify(result)
    except Exception as exc:
        current_app.logger.error(f"Error listing menu items: {exc}")
        return jsonify({'message': 'Failed to list menu items'}), 500


@menu_bp.route('/items/<int:item_id>', methods=['GET'])
@jwt_required()
@roles_required(['manager'])
def get_menu_item(item_id):
    """Get a specific menu item by ID."""
    try:
        item = MenuItem.query.options(
            joinedload(MenuItem.options).joinedload(MenuItemOption.choices)
        ).get(item_id)
        if not item:
            return jsonify({'message': 'Menu item not found'}), 404

        item_schema = MenuItemSchema()
        result = item_schema.dump(item)
        return jsonify(result)
    except Exception as exc:
        current_app.logger.error(f"Error getting menu item: {exc}")
        return jsonify({'message': 'Failed to get menu item'}), 500


@menu_bp.route('/items/<int:item_id>', methods=['PUT'])
@jwt_required()
@roles_required(['manager'])
def update_menu_item(item_id):
    """Update a menu item."""
    try:
        item = MenuItem.query.get(item_id)
        if not item:
            return jsonify({'message': 'Menu item not found'}), 404

        data = request.get_json()
        if not data:
            return jsonify({'message': 'No data provided'}), 400

        # Update only provided fields
        for key, value in data.items():
            if hasattr(item, key) and value is not None:
                setattr(item, key, value)

        item.updated_at = datetime.datetime.utcnow()
        db.session.commit()

        item_schema = MenuItemSchema()
        result = item_schema.dump(item)
        return jsonify(result)
    except Exception as exc:
        db.session.rollback()
        current_app.logger.error(f"Error updating menu item: {exc}")
        return jsonify({'message': 'Failed to update menu item'}), 500


@menu_bp.route('/items/<int:item_id>', methods=['DELETE'])
@jwt_required()
@roles_required(['manager'])
def delete_menu_item(item_id):
    """Delete a menu item."""
    try:
        item = MenuItem.query.get(item_id)
        if not item:
            return jsonify({'message': 'Menu item not found'}), 404

        db.session.delete(item)
        db.session.commit()
        return jsonify({'message': 'Menu item deleted successfully'})
    except Exception as exc:
        db.session.rollback()
        current_app.logger.error(f"Error deleting menu item: {exc}")
        return jsonify({'message': 'Failed to delete menu item'}), 500


@menu_bp.route('/items/<int:item_id>/options', methods=['GET', 'POST', 'OPTIONS'])
@jwt_required()
@roles_required(['manager'])
def get_menu_item_options(item_id):
    """Get all options for a menu item."""
    if request.method == 'OPTIONS':
        return '', 200

    try:
        item = MenuItem.query.get(item_id)
        if not item:
            return jsonify({'message': 'Menu item not found'}), 404

        if request.method == 'GET':
            options = MenuItemOption.query.filter_by(menu_item_id=item_id).all()
            return jsonify([{
                'id': opt.id,
                'option_name': opt.option_name,
                'choices': [{
                    'id': choice.id,
                    'choice_name': choice.choice_name,
                    'price_modifier_usd': float(choice.price_modifier_usd),
                    'is_default': choice.is_default
                } for choice in opt.choices]
            } for opt in options])

        elif request.method == 'POST':
            data = request.get_json()
            if not data or 'option_name' not in data:
                return jsonify({'message': 'option_name is required'}), 400

            option = MenuItemOption(
                menu_item_id=item_id,
                option_name=data['option_name']
            )
            db.session.add(option)
            db.session.commit()

            return jsonify({
                'id': option.id,
                'option_name': option.option_name,
                'menu_item_id': option.menu_item_id
            }), 201

    except Exception as exc:
        db.session.rollback()
        current_app.logger.error(f"Error with menu item options: {exc}")
        return jsonify({'message': 'Failed to process options request'}), 500


@menu_bp.route('/items/<int:item_id>/options', methods=['POST'])
@jwt_required()
@roles_required(['manager'])
def add_menu_item_option(item_id):
    """Add an option to a menu item."""
    try:
        item = MenuItem.query.get(item_id)
        if not item:
            return jsonify({'message': 'Menu item not found'}), 404

        data = request.get_json()
        if not data or 'option_name' not in data:
            return jsonify({'message': 'option_name is required'}), 400

        option = MenuItemOption(
            menu_item_id=item_id,
            option_name=data['option_name']
        )
        db.session.add(option)
        db.session.commit()

        return jsonify({
            'id': option.id,
            'option_name': option.option_name,
            'menu_item_id': option.menu_item_id
        }), 201

    except Exception as exc:
        db.session.rollback()
        current_app.logger.error(f"Error adding option: {exc}")
        return jsonify({'message': 'Failed to add option'}), 500


def register_menu_item_options_shim(app):
    """Register the menu item options shim route."""
    @app.route('/api/v1/menu-item-options', methods=['POST'])
    @jwt_required()
    @roles_required(['manager'])
    def create_menu_item_option_shim():
        """Shim endpoint for creating menu item options."""
        try:
            data = request.get_json()
            if not data:
                return jsonify({'message': 'No data provided'}), 400

            required_fields = ['menu_item_id', 'option_name']
            for field in required_fields:
                if field not in data:
                    return jsonify({'message': f'{field} is required'}), 400

            option = MenuItemOption(
                menu_item_id=data['menu_item_id'],
                option_name=data['option_name']
            )
            db.session.add(option)
            db.session.commit()

            return jsonify({
                'id': option.id,
                'menu_item_id': option.menu_item_id,
                'option_name': option.option_name
            }), 201

        except Exception as exc:
            db.session.rollback()
            current_app.logger.error(f"Error in option shim: {exc}")
            return jsonify({'message': 'Failed to create option'}), 500
