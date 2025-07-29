"""
Marshmallow schemas for API serialization and deserialization.

This module defines schemas for all models used in the Cafe24 POS system,
providing automatic serialization/deserialization for API endpoints.
"""

from marshmallow import fields
from flask_marshmallow import Marshmallow

from app.models import (
    Category, MenuItem, MenuItemOption, MenuItemOptionChoice,
    Order, OrderItem, User
)

ma = Marshmallow()

def configure_ma(app):
    """Initialize Marshmallow with the Flask app."""
    ma.init_app(app)


class UserSchema(ma.SQLAlchemyAutoSchema):
    """Schema for User model serialization."""
    class Meta:
        model = User
        load_instance = True
        exclude = ("hashed_password",)


class CategorySchema(ma.SQLAlchemyAutoSchema):
    """Schema for Category model serialization."""
    class Meta:
        model = Category
        load_instance = True
        include_relationships = True


class MenuItemOptionChoiceSchema(ma.SQLAlchemyAutoSchema):
    """Schema for MenuItemOptionChoice model serialization."""
    price_usd = fields.Decimal(places=2, as_string=False)  # Ensure it's a number
    price_lbp_rounded = fields.Int(dump_only=True)

    class Meta:
        model = MenuItemOptionChoice
        load_instance = True

class MenuItemOptionSchema(ma.SQLAlchemyAutoSchema):
    choices = fields.Nested(MenuItemOptionChoiceSchema, many=True)
    class Meta:
        model = MenuItemOption
        load_instance = True
        include_relationships = True

class MenuItemSchema(ma.SQLAlchemyAutoSchema):
    category_name = fields.String(attribute="category.name", dump_only=True)
    category_id = fields.Int(required=False, allow_none=True)  # Make category_id optional for updates
    options = fields.Nested(MenuItemOptionSchema, many=True)
    price_lbp_rounded = fields.Int(dump_only=True)
    base_price_usd = fields.Decimal(places=2, as_string=False)  # Ensure it's a number

    class Meta:
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
    menu_item_name = fields.String(dump_only=True)
    chosen_option_choice_name = fields.String(dump_only=True)
    class Meta:
        model = OrderItem
        load_instance = True
        include_fk = True

class OrderSchema(ma.SQLAlchemyAutoSchema):
    items = fields.Nested(OrderItemSchema, many=True)
    courier_username = fields.String(attribute="courier.username", dump_only=True)
    cashier_username = fields.String(attribute="cashier.username", dump_only=True, allow_none=True)
    class Meta:
        model = Order
        load_instance = True

class LoginSchema(ma.Schema):
    username = fields.String(required=True)
    password = fields.String(required=True)

class CreateOrderSchema(ma.Schema):
    customer_number = fields.String(allow_none=True)  # Make it optional
    items = fields.List(fields.Nested(lambda: CreateOrderItemSchema()), required=True)

class CreateOrderItemSchema(ma.Schema):
    menu_item_id = fields.Int(required=True)
    quantity = fields.Int(load_default=1)
    chosen_option_choice_id = fields.Int(allow_none=True)


class CreateCategorySchema(ma.Schema):
    name = fields.String(required=True)
    sort_order = fields.Int(load_default=0)

class CreateMenuItemSchema(ma.Schema):
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
