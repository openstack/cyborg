"""new_db_schema

Revision ID: ede4e3f1a232
Revises: d6f033d8fa5b
Create Date: 2018-11-27 22:00:52.080713

"""

# revision identifiers, used by Alembic.
revision = 'ede4e3f1a232'
down_revision = 'd6f033d8fa5b'

from alembic import op
import sqlalchemy as sa

# TODO: The enum value should be further discussed.
state = sa.Enum('Initial', 'Bound', 'BindFailed', name='state')
substate = sa.Enum('Initial', name='substate')
attach_type = sa.Enum('PCI', 'MDEV', name='attach_type')
cpid_type = sa.Enum('PCI', name='cpid_type')
control_type = sa.Enum('PCI', name='control_type')
device_type = sa.Enum('GPU', 'FPGA', name='device_type')


def upgrade():
    # drop old table: deployable, accelerator
    op.drop_table('attributes')
    op.drop_table('deployables')
    op.drop_table('accelerators')

    op.create_table(
        'devices',
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('uuid', sa.String(length=36), nullable=False, unique=True),
        sa.Column('type', device_type, nullable=False),
        sa.Column('vendor', sa.String(length=255), nullable=False),
        sa.Column('model', sa.String(length=255), nullable=False),
        sa.Column('std_board_info', sa.Text(), nullable=True),
        sa.Column('vendor_board_info', sa.Text(), nullable=True),
        sa.Column('hostname', sa.String(length=255), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        mysql_ENGINE='InnoDB',
        mysql_DEFAULT_CHARSET='UTF8'
    )

    op.create_table(
        'deployables',
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('uuid', sa.String(length=36), nullable=False, unique=True),
        sa.Column('parent_id', sa.Integer(),
                  sa.ForeignKey('deployables.id', ondelete='CASCADE'),
                  nullable=True),
        sa.Column('root_id', sa.Integer(),
                  sa.ForeignKey('deployables.id', ondelete='CASCADE'),
                  nullable=True),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('num_accelerators', sa.Integer(), nullable=False),
        sa.Column('device_id', sa.Integer(),
                  sa.ForeignKey('devices.id', ondelete="RESTRICT"),
                  nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.Index('deployables_parent_id_idx', 'parent_id'),
        sa.Index('deployables_root_id_idx', 'root_id'),
        sa.Index('deployables_device_id_idx', 'device_id'),
        mysql_ENGINE='InnoDB',
        mysql_DEFAULT_CHARSET='UTF8'
    )

    op.create_table(
        'attributes',
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('uuid', sa.String(length=36), nullable=False, unique=True),
        sa.Column('deployable_id', sa.Integer(),
                  sa.ForeignKey('deployables.id', ondelete="RESTRICT"),
                  nullable=False, index=True),
        sa.Column('key', sa.Text(), nullable=False),
        sa.Column('value', sa.Text(), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        mysql_ENGINE='InnoDB',
        mysql_DEFAULT_CHARSET='UTF8'
    )

    op.create_table(
        'controlpath_ids',
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('uuid', sa.String(length=36), nullable=False, unique=True),
        sa.Column('device_id', sa.Integer(),
                  sa.ForeignKey('devices.id', ondelete="RESTRICT"),
                  nullable=False, index=True),
        sa.Column('cpid_type', cpid_type, nullable=False),
        sa.Column('cpid_info', sa.String(length=255), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        mysql_ENGINE='InnoDB',
        mysql_DEFAULT_CHARSET='UTF8'
    )

    op.create_table(
        'attach_handles',
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('uuid', sa.String(length=36), nullable=False, unique=True),
        sa.Column('deployable_id', sa.Integer(),
                  sa.ForeignKey('deployables.id', ondelete="RESTRICT"),
                  nullable=False),
        sa.Column('cpid_id', sa.Integer(),
                  sa.ForeignKey('controlpath_ids.id', ondelete="RESTRICT"),
                  nullable=False),
        sa.Column('in_use', sa.Boolean(), default=False),
        sa.Column('attach_type', attach_type, nullable=False),
        sa.Column('attach_info', sa.String(length=255), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.Index('attach_handles_deployable_id_idx', 'deployable_id'),
        sa.Index('attach_handles_cpid_id_idx', 'cpid_id'),
        mysql_ENGINE='InnoDB',
        mysql_DEFAULT_CHARSET='UTF8'
    )

    op.create_table(
        'device_profiles',
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('uuid', sa.String(length=36), nullable=False),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('profile_json', sa.Text(), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('uuid', 'name',
                            name='uniq_device_profiles0uuid0name'),
        mysql_ENGINE='InnoDB',
        mysql_DEFAULT_CHARSET='UTF8'
    )

    op.create_table(
        'extended_accelerator_requests',
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('uuid', sa.String(length=36), nullable=False, unique=True),
        # NOTICE: we don't have project related constraints in Stein Release,
        # set nullable=True but keep this field for further expansion.
        sa.Column('project_id', sa.String(length=255), nullable=True),
        sa.Column('state', state, nullable=False, default='Initial'),
        sa.Column('device_profile_id', sa.Integer(),
                  sa.ForeignKey('device_profiles.id', ondelete="RESTRICT"),
                  nullable=False),
        sa.Column('hostname', sa.String(length=255), nullable=True),
        sa.Column('device_rp_uuid', sa.String(length=36), nullable=True),
        sa.Column('device_instance_uuid', sa.String(length=36),
                  nullable=True),
        sa.Column('attach_handle_id', sa.Integer(),
                  sa.ForeignKey('attach_handles.id', ondelete="RESTRICT"),
                  nullable=True),
        # Cyborg Private Fields begin here.
        sa.Column('substate', substate, nullable=False, default='Initial'),
        sa.Column('deployable_id', sa.Integer(),
                  sa.ForeignKey('deployables.id', ondelete="RESTRICT"),
                  nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.Index('extArqs_project_id_idx', 'project_id'),
        sa.Index('extArqs_device_profile_id_idx', 'device_profile_id'),
        sa.Index('extArqs_device_rp_uuid_idx', 'device_rp_uuid'),
        sa.Index('extArqs_device_instance_uuid_idx', 'device_instance_uuid'),
        sa.Index('extArqs_attach_handle_id_idx', 'attach_handle_id'),
        sa.Index('extArqs_deployable_id_idx', 'deployable_id'),
        mysql_ENGINE='InnoDB',
        mysql_DEFAULT_CHARSET='UTF8'
    )
