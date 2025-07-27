"""add cost and reorder to ingredient

Revision ID: 3f4c91bb0c33
Revises: e856f8d1aeeb
Create Date: 2025-07-13 12:00:00.000000

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '3f4c91bb0c33'
down_revision = 'e856f8d1aeeb'
branch_labels = None
depends_on = None


def upgrade():
    with op.batch_alter_table('ingredients', schema=None) as batch_op:
        batch_op.add_column(sa.Column('cost_per_unit_usd', sa.Numeric(10, 2), nullable=True))
        batch_op.add_column(sa.Column('reorder_level', sa.Float(), nullable=True))


def downgrade():
    with op.batch_alter_table('ingredients', schema=None) as batch_op:
        batch_op.drop_column('reorder_level')
        batch_op.drop_column('cost_per_unit_usd')

