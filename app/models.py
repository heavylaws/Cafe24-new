"""Database models for the Cafe24 POS system.

This module contains all SQLAlchemy models and enums used throughout the application.
"""
import datetime
import enum
from typing import Optional
from werkzeug.security import generate_password_hash, check_password_hash
from sqlalchemy import Enum, Index, MetaData
from app import db


# --- Enums ---
class UserRole(enum.Enum):
    """User role enumeration."""
    COURIER = 'courier'
    CASHIER = 'cashier'
    BARISTA = 'barista'
    MANAGER = 'manager'


class DiscountType(enum.Enum):
    """Discount type enumeration."""
    PERCENTAGE = 'percentage'
    FIXED_AMOUNT = 'fixed_amount'


class AppliesTo(enum.Enum):
    """Applies to enumeration for discounts."""
    ORDER = 'order'
    ITEM = 'item'


class OrderStatus(enum.Enum):
    """Order status enumeration."""
    PENDING_PAYMENT = 'pending_payment'
    PAID_WAITING_PREPARATION = 'paid_waiting_preparation'
    PREPARING = 'preparing'
    READY_FOR_PICKUP = 'ready_for_pickup'
    COMPLETED = 'completed'
    CANCELLED = 'cancelled'


class PaymentMethod(enum.Enum):
    """Payment method enumeration."""
    CASH = 'cash'
    CARD = 'card'
    MIXED = 'mixed'


class PaymentStatus(enum.Enum):
    """Payment status enumeration."""
    PENDING = 'pending'
    PAID = 'paid'
    REFUNDED = 'refunded'
    FAILED = 'failed'
    PARTIALLY_REFUNDED = 'partially_refunded'


# --- Models ---
class User(db.Model):
    """User model for system authentication and authorization."""
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(100), unique=True, nullable=False, index=True)
    hashed_password = db.Column(db.String(255), nullable=False)
    full_name = db.Column(db.String(255))
    role = db.Column(Enum(UserRole), nullable=False)
    is_active = db.Column(db.Boolean, default=True, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow)

    def set_password(self, password):
        """Set the user's password hash."""
        self.hashed_password = generate_password_hash(password)

    def check_password(self, password):
        """Check if the provided password matches the user's password."""
        return check_password_hash(self.hashed_password, password)

    def __repr__(self):
        return f"<User {self.username} ({self.role.value})>"

class Category(db.Model):
    """Category model for organizing menu items."""
    __tablename__ = 'categories'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(255), nullable=False)
    parent_id = db.Column(db.Integer, db.ForeignKey('categories.id'), nullable=True)
    sort_order = db.Column(db.Integer, default=0)
    created_at = db.Column(db.DateTime, default=datetime.datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.datetime.utcnow,
                          onupdate=datetime.datetime.utcnow)

    menu_items = db.relationship('MenuItem', backref='category', lazy=True)
    children = db.relationship('Category',
                             backref=db.backref('parent', remote_side=[id]),
                             lazy='dynamic')

    __table_args__ = (db.UniqueConstraint('parent_id', 'name',
                                        name='_parent_category_name_uc'),)

    def __init__(self, name: str, sort_order: int = 0,
                 parent_id: Optional[int] = None, **kwargs):
        """Initialize a new Category."""
        super().__init__(**kwargs)
        self.name = name
        self.sort_order = sort_order
        self.parent_id = parent_id

    def __repr__(self):
        """Return string representation of Category."""
        return f"<Category {self.parent.name if self.parent else ''} / {self.name}>"


