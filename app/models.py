"""
Database models for the Cafe24 POS system.

This module defines all SQLAlchemy models including User, Category, MenuItem,
Order, and related entities with their relationships and constraints.
"""
import datetime
import enum

from sqlalchemy import Enum
from werkzeug.security import generate_password_hash, check_password_hash

from app import db


class UserRole(enum.Enum):
    """Enumeration of user roles in the POS system."""
    COURIER = 'courier'
    CASHIER = 'cashier'
    BARISTA = 'barista'
    MANAGER = 'manager'


class DiscountType(enum.Enum):
    """Enumeration of discount types."""
    PERCENTAGE = 'percentage'
    FIXED_AMOUNT = 'fixed_amount'


class AppliesTo(enum.Enum):
    """Enumeration of what discounts can apply to."""
    ORDER = 'order'
    ITEM = 'item'


class OrderStatus(enum.Enum):
    """Enumeration of order statuses."""
    PENDING_PAYMENT = 'pending_payment'
    PAID_WAITING_PREPARATION = 'paid_waiting_preparation'
    PREPARING = 'preparing'
    READY_FOR_PICKUP = 'ready_for_pickup'
    COMPLETED = 'completed'
    CANCELLED = 'cancelled'


class PaymentMethod(enum.Enum):
    """Enumeration of payment methods."""
    CASH = 'cash'
    CARD = 'card'
    MIXED = 'mixed'


class PaymentStatus(enum.Enum):
    """Enumeration of payment statuses."""
    PENDING = 'pending'
    PAID = 'paid'
    REFUNDED = 'refunded'
    FAILED = 'failed'
    PARTIALLY_REFUNDED = 'partially_refunded'


class Unit(db.Model):
    """Model for measurement units used with ingredients."""
    __tablename__ = 'units'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), unique=True, nullable=False)
    abbreviation = db.Column(db.String(10), unique=True, nullable=False)
    description = db.Column(db.String(255))
    is_active = db.Column(db.Boolean, default=True, nullable=False)
    created_at = db.Column(
        db.DateTime, default=datetime.datetime.utcnow
    )
    updated_at = db.Column(
        db.DateTime, 
        default=datetime.datetime.utcnow, 
        onupdate=datetime.datetime.utcnow
    )

    ingredients = db.relationship('Ingredient', backref='unit_info', lazy=True)

    def __repr__(self):
        """String representation of the Unit."""
        return f"<Unit {self.name} ({self.abbreviation})>"


class User(db.Model):
    """Model for system users with role-based access."""
    __tablename__ = 'users'
    
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(
        db.String(100), unique=True, nullable=False, index=True
    )
    hashed_password = db.Column(db.String(255), nullable=False)
    full_name = db.Column(db.String(255))
    role = db.Column(Enum(UserRole), nullable=False)
    is_active = db.Column(db.Boolean, default=True, nullable=False)
    created_at = db.Column(
        db.DateTime, default=datetime.datetime.utcnow
    )
    updated_at = db.Column(
        db.DateTime, 
        default=datetime.datetime.utcnow, 
        onupdate=datetime.datetime.utcnow
    )

    def set_password(self, password):
        """Hash and set the user's password."""
        self.hashed_password = generate_password_hash(password)

    def check_password(self, password):
        """Check if the provided password matches the user's password."""
        return check_password_hash(self.hashed_password, password)

    def __repr__(self):
        """String representation of the User."""
        return f"<User {self.username} ({self.role.value})>"


class Category(db.Model):
    """Model for menu item categories with hierarchical support."""
    __tablename__ = 'categories'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(255), nullable=False)
    parent_id = db.Column(
        db.Integer, db.ForeignKey('categories.id'), nullable=True
    )
    sort_order = db.Column(db.Integer, default=0)
    created_at = db.Column(
        db.DateTime, default=datetime.datetime.utcnow
    )
    updated_at = db.Column(
        db.DateTime, 
        default=datetime.datetime.utcnow, 
        onupdate=datetime.datetime.utcnow
    )

    menu_items = db.relationship('MenuItem', backref='category', lazy=True)
    children = db.relationship(
        'Category', 
        backref=db.backref('parent', remote_side=[id]), 
        lazy='dynamic'
    )

    __table_args__ = (
        db.UniqueConstraint('parent_id', 'name', name='_parent_category_name_uc'),
    )

    def __init__(self, name, sort_order=0, parent_id=None, **kwargs):
        """Initialize a new Category."""
        super().__init__(**kwargs)
        self.name = name
        self.sort_order = sort_order
        self.parent_id = parent_id

    def __repr__(self):
        """String representation of the Category."""
        return f"<Category {self.name}>"


