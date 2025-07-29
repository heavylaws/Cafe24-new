"""Marshmallow schemas for serialization and validation.

This module contains all Marshmallow schemas used for API serialization.
"""
from flask_marshmallow import Marshmallow
from marshmallow import fields
from app.models import (User, Category, MenuItem, MenuItemOption,
                       MenuItemOptionChoice, Order, OrderItem)

ma = Marshmallow()


def configure_ma(app):
    """Configure Marshmallow with Flask app."""
    ma.init_app(app)


class UserSchema(ma.SQLAlchemyAutoSchema):
    """User schema for API serialization."""
    class Meta:
        """User schema meta configuration."""
        model = User
        load_instance = True
        exclude = ("hashed_password",)


class CategorySchema(ma.SQLAlchemyAutoSchema):
    """Category schema for API serialization."""
    class Meta:
        """Category schema meta configuration."""
        model = Category
        load_instance = True
        include_relationships = True


class MenuItemOptionChoiceSchema(ma.SQLAlchemyAutoSchema):
    """Menu item option choice schema for API serialization."""
    price_usd = fields.Decimal(places=2, as_string=False)  # Ensure it's a number
    price_lbp_rounded = fields.Int(dump_only=True)

    class Meta:
        """MenuItemOptionChoice schema meta configuration."""
        model = MenuItemOptionChoice
        load_instance = True


class MenuItemOptionSchema(ma.SQLAlchemyAutoSchema):
    """Menu item option schema for API serialization."""
    choices = fields.Nested(MenuItemOptionChoiceSchema, many=True)

    class Meta:
        """MenuItemOption schema meta configuration."""
        model = MenuItemOption
        load_instance = True
        include_relationships = True


class MenuItemSchema(ma.SQLAlchemyAutoSchema):
    """Menu item schema for API serialization."""
    category_name = fields.String(attribute="category.name", dump_only=True)
    category_id = fields.Int(required=False, allow_none=True)
    options = fields.Nested(MenuItemOptionSchema, many=True)
    price_lbp_rounded = fields.Int(dump_only=True)
    base_price_usd = fields.Decimal(places=2, as_string=False)

    class Meta:
        """MenuItem schema meta configuration."""
        model = MenuItem
        load_instance = True
        include_relationships = True
        # Explicitly list fields to control serialization/deserialization
        fields = ('id', 'name', 'description', 'base_price_usd', 'category_id',
                 'is_active', 'image_url', 'created_at', 'updated_at',
                 'category_name', 'options', 'price_lbp_rounded')
        # Allow partial updates
        partial = True


class OrderItemSchema(ma.SQLAlchemyAutoSchema):
    """Order item schema for API serialization."""
    menu_item_name = fields.String(dump_only=True)
    chosen_option_choice_name = fields.String(dump_only=True)

    class Meta:
        """OrderItem schema meta configuration."""
        model = OrderItem
        load_instance = True
        include_fk = True

class OrderSchema(ma.SQLAlchemyAutoSchema):
    """Order schema for API serialization."""
    items = fields.Nested(OrderItemSchema, many=True)
    courier_username = fields.String(attribute="courier.username", dump_only=True)
    cashier_username = fields.String(attribute="cashier.username",
                                   dump_only=True, allow_none=True)

    class Meta:
        """Order schema meta configuration."""
        model = Order
        load_instance = True


class LoginSchema(ma.Schema):
    """Login schema for authentication."""
    username = fields.String(required=True)
    password = fields.String(required=True)

class CreateOrderSchema(ma.Schema):
    """Schema for creating new orders."""
    customer_number = fields.String(allow_none=True)  # Make it optional
    items = fields.List(fields.Nested('CreateOrderItemSchema'), required=True)


class CreateOrderItemSchema(ma.Schema):
    """Schema for creating order items."""
    menu_item_id = fields.Int(required=True)
    quantity = fields.Int(load_default=1)
    chosen_option_choice_id = fields.Int(allow_none=True)


class CreateCategorySchema(ma.Schema):
    """Schema for creating new categories."""
    name = fields.String(required=True)
    sort_order = fields.Int(load_default=0)


class CreateMenuItemSchema(ma.Schema):
    """Schema for creating new menu items."""
    name = fields.String(required=True)
    category_id = fields.Int(required=True)
    base_price_usd = fields.Decimal(required=True, places=2)
    description = fields.String(allow_none=True)
    is_active = fields.Boolean(load_default=True)
    image_url = fields.String(allow_none=True)  # Add this line to allow image_url

# Instantiate schemas
user_schema = UserSchema()
users_schema = UserSchema(many=True)

category_schema = CategorySchema()
categories_schema = CategorySchema(many=True)

menu_item_schema = MenuItemSchema()
menu_items_schema = MenuItemSchema(many=True)

order_schema = OrderSchema()
orders_schema = OrderSchema(many=True)

login_request_schema = LoginSchema()
create_order_request_schema = CreateOrderSchema()
create_category_request_schema = CreateCategorySchema()
create_menu_item_request_schema = CreateMenuItemSchema()

# pass is no longer needed
