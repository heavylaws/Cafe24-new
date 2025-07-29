# pyright: reportGeneralTypeIssues=false
import datetime
from decimal import Decimal, InvalidOperation

from flask import Blueprint, current_app, jsonify, request
from flask_jwt_extended import jwt_required

from app import db
from app.models import Ingredient, MenuItem, Recipe
from app.utils.decorators import roles_required


# Helper function to safely convert to float with default
def safe_float(value, default=0.0):
    if value is None or value == "":
        return default
    try:
        return float(value)
    except (ValueError, TypeError):
        return default


# Helper function to safely convert to Decimal with default
def safe_decimal(value, default="0.0"):
    if value is None or value == "":
        return Decimal(default)
    try:
        return Decimal(str(value))
    except (InvalidOperation, TypeError):
        return Decimal(default)


ingredient_bp = Blueprint("ingredient_bp", __name__)


@ingredient_bp.route("/ingredients", methods=["GET"])
@jwt_required()
@roles_required(["manager"])
def get_ingredients():
    """Get all ingredients for manager."""
    try:
        ingredients = (
            Ingredient.query.filter_by(is_active=True)
            .order_by(Ingredient.name.asc())
            .all()
        )
        result = []
        for ingredient in ingredients:
            reorder_level = (
                ingredient.reorder_level
                if ingredient.reorder_level is not None
                else ingredient.min_stock_alert
            )
            result.append(
                {
                    "id": ingredient.id,
                    "name": ingredient.name,
                    "unit": ingredient.unit,
                    "current_stock": ingredient.current_stock,
                    "min_stock_alert": ingredient.min_stock_alert,
                    "cost_per_unit_usd": (
                        float(ingredient.cost_per_unit_usd)
                        if ingredient.cost_per_unit_usd is not None
                        else None
                    ),
                    "reorder_level": ingredient.reorder_level,
                    "is_low_stock": ingredient.current_stock <= reorder_level,
                    "is_active": ingredient.is_active,
                    "created_at": ingredient.created_at.isoformat(),
                    "updated_at": ingredient.updated_at.isoformat(),
                }
            )
        return jsonify(result), 200
    except Exception as e:
        current_app.logger.error(f"Error fetching ingredients: {e}")
        return jsonify({"message": "Could not retrieve ingredients."}), 500


@ingredient_bp.route("/ingredients", methods=["POST"])
@jwt_required()
@roles_required(["manager"])
def create_ingredient(current_user):
    """Create a new ingredient."""
    try:
        data = request.get_json()
        if not data or not data.get("name") or not data.get("unit"):
            return jsonify({"message": "Name and unit are required"}), 400

        # Validate unit
        if data["unit"] not in ["kg", "liter", "piece"]:
            return jsonify({"message": 'Unit must be "kg", "liter", or "piece"'}), 400

        # Check if ingredient already exists
        existing = Ingredient.query.filter_by(name=data["name"]).first()
        if existing:
            return jsonify({"message": "Ingredient with this name already exists"}), 400

        ingredient = Ingredient(  # type: ignore
            name=data["name"].strip(),  # type: ignore[arg-type]
            unit=data["unit"],  # type: ignore[arg-type]
            current_stock=safe_float(data.get("current_stock")),
            min_stock_alert=safe_float(data.get("min_stock_alert")),
            cost_per_unit_usd=safe_decimal(data.get("cost_per_unit_usd")),
            reorder_level=safe_float(data.get("reorder_level")),
            is_active=data.get("is_active", True),  # type: ignore[arg-type]
        )

        db.session.add(ingredient)
        db.session.commit()

        return (
            jsonify(
                {
                    "message": "Ingredient created successfully",
                    "ingredient": {
                        "id": ingredient.id,
                        "name": ingredient.name,
                        "unit": ingredient.unit,
                        "current_stock": ingredient.current_stock,
                        "min_stock_alert": ingredient.min_stock_alert,
                        "cost_per_unit_usd": (
                            float(ingredient.cost_per_unit_usd)
                            if ingredient.cost_per_unit_usd is not None
                            else None
                        ),
                        "reorder_level": ingredient.reorder_level,
                        "is_active": ingredient.is_active,
                    },
                }
            ),
            201,
        )

    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Error creating ingredient: {e}", exc_info=True)
        return jsonify({"message": "Could not create ingredient."}), 500


