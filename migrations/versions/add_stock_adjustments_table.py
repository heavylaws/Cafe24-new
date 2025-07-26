"""Add stock adjustments table

Revision ID: add_stock_adjustments
Revises: 
Create Date: 2025-07-24 20:15:00.000000

"""
from alembic import op
import sqlalchemy as sa
import datetime

# revision identifiers, used by Alembic.
revision = 'add_stock_adjustments'
down_revision = None
branch_labels = None
depends_on = None

def upgrade():
    # Create stockadjustments table
    op.create_table(
        'stockadjustments',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('ingredient_id', sa.Integer(), nullable=False),
        sa.Column('change_amount', sa.Float(), nullable=False),
        sa.Column('reason', sa.String(length=255), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=True, default=datetime.datetime.utcnow),
        sa.ForeignKeyConstraint(['ingredient_id'], ['ingredients.id'], ),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    
    # Create index for better query performance
    op.create_index(op.f('ix_stockadjustments_ingredient_id'), 'stockadjustments', ['ingredient_id'], unique=False)
    op.create_index(op.f('ix_stockadjustments_created_at'), 'stockadjustments', ['created_at'], unique=False)

def downgrade():
    # Drop indexes first
    op.drop_index(op.f('ix_stockadjustments_created_at'), table_name='stockadjustments')
    op.drop_index(op.f('ix_stockadjustments_ingredient_id'), table_name='stockadjustments')
    
    # Then drop the table
    op.drop_table('stockadjustments')
