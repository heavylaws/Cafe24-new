"""
Database models for the Cafe24 POS system.

This module defines all SQLAlchemy models used in the application including
users, menu items, orders, and system settings.
"""

import datetime
import enum
from typing import Optional

from sqlalchemy import Enum, Index, MetaData
from werkzeug.security import check_password_hash, generate_password_hash
from app import db

# --- Enums ---
class UserRole(enum.Enum):
    courier = "courier"
    cashier = "cashier"
    barista = "barista"
    manager = "manager"

class DiscountType(enum.Enum):
    percentage = "percentage"
    fixed_amount = "fixed_amount"

class AppliesTo(enum.Enum):
    order = "order"
    item = "item"

class OrderStatus(enum.Enum):
    pending_payment = "pending_payment"
    paid_waiting_preparation = "paid_waiting_preparation"
    preparing = "preparing"
    ready_for_pickup = "ready_for_pickup"
    completed = "completed"
    cancelled = "cancelled"

class PaymentMethod(enum.Enum):
    cash = "cash"
    card = "card"
    mixed = "mixed"

class PaymentStatus(enum.Enum):
    pending = "pending"
    paid = "paid"
    refunded = "refunded"
    failed = "failed"
    partially_refunded = "partially_refunded"

# --- Models ---
class User(db.Model):
    __tablename__ = "users"
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(100), unique=True, nullable=False, index=True)
    hashed_password = db.Column(db.String(255), nullable=False)
    full_name = db.Column(db.String(255))
    role = db.Column(Enum(UserRole), nullable=False)
    is_active = db.Column(db.Boolean, default=True, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.datetime.utcnow)
    updated_at = db.Column(
        db.DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow
    )

    def set_password(self, password):
        """Set the user's password hash."""
        self.hashed_password = generate_password_hash(password)

    def check_password(self, password):
        """Check if the provided password matches the user's password."""
        return check_password_hash(self.hashed_password, password)

    def __repr__(self):
        return f"<User {self.username} ({self.role.value})>"

class Category(db.Model):
    __tablename__ = "categories"
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(255), nullable=False)
    parent_id = db.Column(db.Integer, db.ForeignKey("categories.id"), nullable=True)
    sort_order = db.Column(db.Integer, default=0)
    created_at = db.Column(db.DateTime, default=datetime.datetime.utcnow)
    updated_at = db.Column(
        db.DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow
    )

    menu_items = db.relationship("MenuItem", backref="category", lazy=True)
    children = db.relationship(
        "Category", backref=db.backref("parent", remote_side=[id]), lazy="dynamic"
    )

    __table_args__ = (
        db.UniqueConstraint("parent_id", "name", name="_parent_category_name_uc"),
    )

    def __init__(
        self, name: str, sort_order: int = 0, parent_id: Optional[int] = None, **kwargs
    ):
        super().__init__(**kwargs)
        self.name = name
        self.sort_order = sort_order
        self.parent_id = parent_id

    def __repr__(self):
        """Return string representation of Category."""
        return f"<Category {self.parent.name if self.parent else ''} / {self.name}>"

class MenuItem(db.Model):
    __tablename__ = "menuitems"
    id = db.Column(db.Integer, primary_key=True)
    category_id = db.Column(
        db.Integer, db.ForeignKey("categories.id"), nullable=False, index=True
    )
    name = db.Column(db.String(255), nullable=False)
    description = db.Column(db.Text)
    base_price_usd = db.Column(db.Numeric(10, 2), nullable=False, default=0.00)
    is_active = db.Column(db.Boolean, default=True, nullable=False)
    image_url = db.Column(db.String(255))
    created_at = db.Column(db.DateTime, default=datetime.datetime.utcnow)
    updated_at = db.Column(
        db.DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow
    )

    options = db.relationship(
        "MenuItemOption",
        backref="menu_item",
        lazy="select",
        cascade="all, delete-orphan",
    )
    order_items = db.relationship("OrderItem", backref="menu_item", lazy=True)

    __table_args__ = (
        db.UniqueConstraint("category_id", "name", name="_category_item_name_uc"),
    )

    def __init__(self, name: str, category_id: int, base_price_usd: float, description: Optional[str] = None, is_active: bool = True, image_url: Optional[str] = None, **kwargs):
        super().__init__(**kwargs)
        self.name = name
        self.category_id = category_id
        self.base_price_usd = base_price_usd
        self.description = description
        self.is_active = is_active
        self.image_url = image_url

    def __repr__(self):
        """Return string representation of MenuItem."""
        return f"<MenuItem {self.name}>"

