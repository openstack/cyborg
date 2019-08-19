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

"""update_for_nova_integ

Revision ID: c1b5abada09c
Revises: 589ff20545b7
Create Date: 2019-07-11 22:13:45.773499

"""

# revision identifiers, used by Alembic.
revision = 'c1b5abada09c'
down_revision = '589ff20545b7'

from alembic import op
import sqlalchemy as sa

from cyborg.common import constants


def upgrade():
    # Update Deployables
    op.add_column(
        'deployables',
        sa.Column('rp_uuid', sa.String(length=36), nullable=True))
    op.add_column(
        'deployables',
        sa.Column('driver_name', sa.String(length=100), nullable=True))
    op.add_column(
        'deployables',
        sa.Column('bitstream_id', sa.String(length=36), nullable=True))

    # Update ExtARQ table
    op.add_column(
        'extended_accelerator_requests',
        sa.Column('device_profile_group_id', sa.Integer(), nullable=False))
    op.add_column(
        'extended_accelerator_requests',
        sa.Column('instance_uuid', sa.String(length=36),
                  nullable=True))
    op.create_index('extArqs_instance_uuid_idx',  # index name
                    'extended_accelerator_requests',  # table name
                    ['instance_uuid']  # columns on which index is defined
                    )
    op.drop_index('extArqs_device_instance_uuid_idx',  # index name
                  'extended_accelerator_requests',  # table name
                  )
    op.drop_column('extended_accelerator_requests', 'device_instance_uuid')
    # Add more valid states for 'state' field
    ns = sa.Enum(constants.ARQ_INITIAL,
                 constants.ARQ_BIND_STARTED,
                 constants.ARQ_BOUND,
                 constants.ARQ_UNBOUND,
                 constants.ARQ_BIND_FAILED,
                 constants.ARQ_DELETING, name='state')
    op.alter_column(
        'extended_accelerator_requests', 'state',
        existing_type=ns, nullable=False, default=constants.ARQ_INITIAL)

    # update attach type fields
    new_attach_type = sa.Enum(constants.AH_TYPE_PCI,
                              constants.AH_TYPE_MDEV,
                              constants.AH_TYPE_TEST_PCI,
                              name='attach_type')
    op.alter_column('attach_handles', 'attach_type',
                    existing_type=new_attach_type,
                    nullable=False)

    # Update device_profiles table to make name and uuid unique separately.
    # Previous schema made the pair unique.
    op.create_unique_constraint('uniq_device_profiles0uuid',
                                'device_profiles', ['uuid'])
    op.create_unique_constraint('uniq_device_profiles0name',
                                'device_profiles', ['name'])
    op.drop_constraint('uniq_device_profiles0uuid0name',
                       'device_profiles', type_='unique')
