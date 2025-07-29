"""Menu-related routes for the Cafe24 POS system."""

import datetime

from flask import Blueprint, current_app, jsonify, request
from flask_jwt_extended import jwt_required
from marshmallow import ValidationError
from sqlalchemy.orm import joinedload

from app.models import (
    Category,
    Ingredient,
    MenuItem,
    MenuItemOption,
    MenuItemOptionChoice,
    Recipe,
    SystemSettings,
    db,
)
from app.schemas import CreateMenuItemSchema, MenuItemSchema
from app.utils.decorators import roles_required
from app.utils.helpers import get_current_exchange_rate

menu_bp = Blueprint("menu_bp", __name__)

# --- System Settings for Dual Currency ---
@menu_bp.route("/system-settings", methods=["GET"])
@jwt_required()
@roles_required(
    ["manager", "cashier", "courier"]
)  # Allow all authenticated users to read settings
def get_system_settings():
    """Get system settings for dual currency support."""
    try:
        settings = SystemSettings.query.all()
        settings_dict = {s.setting_key: s.setting_value for s in settings}
        return jsonify(settings_dict)
    except Exception as e:
        current_app.logger.error(f"Error fetching system settings: {e}")
        return jsonify({"message": "Failed to fetch system settings"}), 500


# --- Manager: Update System Settings ---
@menu_bp.route("/system-settings", methods=["PUT"])
@jwt_required()
@roles_required(["manager"])
def update_system_settings():
    """Manager: Update system settings."""
    try:
        data = request.get_json()
        if not data:
            return jsonify({"message": "No data provided"}), 400

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
        return jsonify({"message": "Settings updated successfully"}), 200
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Error updating system settings: {e}")
        return jsonify({"message": "Failed to update settings"}), 500


# --- Active Menu with Categories ---
@menu_bp.route("/active", methods=["GET"])
@jwt_required()
@roles_required(["manager", "cashier", "courier"])
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

        categories_with_paths = [
            {"id": c.id, "name": c.name, "path": get_path(c.id)} for c in all_categories
        ]

        active_items = (
            MenuItem.query.options(
                joinedload(MenuItem.options).joinedload(MenuItemOption.choices)
            )
            .filter_by(is_active=True)
            .all()
        )
        items_schema = MenuItemSchema(many=True)
        items_data = items_schema.dump(active_items)

        settings = SystemSettings.query.filter_by(
            setting_key="usd_to_lbp_exchange_rate"
        ).first()
        settings_data = {
            "current_exchange_rate": settings.setting_value if settings else "90000"
        }

        return jsonify(
            {
                "menu_items": items_data,
                "categories": categories_with_paths,
                "settings": settings_data,
            }
        )
    except Exception as e:
        current_app.logger.error(f"Error fetching active menu: {e}", exc_info=True)
        return jsonify({"message": "An error occurred while fetching the menu."}), 500


@menu_bp.route("/active-for-courier", methods=["GET"])
@jwt_required()
def get_active_menu_for_courier():
    """Returns a simplified, flattened menu structure for couriers/cashiers."""
    # This endpoint is now identical to /active, can be consolidated later.
    return get_active_menu()


