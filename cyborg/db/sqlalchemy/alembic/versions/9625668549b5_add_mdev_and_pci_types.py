"""add_mdev_and_pci_types

Revision ID: 9625668549b5
Revises: 6c77bd6afea5
Create Date: 2026-07-07 12:00:00.000000

"""

import sqlalchemy as sa

from alembic import op


# revision identifiers, used by Alembic.
revision = '9625668549b5'
down_revision = '6c77bd6afea5'


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
        name='device_type',
    )
    op.alter_column(
        'devices',
        'type',
        existing_type=new_device_type,
        nullable=False,
    )
