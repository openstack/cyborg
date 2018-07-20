#
#    Licensed under the Apache License, Version 2.0 (the "License"); you may
#    not use this file except in compliance with the License. You may obtain
#    a copy of the License at
#
#         http://www.apache.org/licenses/LICENSE-2.0
#
#    Unless required by applicable law or agreed to in writing, software
#    distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
#    WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
#    License for the specific language governing permissions and limitations
#    under the License.

"""initial migration.

Revision ID: f50980397351
Revises: None
Create Date: 2017-08-15 08:44:36.010417

"""

# revision identifiers, used by Alembic.
revision = 'f50980397351'
down_revision = None


from alembic import op
import sqlalchemy as sa


def upgrade():
    op.create_table(
        'accelerators',
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('uuid', sa.String(length=36), nullable=False),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('project_id', sa.String(length=36), nullable=True),
        sa.Column('user_id', sa.String(length=36), nullable=True),
        sa.Column('device_type', sa.Text(), nullable=False),
        sa.Column('acc_type', sa.Text(), nullable=True),
        sa.Column('acc_capability', sa.Text(), nullable=True),
        sa.Column('vendor_id', sa.Text(), nullable=False),
        sa.Column('product_id', sa.Text(), nullable=False),
        sa.Column('remotable', sa.Integer(), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('uuid', name='uniq_accelerators0uuid'),
        mysql_ENGINE='InnoDB',
        mysql_DEFAULT_CHARSET='UTF8'
    )

    op.create_table(
        'deployables',
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('uuid', sa.String(length=36), nullable=False),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('parent_uuid', sa.String(length=36),
                  sa.ForeignKey('deployables.uuid'), nullable=True),
        sa.Column('root_uuid', sa.String(length=36),
                  sa.ForeignKey('deployables.uuid'), nullable=True),
        sa.Column('address', sa.Text(), nullable=False),
        sa.Column('host', sa.Text(), nullable=False),
        sa.Column('board', sa.Text(), nullable=False),
        sa.Column('vendor', sa.Text(), nullable=False),
        sa.Column('version', sa.Text(), nullable=False),
        sa.Column('type', sa.Text(), nullable=False),
        sa.Column('interface_type', sa.Text(), nullable=False),
        sa.Column('assignable', sa.Boolean(), nullable=False),
        sa.Column('instance_uuid', sa.String(length=36), nullable=True),
        sa.Column('availability', sa.Text(), nullable=False),
        sa.Column('accelerator_id', sa.Integer(),
                  sa.ForeignKey('accelerators.id', ondelete="CASCADE"),
                  nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('uuid', name='uniq_deployables0uuid'),
        sa.Index('deployables_parent_uuid_idx', 'parent_uuid'),
        sa.Index('deployables_root_uuid_idx', 'root_uuid'),
        mysql_ENGINE='InnoDB',
        mysql_DEFAULT_CHARSET='UTF8'
    )

    op.create_table(
        'attributes',
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('uuid', sa.String(length=36), nullable=False),
        sa.Column('deployable_id', sa.Integer(),
                  sa.ForeignKey('deployables.id', ondelete="CASCADE"),
                  nullable=False),
        sa.Column('key', sa.Text(), nullable=False),
        sa.Column('value', sa.Text(), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('uuid', name='uniq_attributes0uuid'),
        sa.Index('attributes_deployable_id_idx', 'deployable_id'),
        mysql_ENGINE='InnoDB',
        mysql_DEFAULT_CHARSET='UTF8'
    )