# --- Menu Item Management ---
@menu_bp.route("/items", methods=["POST"])
@jwt_required()
@roles_required(["manager"])
def create_menu_item():
    """Create a new menu item.

    Expected JSON payload:
    {
        "name": "Item Name",
        "category_id": 1,  # Must be an existing category ID
        "base_price_usd": 2.50,  # Must be a number with 2 decimal places
        "description": "Optional description",
        "is_active": true  # Optional, defaults to true
    }
    """
    try:
        data = request.get_json()
        if not data:
            return jsonify({"message": "No input data provided"}), 400

        # Log the incoming request data for debugging
        current_app.logger.info(f"Received menu item data: {data}")

        # Manually validate required fields first
        required_fields = ["name", "category_id", "base_price_usd"]
        missing_fields = [field for field in required_fields if field not in data]
        if missing_fields:
            return (
                jsonify(
                    {
                        "message": "Missing required fields",
                        "missing_fields": missing_fields,
                    }
                ),
                400,
            )

        # Convert base_price_usd to float if it's a string
        if isinstance(data.get("base_price_usd"), str):
            try:
                data["base_price_usd"] = float(data["base_price_usd"])
            except (ValueError, TypeError):
                return (
                    jsonify(
                        {
                            "message": "Invalid price format. Must be a number.",
                            "field": "base_price_usd",
                            "value": data.get("base_price_usd"),
                        }
                    ),
                    400,
                )

        # Validate input using CreateMenuItemSchema
        try:
            validated_data = CreateMenuItemSchema().load(data)
        except ValidationError as err:
            current_app.logger.error(f"Validation error: {err.messages}")
            return jsonify({"message": "Validation error", "errors": err.messages}), 400

        # Check if category exists
        category = Category.query.get(validated_data.get("category_id"))
        if not category:
            return (
                jsonify(
                    {
                        "message": "Category not found",
                        "category_id": validated_data.get("category_id"),
                    }
                ),
                404,
            )

        # Create new menu item with validated data
        menu_item = MenuItem(
            name=validated_data["name"].strip(),
            category_id=validated_data["category_id"],
            base_price_usd=validated_data["base_price_usd"],
            description=validated_data.get("description", "").strip(),
            is_active=validated_data.get("is_active", True),
        )

        db.session.add(menu_item)
        db.session.commit()

        # Return the created menu item using MenuItemSchema
        menu_item_data = MenuItemSchema().dump(menu_item)
        current_app.logger.info(f"Successfully created menu item: {menu_item_data}")

        return (
            jsonify(
                {"message": "Menu item created successfully", "data": menu_item_data}
            ),
            201,
        )

    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Error creating menu item: {str(e)}", exc_info=True)
        return jsonify({"message": "Failed to create menu item", "error": str(e)}), 500


@menu_bp.route("/items", methods=["GET"])
@jwt_required()
@roles_required(["manager"])
def list_menu_items():
    """List all menu items for management."""
    try:
        items = MenuItem.query.options(
            joinedload(MenuItem.options).joinedload(MenuItemOption.choices)
        ).all()
        menu_item_schema = MenuItemSchema(many=True)
        return jsonify(menu_item_schema.dump(items))
    except Exception as e:
        current_app.logger.error(f"Error listing menu items: {str(e)}")
        return jsonify({"message": "Failed to fetch menu items"}), 500


@menu_bp.route("/items/<int:item_id>", methods=["GET"])
@jwt_required()
@roles_required(["manager"])
def get_menu_item(item_id):
    """Get a specific menu item by ID."""
    try:
        item = MenuItem.query.options(
            joinedload(MenuItem.options).joinedload(MenuItemOption.choices)
        ).get_or_404(item_id)

        menu_item_schema = MenuItemSchema()
        return jsonify(menu_item_schema.dump(item))
    except Exception as e:
        current_app.logger.error(f"Error fetching menu item {item_id}: {str(e)}")
        return jsonify({"message": "Failed to fetch menu item"}), 500


@menu_bp.route("/items/<int:item_id>", methods=["PUT"])
@jwt_required()
@roles_required(["manager"])
def update_menu_item(item_id):
    """Update a menu item."""
    try:
        item = MenuItem.query.get_or_404(item_id)
        data = request.get_json()

        if not data:
            return jsonify({"message": "No input data provided"}), 400

        # Log the incoming data for debugging
        current_app.logger.info(f"Updating menu item {item_id} with data: {data}")

        # Validate input
        try:
            menu_item_schema = MenuItemSchema(partial=True)
            validated_data = menu_item_schema.load(data)
            # Ensure validated_data is a dict (Marshmallow may return a model instance)
            if not isinstance(validated_data, dict):
                validated_data = menu_item_schema.dump(validated_data)
        except ValidationError as err:
            current_app.logger.error(
                f"Validation error updating menu item {item_id}: {err.messages}"
            )
            return jsonify({"message": "Validation error", "errors": err.messages}), 400

        # Update fields
        protected_fields = ["id", "created_at", "updated_at"]
        update_fields = []
        for key, value in validated_data.items():
            if key in protected_fields:
                continue
            if hasattr(item, key):
                setattr(item, key, value)
                update_fields.append(key)
            else:
                current_app.logger.warning(f"Ignoring unknown field in update: {key}")

        if not update_fields:
            return jsonify({"message": "No valid fields provided for update"}), 400

        item.updated_at = datetime.datetime.utcnow()
        db.session.commit()

        current_app.logger.info(
            f"Successfully updated menu item {item_id}. Updated fields: {', '.join(update_fields)}"
        )
        return jsonify(
            {
                "message": "Menu item updated successfully",
                "updated_fields": update_fields,
            }
        )

    except Exception as e:
        db.session.rollback()
        error_msg = f"Error updating menu item {item_id}: {str(e)}"
        current_app.logger.error(error_msg, exc_info=True)
        return jsonify({"message": "Failed to update menu item", "error": str(e)}), 500


