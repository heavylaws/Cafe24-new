#!/usr/bin/env python3
"""
Script to manually create units table and update ingredients
"""
from app import create_app, db
from app.models import Unit, Ingredient
import sqlite3
import os

def create_units_manually():
    app = create_app()
    
    with app.app_context():
        print("🔧 Creating Units Table Manually...")
        print("=" * 50)
        
        # Get database path
        db_path = app.config['SQLALCHEMY_DATABASE_URI'].replace('sqlite:///', '')
        if not os.path.exists(db_path):
            print(f"❌ Database file not found: {db_path}")
            return
        
        # Connect to SQLite directly
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        try:
            # Check if units table exists
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='units'")
            if cursor.fetchone():
                print("✅ Units table already exists")
            else:
                # Create units table
                cursor.execute("""
                    CREATE TABLE units (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        name VARCHAR(50) NOT NULL UNIQUE,
                        abbreviation VARCHAR(10) NOT NULL UNIQUE,
                        description VARCHAR(255),
                        is_active BOOLEAN NOT NULL DEFAULT 1,
                        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                        updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
                    )
                """)
                print("✅ Created units table")
            
            # Check if unit_id column exists in ingredients table
            cursor.execute("PRAGMA table_info(ingredients)")
            columns = [column[1] for column in cursor.fetchall()]
            
            if 'unit_id' not in columns:
                # Add unit_id column to ingredients table
                cursor.execute("ALTER TABLE ingredients ADD COLUMN unit_id INTEGER")
                print("✅ Added unit_id column to ingredients table")
            
            # Insert default units
            default_units = [
                ('Kilogram', 'kg', 'Kilogram unit for weight measurements'),
                ('Gram', 'g', 'Gram unit for small weight measurements'),
                ('Liter', 'L', 'Liter unit for volume measurements'),
                ('Milliliter', 'ml', 'Milliliter unit for small volume measurements'),
                ('Piece', 'piece', 'Piece unit for countable items'),
                ('Pack', 'pack', 'Pack unit for packaged items'),
                ('Bottle', 'bottle', 'Bottle unit for bottled items'),
                ('Cup', 'cup', 'Cup unit for cup measurements'),
                ('Tablespoon', 'tbsp', 'Tablespoon unit for cooking measurements'),
                ('Teaspoon', 'tsp', 'Teaspoon unit for small cooking measurements'),
                ('Ounce', 'oz', 'Ounce unit for weight measurements'),
                ('Pound', 'lb', 'Pound unit for weight measurements'),
                ('Gallon', 'gal', 'Gallon unit for volume measurements'),
                ('Quart', 'qt', 'Quart unit for volume measurements'),
                ('Pint', 'pt', 'Pint unit for volume measurements'),
                ('Can', 'can', 'Can unit for canned items'),
                ('Box', 'box', 'Box unit for boxed items'),
                ('Bag', 'bag', 'Bag unit for bagged items'),
                ('Jar', 'jar', 'Jar unit for jarred items'),
                ('Sachet', 'sachet', 'Sachet unit for small packaged items')
            ]
            
            for unit_name, abbreviation, description in default_units:
                cursor.execute("""
                    INSERT OR IGNORE INTO units (name, abbreviation, description)
                    VALUES (?, ?, ?)
                """, (unit_name, abbreviation, description))
            
            print(f"✅ Inserted {len(default_units)} default units")
            
            # Update existing ingredients to use appropriate units
            print("\n🔄 Updating existing ingredients...")
            
            # Get all ingredients
            cursor.execute("SELECT id, name, unit FROM ingredients")
            ingredients = cursor.fetchall()
            
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
            
            updated_count = 0
            for ingredient_id, ingredient_name, old_unit in ingredients:
                if old_unit:
                    old_unit_lower = old_unit.lower()
                    new_abbreviation = unit_mapping.get(old_unit_lower, 'piece')
                    
                    # Get unit ID
                    cursor.execute("SELECT id FROM units WHERE abbreviation = ?", (new_abbreviation,))
                    unit_result = cursor.fetchone()
                    
                    if unit_result:
                        unit_id = unit_result[0]
                        cursor.execute("UPDATE ingredients SET unit_id = ? WHERE id = ?", (unit_id, ingredient_id))
                        print(f"✅ Updated {ingredient_name}: {old_unit} → {new_abbreviation}")
                        updated_count += 1
                    else:
                        # Fallback to piece unit
                        cursor.execute("SELECT id FROM units WHERE abbreviation = 'piece'")
                        piece_unit_id = cursor.fetchone()[0]
                        cursor.execute("UPDATE ingredients SET unit_id = ? WHERE id = ?", (piece_unit_id, ingredient_id))
                        print(f"⚠️ Updated {ingredient_name}: {old_unit} → piece (fallback)")
                        updated_count += 1
            
            # Set default unit for any remaining ingredients
            cursor.execute("SELECT id FROM units WHERE abbreviation = 'piece'")
            piece_unit_id = cursor.fetchone()[0]
            cursor.execute("UPDATE ingredients SET unit_id = ? WHERE unit_id IS NULL", (piece_unit_id,))
            
            conn.commit()
            print(f"\n🎉 Successfully updated {updated_count} ingredients!")
            
            # Show final status
            cursor.execute("SELECT COUNT(*) FROM units")
            units_count = cursor.fetchone()[0]
            cursor.execute("SELECT COUNT(*) FROM ingredients")
            ingredients_count = cursor.fetchone()[0]
            
            print(f"\n📊 Final Status:")
            print(f"   Units: {units_count}")
            print(f"   Ingredients: {ingredients_count}")
            
            # Show sample ingredients with their units
            print(f"\n📋 Sample ingredients with units:")
            cursor.execute("""
                SELECT i.name, i.current_stock, u.abbreviation 
                FROM ingredients i 
                JOIN units u ON i.unit_id = u.id 
                LIMIT 5
            """)
            sample_ingredients = cursor.fetchall()
            for ingredient_name, stock, unit_abbr in sample_ingredients:
                print(f"   - {ingredient_name}: {stock} {unit_abbr}")
                
        except Exception as e:
            print(f"❌ Error: {e}")
            conn.rollback()
        finally:
            conn.close()

if __name__ == "__main__":
    create_units_manually() 