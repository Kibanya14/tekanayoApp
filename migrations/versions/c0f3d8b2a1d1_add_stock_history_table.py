"""Add stock history table for order and inventory changes

Revision ID: c0f3d8b2a1d1
Revises: 9b30d0ac10ff
Create Date: 2026-05-13 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'c0f3d8b2a1d1'
down_revision = '9b30d0ac10ff'
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        'stock_history',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('product_id', sa.Integer(), sa.ForeignKey('seller_products.id'), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('user_type', sa.String(length=20), nullable=True),
        sa.Column('old_quantity', sa.Integer(), nullable=True, default=0),
        sa.Column('new_quantity', sa.Integer(), nullable=True, default=0),
        sa.Column('quantity_change', sa.Integer(), nullable=True),
        sa.Column('reason', sa.String(length=255), nullable=True),
        sa.Column('timestamp', sa.DateTime(), nullable=True),
    )


def downgrade():
    op.drop_table('stock_history')
