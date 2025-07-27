"""Add units table and update ingredients

Revision ID: add_units_table
Revises: e856f8d1aeeb
Create Date: 2024-12-19 10:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import sqlite

# revision identifiers, used by Alembic.
revision = 'add_units_table'
down_revision = 'e856f8d1aeeb'
branch_labels = None
depends_on = None


def upgrade():
    # Create units table
    op.create_table('units',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(length=50), nullable=False),
        sa.Column('abbreviation', sa.String(length=10), nullable=False),
        sa.Column('description', sa.String(length=255), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=False, default=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('name'),
        sa.UniqueConstraint('abbreviation')
    )
    
    # Add unit_id column to ingredients table
    op.add_column('ingredients', sa.Column('unit_id', sa.Integer(), nullable=True))
    op.create_foreign_key('fk_ingredients_unit_id', 'ingredients', 'units', ['unit_id'], ['id'])
    
    # Insert default units
    op.execute("""
        INSERT INTO units (name, abbreviation, description, is_active, created_at, updated_at) VALUES
        ('Kilogram', 'kg', 'Kilogram unit for weight measurements', 1, datetime('now'), datetime('now')),
        ('Gram', 'g', 'Gram unit for small weight measurements', 1, datetime('now'), datetime('now')),
        ('Liter', 'L', 'Liter unit for volume measurements', 1, datetime('now'), datetime('now')),
        ('Milliliter', 'ml', 'Milliliter unit for small volume measurements', 1, datetime('now'), datetime('now')),
        ('Piece', 'piece', 'Piece unit for countable items', 1, datetime('now'), datetime('now')),
        ('Pack', 'pack', 'Pack unit for packaged items', 1, datetime('now'), datetime('now')),
        ('Bottle', 'bottle', 'Bottle unit for bottled items', 1, datetime('now'), datetime('now')),
        ('Cup', 'cup', 'Cup unit for cup measurements', 1, datetime('now'), datetime('now')),
        ('Tablespoon', 'tbsp', 'Tablespoon unit for cooking measurements', 1, datetime('now'), datetime('now')),
        ('Teaspoon', 'tsp', 'Teaspoon unit for small cooking measurements', 1, datetime('now'), datetime('now'))
    """)
    
    # Update existing ingredients to use appropriate units
    op.execute("""
        UPDATE ingredients SET unit_id = (SELECT id FROM units WHERE abbreviation = 'kg') 
        WHERE unit IN ('kg', 'kilogram', 'kilograms')
    """)
    op.execute("""
        UPDATE ingredients SET unit_id = (SELECT id FROM units WHERE abbreviation = 'g') 
        WHERE unit IN ('g', 'gram', 'grams')
    """)
    op.execute("""
        UPDATE ingredients SET unit_id = (SELECT id FROM units WHERE abbreviation = 'L') 
        WHERE unit IN ('L', 'l', 'liter', 'liters')
    """)
    op.execute("""
        UPDATE ingredients SET unit_id = (SELECT id FROM units WHERE abbreviation = 'ml') 
        WHERE unit IN ('ml', 'milliliter', 'milliliters')
    """)
    op.execute("""
        UPDATE ingredients SET unit_id = (SELECT id FROM units WHERE abbreviation = 'piece') 
        WHERE unit IN ('piece', 'pieces', 'pcs', 'pc')
    """)
    op.execute("""
        UPDATE ingredients SET unit_id = (SELECT id FROM units WHERE abbreviation = 'pack') 
        WHERE unit IN ('pack', 'packs', 'package', 'packages')
    """)
    op.execute("""
        UPDATE ingredients SET unit_id = (SELECT id FROM units WHERE abbreviation = 'bottle') 
        WHERE unit IN ('bottle', 'bottles')
    """)
    op.execute("""
        UPDATE ingredients SET unit_id = (SELECT id FROM units WHERE abbreviation = 'cup') 
        WHERE unit IN ('cup', 'cups')
    """)
    op.execute("""
        UPDATE ingredients SET unit_id = (SELECT id FROM units WHERE abbreviation = 'tbsp') 
        WHERE unit IN ('tbsp', 'tablespoon', 'tablespoons')
    """)
    op.execute("""
        UPDATE ingredients SET unit_id = (SELECT id FROM units WHERE abbreviation = 'tsp') 
        WHERE unit IN ('tsp', 'teaspoon', 'teaspoons')
    """)
    
    # Set default unit for any remaining ingredients
    op.execute("""
        UPDATE ingredients SET unit_id = (SELECT id FROM units WHERE abbreviation = 'piece') 
        WHERE unit_id IS NULL
    """)
    
    # Make unit_id not nullable after setting all values
    op.alter_column('ingredients', 'unit_id', nullable=False)
    
    # Drop the old unit column
    op.drop_column('ingredients', 'unit')


def downgrade():
    # Add back the old unit column
    op.add_column('ingredients', sa.Column('unit', sa.String(length=10), nullable=True))
    
    # Copy unit abbreviations back to the old column
    op.execute("""
        UPDATE ingredients SET unit = (SELECT abbreviation FROM units WHERE units.id = ingredients.unit_id)
    """)
    
    # Make unit not nullable
    op.alter_column('ingredients', 'unit', nullable=False)
    
    # Drop the foreign key and unit_id column
    op.drop_constraint('fk_ingredients_unit_id', 'ingredients', type_='foreignkey')
    op.drop_column('ingredients', 'unit_id')
    
    # Drop the units table
    op.drop_table('units') 