@ingredient_bp.route("/ingredients/<int:ingredient_id>", methods=["PUT"])
@jwt_required()
@roles_required(["manager"])
def update_ingredient(current_user, ingredient_id):
    """Update an existing ingredient."""
    try:
        ingredient = Ingredient.query.get_or_404(ingredient_id)
        data = request.get_json()

        if not data:
            return jsonify({"message": "No data provided"}), 400

        # Update fields if provided
        if "name" in data:
            # Check if new name conflicts with existing ingredient
            existing = Ingredient.query.filter(
                Ingredient.name == data["name"].strip(), Ingredient.id != ingredient_id
            ).first()
            if existing:
                return (
                    jsonify({"message": "Ingredient with this name already exists"}),
                    400,
                )
            ingredient.name = data["name"].strip()

        if "unit" in data:
            if data["unit"] not in ["kg", "liter", "piece"]:
                return (
                    jsonify({"message": 'Unit must be "kg", "liter", or "piece"'}),
                    400,
                )
            ingredient.unit = data["unit"]

        if "current_stock" in data:
            ingredient.current_stock = safe_float(data["current_stock"])

        if "min_stock_alert" in data:
            ingredient.min_stock_alert = safe_float(data["min_stock_alert"])

        if "cost_per_unit_usd" in data:
            ingredient.cost_per_unit_usd = safe_decimal(data["cost_per_unit_usd"])

        if "reorder_level" in data:
            ingredient.reorder_level = safe_float(data["reorder_level"])

        if "is_active" in data:
            ingredient.is_active = data["is_active"]

        ingredient.updated_at = datetime.datetime.utcnow()
        db.session.commit()

        return (
            jsonify(
                {
                    "message": "Ingredient updated successfully",
                    "ingredient": {
                        "id": ingredient.id,
                        "name": ingredient.name,
                        "unit": ingredient.unit,
                        "current_stock": ingredient.current_stock,
                        "min_stock_alert": ingredient.min_stock_alert,
                        "cost_per_unit_usd": (
                            float(ingredient.cost_per_unit_usd)
                            if ingredient.cost_per_unit_usd is not None
                            else None
                        ),
                        "reorder_level": ingredient.reorder_level,
                        "is_active": ingredient.is_active,
                    },
                }
            ),
            200,
        )

    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Error updating ingredient: {e}")
        return jsonify({"message": "Could not update ingredient."}), 500


@ingredient_bp.route("/ingredients/<int:ingredient_id>", methods=["DELETE"])
@jwt_required()
@roles_required(["manager"])
def delete_ingredient(current_user, ingredient_id):
    """Soft delete an ingredient (set is_active to False)."""
    try:
        ingredient = Ingredient.query.get_or_404(ingredient_id)
        ingredient.is_active = False
        ingredient.updated_at = datetime.datetime.utcnow()
        db.session.commit()

        return jsonify({"message": "Ingredient deactivated successfully"}), 200

    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Error deleting ingredient: {e}")
        return jsonify({"message": "Could not delete ingredient."}), 500


@ingredient_bp.route("/ingredients/low-stock", methods=["GET"])
@jwt_required()
@roles_required(["manager"])
def get_low_stock_ingredients(current_user):
    """Get ingredients with low stock."""
    try:
        ingredients = (
            Ingredient.query.filter(Ingredient.is_active.is_(True))
            .order_by(Ingredient.name.asc())
            .all()
        )
        low_stock = [
            ing
            for ing in ingredients
            if ing.current_stock
            <= (
                ing.reorder_level
                if ing.reorder_level is not None
                else ing.min_stock_alert
            )
        ]

        result = []
        for ingredient in low_stock:
            result.append(
                {
                    "id": ingredient.id,
                    "name": ingredient.name,
                    "unit": ingredient.unit,
                    "current_stock": ingredient.current_stock,
                    "min_stock_alert": ingredient.min_stock_alert,
                    "cost_per_unit_usd": (
                        float(ingredient.cost_per_unit_usd)
                        if ingredient.cost_per_unit_usd is not None
                        else None
                    ),
                    "reorder_level": ingredient.reorder_level,
                    "shortage": (
                        ingredient.reorder_level
                        if ingredient.reorder_level is not None
                        else ingredient.min_stock_alert
                    )
                    - ingredient.current_stock,
                }
            )

        return jsonify(result), 200

    except Exception as e:
        current_app.logger.error(f"Error fetching low stock ingredients: {e}")
        return jsonify({"message": "Could not retrieve low stock ingredients."}), 500
