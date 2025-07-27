#!/usr/bin/env python3
"""
Script to initialize units table and update existing ingredients
"""
from app import create_app, db
from app.models import Unit, Ingredient

def init_units():
    app = create_app()
    
    with app.app_context():
        print("🔧 Initializing Units System...")
        print("=" * 50)
        
        # Create default units
        default_units = [
            {'name': 'Kilogram', 'abbreviation': 'kg', 'description': 'Kilogram unit for weight measurements'},
            {'name': 'Gram', 'abbreviation': 'g', 'description': 'Gram unit for small weight measurements'},
            {'name': 'Liter', 'abbreviation': 'L', 'description': 'Liter unit for volume measurements'},
            {'name': 'Milliliter', 'abbreviation': 'ml', 'description': 'Milliliter unit for small volume measurements'},
            {'name': 'Piece', 'abbreviation': 'piece', 'description': 'Piece unit for countable items'},
            {'name': 'Pack', 'abbreviation': 'pack', 'description': 'Pack unit for packaged items'},
            {'name': 'Bottle', 'abbreviation': 'bottle', 'description': 'Bottle unit for bottled items'},
            {'name': 'Cup', 'abbreviation': 'cup', 'description': 'Cup unit for cup measurements'},
            {'name': 'Tablespoon', 'abbreviation': 'tbsp', 'description': 'Tablespoon unit for cooking measurements'},
            {'name': 'Teaspoon', 'abbreviation': 'tsp', 'description': 'Teaspoon unit for small cooking measurements'},
            {'name': 'Ounce', 'abbreviation': 'oz', 'description': 'Ounce unit for weight measurements'},
            {'name': 'Pound', 'abbreviation': 'lb', 'description': 'Pound unit for weight measurements'},
            {'name': 'Gallon', 'abbreviation': 'gal', 'description': 'Gallon unit for volume measurements'},
            {'name': 'Quart', 'abbreviation': 'qt', 'description': 'Quart unit for volume measurements'},
            {'name': 'Pint', 'abbreviation': 'pt', 'description': 'Pint unit for volume measurements'},
            {'name': 'Can', 'abbreviation': 'can', 'description': 'Can unit for canned items'},
            {'name': 'Box', 'abbreviation': 'box', 'description': 'Box unit for boxed items'},
            {'name': 'Bag', 'abbreviation': 'bag', 'description': 'Bag unit for bagged items'},
            {'name': 'Jar', 'abbreviation': 'jar', 'description': 'Jar unit for jarred items'},
            {'name': 'Sachet', 'abbreviation': 'sachet', 'description': 'Sachet unit for small packaged items'}
        ]
        
        # Check if units table exists and has data
        try:
            existing_units = Unit.query.count()
            if existing_units > 0:
                print(f"✅ Units table already has {existing_units} units")
                units = Unit.query.all()
                print("📋 Existing units:")
                for unit in units:
                    print(f"   - {unit.name} ({unit.abbreviation})")
                return
        except Exception as e:
            print(f"⚠️ Units table doesn't exist yet: {e}")
            print("Creating units table...")
        
        # Create units
        created_units = []
        for unit_data in default_units:
            # Check if unit already exists
            existing = Unit.query.filter(
                (Unit.name == unit_data['name']) | (Unit.abbreviation == unit_data['abbreviation'])
            ).first()
            
            if existing:
                print(f"⚠️ Unit {unit_data['name']} already exists")
                created_units.append(existing)
            else:
                unit = Unit(**unit_data)
                db.session.add(unit)
                created_units.append(unit)
                print(f"✅ Created unit: {unit.name} ({unit.abbreviation})")
        
        db.session.commit()
        print(f"\n🎉 Successfully created {len(created_units)} units!")
        
        # Update existing ingredients to use the new unit system
        print("\n🔄 Updating existing ingredients...")
        ingredients = Ingredient.query.all()
        
        for ingredient in ingredients:
            if hasattr(ingredient, 'unit') and ingredient.unit:
                # Map old unit strings to new unit IDs
                unit_mapping = {
                    'kg': 'kg', 'kilogram': 'kg', 'kilograms': 'kg',
                    'g': 'g', 'gram': 'g', 'grams': 'g',
                    'L': 'L', 'l': 'L', 'liter': 'L', 'liters': 'L',
                    'ml': 'ml', 'milliliter': 'ml', 'milliliters': 'ml',
                    'piece': 'piece', 'pieces': 'piece', 'pcs': 'piece', 'pc': 'piece',
                    'pack': 'pack', 'packs': 'pack', 'package': 'pack', 'packages': 'pack',
                    'bottle': 'bottle', 'bottles': 'bottle',
                    'cup': 'cup', 'cups': 'cup',
                    'tbsp': 'tbsp', 'tablespoon': 'tbsp', 'tablespoons': 'tbsp',
                    'tsp': 'tsp', 'teaspoon': 'tsp', 'teaspoons': 'tsp',
                    'oz': 'oz', 'ounce': 'oz', 'ounces': 'oz',
                    'lb': 'lb', 'pound': 'lb', 'pounds': 'lb',
                    'gal': 'gal', 'gallon': 'gal', 'gallons': 'gal',
                    'qt': 'qt', 'quart': 'qt', 'quarts': 'qt',
                    'pt': 'pt', 'pint': 'pt', 'pints': 'pt',
                    'can': 'can', 'cans': 'can',
                    'box': 'box', 'boxes': 'box',
                    'bag': 'bag', 'bags': 'bag',
                    'jar': 'jar', 'jars': 'jar',
                    'sachet': 'sachet', 'sachets': 'sachet'
                }
                
                old_unit = ingredient.unit.lower()
                new_abbreviation = unit_mapping.get(old_unit, 'piece')  # Default to piece
                
                # Find the corresponding unit
                unit = Unit.query.filter_by(abbreviation=new_abbreviation).first()
                if unit:
                    ingredient.unit_id = unit.id
                    print(f"✅ Updated {ingredient.name}: {old_unit} → {unit.abbreviation}")
                else:
                    # Fallback to piece unit
                    piece_unit = Unit.query.filter_by(abbreviation='piece').first()
                    if piece_unit:
                        ingredient.unit_id = piece_unit.id
                        print(f"⚠️ Updated {ingredient.name}: {old_unit} → piece (fallback)")
        
        db.session.commit()
        print(f"\n🎉 Successfully updated {len(ingredients)} ingredients!")
        
        # Show final status
        print("\n📊 Final Status:")
        print(f"   Units: {Unit.query.count()}")
        print(f"   Ingredients: {Ingredient.query.count()}")
        
        # Show sample ingredients with their units
        print("\n📋 Sample ingredients with units:")
        sample_ingredients = Ingredient.query.limit(5).all()
        for ingredient in sample_ingredients:
            unit_abbr = ingredient.unit_info.abbreviation if hasattr(ingredient, 'unit_info') and ingredient.unit_info else 'N/A'
            print(f"   - {ingredient.name}: {ingredient.current_stock} {unit_abbr}")

if __name__ == "__main__":
    init_units() 