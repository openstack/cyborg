"""add_nic_type

Revision ID: 899cead40bc9
Revises: 7e6f1f107f2b
Create Date: 2020-09-18 02:33:42.640673

"""

# revision identifiers, used by Alembic.
revision = '899cead40bc9'
down_revision = '7e6f1f107f2b'

from alembic import op
import sqlalchemy as sa


def upgrade():
    new_device_type = sa.Enum('GPU', 'FPGA', 'AICHIP', 'QAT', 'NIC',
                             name='device_type')
    op.alter_column('devices', 'type',
                    existing_type=new_device_type,
                    nullable=False)
