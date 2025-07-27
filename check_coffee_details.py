#!/usr/bin/env python3
"""
Comprehensive script to check all details of the coffee item including options
"""
from app import create_app, db
from app.models import MenuItem, Ingredient, Recipe, MenuItemOption, MenuItemOptionChoice

def check_coffee_details():
    app = create_app()
    
    with app.app_context():
        print("🔍 COMPREHENSIVE COFFEE ITEM CHECK")
        print("=" * 60)
        
        # Find the coffee menu item
        coffee = MenuItem.query.filter_by(name='Coffee').first()
        
        if coffee:
            print(f"✅ Coffee item found:")
            print(f"   ID: {coffee.id}")
            print(f"   Name: {coffee.name}")
            print(f"   Description: {coffee.description}")
            print(f"   Price: ${coffee.base_price_usd}")
            print(f"   Category: {coffee.category.name if coffee.category else 'N/A'}")
            print(f"   Is Active: {coffee.is_active}")
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
            print()
            
            # Check menu item options
            options = MenuItemOption.query.filter_by(menu_item_id=coffee.id).all()
            if options:
                print(f"⚙️ Coffee has {len(options)} options:")
                for option in options:
                    print(f"   📝 Option: {option.name}")
                    print(f"      Required: {option.is_required}")
                    print(f"      Sort Order: {option.sort_order}")
                    
                    # Check choices for this option
                    choices = MenuItemOptionChoice.query.filter_by(option_id=option.id).all()
                    if choices:
                        print(f"      Choices ({len(choices)}):")
                        for choice in choices:
                            print(f"        • {choice.name} (${choice.price_delta}) - Default: {choice.is_default}")
                    else:
                        print(f"      ❌ No choices found for option '{option.name}'")
                    print()
            else:
                print("❌ No options found for Coffee")
                print("   This explains why there's no button under the coffee item!")
            print()
            
        else:
            print("❌ Coffee item not found in database")
        
        print("=" * 60)
        print("🔧 DEBUGGING: All menu items with options:")
        all_items = MenuItem.query.all()
        for item in all_items:
            item_options = MenuItemOption.query.filter_by(menu_item_id=item.id).all()
            print(f"   {item.name}: {len(item_options)} options")

if __name__ == "__main__":
    check_coffee_details() 