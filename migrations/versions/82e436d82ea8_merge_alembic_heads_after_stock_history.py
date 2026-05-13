"""Merge Alembic heads after stock history

Revision ID: 82e436d82ea8
Revises: 
Create Date: 2026-05-13 09:10:48.910075

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '82e436d82ea8'
down_revision = ('6f3dfe46388e', 'c0f3d8b2a1d1')
branch_labels = None
depends_on = None


def upgrade():
    pass


def downgrade():
    pass
