"""add_description_field_to_dps

Revision ID: 60d8ac91fd20
Revises: 7a4fd0fc3f8c
Create Date: 2020-01-19 16:15:04.231512

"""

# revision identifiers, used by Alembic.
revision = '60d8ac91fd20'
down_revision = '7a4fd0fc3f8c'

from alembic import op
import sqlalchemy as sa


def upgrade():
    op.add_column('device_profiles', sa.Column('description',
                  sa.Text(), nullable=True))
