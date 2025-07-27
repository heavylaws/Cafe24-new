#!/usr/bin/env python3
"""
Script to add sample options to the Coffee item
"""
from app import create_app, db
from app.models import MenuItem, MenuItemOption, MenuItemOptionChoice

def add_coffee_options():
    app = create_app()
    
    with app.app_context():
        print("Adding options to Coffee item...")
        
        # Find the coffee menu item
        coffee = MenuItem.query.filter_by(name='Coffee').first()
        
        if not coffee:
            print("❌ Coffee item not found!")
            return
        
        print(f"✅ Found Coffee item (ID: {coffee.id})")
        
        # Check if options already exist
        existing_options = MenuItemOption.query.filter_by(menu_item_id=coffee.id).all()
        if existing_options:
            print(f"⚠️ Coffee already has {len(existing_options)} options:")
            for option in existing_options:
                print(f"   - {option.name}")
            return
        
        # Add Size option
        size_option = MenuItemOption(
            menu_item_id=coffee.id,
            name="Size",
            is_required=True,
            sort_order=1
        )
        db.session.add(size_option)
        db.session.flush()  # Get the ID
        
        # Add size choices
        size_choices = [
            MenuItemOptionChoice(option_id=size_option.id, name="Small", price_delta=0.00, is_default=True, sort_order=1),
            MenuItemOptionChoice(option_id=size_option.id, name="Medium", price_delta=0.50, is_default=False, sort_order=2),
            MenuItemOptionChoice(option_id=size_option.id, name="Large", price_delta=1.00, is_default=False, sort_order=3)
        ]
        for choice in size_choices:
            db.session.add(choice)
        
        # Add Milk option
        milk_option = MenuItemOption(
            menu_item_id=coffee.id,
            name="Milk",
            is_required=False,
            sort_order=2
        )
        db.session.add(milk_option)
        db.session.flush()
        
        # Add milk choices
        milk_choices = [
            MenuItemOptionChoice(option_id=milk_option.id, name="No Milk", price_delta=0.00, is_default=True, sort_order=1),
            MenuItemOptionChoice(option_id=milk_option.id, name="Regular Milk", price_delta=0.25, is_default=False, sort_order=2),
            MenuItemOptionChoice(option_id=milk_option.id, name="Almond Milk", price_delta=0.50, is_default=False, sort_order=3)
        ]
        for choice in milk_choices:
            db.session.add(choice)
        
        # Add Sweetener option
        sweetener_option = MenuItemOption(
            menu_item_id=coffee.id,
            name="Sweetener",
            is_required=False,
            sort_order=3
        )
        db.session.add(sweetener_option)
        db.session.flush()
        
        # Add sweetener choices
        sweetener_choices = [
            MenuItemOptionChoice(option_id=sweetener_option.id, name="No Sweetener", price_delta=0.00, is_default=True, sort_order=1),
            MenuItemOptionChoice(option_id=sweetener_option.id, name="Sugar", price_delta=0.00, is_default=False, sort_order=2),
            MenuItemOptionChoice(option_id=sweetener_option.id, name="Honey", price_delta=0.25, is_default=False, sort_order=3)
        ]
        for choice in sweetener_choices:
            db.session.add(choice)
        
        # Commit all changes
        db.session.commit()
        
        print("✅ Successfully added options to Coffee:")
        print("   📏 Size: Small (default), Medium (+$0.50), Large (+$1.00)")
        print("   🥛 Milk: No Milk (default), Regular Milk (+$0.25), Almond Milk (+$0.50)")
        print("   🍯 Sweetener: No Sweetener (default), Sugar (free), Honey (+$0.25)")
        print()
        print("🔄 Now refresh your frontend to see the options button!")

if __name__ == "__main__":
    add_coffee_options() 