@menu_bp.route("/items/<int:item_id>", methods=["DELETE"])
@jwt_required()
@roles_required(["manager"])
def delete_menu_item(item_id):
    """Delete a menu item."""
    try:
        item = MenuItem.query.get_or_404(item_id)
        db.session.delete(item)
        db.session.commit()
        return jsonify({"message": "Menu item deleted successfully"})
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Error deleting menu item {item_id}: {str(e)}")
        return jsonify({"message": "Failed to delete menu item"}), 500


# --- Menu Item Options Endpoints (for manager dashboard) ---
@menu_bp.route("/menu-items/<int:item_id>/options", methods=["GET", "OPTIONS"])
@jwt_required()
@roles_required(["manager"])
def get_menu_item_options(item_id):
    """Get all options for a menu item."""
    if request.method == "OPTIONS":
        return (
            "",
            204,
            {
                "Access-Control-Allow-Origin": "*",
                "Access-Control-Allow-Methods": "GET,POST,OPTIONS",
                "Access-Control-Allow-Headers": "Content-Type,Authorization",
            },
        )
    try:
        item = MenuItem.query.options(
            joinedload(MenuItem.options).joinedload(MenuItemOption.choices)
        ).get_or_404(item_id)
        options = MenuItemOption.query.filter_by(menu_item_id=item_id).all()
        result = []
        for option in options:
            choices = MenuItemOptionChoice.query.filter_by(option_id=option.id).all()
            result.append(
                {
                    "id": option.id,
                    "name": option.name,
                    "is_required": option.is_required,
                    "sort_order": option.sort_order,
                    "choices": [
                        {
                            "id": choice.id,
                            "name": choice.name,
                            "price_delta": choice.price_delta,
                            "is_default": choice.is_default,
                            "sort_order": choice.sort_order,
                        }
                        for choice in choices
                    ],
                }
            )
        return jsonify(result), 200
    except Exception as e:
        current_app.logger.error(
            f"Error fetching options for menu item {item_id}: {str(e)}"
        )
        return jsonify({"message": "Failed to fetch options"}), 500


@menu_bp.route("/menu-items/<int:item_id>/options", methods=["POST"])
@jwt_required()
@roles_required(["manager"])
def add_menu_item_option(item_id):
    """Add an option to a menu item."""
    try:
        data = request.get_json()
        option = MenuItemOption(
            menu_item_id=item_id,
            name=data.get("name"),
            is_required=data.get("is_required", False),
            sort_order=data.get("sort_order", 0),
        )
        db.session.add(option)
        db.session.commit()
        return jsonify({"message": "Option added", "option_id": option.id}), 201
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(
            f"Error adding option for menu item {item_id}: {str(e)}"
        )
        return jsonify({"message": "Failed to add option"}), 500


# --- SHIM: Register /api/v1/menu-items/<id>/options at top-level for frontend compatibility ---

def register_menu_item_options_shim(app):
    app.add_url_rule(
        "/api/v1/menu-items/<int:item_id>/options",
        view_func=get_menu_item_options,
        methods=["GET", "OPTIONS"],
    )
    app.add_url_rule(
        "/api/v1/menu-items/<int:item_id>/options",
        view_func=add_menu_item_option,
        methods=["POST"],
    )