class MenuItem(db.Model):
    """Model for menu items."""
    __tablename__ = 'menuitems'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(255), nullable=False)
    category_id = db.Column(
        db.Integer, db.ForeignKey('categories.id'), nullable=False
    )
    base_price_usd = db.Column(db.Numeric(10, 2), nullable=False)
    description = db.Column(db.Text)
    is_active = db.Column(db.Boolean, default=True, nullable=False)
    created_at = db.Column(
        db.DateTime, default=datetime.datetime.utcnow
    )
    updated_at = db.Column(
        db.DateTime, 
        default=datetime.datetime.utcnow, 
        onupdate=datetime.datetime.utcnow
    )

    options = db.relationship(
        'MenuItemOption', backref='menu_item', lazy=True, cascade='all, delete-orphan'
    )
    recipes = db.relationship(
        'Recipe', backref='menu_item', lazy=True, cascade='all, delete-orphan'
    )
    order_items = db.relationship('OrderItem', backref='menu_item', lazy=True)

    def __repr__(self):
        """String representation of the MenuItem."""
        return f"<MenuItem {self.name} - ${self.base_price_usd}>"


class MenuItemOption(db.Model):
    """Model for menu item options (e.g., size, milk type)."""
    __tablename__ = 'menuitem_options'
    
    id = db.Column(db.Integer, primary_key=True)
    menu_item_id = db.Column(
        db.Integer, db.ForeignKey('menuitems.id'), nullable=False
    )
    option_name = db.Column(db.String(100), nullable=False)
    created_at = db.Column(
        db.DateTime, default=datetime.datetime.utcnow
    )

    choices = db.relationship(
        'MenuItemOptionChoice', 
        backref='option', 
        lazy=True, 
        cascade='all, delete-orphan'
    )

    def __repr__(self):
        """String representation of the MenuItemOption."""
        return f"<MenuItemOption {self.option_name}>"


class MenuItemOptionChoice(db.Model):
    """Model for individual choices within menu item options."""
    __tablename__ = 'menuitem_option_choices'
    
    id = db.Column(db.Integer, primary_key=True)
    option_id = db.Column(
        db.Integer, db.ForeignKey('menuitem_options.id'), nullable=False
    )
    choice_name = db.Column(db.String(100), nullable=False)
    price_modifier_usd = db.Column(
        db.Numeric(10, 2), default=0.00, nullable=False
    )
    is_default = db.Column(db.Boolean, default=False, nullable=False)
    created_at = db.Column(
        db.DateTime, default=datetime.datetime.utcnow
    )

    def __repr__(self):
        """String representation of the MenuItemOptionChoice."""
        modifier = f"+${self.price_modifier_usd}" if self.price_modifier_usd > 0 else ""
        return f"<Choice {self.choice_name} {modifier}>"


class Ingredient(db.Model):
    """Model for ingredients used in recipes."""
    __tablename__ = 'ingredients'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(255), unique=True, nullable=False)
    unit_id = db.Column(
        db.Integer, db.ForeignKey('units.id'), nullable=False
    )
    current_stock = db.Column(
        db.Numeric(10, 3), default=0.000, nullable=False
    )
    reorder_level = db.Column(
        db.Numeric(10, 3), default=10.000, nullable=False
    )
    cost_per_unit_usd = db.Column(db.Numeric(10, 2), nullable=True)
    is_active = db.Column(db.Boolean, default=True, nullable=False)
    created_at = db.Column(
        db.DateTime, default=datetime.datetime.utcnow
    )
    updated_at = db.Column(
        db.DateTime, 
        default=datetime.datetime.utcnow, 
        onupdate=datetime.datetime.utcnow
    )

    recipes = db.relationship('Recipe', backref='ingredient', lazy=True)

    def __repr__(self):
        """String representation of the Ingredient."""
        unit_abbr = self.unit_info.abbreviation if self.unit_info else 'N/A'
        return (f"<Ingredient {self.name} ({unit_abbr}) - "
                f"Stock: {self.current_stock}>")


