"""add-device-status

Revision ID: 6c77bd6afea5
Revises: 4cc1d79978fc
Create Date: 2023-08-15 23:05:31.918963

"""

# revision identifiers, used by Alembic.
revision = '6c77bd6afea5'
down_revision = '4cc1d79978fc'

from alembic import op
import sqlalchemy as sa



def upgrade():
    new_column = sa.Column('status', sa.Enum('enabled', 'maintaining'),
                           nullable=False, default='enabled')
    op.add_column('devices', new_column)