class MenuItem(db.Model):
    """Menu item model representing items available for order."""
    __tablename__ = 'menuitems'
    id = db.Column(db.Integer, primary_key=True)
    category_id = db.Column(db.Integer, db.ForeignKey('categories.id'),
                          nullable=False, index=True)
    name = db.Column(db.String(255), nullable=False)
    description = db.Column(db.Text)
    base_price_usd = db.Column(db.Numeric(10, 2), nullable=False, default=0.00)
    is_active = db.Column(db.Boolean, default=True, nullable=False)
    image_url = db.Column(db.String(255))
    created_at = db.Column(db.DateTime, default=datetime.datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.datetime.utcnow,
                          onupdate=datetime.datetime.utcnow)

    options = db.relationship('MenuItemOption', backref='menu_item', lazy='select',
                            cascade="all, delete-orphan")
    order_items = db.relationship('OrderItem', backref='menu_item', lazy=True)

    __table_args__ = (db.UniqueConstraint('category_id', 'name',
                                        name='_category_item_name_uc'),)

    def __repr__(self):
        return f"<MenuItem {self.name}>"

class MenuItemOption(db.Model):
    __tablename__ = 'menuitemoptions'
    id = db.Column(db.Integer, primary_key=True)
    menu_item_id = db.Column(db.Integer, db.ForeignKey('menuitems.id'), nullable=False)
    name = db.Column(db.String(255), nullable=False)
    is_required = db.Column(db.Boolean, default=False)
    sort_order = db.Column(db.Integer, default=0)
    created_at = db.Column(db.DateTime, default=datetime.datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow)

    choices = db.relationship('MenuItemOptionChoice', backref='option', lazy='select', cascade="all, delete-orphan")

class MenuItemOptionChoice(db.Model):
    __tablename__ = 'menuitemoptionchoices'
    id = db.Column(db.Integer, primary_key=True)
    option_id = db.Column(db.Integer, db.ForeignKey('menuitemoptions.id'), nullable=False)
    name = db.Column(db.String(255), nullable=False)
    price_delta = db.Column(db.Numeric(10, 2), default=0.00)
    is_default = db.Column(db.Boolean, default=False)
    sort_order = db.Column(db.Integer, default=0)
    created_at = db.Column(db.DateTime, default=datetime.datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow)

class Ingredient(db.Model):
    __tablename__ = 'ingredients'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(255), unique=True, nullable=False)
    unit = db.Column(db.String(10), nullable=False)
    current_stock = db.Column(db.Float, nullable=False, default=0.0)
    min_stock_alert = db.Column(db.Float, nullable=False, default=0.0)
    cost_per_unit_usd = db.Column(db.Numeric(10, 2), nullable=True, default=0.00)
    reorder_level = db.Column(db.Float, nullable=True, default=0.0)
    is_active = db.Column(db.Boolean, default=True, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow)

    def __repr__(self):
        return f"<Ingredient {self.name} ({self.unit}) - Stock: {self.current_stock}>"

class Recipe(db.Model):
    __tablename__ = 'recipes'
    id = db.Column(db.Integer, primary_key=True)
    menu_item_id = db.Column(db.Integer, db.ForeignKey('menuitems.id'), nullable=False)
    ingredient_id = db.Column(db.Integer, db.ForeignKey('ingredients.id'), nullable=False)
    amount = db.Column(db.Float, nullable=False)

    ingredient = db.relationship('Ingredient')

    def __repr__(self):
        return f"<Recipe MenuItem {self.menu_item_id} needs {self.amount} of Ingredient {self.ingredient_id}>"

class Discount(db.Model):
    __tablename__ = 'discounts'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(255), nullable=False)
    description = db.Column(db.Text)
    discount_type = db.Column(Enum(DiscountType), nullable=False)
    discount_value = db.Column(db.Numeric(10, 2), nullable=False)
    applies_to = db.Column(Enum(AppliesTo), nullable=False)
    is_active = db.Column(db.Boolean, default=True, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow)

    def __repr__(self):
        return f"<Discount {self.name} - {self.discount_value}{'%' if self.discount_type == DiscountType.percentage else 'USD'}>"

