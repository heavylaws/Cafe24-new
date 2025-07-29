"""
Cafe24 POS System - Marshmallow Schemas

This module defines schemas for all models used in the Cafe24 POS system,
providing automatic serialization/deserialization for API endpoints.
"""

from flask_marshmallow import Marshmallow
from marshmallow import fields

from app.models import (
    Category,
    MenuItem,
    MenuItemOption,
    MenuItemOptionChoice,
    Order,
    OrderItem,
    User,
)

ma = Marshmallow()

def configure_ma(app):
    """Initialize Marshmallow with Flask app."""
    ma.init_app(app)


class UserSchema(ma.SQLAlchemyAutoSchema):
    """Schema for User model serialization."""

    class Meta:
        """Meta configuration for UserSchema."""
        model = User
        load_instance = True
        exclude = ("hashed_password",)


class CategorySchema(ma.SQLAlchemyAutoSchema):
    """Schema for Category model serialization."""

    class Meta:
        """Meta configuration for CategorySchema."""
        model = Category
        load_instance = True
        include_relationships = True


class MenuItemOptionChoiceSchema(ma.SQLAlchemyAutoSchema):
    """Schema for MenuItemOptionChoice model serialization."""

    price_usd = fields.Decimal(places=2, as_string=False)
    price_lbp_rounded = fields.Int(dump_only=True)

    class Meta:
        """Meta configuration for MenuItemOptionChoiceSchema."""
        model = MenuItemOptionChoice
        load_instance = True


class MenuItemOptionSchema(ma.SQLAlchemyAutoSchema):
    """Schema for MenuItemOption model serialization."""

    choices = fields.Nested(MenuItemOptionChoiceSchema, many=True)

    class Meta:
        """Meta configuration for MenuItemOptionSchema."""
        model = MenuItemOption
        load_instance = True
        include_relationships = True


class MenuItemSchema(ma.SQLAlchemyAutoSchema):
    """Schema for MenuItem model serialization."""

    category_name = fields.String(attribute="category.name", dump_only=True)
    category_id = fields.Int(required=False, allow_none=True)
    options = fields.Nested(MenuItemOptionSchema, many=True)
    price_lbp_rounded = fields.Int(dump_only=True)
    base_price_usd = fields.Decimal(places=2, as_string=False)

    class Meta:
        """Meta configuration for MenuItemSchema."""
        model = MenuItem
        load_instance = True
        include_relationships = True
        fields = (
            "id",
            "name",
            "description",
            "base_price_usd",
            "category_id",
            "is_active",
            "image_url",
            "created_at",
            "updated_at",
            "category_name",
            "options",
            "price_lbp_rounded",
        )
        partial = True


class OrderItemSchema(ma.SQLAlchemyAutoSchema):
    """Schema for OrderItem model serialization."""

    menu_item_name = fields.String(dump_only=True)
    chosen_option_choice_name = fields.String(dump_only=True)

    class Meta:
        """Meta configuration for OrderItemSchema."""
        model = OrderItem
        load_instance = True
        include_fk = True


class OrderSchema(ma.SQLAlchemyAutoSchema):
    """Schema for Order model serialization."""

    items = fields.Nested(OrderItemSchema, many=True)
    courier_username = fields.String(attribute="courier.username", dump_only=True)
    cashier_username = fields.String(
        attribute="cashier.username", dump_only=True, allow_none=True
    )

    class Meta:
        """Meta configuration for OrderSchema."""
        model = Order
        load_instance = True


class LoginSchema(ma.Schema):
    """Schema for login request validation."""

    username = fields.String(required=True)
    password = fields.String(required=True)


class CreateOrderSchema(ma.Schema):
    """Schema for order creation request validation."""

    customer_number = fields.String(allow_none=True)
    items = fields.List(fields.Nested(lambda: CreateOrderItemSchema()), required=True)


class CreateOrderItemSchema(ma.Schema):
    """Schema for order item creation request validation."""

    menu_item_id = fields.Int(required=True)
    quantity = fields.Int(load_default=1)
    chosen_option_choice_id = fields.Int(allow_none=True)


class CreateCategorySchema(ma.Schema):
    """Schema for category creation request validation."""

    name = fields.String(required=True)
    sort_order = fields.Int(load_default=0)


class CreateMenuItemSchema(ma.Schema):
    """Schema for menu item creation request validation."""

    name = fields.String(required=True)
    category_id = fields.Int(required=True)
    base_price_usd = fields.Decimal(required=True, places=2)
    description = fields.String(allow_none=True)
    is_active = fields.Boolean(load_default=True)
    image_url = fields.String(allow_none=True)


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