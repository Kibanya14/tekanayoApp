"""Add categories table and link products to categories

Revision ID: a42d3c5e8f7b
Revises: 82e436d82ea8
Create Date: 2026-06-01 12:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'a42d3c5e8f7b'
down_revision = '6360133e734d'
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        'categories',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('shop_id', sa.Integer(), sa.ForeignKey('seller_shops.id'), nullable=False),
        sa.Column('name', sa.String(length=100), nullable=False),
        sa.Column('is_active', sa.Boolean(), nullable=True, default=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
    )
    with op.batch_alter_table('categories', schema=None) as batch_op:
        batch_op.create_unique_constraint('uq_category_shop_name', ['shop_id', 'name'])
        batch_op.create_index(batch_op.f('ix_categories_shop_id'), ['shop_id'], unique=False)

    with op.batch_alter_table('seller_products', schema=None) as batch_op:
        batch_op.add_column(sa.Column('category_id', sa.Integer(), nullable=True))
        batch_op.create_foreign_key('fk_seller_products_category_id', 'categories', ['category_id'], ['id'])
        batch_op.create_index(batch_op.f('ix_seller_products_category_id'), ['category_id'], unique=False)


def downgrade():
    with op.batch_alter_table('seller_products', schema=None) as batch_op:
        batch_op.drop_constraint('fk_seller_products_category_id', type_='foreignkey')
        batch_op.drop_index(batch_op.f('ix_seller_products_category_id'))
        batch_op.drop_column('category_id')

    with op.batch_alter_table('categories', schema=None) as batch_op:
        batch_op.drop_constraint('uq_category_shop_name', type_='unique')
        batch_op.drop_index(batch_op.f('ix_categories_shop_id'))

    op.drop_table('categories')
