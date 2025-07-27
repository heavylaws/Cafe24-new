#!/usr/bin/env python3
"""
Script to check the coffee item and its ingredient list
"""
from app import create_app, db
from app.models import MenuItem, Ingredient, Recipe

def check_coffee_ingredients():
    app = create_app()
    
    with app.app_context():
        print("Checking Coffee Item and Ingredients...")
        print("=" * 50)
        
        # Find the coffee menu item
        coffee = MenuItem.query.filter_by(name='Coffee').first()
        
        if coffee:
            print(f"✅ Coffee item found:")
            print(f"   ID: {coffee.id}")
            print(f"   Name: {coffee.name}")
            print(f"   Description: {coffee.description}")
            print(f"   Price: ${coffee.base_price_usd}")
            print(f"   Category: {coffee.category.name if coffee.category else 'N/A'}")
            print()
            
            # Check recipes (ingredients)
            recipes = Recipe.query.filter_by(menu_item_id=coffee.id).all()
            
            if recipes:
                print(f"📋 Coffee has {len(recipes)} ingredients:")
                for recipe in recipes:
                    ingredient = recipe.ingredient
                    print(f"   • {ingredient.name}: {recipe.amount} {ingredient.unit}")
            else:
                print("❌ No ingredients found for Coffee")
                print("   You can add ingredients through the Recipe Manager")
        else:
            print("❌ Coffee item not found in database")
        
        print("\n" + "=" * 50)
        print("All available ingredients:")
        ingredients = Ingredient.query.all()
        for ingredient in ingredients:
            print(f"   • {ingredient.name} ({ingredient.unit}) - Stock: {ingredient.current_stock}")

if __name__ == "__main__":
    check_coffee_ingredients() 