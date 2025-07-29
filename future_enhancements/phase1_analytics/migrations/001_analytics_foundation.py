"""
Database migration template for Phase 1: Analytics & Reporting
Revision ID: analytics_foundation
Revises: (current latest revision)
Create Date: 2025-01-29
"""

from alembic import op
import sqlalchemy as sa
from datetime import datetime


# revision identifiers, used by Alembic.
revision = 'analytics_foundation'
down_revision = None  # Set to current latest revision when implementing
branch_labels = None
depends_on = None


def upgrade():
    """Create analytics foundation tables"""
    
    # Analytics metrics table
    op.create_table(
        'analytics_metrics',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('metric_name', sa.String(100), nullable=False),
        sa.Column('metric_value', sa.Float, nullable=False),
        sa.Column('metric_type', sa.String(50), nullable=False),  # sales, inventory, customer
        sa.Column('date_recorded', sa.DateTime, nullable=False, default=datetime.utcnow),
        sa.Column('metadata', sa.JSON, nullable=True),
        sa.Column('created_at', sa.DateTime, nullable=False, default=datetime.utcnow),
        sa.PrimaryKeyConstraint('id'),
        sa.Index('idx_analytics_metrics_date', 'date_recorded'),
        sa.Index('idx_analytics_metrics_type', 'metric_type'),
    )
    
    # Customer behavior tracking
    op.create_table(
        'customer_behavior',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=True),
        sa.Column('session_id', sa.String(100), nullable=False),
        sa.Column('action_type', sa.String(50), nullable=False),  # view, add_to_cart, purchase
        sa.Column('action_data', sa.JSON, nullable=True),
        sa.Column('timestamp', sa.DateTime, nullable=False, default=datetime.utcnow),
        sa.Column('ip_address', sa.String(45), nullable=True),
        sa.Column('user_agent', sa.String(500), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='SET NULL'),
        sa.Index('idx_customer_behavior_user', 'user_id'),
        sa.Index('idx_customer_behavior_session', 'session_id'),
        sa.Index('idx_customer_behavior_timestamp', 'timestamp'),
    )
    
    # Product performance metrics
    op.create_table(
        'product_performance',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('menu_item_id', sa.Integer(), nullable=False),
        sa.Column('date', sa.Date, nullable=False),
        sa.Column('orders_count', sa.Integer, nullable=False, default=0),
        sa.Column('total_revenue', sa.Decimal(10, 2), nullable=False, default=0.00),
        sa.Column('avg_rating', sa.Float, nullable=True),
        sa.Column('return_rate', sa.Float, nullable=False, default=0.0),
        sa.Column('profit_margin', sa.Float, nullable=True),
        sa.Column('created_at', sa.DateTime, nullable=False, default=datetime.utcnow),
        sa.Column('updated_at', sa.DateTime, nullable=False, default=datetime.utcnow),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['menu_item_id'], ['menu_items.id'], ondelete='CASCADE'),
        sa.UniqueConstraint('menu_item_id', 'date', name='uq_product_performance_item_date'),
        sa.Index('idx_product_performance_date', 'date'),
    )
    
    # Sales forecasting data
    op.create_table(
        'sales_forecasts',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('forecast_date', sa.Date, nullable=False),
        sa.Column('menu_item_id', sa.Integer(), nullable=True),
        sa.Column('category_id', sa.Integer(), nullable=True),
        sa.Column('predicted_quantity', sa.Integer, nullable=False),
        sa.Column('predicted_revenue', sa.Decimal(10, 2), nullable=False),
        sa.Column('confidence_level', sa.Float, nullable=False),
        sa.Column('model_version', sa.String(50), nullable=False),
        sa.Column('created_at', sa.DateTime, nullable=False, default=datetime.utcnow),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['menu_item_id'], ['menu_items.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['category_id'], ['categories.id'], ondelete='CASCADE'),
        sa.Index('idx_sales_forecasts_date', 'forecast_date'),
        sa.Index('idx_sales_forecasts_item', 'menu_item_id'),
    )
    
    # Custom dashboards
    op.create_table(
        'custom_dashboards',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(100), nullable=False),
        sa.Column('description', sa.Text, nullable=True),
        sa.Column('layout_config', sa.JSON, nullable=False),
        sa.Column('widgets', sa.JSON, nullable=False),
        sa.Column('is_public', sa.Boolean, nullable=False, default=False),
        sa.Column('created_at', sa.DateTime, nullable=False, default=datetime.utcnow),
        sa.Column('updated_at', sa.DateTime, nullable=False, default=datetime.utcnow),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.Index('idx_custom_dashboards_user', 'user_id'),
    )
    
    # Scheduled reports
    op.create_table(
        'scheduled_reports',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(100), nullable=False),
        sa.Column('report_type', sa.String(50), nullable=False),
        sa.Column('schedule_expression', sa.String(100), nullable=False),  # cron expression
        sa.Column('parameters', sa.JSON, nullable=True),
        sa.Column('email_recipients', sa.JSON, nullable=True),
        sa.Column('is_active', sa.Boolean, nullable=False, default=True),
        sa.Column('last_run', sa.DateTime, nullable=True),
        sa.Column('next_run', sa.DateTime, nullable=True),
        sa.Column('created_at', sa.DateTime, nullable=False, default=datetime.utcnow),
        sa.Column('updated_at', sa.DateTime, nullable=False, default=datetime.utcnow),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.Index('idx_scheduled_reports_user', 'user_id'),
        sa.Index('idx_scheduled_reports_next_run', 'next_run'),
    )


def downgrade():
    """Drop analytics foundation tables"""
    op.drop_table('scheduled_reports')
    op.drop_table('custom_dashboards')
    op.drop_table('sales_forecasts')
    op.drop_table('product_performance')
    op.drop_table('customer_behavior')
    op.drop_table('analytics_metrics')