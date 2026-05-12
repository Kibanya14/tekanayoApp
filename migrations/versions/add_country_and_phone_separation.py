"""Add country_code and phone_number fields to support separated phone numbers

Revision ID: add_phone_separation
Revises: 730c7142aef6
Create Date: 2026-03-07 12:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'add_phone_separation'
down_revision = '730c7142aef6'
branch_labels = None
depends_on = None


def upgrade():
    # Add country_code and phone_number to platform_admins
    with op.batch_alter_table('platform_admins', schema=None) as batch_op:
        batch_op.add_column(sa.Column('country_code', sa.String(2), nullable=True))
        batch_op.add_column(sa.Column('phone_number', sa.String(20), nullable=True))

    # Add country_code and phone_number to seller_admins
    with op.batch_alter_table('seller_admins', schema=None) as batch_op:
        batch_op.add_column(sa.Column('country_code', sa.String(2), nullable=True))
        batch_op.add_column(sa.Column('phone_number', sa.String(20), nullable=True))

    # Add country_code and phone_number to seller_deliverers
    with op.batch_alter_table('seller_deliverers', schema=None) as batch_op:
        batch_op.add_column(sa.Column('country_code', sa.String(2), nullable=True))
        batch_op.add_column(sa.Column('phone_number', sa.String(20), nullable=True))

    # Add country_code and phone_number to seller_customers
    with op.batch_alter_table('seller_customers', schema=None) as batch_op:
        batch_op.add_column(sa.Column('country_code', sa.String(2), nullable=True))
        batch_op.add_column(sa.Column('phone_number', sa.String(20), nullable=True))


def downgrade():
    # Remove country_code and phone_number from platform_admins
    with op.batch_alter_table('platform_admins', schema=None) as batch_op:
        batch_op.drop_column('country_code')
        batch_op.drop_column('phone_number')

    # Remove country_code and phone_number from seller_admins
    with op.batch_alter_table('seller_admins', schema=None) as batch_op:
        batch_op.drop_column('country_code')
        batch_op.drop_column('phone_number')

    # Remove country_code and phone_number from seller_deliverers
    with op.batch_alter_table('seller_deliverers', schema=None) as batch_op:
        batch_op.drop_column('country_code')
        batch_op.drop_column('phone_number')

    # Remove country_code and phone_number from seller_customers
    with op.batch_alter_table('seller_customers', schema=None) as batch_op:
        batch_op.drop_column('country_code')
        batch_op.drop_column('phone_number')
