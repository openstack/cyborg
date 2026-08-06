"""add device_state

Revision ID: b47c8f2d1e3a
Revises: a35b4295a0e5
Create Date: 2026-08-04 00:01:00.000000

"""

import sqlalchemy as sa

from alembic import op


# revision identifiers, used by Alembic.
revision = 'b47c8f2d1e3a'
down_revision = 'a35b4295a0e5'


def upgrade():
    device_state_enum = sa.Enum(
        'available',
        'allocated',
        'pending_cleaning',
        'cleaning',
        'error',
        name='device_state',
    )
    device_state_enum.create(op.get_bind(), checkfirst=True)
    op.add_column(
        'devices',
        sa.Column('device_state', device_state_enum, nullable=True),
    )