class MenuItemOption(db.Model):
    __tablename__ = "menuitemoptions"
    id = db.Column(db.Integer, primary_key=True)
    menu_item_id = db.Column(db.Integer, db.ForeignKey("menuitems.id"), nullable=False)
    name = db.Column(db.String(255), nullable=False)
    is_required = db.Column(db.Boolean, default=False)
    sort_order = db.Column(db.Integer, default=0)
    created_at = db.Column(db.DateTime, default=datetime.datetime.utcnow)
    updated_at = db.Column(
        db.DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow
    )

    choices = db.relationship(
        "MenuItemOptionChoice",
        backref="option",
        lazy="select",
        cascade="all, delete-orphan",
    )

    def __init__(self, menu_item_id, name, is_required=False, sort_order=0):
        self.menu_item_id = menu_item_id
        self.name = name
        self.is_required = is_required
        self.sort_order = sort_order


class MenuItemOptionChoice(db.Model):
    __tablename__ = "menuitemoptionchoices"
    id = db.Column(db.Integer, primary_key=True)
    option_id = db.Column(
        db.Integer, db.ForeignKey("menuitemoptions.id"), nullable=False
    )
    name = db.Column(db.String(255), nullable=False)
    price_delta = db.Column(db.Numeric(10, 2), default=0.00)
    is_default = db.Column(db.Boolean, default=False)
    sort_order = db.Column(db.Integer, default=0)
    created_at = db.Column(db.DateTime, default=datetime.datetime.utcnow)
    updated_at = db.Column(
        db.DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow
    )

    def __init__(self, option_id, name, price_delta=0.00, is_default=False, sort_order=0):
        self.option_id = option_id
        self.name = name
        self.price_delta = price_delta
        self.is_default = is_default
        self.sort_order = sort_order


class Ingredient(db.Model):
    __tablename__ = "ingredients"
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(255), unique=True, nullable=False)
    unit = db.Column(db.String(10), nullable=False)
    current_stock = db.Column(db.Float, nullable=False, default=0.0)
    min_stock_alert = db.Column(db.Float, nullable=False, default=0.0)
    cost_per_unit_usd = db.Column(db.Numeric(10, 2), nullable=True, default=0.00)
    reorder_level = db.Column(db.Float, nullable=True, default=0.0)
    is_active = db.Column(db.Boolean, default=True, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.datetime.utcnow)
    updated_at = db.Column(
        db.DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow
    )

    def __repr__(self):
        """Return string representation of Ingredient."""
        return f"<Ingredient {self.name} ({self.unit}) - Stock: {self.current_stock}>"

class Recipe(db.Model):
    __tablename__ = "recipes"
    id = db.Column(db.Integer, primary_key=True)
    menu_item_id = db.Column(db.Integer, db.ForeignKey("menuitems.id"), nullable=False)
    ingredient_id = db.Column(
        db.Integer, db.ForeignKey("ingredients.id"), nullable=False
    )
    amount = db.Column(db.Float, nullable=False)

    ingredient = db.relationship("Ingredient")

    def __repr__(self):
        """Return string representation of Recipe."""
        return (f"<Recipe MenuItem {self.menu_item_id} needs {self.amount} "
                f"of Ingredient {self.ingredient_id}>")

class Discount(db.Model):
    __tablename__ = "discounts"
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(255), nullable=False)
    description = db.Column(db.Text)
    discount_type = db.Column(Enum(DiscountType), nullable=False)
    discount_value = db.Column(db.Numeric(10, 2), nullable=False)
    applies_to = db.Column(Enum(AppliesTo), nullable=False)
    is_active = db.Column(db.Boolean, default=True, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.datetime.utcnow)
    updated_at = db.Column(
        db.DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow
    )

    def __repr__(self):
        """Return string representation of Discount."""
        discount_unit = '%' if self.discount_type == DiscountType.percentage else 'USD'
        return f"<Discount {self.name} - {self.discount_value}{discount_unit}>"

