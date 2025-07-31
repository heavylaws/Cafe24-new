"""Menu-related routes for the Cafe24 POS system."""

import datetime

from flask import Blueprint, current_app, jsonify, request
from flask_jwt_extended import jwt_required
from marshmallow import ValidationError
from sqlalchemy.orm import joinedload

from app import db
from app.models import (
    Category,
    Ingredient,
    MenuItem,
    MenuItemOption,
    MenuItemOptionChoice,
    Recipe,
    SystemSettings,
)
from app.schemas import CreateMenuItemSchema, MenuItemSchema
from app.utils.decorators import roles_required
from app.utils.helpers import get_current_exchange_rate

menu_bp = Blueprint("menu_bp", __name__)
menu_items_bp = Blueprint("menu_items_bp", __name__)

@menu_items_bp.before_request
def handle_options():
    """Handle OPTIONS requests for all menu_items_bp routes."""
    if request.method == "OPTIONS":
        # Get the URL path components
        path_parts = request.path.strip('/').split('/')
        # Extract the path parameters (like item_id)
        path_params = [p for p in path_parts if p.isdigit()]
        
        # Reconstruct the route pattern
        route_pattern = request.path
        for param in path_params:
            route_pattern = route_pattern.replace(f"/{param}", "/<id>")
            
        # Define allowed methods based on the route pattern
        if route_pattern.endswith("/<id>"):
            methods = ["GET", "PUT", "DELETE", "OPTIONS"]
        else:
            methods = ["GET", "POST", "OPTIONS"]
            
        return (
            "",
            204,
            {
                "Access-Control-Allow-Origin": "*",
                "Access-Control-Allow-Methods": ",".join(methods),
                "Access-Control-Allow-Headers": "Content-Type,Authorization",
            },
        )

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
@menu_items_bp.route("", methods=["POST", "OPTIONS"])
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

        if not isinstance(validated_data, dict):
            return jsonify({"message": "Internal server error: Invalid data type after validation"}), 500

        # Check if category exists
        category_id = validated_data.get("category_id")
        if not category_id:
            return jsonify({"message": "category_id is required"}), 400

        category = db.session.get(Category, category_id)
        if not category:
            return (
                jsonify(
                    {
                        "message": "Category not found",
                        "category_id": category_id,
                    }
                ),
                404,
            )

        # Create new menu item with validated data
        name = validated_data.get("name")
        base_price_usd = validated_data.get("base_price_usd")

        if not name or not base_price_usd:
            return jsonify({"message": "name and base_price_usd are required"}), 400

        menu_item = MenuItem(
            name=str(name).strip(),
            category_id=int(category_id),
            base_price_usd=base_price_usd,
            description=str(validated_data.get("description", "")).strip(),
            is_active=bool(validated_data.get("is_active", True)),
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


@menu_items_bp.route("", methods=["GET"])
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


@menu_items_bp.route("/<int:item_id>", methods=["GET"])
@jwt_required()
@roles_required(["manager"])
def get_menu_item(item_id):
    """Get a specific menu item by ID."""
    try:
        item = db.session.get(MenuItem, item_id)
        if not item:
            return jsonify({"message": "Menu item not found"}), 404

        menu_item_schema = MenuItemSchema()
        return jsonify(menu_item_schema.dump(item))
    except Exception as e:
        current_app.logger.error(f"Error fetching menu item {item_id}: {str(e)}")
        return jsonify({"message": "Failed to fetch menu item"}), 500


@menu_items_bp.route("/<int:item_id>", methods=["PUT"])
@jwt_required()
@roles_required(["manager"])
def update_menu_item(item_id):
    """Update a menu item."""
    try:
        item = db.session.get(MenuItem, item_id)
        if not item:
            return jsonify({"message": "Menu item not found"}), 404
        data = request.get_json()

        if not data:
            return jsonify({"message": "No input data provided"}), 400

        # Log the incoming data for debugging
        current_app.logger.info(f"Updating menu item {item_id} with data: {data}")

        # Update only the fields that were actually provided in the request
        protected_fields = ["id", "created_at", "updated_at"]
        update_fields = []
        
        # Get all the allowed fields from the model (not including relationships or computed fields)
        allowed_fields = {
            'category_id', 'name', 'description', 'base_price_usd', 'is_active', 'image_url'
        }
        
        for key, value in data.items():
            if key in protected_fields:
                current_app.logger.warning(f"Ignoring protected field in update: {key}")
                continue
            
            if key not in allowed_fields:
                current_app.logger.warning(f"Ignoring unknown field in update: {key}")
                continue
                
            if hasattr(item, key):
                # Basic validation - check that required fields aren't being set to None
                if key in ['category_id', 'base_price_usd'] and value is None:
                    current_app.logger.warning(f"Ignoring attempt to set required field {key} to None")
                    continue
                    
                setattr(item, key, value)
                update_fields.append(key)

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


@menu_items_bp.route("/<int:item_id>", methods=["DELETE"])
@jwt_required()
@roles_required(["manager"])
def delete_menu_item(item_id):
    """Delete a menu item."""
    try:
        item = db.session.get(MenuItem, item_id)
        if not item:
            return jsonify({"message": "Menu item not found"}), 404
        db.session.delete(item)
        db.session.commit()
        return jsonify({"message": "Menu item deleted successfully"})
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Error deleting menu item {item_id}: {str(e)}")
        return jsonify({"message": "Failed to delete menu item"}), 500


# --- Menu Item Options Endpoints (for manager dashboard) ---
@menu_items_bp.route("/<int:item_id>/options", methods=["GET"])
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
                "Access-Control-Allow-Methods": "GET,POST,PUT,DELETE,OPTIONS",
                "Access-Control-Allow-Headers": "Content-Type,Authorization",
            },
        )
    try:
        item = db.session.get(MenuItem, item_id)
        if not item:
            return jsonify({"message": "Menu item not found"}), 404
        
        options = MenuItemOption.query.filter_by(menu_item_id=item_id).order_by(MenuItemOption.sort_order).all()
        
        result = []
        for option in options:
            choices = MenuItemOptionChoice.query.filter_by(option_id=option.id).order_by(MenuItemOptionChoice.sort_order).all()
            result.append(
                {
                    "id": option.id,
                    "name": option.name,
                    "is_required": option.is_required,
                    "sort_order": option.sort_order,
                    "choices": [
                        {
                            "id": choice.id,
                            "choice_name": choice.name,
                            "price_modifier": float(choice.price_delta) if choice.price_delta is not None else 0.0,
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
            f"Error fetching options for menu item {item_id}: {str(e)}", exc_info=True
        )
        return jsonify({"message": "Failed to fetch options"}), 500


@menu_items_bp.route("/<int:item_id>/options", methods=["POST"])
@jwt_required()
@roles_required(["manager"])
def add_menu_item_option(item_id):
    """Add an option to a menu item with optional choices.
    
    Expected JSON payload:
    {
        "name": "Size",  # Required: The name of the option (e.g., "Size", "Milk Type", "Temperature")
        "is_required": true,  # Optional: Whether customers must select this option (default: false)
        "sort_order": 1,  # Optional: Display order (lower numbers appear first, default: 0)
        "choices": [  # Optional: Array of choices for this option
            {
                "choice_name": "Small",  # Required: Display name for the choice
                "price_modifier": 0.00,  # Optional: Price adjustment in USD (default: 0.00)
                "is_default": true,  # Optional: Whether this is the default selection (default: false)
                "sort_order": 1  # Optional: Display order within the option (default: 0)
            },
            {
                "choice_name": "Large", 
                "price_modifier": 1.50, 
                "is_default": false, 
                "sort_order": 2
            }
        ]
    }
    """
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({"message": "No input data provided"}), 400
            
        # Validate required fields
        if not data.get("name"):
            return jsonify({"message": "Option name is required"}), 400
            
        # Verify menu item exists
        menu_item = db.session.get(MenuItem, item_id)
        if not menu_item:
            return jsonify({"message": "Menu item not found"}), 404
        
        current_app.logger.info(f"Adding option to menu item {item_id}: {data}")
        
        # Create the option
        option = MenuItemOption(
            menu_item_id=item_id,
            name=data.get("name").strip(),
            is_required=data.get("is_required", False),
            sort_order=data.get("sort_order", 0),
        )
        db.session.add(option)
        db.session.flush()  # Get the option ID before creating choices
        
        # Add choices if provided
        choices_data = data.get("choices", [])
        created_choices = []
        
        # Validate that only one choice can be default
        default_count = sum(1 for choice in choices_data if choice.get("is_default", False))
        if default_count > 1:
            return jsonify({"message": "Only one choice can be marked as default per option"}), 400
        
        for choice_data in choices_data:
            if not choice_data.get("choice_name"):
                return jsonify({"message": "Choice name is required for all choices"}), 400
                
            # Validate price_modifier is a valid number
            price_modifier = choice_data.get("price_modifier", 0.00)
            try:
                price_modifier = float(price_modifier)
            except (ValueError, TypeError):
                return jsonify({"message": f"Invalid price_modifier '{price_modifier}' for choice '{choice_data.get('choice_name')}'. Must be a number."}), 400
            
            choice = MenuItemOptionChoice(
                option_id=option.id,
                name=choice_data.get("choice_name").strip(),
                price_delta=price_modifier,
                is_default=choice_data.get("is_default", False),
                sort_order=choice_data.get("sort_order", 0),
            )
            db.session.add(choice)
            created_choices.append({
                "id": choice.id,
                "choice_name": choice.name,
                "price_modifier": float(choice.price_delta),
                "is_default": choice.is_default,
                "sort_order": choice.sort_order
            })
        
        db.session.commit()
        
        result = {
            "message": "Option added successfully",
            "option": {
                "id": option.id,
                "name": option.name,
                "is_required": option.is_required,
                "sort_order": option.sort_order,
                "choices": created_choices
            }
        }
        
        current_app.logger.info(f"Successfully created option {option.id} with {len(created_choices)} choices")
        return jsonify(result), 201
        
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Error adding option for menu item {item_id}: {str(e)}", exc_info=True)
        return jsonify({"message": "Failed to add option", "error": str(e)}), 500


@menu_items_bp.route("/<int:item_id>/options/<int:option_id>/choices", methods=["POST"])
@jwt_required()
@roles_required(["manager"])
def add_option_choice(item_id, option_id):
    """Add a choice to an existing menu item option.
    
    Expected JSON payload:
    {
        "choice_name": "Medium",  # Required: Display name for the choice
        "price_modifier": 0.75,  # Optional: Price adjustment in USD (default: 0.00)
        "is_default": false,  # Optional: Whether this is the default selection (default: false)
        "sort_order": 2  # Optional: Display order within the option (default: 0)
    }
    """
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({"message": "No input data provided"}), 400
            
        # Validate required fields
        if not data.get("choice_name"):
            return jsonify({"message": "Choice name is required"}), 400
            
        # Verify menu item and option exist
        menu_item = db.session.get(MenuItem, item_id)
        if not menu_item:
            return jsonify({"message": "Menu item not found"}), 404
        option = db.session.query(MenuItemOption).filter_by(id=option_id, menu_item_id=item_id).first()
        if not option:
            return jsonify({"message": "Option not found"}), 404
        
        # Validate price_modifier is a valid number
        price_modifier = data.get("price_modifier", 0.00)
        try:
            price_modifier = float(price_modifier)
        except (ValueError, TypeError):
            return jsonify({"message": f"Invalid price_modifier '{price_modifier}'. Must be a number."}), 400
        
        # Check if setting as default and unset other defaults if needed
        is_default = data.get("is_default", False)
        if is_default:
            # Unset any existing default choices for this option
            existing_defaults = MenuItemOptionChoice.query.filter_by(option_id=option_id, is_default=True).all()
            for existing_choice in existing_defaults:
                existing_choice.is_default = False
        
        current_app.logger.info(f"Adding choice to option {option_id}: {data}")
        
        # Create the choice
        choice = MenuItemOptionChoice(
            option_id=option_id,
            name=data.get("choice_name").strip(),
            price_delta=price_modifier,
            is_default=is_default,
            sort_order=data.get("sort_order", 0),
        )
        db.session.add(choice)
        db.session.commit()
        
        result = {
            "message": "Choice added successfully",
            "choice": {
                "id": choice.id,
                "choice_name": choice.name,
                "price_modifier": float(choice.price_delta),
                "is_default": choice.is_default,
                "sort_order": choice.sort_order
            }
        }
        
        current_app.logger.info(f"Successfully created choice {choice.id} for option {option_id}")
        return jsonify(result), 201
        
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Error adding choice to option {option_id}: {str(e)}", exc_info=True)
        return jsonify({"message": "Failed to add choice", "error": str(e)}), 500


@menu_items_bp.route("/<int:item_id>/options/<int:option_id>", methods=["PUT"])
@jwt_required()
@roles_required(["manager"])
def update_menu_item_option(item_id, option_id):
    """Update a menu item option.
    
    Expected JSON payload:
    {
        "name": "Updated Size",  # Optional: The name of the option
        "is_required": true,  # Optional: Whether customers must select this option
        "sort_order": 2  # Optional: Display order
    }
    """
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({"message": "No input data provided"}), 400
            
        # Verify menu item and option exist
        menu_item = db.session.get(MenuItem, item_id)
        if not menu_item:
            return jsonify({"message": "Menu item not found"}), 404
        option = db.session.query(MenuItemOption).filter_by(id=option_id, menu_item_id=item_id).first()
        if not option:
            return jsonify({"message": "Option not found"}), 404
        
        current_app.logger.info(f"Updating option {option_id}: {data}")
        
        # Update allowed fields
        update_fields = []
        if "name" in data and data["name"]:
            option.name = data["name"].strip()
            update_fields.append("name")
            
        if "is_required" in data:
            option.is_required = bool(data["is_required"])
            update_fields.append("is_required")
            
        if "sort_order" in data:
            try:
                option.sort_order = int(data["sort_order"])
                update_fields.append("sort_order")
            except (ValueError, TypeError):
                return jsonify({"message": "sort_order must be a number"}), 400
        
        if not update_fields:
            return jsonify({"message": "No valid fields provided for update"}), 400
            
        option.updated_at = datetime.datetime.utcnow()
        db.session.commit()
        
        current_app.logger.info(f"Successfully updated option {option_id}. Updated fields: {', '.join(update_fields)}")
        return jsonify({
            "message": "Option updated successfully",
            "updated_fields": update_fields,
            "option": {
                "id": option.id,
                "name": option.name,
                "is_required": option.is_required,
                "sort_order": option.sort_order
            }
        })
        
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Error updating option {option_id}: {str(e)}", exc_info=True)
        return jsonify({"message": "Failed to update option", "error": str(e)}), 500


@menu_items_bp.route("/<int:item_id>/options/<int:option_id>/choices/<int:choice_id>", methods=["PUT"])
@jwt_required()
@roles_required(["manager"])
def update_option_choice(item_id, option_id, choice_id):
    """Update a menu item option choice.
    
    Expected JSON payload:
    {
        "choice_name": "Updated Choice",  # Optional: Display name for the choice
        "price_modifier": 1.25,  # Optional: Price adjustment in USD
        "is_default": true,  # Optional: Whether this is the default selection
        "sort_order": 3  # Optional: Display order within the option
    }
    """
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({"message": "No input data provided"}), 400
            
        # Verify menu item, option, and choice exist
        menu_item = db.session.get(MenuItem, item_id)
        if not menu_item:
            return jsonify({"message": "Menu item not found"}), 404
        option = db.session.query(MenuItemOption).filter_by(id=option_id, menu_item_id=item_id).first()
        if not option:
            return jsonify({"message": "Option not found"}), 404
        choice = db.session.query(MenuItemOptionChoice).filter_by(id=choice_id, option_id=option_id).first()
        if not choice:
            return jsonify({"message": "Choice not found"}), 404
        
        current_app.logger.info(f"Updating choice {choice_id}: {data}")
        
        # Update allowed fields
        update_fields = []
        if "choice_name" in data and data["choice_name"]:
            choice.name = data["choice_name"].strip()
            update_fields.append("choice_name")
            
        if "price_modifier" in data:
            try:
                choice.price_delta = float(data["price_modifier"])
                update_fields.append("price_modifier")
            except (ValueError, TypeError):
                return jsonify({"message": "price_modifier must be a number"}), 400
                
        if "is_default" in data:
            is_default = bool(data["is_default"])
            if is_default and not choice.is_default:
                # Unset any existing default choices for this option
                existing_defaults = MenuItemOptionChoice.query.filter_by(option_id=option_id, is_default=True).all()
                for existing_choice in existing_defaults:
                    existing_choice.is_default = False
            choice.is_default = is_default
            update_fields.append("is_default")
            
        if "sort_order" in data:
            try:
                choice.sort_order = int(data["sort_order"])
                update_fields.append("sort_order")
            except (ValueError, TypeError):
                return jsonify({"message": "sort_order must be a number"}), 400
        
        if not update_fields:
            return jsonify({"message": "No valid fields provided for update"}), 400
            
        choice.updated_at = datetime.datetime.utcnow()
        db.session.commit()
        
        current_app.logger.info(f"Successfully updated choice {choice_id}. Updated fields: {', '.join(update_fields)}")
        return jsonify({
            "message": "Choice updated successfully",
            "updated_fields": update_fields,
            "choice": {
                "id": choice.id,
                "choice_name": choice.name,
                "price_modifier": float(choice.price_delta),
                "is_default": choice.is_default,
                "sort_order": choice.sort_order
            }
        })
        
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Error updating choice {choice_id}: {str(e)}", exc_info=True)
        return jsonify({"message": "Failed to update choice", "error": str(e)}), 500


@menu_items_bp.route(
    "/<int:item_id>/options/<int:option_id>", methods=["DELETE"]
)
@jwt_required()
@roles_required(["manager"])
def delete_menu_item_option(item_id, option_id):
    """Delete a menu item option and all its choices."""
    if request.method == "OPTIONS":
        return (
            "",
            204,
            {
                "Access-Control-Allow-Origin": "*",
                "Access-Control-Allow-Methods": "DELETE,OPTIONS",
                "Access-Control-Allow-Headers": "Content-Type,Authorization",
            },
        )
    try:
        # Verify menu item and option exist
        menu_item = db.session.get(MenuItem, item_id)
        if not menu_item:
            return jsonify({"message": "Menu item not found"}), 404
        option = (
            db.session.query(MenuItemOption)
            .filter_by(id=option_id, menu_item_id=item_id)
            .first()
        )
        if not option:
            return jsonify({"message": "Option not found"}), 404

        current_app.logger.info(
            f"Deleting option {option_id} from menu item {item_id}"
        )

        db.session.delete(option)  # Cascade will delete all choices
        db.session.commit()

        return jsonify({"message": "Option deleted successfully"})

    except Exception as e:
        db.session.rollback()
        current_app.logger.error(
            f"Error deleting option {option_id}: {str(e)}", exc_info=True
        )
        return jsonify({"message": "Failed to delete option", "error": str(e)}), 500


@menu_items_bp.route(
    "/<int:item_id>/options/<int:option_id>/choices/<int:choice_id>",
    methods=["DELETE"],
)
@jwt_required()
@roles_required(["manager"])
def delete_option_choice(item_id, option_id, choice_id):
    """Delete a menu item option choice."""
    if request.method == "OPTIONS":
        return (
            "",
            204,
            {
                "Access-Control-Allow-Origin": "*",
                "Access-Control-Allow-Methods": "DELETE,OPTIONS",
                "Access-Control-Allow-Headers": "Content-Type,Authorization",
            },
        )
    try:
        # Verify menu item, option, and choice exist
        menu_item = db.session.get(MenuItem, item_id)
        if not menu_item:
            return jsonify({"message": "Menu item not found"}), 404
        option = (
            db.session.query(MenuItemOption)
            .filter_by(id=option_id, menu_item_id=item_id)
            .first()
        )
        if not option:
            return jsonify({"message": "Option not found"}), 404
        choice = (
            db.session.query(MenuItemOptionChoice)
            .filter_by(id=choice_id, option_id=option_id)
            .first()
        )
        if not choice:
            return jsonify({"message": "Choice not found"}), 404

        current_app.logger.info(f"Deleting choice {choice_id} from option {option_id}")

        db.session.delete(choice)
        db.session.commit()

        return jsonify({"message": "Choice deleted successfully"})

    except Exception as e:
        db.session.rollback()
        current_app.logger.error(
            f"Error deleting choice {choice_id}: {str(e)}", exc_info=True
        )
        return jsonify({"message": "Failed to delete choice", "error": str(e)}), 500
