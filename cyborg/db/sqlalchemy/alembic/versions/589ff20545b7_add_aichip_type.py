"""add_aichip_type

Revision ID: 589ff20545b7
Revises: ede4e3f1a232
Create Date: 2019-05-22 06:01:08.292535

"""

import sqlalchemy as sa

from alembic import op


# revision identifiers, used by Alembic.
revision = '589ff20545b7'
down_revision = 'ede4e3f1a232'


def upgrade():
    new_device_type = sa.Enum('GPU', 'FPGA', 'AICHIP', name='device_type')
    op.alter_column(
        'devices', 'type', existing_type=new_device_type, nullable=False
    )
