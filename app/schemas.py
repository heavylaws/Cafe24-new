from flask_marshmallow import Marshmallow
from marshmallow import fields
from app.models import User, Category, MenuItem, MenuItemOption, MenuItemOptionChoice, Order, OrderItem

ma = Marshmallow()

def configure_ma(app):
    ma.init_app(app)

class UserSchema(ma.SQLAlchemyAutoSchema):
    class Meta:
        model = User
        load_instance = True
        exclude = ("hashed_password",)

class CategorySchema(ma.SQLAlchemyAutoSchema):
    class Meta:
        model = Category
        load_instance = True
        include_relationships = True

class MenuItemOptionChoiceSchema(ma.SQLAlchemyAutoSchema):
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
    options = fields.Nested(MenuItemOptionSchema, many=True)
    price_lbp_rounded = fields.Int(dump_only=True)
    base_price_usd = fields.Decimal(places=2, as_string=False)  # Ensure it's a number

    class Meta:
        model = MenuItem
        load_instance = True
        include_relationships = True


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
