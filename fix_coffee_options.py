#!/usr/bin/env python3
"""
Script to fix the coffee options by adding choices to incomplete options
"""
from app import create_app, db
from app.models import MenuItem, MenuItemOption, MenuItemOptionChoice

def fix_coffee_options():
    app = create_app()
    
    with app.app_context():
        print("🔧 Fixing Coffee options...")
        
        # Find the coffee menu item
        coffee = MenuItem.query.filter_by(name='Coffee').first()
        
        if not coffee:
            print("❌ Coffee item not found!")
            return
        
        print(f"✅ Found Coffee item (ID: {coffee.id})")
        
        # Get all options for coffee
        options = MenuItemOption.query.filter_by(menu_item_id=coffee.id).all()
        
        for option in options:
            print(f"📝 Checking option: {option.name}")
            
            # Check if this option has choices
            choices = MenuItemOptionChoice.query.filter_by(option_id=option.id).all()
            
            if not choices:
                print(f"   ❌ Option '{option.name}' has no choices - adding them...")
                
                if option.name.lower() == "cartoon":
                    # Add cartoon choices
                    cartoon_choices = [
                        MenuItemOptionChoice(option_id=option.id, name="No Cartoon", price_delta=0.00, is_default=True, sort_order=1),
                        MenuItemOptionChoice(option_id=option.id, name="With Cartoon", price_delta=0.25, is_default=False, sort_order=2)
                    ]
                    for choice in cartoon_choices:
                        db.session.add(choice)
                    print(f"   ✅ Added choices for 'cartoon' option")
                
                elif option.name.lower() == "plastic":
                    # Add plastic choices if missing
                    plastic_choices = [
                        MenuItemOptionChoice(option_id=option.id, name="No Plastic", price_delta=0.00, is_default=True, sort_order=1),
                        MenuItemOptionChoice(option_id=option.id, name="With Plastic", price_delta=0.10, is_default=False, sort_order=2)
                    ]
                    for choice in plastic_choices:
                        db.session.add(choice)
                    print(f"   ✅ Added choices for 'plastic' option")
                
                else:
                    # Generic choices for any other option
                    generic_choices = [
                        MenuItemOptionChoice(option_id=option.id, name="No", price_delta=0.00, is_default=True, sort_order=1),
                        MenuItemOptionChoice(option_id=option.id, name="Yes", price_delta=0.25, is_default=False, sort_order=2)
                    ]
                    for choice in generic_choices:
                        db.session.add(choice)
                    print(f"   ✅ Added generic choices for '{option.name}' option")
            else:
                print(f"   ✅ Option '{option.name}' has {len(choices)} choices")
        
        # Commit changes
        db.session.commit()
        
        print("\n✅ Coffee options fixed!")
        print("🔄 Now refresh your frontend - you should see the options button!")

if __name__ == "__main__":
    fix_coffee_options() 