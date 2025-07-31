#!/usr/bin/env python3
"""
Coffee Shop Menu Data Seeder
Adds realistic coffee shop menu items, categories, and ingredients for testing.
"""

from app import create_app, db
from app.models import Category, MenuItem, Ingredient
from decimal import Decimal

def main():
    app = create_app()
    with app.app_context():
        print("Starting coffee shop menu seeding...")
        
        # Create Categories
        categories_data = [
            {"name": "Hot Coffee", "sort_order": 1},
            {"name": "Cold Coffee", "sort_order": 2},
            {"name": "Tea & Hot Drinks", "sort_order": 3},
            {"name": "Pastries & Snacks", "sort_order": 4},
            {"name": "Breakfast", "sort_order": 5},
        ]
        
        categories = {}
        for cat_data in categories_data:
            existing = Category.query.filter_by(name=cat_data["name"]).first()
            if not existing:
                category = Category(name=cat_data["name"], sort_order=cat_data["sort_order"])
                db.session.add(category)
                db.session.flush()  # To get the ID
                categories[cat_data["name"]] = category
                print(f"Created category: {cat_data['name']}")
            else:
                categories[cat_data["name"]] = existing
                print(f"Category already exists: {cat_data['name']}")
        
        # Create Ingredients
        ingredients_data = [
            {"name": "Coffee Beans", "unit": "g", "current_stock": 5000.0, "min_stock_alert": 500.0, "cost_per_unit_usd": 0.02},
            {"name": "Milk", "unit": "ml", "current_stock": 10000.0, "min_stock_alert": 1000.0, "cost_per_unit_usd": 0.001},
            {"name": "Sugar", "unit": "g", "current_stock": 2000.0, "min_stock_alert": 200.0, "cost_per_unit_usd": 0.002},
            {"name": "Vanilla Syrup", "unit": "ml", "current_stock": 1000.0, "min_stock_alert": 100.0, "cost_per_unit_usd": 0.01},
            {"name": "Caramel Syrup", "unit": "ml", "current_stock": 1000.0, "min_stock_alert": 100.0, "cost_per_unit_usd": 0.01},
            {"name": "Chocolate Powder", "unit": "g", "current_stock": 500.0, "min_stock_alert": 50.0, "cost_per_unit_usd": 0.05},
            {"name": "Whipped Cream", "unit": "ml", "current_stock": 500.0, "min_stock_alert": 50.0, "cost_per_unit_usd": 0.02},
            {"name": "Ice", "unit": "g", "current_stock": 5000.0, "min_stock_alert": 500.0, "cost_per_unit_usd": 0.001},
            {"name": "Tea Leaves", "unit": "g", "current_stock": 1000.0, "min_stock_alert": 100.0, "cost_per_unit_usd": 0.03},
            {"name": "Croissant", "unit": "piece", "current_stock": 50.0, "min_stock_alert": 5.0, "cost_per_unit_usd": 1.50},
        ]
        
        ingredients = {}
        for ing_data in ingredients_data:
            existing = Ingredient.query.filter_by(name=ing_data["name"]).first()
            if not existing:
                ingredient = Ingredient()
                ingredient.name = ing_data["name"]
                ingredient.unit = ing_data["unit"]
                ingredient.current_stock = ing_data["current_stock"]
                ingredient.min_stock_alert = ing_data["min_stock_alert"]
                ingredient.cost_per_unit_usd = Decimal(str(ing_data["cost_per_unit_usd"]))
                ingredient.is_active = True
                db.session.add(ingredient)
                db.session.flush()
                ingredients[ing_data["name"]] = ingredient
                print(f"Created ingredient: {ing_data['name']}")
            else:
                ingredients[ing_data["name"]] = existing
                print(f"Ingredient already exists: {ing_data['name']}")
        
        # Create Menu Items
        menu_items_data = [
            # Hot Coffee
            {
                "category": "Hot Coffee",
                "name": "Espresso",
                "description": "Rich and bold single shot of espresso",
                "base_price_usd": 2.50,
                "image_url": None
            },
            {
                "category": "Hot Coffee", 
                "name": "Doppio",
                "description": "Double shot of espresso for the coffee lover",
                "base_price_usd": 3.50,
                "image_url": None
            },
            {
                "category": "Hot Coffee",
                "name": "Lungo",
                "description": "Long extraction espresso with more water",
                "base_price_usd": 3.00,
                "image_url": None
            },
            {
                "category": "Hot Coffee",
                "name": "Ristretto",
                "description": "Short extraction espresso, concentrated and intense",
                "base_price_usd": 3.00,
                "image_url": None
            },
            {
                "category": "Hot Coffee",
                "name": "Americano", 
                "description": "Espresso diluted with hot water",
                "base_price_usd": 3.25,
                "image_url": None
            },
            {
                "category": "Hot Coffee",
                "name": "Cappuccino",
                "description": "Espresso with steamed milk and foam",
                "base_price_usd": 4.50,
                "image_url": None
            },
            {
                "category": "Hot Coffee",
                "name": "Latte",
                "description": "Espresso with steamed milk and light foam",
                "base_price_usd": 4.75,
                "image_url": None
            },
            {
                "category": "Hot Coffee",
                "name": "Macchiato",
                "description": "Espresso 'marked' with a dollop of steamed milk",
                "base_price_usd": 4.25,
                "image_url": None
            },
            {
                "category": "Hot Coffee",
                "name": "Mocha",
                "description": "Espresso with chocolate, steamed milk and whipped cream",
                "base_price_usd": 5.25,
                "image_url": None
            },
            {
                "category": "Hot Coffee",
                "name": "Flat White",
                "description": "Double espresso with steamed milk, no foam",
                "base_price_usd": 4.50,
                "image_url": None
            },
            
            # Cold Coffee
            {
                "category": "Cold Coffee",
                "name": "Iced Americano",
                "description": "Espresso with cold water and ice",
                "base_price_usd": 3.50,
                "image_url": None
            },
            {
                "category": "Cold Coffee",
                "name": "Iced Latte", 
                "description": "Espresso with cold milk and ice",
                "base_price_usd": 5.00,
                "image_url": None
            },
            {
                "category": "Cold Coffee",
                "name": "Cold Brew",
                "description": "Slow-steeped coffee served over ice",
                "base_price_usd": 4.25,
                "image_url": None
            },
            {
                "category": "Cold Coffee",
                "name": "Frappé",
                "description": "Blended iced coffee with milk and sugar",
                "base_price_usd": 5.50,
                "image_url": None
            },
            
            # Tea & Hot Drinks
            {
                "category": "Tea & Hot Drinks",
                "name": "English Breakfast Tea",
                "description": "Classic black tea blend",
                "base_price_usd": 2.75,
                "image_url": None
            },
            {
                "category": "Tea & Hot Drinks", 
                "name": "Earl Grey Tea",
                "description": "Black tea with bergamot oil",
                "base_price_usd": 2.75,
                "image_url": None
            },
            {
                "category": "Tea & Hot Drinks",
                "name": "Hot Chocolate",
                "description": "Rich chocolate drink with whipped cream",
                "base_price_usd": 4.00,
                "image_url": None
            },
            
            # Pastries & Snacks
            {
                "category": "Pastries & Snacks",
                "name": "Butter Croissant",
                "description": "Fresh baked buttery croissant",
                "base_price_usd": 3.50,
                "image_url": None
            },
            {
                "category": "Pastries & Snacks",
                "name": "Pain au Chocolat",
                "description": "Croissant with dark chocolate",
                "base_price_usd": 4.00,
                "image_url": None
            },
            {
                "category": "Pastries & Snacks",
                "name": "Blueberry Muffin",
                "description": "Fresh blueberry muffin",
                "base_price_usd": 3.25,
                "image_url": None
            },
            
            # Breakfast
            {
                "category": "Breakfast",
                "name": "Avocado Toast",
                "description": "Smashed avocado on sourdough bread",
                "base_price_usd": 8.50,
                "image_url": None
            },
            {
                "category": "Breakfast",
                "name": "Breakfast Sandwich",
                "description": "Egg, cheese, and bacon on English muffin",
                "base_price_usd": 7.75,
                "image_url": None
            }
        ]
        
        for item_data in menu_items_data:
            category = categories[item_data["category"]]
            existing = MenuItem.query.filter_by(
                category_id=category.id, 
                name=item_data["name"]
            ).first()
            
            if not existing:
                menu_item = MenuItem()
                menu_item.category_id = category.id
                menu_item.name = item_data["name"]
                menu_item.description = item_data["description"]
                menu_item.base_price_usd = Decimal(str(item_data["base_price_usd"]))
                menu_item.is_active = True
                menu_item.image_url = item_data["image_url"]
                db.session.add(menu_item)
                print(f"Created menu item: {item_data['name']} (${item_data['base_price_usd']})")
            else:
                print(f"Menu item already exists: {item_data['name']}")
        
        # Commit all changes
        db.session.commit()
        print("\n✅ Coffee shop menu seeding completed successfully!")
        print(f"Categories: {len(categories_data)}")
        print(f"Ingredients: {len(ingredients_data)}")
        print(f"Menu Items: {len(menu_items_data)}")

if __name__ == "__main__":
    main()
