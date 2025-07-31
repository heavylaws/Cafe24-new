"""Merge multiple migration heads

Revision ID: 8d351cc2dd91
Revises: 3f4c91bb0c33, add_stock_adjustments, cf440a3876a2
Create Date: 2025-07-29 14:06:31.923545

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '8d351cc2dd91'
down_revision = ('3f4c91bb0c33', 'add_stock_adjustments', 'cf440a3876a2')
branch_labels = None
depends_on = None


def upgrade():
    pass


def downgrade():
    pass