class Order(db.Model):
    __tablename__ = 'orders'
    id = db.Column(db.Integer, primary_key=True)
    order_number = db.Column(db.String(20), unique=True, nullable=False)
    courier_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    customer_number = db.Column(db.String(20), nullable=True)  # Can be anonymous
    status = db.Column(Enum(OrderStatus), nullable=False, default=OrderStatus.pending_payment)
    payment_status = db.Column(Enum(PaymentStatus), nullable=False, default=PaymentStatus.pending)
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
    updated_at = db.Column(db.DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow)

    order_items = db.relationship('OrderItem', backref='order', lazy=True)

    def __repr__(self):
        return f"<Order {self.id} by User {self.courier_id}>"

class OrderItem(db.Model):
    __tablename__ = 'orderitems'
    id = db.Column(db.Integer, primary_key=True)
    order_id = db.Column(db.Integer, db.ForeignKey('orders.id'), nullable=False)
    menu_item_id = db.Column(db.Integer, db.ForeignKey('menuitems.id'), nullable=False)
    menu_item_name = db.Column(db.String(255), nullable=False)
    quantity = db.Column(db.Integer, nullable=False, default=1)
    chosen_option_choice_id = db.Column(db.Integer, db.ForeignKey('menuitemoptionchoices.id'), nullable=True)
    chosen_option_choice_name = db.Column(db.String(255), nullable=True)
    unit_price_usd_at_order = db.Column(db.Numeric(10, 2), nullable=False)
    unit_price_lbp_rounded_at_order = db.Column(db.Integer, nullable=False)
    line_total_usd_at_order = db.Column(db.Numeric(10, 2), nullable=False)
    line_total_lbp_rounded_at_order = db.Column(db.Integer, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow)

    def __repr__(self):
        return f"<OrderItem {self.id} for Order {self.order_id}>"

# --- Placeholders for missing models to resolve import errors ---
class SystemSettings(db.Model):
    __tablename__ = 'systemsettings'
    id = db.Column(db.Integer, primary_key=True)
    setting_key = db.Column(db.String(255), unique=True, nullable=False)
    setting_value = db.Column(db.String(255), nullable=False)

class StockAdjustment(db.Model):
    __tablename__ = 'stockadjustments'
    id = db.Column(db.Integer, primary_key=True)
    ingredient_id = db.Column(db.Integer, db.ForeignKey('ingredients.id'), nullable=False)
    change_amount = db.Column(db.Float, nullable=False)
    reason = db.Column(db.String(255), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.datetime.utcnow)

class StockInvoice(db.Model):
    __tablename__ = 'stockinvoices'
    id = db.Column(db.Integer, primary_key=True)
    invoice_number = db.Column(db.String(255), unique=True, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.datetime.utcnow)

class StockInvoiceItem(db.Model):
    __tablename__ = 'stockinvoiceitems'
    id = db.Column(db.Integer, primary_key=True)
    invoice_id = db.Column(db.Integer, db.ForeignKey('stockinvoices.id'), nullable=False)
    ingredient_id = db.Column(db.Integer, db.ForeignKey('ingredients.id'), nullable=False)
    quantity = db.Column(db.Float, nullable=False)

class OrderDiscount(db.Model):
    __tablename__ = 'orderdiscounts'
    id = db.Column(db.Integer, primary_key=True)
    order_id = db.Column(db.Integer, db.ForeignKey('orders.id'), nullable=False)
    discount_id = db.Column(db.Integer, db.ForeignKey('discounts.id'), nullable=False)
    amount = db.Column(db.Numeric(10, 2), nullable=False)

class OrderItemDiscount(db.Model):
    __tablename__ = 'orderitemdiscounts'
    id = db.Column(db.Integer, primary_key=True)
    order_item_id = db.Column(db.Integer, db.ForeignKey('orderitems.id'), nullable=False)
    discount_id = db.Column(db.Integer, db.ForeignKey('discounts.id'), nullable=False)
    amount = db.Column(db.Numeric(10, 2), nullable=False)
