"""add_ssd_type

Revision ID: 4cc1d79978fc
Revises: 899cead40bc9
Create Date: 2021-02-15 16:02:58.856126

"""

# revision identifiers, used by Alembic.
revision = '4cc1d79978fc'
down_revision = '899cead40bc9'

from alembic import op
import sqlalchemy as sa


def upgrade():
    new_device_type = sa.Enum('GPU', 'FPGA', 'AICHIP', 'QAT', 'NIC', 'SSD',
                             name='device_type')
    op.alter_column('devices', 'type',
                    existing_type=new_device_type,
                    nullable=False)