class Recipe(db.Model):
    """Model for ingredient recipes used in menu items."""
    __tablename__ = 'recipes'
    
    id = db.Column(db.Integer, primary_key=True)
    menu_item_id = db.Column(
        db.Integer, db.ForeignKey('menuitems.id'), nullable=False
    )
    ingredient_id = db.Column(
        db.Integer, db.ForeignKey('ingredients.id'), nullable=False
    )
    amount = db.Column(db.Numeric(10, 3), nullable=False)
    created_at = db.Column(
        db.DateTime, default=datetime.datetime.utcnow
    )

    def __repr__(self):
        """String representation of the Recipe."""
        return f"<Recipe {self.amount} of ingredient {self.ingredient_id}>"


class Discount(db.Model):
    """Model for discounts that can be applied to orders or items."""
    __tablename__ = 'discounts'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(255), nullable=False)
    discount_type = db.Column(Enum(DiscountType), nullable=False)
    discount_value = db.Column(db.Numeric(10, 2), nullable=False)
    applies_to = db.Column(Enum(AppliesTo), nullable=False)
    is_active = db.Column(db.Boolean, default=True, nullable=False)
    start_date = db.Column(db.Date, nullable=True)
    end_date = db.Column(db.Date, nullable=True)
    created_at = db.Column(
        db.DateTime, default=datetime.datetime.utcnow
    )
    updated_at = db.Column(
        db.DateTime, 
        default=datetime.datetime.utcnow, 
        onupdate=datetime.datetime.utcnow
    )

    def __repr__(self):
        """String representation of the Discount."""
        return f"<Discount {self.name} - {self.discount_value}>"


class Order(db.Model):
    """Model for customer orders."""
    __tablename__ = 'orders'
    
    id = db.Column(db.Integer, primary_key=True)
    order_number = db.Column(db.String(50), unique=True, nullable=False)
    customer_number = db.Column(db.String(50), nullable=True)
    status = db.Column(Enum(OrderStatus), nullable=False)
    total_amount_usd = db.Column(db.Numeric(10, 2), nullable=False)
    payment_method = db.Column(Enum(PaymentMethod), nullable=True)
    payment_status = db.Column(Enum(PaymentStatus), nullable=False)
    created_by_user_id = db.Column(
        db.Integer, db.ForeignKey('users.id'), nullable=False
    )
    created_at = db.Column(
        db.DateTime, default=datetime.datetime.utcnow
    )
    updated_at = db.Column(
        db.DateTime, 
        default=datetime.datetime.utcnow, 
        onupdate=datetime.datetime.utcnow
    )

    created_by = db.relationship('User', backref='orders')
    order_items = db.relationship(
        'OrderItem', backref='order', lazy=True, cascade='all, delete-orphan'
    )

    def __repr__(self):
        """String representation of the Order."""
        return f"<Order {self.order_number} - ${self.total_amount_usd}>"


class OrderItem(db.Model):
    """Model for individual items within an order."""
    __tablename__ = 'order_items'
    
    id = db.Column(db.Integer, primary_key=True)
    order_id = db.Column(
        db.Integer, db.ForeignKey('orders.id'), nullable=False
    )
    menu_item_id = db.Column(
        db.Integer, db.ForeignKey('menuitems.id'), nullable=False
    )
    quantity = db.Column(db.Integer, nullable=False)
    unit_price_usd = db.Column(db.Numeric(10, 2), nullable=False)
    chosen_option_choice_id = db.Column(
        db.Integer, 
        db.ForeignKey('menuitem_option_choices.id'), 
        nullable=True
    )

    chosen_option_choice = db.relationship('MenuItemOptionChoice')

    def __repr__(self):
        """String representation of the OrderItem."""
        return f"<OrderItem {self.quantity}x - ${self.unit_price_usd}>"


class SystemSettings(db.Model):
    """Model for system-wide configuration settings."""
    __tablename__ = 'system_settings'
    
    id = db.Column(db.Integer, primary_key=True)
    setting_key = db.Column(db.String(255), unique=True, nullable=False)
    setting_value = db.Column(db.Text, nullable=False)
    created_at = db.Column(
        db.DateTime, default=datetime.datetime.utcnow
    )
    updated_at = db.Column(
        db.DateTime, 
        default=datetime.datetime.utcnow, 
        onupdate=datetime.datetime.utcnow
    )

    def __repr__(self):
        """String representation of the SystemSettings."""
        return f"<Setting {self.setting_key}: {self.setting_value}>"