class Order(db.Model):
    __tablename__ = "orders"
    id = db.Column(db.Integer, primary_key=True)
    order_number = db.Column(db.String(20), unique=True, nullable=False)
    courier_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    customer_number = db.Column(db.String(20), nullable=True)  # Can be anonymous
    status = db.Column(
        Enum(OrderStatus), nullable=False, default=OrderStatus.pending_payment
    )
    payment_status = db.Column(
        Enum(PaymentStatus), nullable=False, default=PaymentStatus.pending
    )
    payment_method = db.Column(Enum(PaymentMethod), nullable=True)
    subtotal_usd = db.Column(db.Numeric(10, 2), nullable=False)
    subtotal_lbp_rounded = db.Column(db.Integer, nullable=False)
    discount_total_usd = db.Column(db.Numeric(10, 2), nullable=False, default=0.00)
    discount_total_lbp_rounded = db.Column(db.Integer, nullable=False, default=0)
    final_total_usd = db.Column(db.Numeric(10, 2), nullable=False)
    final_total_lbp_rounded = db.Column(db.Integer, nullable=False)
    exchange_rate_at_order_time = db.Column(db.Numeric(15, 2), nullable=True)
    notes = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.datetime.utcnow)
    updated_at = db.Column(
        db.DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow
    )

    order_items = db.relationship("OrderItem", backref="order", lazy=True)

    def __repr__(self):
        """Return string representation of Order."""
        return f"<Order {self.id} by User {self.courier_id}>"

class OrderItem(db.Model):
    __tablename__ = "orderitems"
    id = db.Column(db.Integer, primary_key=True)
    order_id = db.Column(db.Integer, db.ForeignKey("orders.id"), nullable=False)
    menu_item_id = db.Column(db.Integer, db.ForeignKey("menuitems.id"), nullable=False)
    menu_item_name = db.Column(db.String(255), nullable=False)
    quantity = db.Column(db.Integer, nullable=False, default=1)
    chosen_option_choice_id = db.Column(
        db.Integer, db.ForeignKey("menuitemoptionchoices.id"), nullable=True
    )
    chosen_option_choice_name = db.Column(db.String(255), nullable=True)
    unit_price_usd_at_order = db.Column(db.Numeric(10, 2), nullable=False)
    unit_price_lbp_rounded_at_order = db.Column(db.Integer, nullable=False)
    line_total_usd_at_order = db.Column(db.Numeric(10, 2), nullable=False)
    line_total_lbp_rounded_at_order = db.Column(db.Integer, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.datetime.utcnow)
    updated_at = db.Column(
        db.DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow
    )

    def __repr__(self):
        """Return string representation of OrderItem."""
        return f"<OrderItem {self.id} for Order {self.order_id}>"

# --- Placeholders for missing models to resolve import errors ---
class SystemSettings(db.Model):
    __tablename__ = "systemsettings"
    id = db.Column(db.Integer, primary_key=True)
    setting_key = db.Column(db.String(255), unique=True, nullable=False)
    setting_value = db.Column(db.String(255), nullable=False)

    def __init__(self, setting_key: str, setting_value: str, **kwargs):
        super().__init__(**kwargs)
        self.setting_key = setting_key
        self.setting_value = setting_value

class StockAdjustment(db.Model):
    __tablename__ = "stockadjustments"
    id = db.Column(db.Integer, primary_key=True)
    ingredient_id = db.Column(
        db.Integer, db.ForeignKey("ingredients.id"), nullable=False
    )
    change_amount = db.Column(db.Float, nullable=False)
    reason = db.Column(db.String(255), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.datetime.utcnow)

class StockInvoice(db.Model):
    __tablename__ = "stockinvoices"
    id = db.Column(db.Integer, primary_key=True)
    invoice_number = db.Column(db.String(255), unique=True, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.datetime.utcnow)

class StockInvoiceItem(db.Model):
    __tablename__ = "stockinvoiceitems"
    id = db.Column(db.Integer, primary_key=True)
    invoice_id = db.Column(
        db.Integer, db.ForeignKey("stockinvoices.id"), nullable=False
    )
    ingredient_id = db.Column(
        db.Integer, db.ForeignKey("ingredients.id"), nullable=False
    )
    quantity = db.Column(db.Float, nullable=False)

class OrderDiscount(db.Model):
    __tablename__ = "orderdiscounts"
    id = db.Column(db.Integer, primary_key=True)
    order_id = db.Column(db.Integer, db.ForeignKey("orders.id"), nullable=False)
    discount_id = db.Column(db.Integer, db.ForeignKey("discounts.id"), nullable=False)
    amount = db.Column(db.Numeric(10, 2), nullable=False)

class OrderItemDiscount(db.Model):
    __tablename__ = "orderitemdiscounts"
    id = db.Column(db.Integer, primary_key=True)
    order_item_id = db.Column(
        db.Integer, db.ForeignKey("orderitems.id"), nullable=False
    )
    discount_id = db.Column(db.Integer, db.ForeignKey("discounts.id"), nullable=False)
    amount = db.Column(db.Numeric(10, 2), nullable=False)