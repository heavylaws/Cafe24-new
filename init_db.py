"""
Database initialization script for the Cafe24 POS system.

This script creates the database tables and sets up initial data including
default users, system settings, and sample menu items.
"""

import datetime
import os

from app import create_app, db
from app.models import (
    AppliesTo,
    Category,
    Discount,
    DiscountType,
    Ingredient,
    MenuItem,
    MenuItemOption,
    MenuItemOptionChoice,
    Order,
    OrderDiscount,
    OrderItem,
    OrderItemDiscount,
    OrderStatus,
    PaymentMethod,
    Recipe,
    StockAdjustment,
    StockInvoice,
    StockInvoiceItem,
    SystemSettings,
    User,
    UserRole,
)

def init_database():
    """Initialize database with tables and default data."""
    app = create_app()
    with app.app_context():
        # Drop all tables and recreate them
        db.drop_all()
        db.create_all()

        print("Database tables created successfully!")

        # Create a default manager user
        manager = User(
            username="manager",
            full_name="System Manager",
            role=UserRole.manager,
            is_active=True,
        )
        manager.set_password("password123")

        # Create a default cashier user
        cashier = User(
            username="cashier",
            full_name="Cashier User",
            role=UserRole.cashier,
            is_active=True,
        )
        cashier.set_password("password123")

        # Create a default barista user
        barista = User(
            username="barista",
            full_name="Barista User",
            role=UserRole.barista,
            is_active=True,
        )
        barista.set_password("password123")

        # Create a default courier user
        courier = User(
            username="courier",
            full_name="Courier User",
            role=UserRole.courier,
            is_active=True,
        )
        courier.set_password("password123")

        # Add users to database
        db.session.add(manager)
        db.session.add(cashier)
        db.session.add(barista)
        db.session.add(courier)

        # Create some default categories
        beverages = Category(name="Beverages", sort_order=1)
        food = Category(name="Food", sort_order=2)
        desserts = Category(name="Desserts", sort_order=3)

        db.session.add(beverages)
        db.session.add(food)
        db.session.add(desserts)

        # Commit to get IDs
        db.session.commit()

        # Create some sample menu items
        coffee = MenuItem(
            category_id=beverages.id,
            name="Coffee",
            description="Fresh brewed coffee",
            base_price_usd=3.50,
            is_active=True,
        )

        sandwich = MenuItem(
            category_id=food.id,
            name="Sandwich",
            description="Fresh sandwich",
            base_price_usd=8.00,
            is_active=True,
        )

        cake = MenuItem(
            category_id=desserts.id,
            name="Cake",
            description="Delicious cake",
            base_price_usd=5.00,
            is_active=True,
        )

        db.session.add(coffee)
        db.session.add(sandwich)
        db.session.add(cake)

        # Commit to get menu item IDs
        db.session.commit()

        # Create some sample ingredients
        coffee_beans = Ingredient(
            name="Coffee Beans", unit="kg", current_stock=10.0, min_stock_alert=2.0
        )
        bread = Ingredient(
            name="Bread", unit="piece", current_stock=50, min_stock_alert=10
        )
        flour = Ingredient(
            name="Flour", unit="kg", current_stock=5.0, min_stock_alert=1.0
        )

        db.session.add(coffee_beans)
        db.session.add(bread)
        db.session.add(flour)

        # Create some sample discounts
        happy_hour = Discount(
            name="Happy Hour",
            description="20% off all beverages",
            discount_type=DiscountType.percentage,
            discount_value=20.00,
            applies_to=AppliesTo.item,
            is_active=True,
        )

        db.session.add(happy_hour)

        # Create some system settings
        exchange_rate = SystemSettings(
            setting_key="exchange_rate", setting_value="89000"
        )
        currency = SystemSettings(setting_key="currency", setting_value="LBP")

        db.session.add(exchange_rate)
        db.session.add(currency)

        # Final commit
        db.session.commit()

        print("Sample data created successfully!")
        print("\nDefault users created:")
        print("- Username: manager, Password: password123")
        print("- Username: cashier, Password: password123")
        print("- Username: barista, Password: password123")
        print("- Username: courier, Password: password123")


if __name__ == "__main__":
    init_database()