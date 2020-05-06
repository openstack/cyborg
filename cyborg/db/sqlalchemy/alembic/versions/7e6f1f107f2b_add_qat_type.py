"""add_qat_type

Revision ID: 7e6f1f107f2b
Revises: c1b5abada09c
Create Date: 2019-07-17 04:21:52.055863

"""

# revision identifiers, used by Alembic.
revision = '7e6f1f107f2b'
down_revision = '60d8ac91fd20'

from alembic import op
import sqlalchemy as sa


def upgrade():
    new_device_type = sa.Enum('GPU', 'FPGA', 'AICHIP', 'QAT',
                              name='device_type')
    op.alter_column('devices', 'type',
                    existing_type=new_device_type,
                    nullable=False)
