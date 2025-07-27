"""
Marshmallow schemas for the Cafe24 POS system.

This module defines all serialization and validation schemas for API endpoints,
handling data transformation between JSON and Python objects.
"""
from flask_marshmallow import Marshmallow
from marshmallow import fields

from app.models import (
    Category, Discount, Ingredient, MenuItem, MenuItemOption,
    MenuItemOptionChoice, Order, OrderItem, Recipe, SystemSettings,
    Unit, User
)

ma = Marshmallow()


class UserSchema(ma.SQLAlchemyAutoSchema):
    """Schema for User model serialization."""
    
    class Meta:
        """Meta configuration for UserSchema."""
        model = User
        load_instance = True
        exclude = ('hashed_password',)


class CategorySchema(ma.SQLAlchemyAutoSchema):
    """Schema for Category model serialization."""
    
    class Meta:
        """Meta configuration for CategorySchema."""
        model = Category
        load_instance = True


class MenuItemSchema(ma.SQLAlchemyAutoSchema):
    """Schema for MenuItem model serialization."""
    
    # Custom fields for better API responses
    category_name = fields.Str(dump_only=True)
    category_id = fields.Int(required=True, allow_none=False)
    
    class Meta:
        """Meta configuration for MenuItemSchema."""
        model = MenuItem
        load_instance = True
        include_fk = True


class CreateMenuItemSchema(ma.Schema):
    """Schema for creating new menu items with validation."""
    
    name = fields.Str(required=True, validate=lambda x: len(x.strip()) > 0)
    category_id = fields.Int(required=True)
    base_price_usd = fields.Decimal(required=True, places=2)
    description = fields.Str(allow_none=True)
    is_active = fields.Bool(allow_none=True)


class MenuItemOptionSchema(ma.SQLAlchemyAutoSchema):
    """Schema for MenuItemOption model serialization."""
    
    class Meta:
        """Meta configuration for MenuItemOptionSchema."""
        model = MenuItemOption
        load_instance = True


class MenuItemOptionChoiceSchema(ma.SQLAlchemyAutoSchema):
    """Schema for MenuItemOptionChoice model serialization."""
    
    class Meta:
        """Meta configuration for MenuItemOptionChoiceSchema."""
        model = MenuItemOptionChoice
        load_instance = True


class IngredientSchema(ma.SQLAlchemyAutoSchema):
    """Schema for Ingredient model serialization."""
    
    unit_name = fields.Method("get_unit_name")
    unit_abbreviation = fields.Method("get_unit_abbreviation")
    
    class Meta:
        """Meta configuration for IngredientSchema."""
        model = Ingredient
        load_instance = True
    
    def get_unit_name(self, obj):
        """Get the unit name for the ingredient."""
        return obj.unit_info.name if obj.unit_info else None
    
    def get_unit_abbreviation(self, obj):
        """Get the unit abbreviation for the ingredient."""
        return obj.unit_info.abbreviation if obj.unit_info else None


class RecipeSchema(ma.SQLAlchemyAutoSchema):
    """Schema for Recipe model serialization."""
    
    class Meta:
        """Meta configuration for RecipeSchema."""
        model = Recipe
        load_instance = True


class DiscountSchema(ma.SQLAlchemyAutoSchema):
    """Schema for Discount model serialization."""
    
    class Meta:
        """Meta configuration for DiscountSchema."""
        model = Discount
        load_instance = True


class OrderSchema(ma.SQLAlchemyAutoSchema):
    """Schema for Order model serialization."""
    
    class Meta:
        """Meta configuration for OrderSchema."""
        model = Order
        load_instance = True


class OrderItemSchema(ma.SQLAlchemyAutoSchema):
    """Schema for OrderItem model serialization."""
    
    class Meta:
        """Meta configuration for OrderItemSchema."""
        model = OrderItem
        load_instance = True


class SystemSettingsSchema(ma.SQLAlchemyAutoSchema):
    """Schema for SystemSettings model serialization."""
    
    class Meta:
        """Meta configuration for SystemSettingsSchema."""
        model = SystemSettings
        load_instance = True


class UnitSchema(ma.SQLAlchemyAutoSchema):
    """Schema for Unit model serialization."""
    
    class Meta:
        """Meta configuration for UnitSchema."""
        model = Unit
        load_instance = True
