"""add nvme type

Revision ID: a35b4295a0e5
Revises: 9625668549b5
Create Date: 2026-08-04 00:00:00.000000

"""

import sqlalchemy as sa

from alembic import op


# revision identifiers, used by Alembic.
revision = 'a35b4295a0e5'
down_revision = '9625668549b5'


def upgrade():
    new_device_type = sa.Enum(
        'GPU',
        'FPGA',
        'AICHIP',
        'QAT',
        'NIC',
        'SSD',
        'MDEV',
        'PCI',
        'NVME',
        name='device_type',
    )
    op.alter_column(
        'devices',
        'type',
        existing_type=new_device_type,
        nullable=False,
    )
