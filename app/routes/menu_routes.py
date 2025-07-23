from flask import Blueprint, request, jsonify, current_app
from flask_jwt_extended import jwt_required
from sqlalchemy.orm import joinedload
from app.models import db, MenuItem, Category, MenuItemOption, MenuItemOptionChoice, SystemSettings, Recipe, Ingredient
from app.schemas import MenuItemSchema
from app.utils.decorators import roles_required
from app.utils.helpers import get_current_exchange_rate
import datetime


menu_bp = Blueprint('menu_bp', __name__)

# --- System Settings for Dual Currency ---
@menu_bp.route('/system-settings', methods=['GET'])
@jwt_required()
@roles_required(['manager', 'cashier', 'courier']) # Allow all authenticated users to read settings
def get_system_settings():
    """Get system settings for dual currency support."""
    try:
        settings = SystemSettings.query.all()
        settings_dict = {s.setting_key: s.setting_value for s in settings}
        return jsonify(settings_dict)
    except Exception as e:
        current_app.logger.error(f"Error fetching system settings: {e}")
        return jsonify({'message': 'Failed to fetch system settings'}), 500

# --- Manager: Update System Settings ---
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
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Error updating system settings: {e}")
        return jsonify({'message': 'Failed to update settings'}), 500

# --- Active Menu with Categories ---
@menu_bp.route('/active', methods=['GET'])
@jwt_required()
@roles_required(['manager', 'cashier', 'courier'])
def get_active_menu():
    """Returns a structured menu with active items and categories."""
    try:
        # This logic is now duplicated from the courier endpoint, consider refactoring later
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

        settings = SystemSettings.query.filter_by(setting_key='usd_to_lbp_exchange_rate').first()
        settings_data = {
            'current_exchange_rate': settings.setting_value if settings else '90000'
        }

        return jsonify({
            'menu_items': items_data,
            'categories': categories_with_paths,
            'settings': settings_data
        })
    except Exception as e:
        current_app.logger.error(f"Error fetching active menu: {e}", exc_info=True)
        return jsonify({"message": "An error occurred while fetching the menu."}), 500


@menu_bp.route('/active-for-courier', methods=['GET'])
@jwt_required()
def get_active_menu_for_courier():
    """Returns a simplified, flattened menu structure for couriers/cashiers."""
    # This endpoint is now identical to /active, can be consolidated later.
    return get_active_menu()