class StockAdjustment(db.Model):
    """Model for tracking stock adjustments."""
    __tablename__ = 'stock_adjustments'
    
    id = db.Column(db.Integer, primary_key=True)
    ingredient_id = db.Column(
        db.Integer, db.ForeignKey('ingredients.id'), nullable=False
    )
    change_amount = db.Column(db.Numeric(10, 3), nullable=False)
    reason = db.Column(db.String(255), nullable=False)
    adjusted_by_user_id = db.Column(
        db.Integer, db.ForeignKey('users.id'), nullable=False
    )
    created_at = db.Column(
        db.DateTime, default=datetime.datetime.utcnow
    )

    ingredient = db.relationship('Ingredient')
    adjusted_by = db.relationship('User')

    def __repr__(self):
        """String representation of the StockAdjustment."""
        return f"<StockAdjustment {self.change_amount} - {self.reason}>"


class StockInvoice(db.Model):
    """Model for stock purchase invoices."""
    __tablename__ = 'stock_invoices'
    
    id = db.Column(db.Integer, primary_key=True)
    invoice_number = db.Column(db.String(100), unique=True, nullable=False)
    supplier_name = db.Column(db.String(255), nullable=False)
    total_amount_usd = db.Column(db.Numeric(10, 2), nullable=False)
    created_by_user_id = db.Column(
        db.Integer, db.ForeignKey('users.id'), nullable=False
    )
    created_at = db.Column(
        db.DateTime, default=datetime.datetime.utcnow
    )

    created_by = db.relationship('User')
    items = db.relationship(
        'StockInvoiceItem', 
        backref='invoice', 
        lazy=True, 
        cascade='all, delete-orphan'
    )

    def __repr__(self):
        """String representation of the StockInvoice."""
        return f"<StockInvoice {self.invoice_number} - ${self.total_amount_usd}>"


class StockInvoiceItem(db.Model):
    """Model for individual items within a stock invoice."""
    __tablename__ = 'stock_invoice_items'
    
    id = db.Column(db.Integer, primary_key=True)
    invoice_id = db.Column(
        db.Integer, db.ForeignKey('stock_invoices.id'), nullable=False
    )
    ingredient_id = db.Column(
        db.Integer, db.ForeignKey('ingredients.id'), nullable=False
    )
    quantity = db.Column(db.Numeric(10, 3), nullable=False)
    unit_cost_usd = db.Column(db.Numeric(10, 2), nullable=False)

    ingredient = db.relationship('Ingredient')

    def __repr__(self):
        """String representation of the StockInvoiceItem."""
        return f"<StockInvoiceItem {self.quantity} @ ${self.unit_cost_usd}>"


class OrderDiscount(db.Model):
    """Model for discounts applied to entire orders."""
    __tablename__ = 'order_discounts'
    
    id = db.Column(db.Integer, primary_key=True)
    order_id = db.Column(
        db.Integer, db.ForeignKey('orders.id'), nullable=False
    )
    discount_id = db.Column(
        db.Integer, db.ForeignKey('discounts.id'), nullable=False
    )
    discount_amount_usd = db.Column(db.Numeric(10, 2), nullable=False)

    order = db.relationship('Order')
    discount = db.relationship('Discount')

    def __repr__(self):
        """String representation of the OrderDiscount."""
        return f"<OrderDiscount ${self.discount_amount_usd}>"


class OrderItemDiscount(db.Model):
    """Model for discounts applied to specific order items."""
    __tablename__ = 'order_item_discounts'
    
    id = db.Column(db.Integer, primary_key=True)
    order_item_id = db.Column(
        db.Integer, db.ForeignKey('order_items.id'), nullable=False
    )
    discount_id = db.Column(
        db.Integer, db.ForeignKey('discounts.id'), nullable=False
    )
    discount_amount_usd = db.Column(db.Numeric(10, 2), nullable=False)

    order_item = db.relationship('OrderItem')
    discount = db.relationship('Discount')

    def __repr__(self):
        """String representation of the OrderItemDiscount."""
        return f"<OrderItemDiscount ${self.discount_amount_usd}>"
