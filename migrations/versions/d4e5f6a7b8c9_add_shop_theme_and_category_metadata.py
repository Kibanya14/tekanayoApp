"""Add shop theme and category metadata

Revision ID: d4e5f6a7b8c9
Revises: a42d3c5e8f7b
Create Date: 2026-06-01 12:30:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'd4e5f6a7b8c9'
down_revision = 'a42d3c5e8f7b'
branch_labels = None
depends_on = None


def upgrade():
    with op.batch_alter_table('seller_shops', schema=None) as batch_op:
        batch_op.add_column(sa.Column('shop_theme', sa.String(length=60), nullable=True))
    op.execute("UPDATE seller_shops SET shop_theme='classic' WHERE shop_theme IS NULL")

    with op.batch_alter_table('categories', schema=None) as batch_op:
        batch_op.add_column(sa.Column('description', sa.Text(), nullable=True))
        batch_op.add_column(sa.Column('icon', sa.String(length=80), nullable=True))
    op.execute("UPDATE categories SET icon='fas fa-tag' WHERE icon IS NULL")


def downgrade():
    with op.batch_alter_table('categories', schema=None) as batch_op:
        batch_op.drop_column('icon')
        batch_op.drop_column('description')

    with op.batch_alter_table('seller_shops', schema=None) as batch_op:
        batch_op.drop_column('shop_theme')
