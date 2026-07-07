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

import contextlib

from unittest import mock

import fixtures
import sqlalchemy

from alembic import script
from oslo_db import exception as db_exc
from oslo_db.sqlalchemy import enginefacade
from oslo_db.sqlalchemy import test_fixtures
from oslo_db.sqlalchemy import utils as db_utils
from oslo_log import log as logging
from oslotest import base as test_base

from cyborg.db.sqlalchemy import migration
from cyborg.tests import base


LOG = logging.getLogger(__name__)

# NOTE(brinzhang): This was introduced after migration tests started taking
# more time in gate. Timeout value in seconds for tests performing migrations.
MIGRATIONS_TIMEOUT = 300


@contextlib.contextmanager
def patch_with_engine(engine):
    with mock.patch.object(enginefacade.writer, 'get_engine') as patch_engine:
        patch_engine.return_value = engine
        yield


class WalkVersionsMixin:
    def _walk_versions(self, engine=None, alembic_cfg=None):
        # Determine latest version script from the repo, then
        # upgrade from 1 through to the latest, with no data
        # in the databases. This just checks that the schema itself
        # upgrades successfully.

        # Place the database under version control
        with patch_with_engine(engine):
            script_directory = script.ScriptDirectory.from_config(alembic_cfg)

            self.assertIsNone(self.migration_api.version(alembic_cfg))

            versions = [ver for ver in script_directory.walk_revisions()]

            for version in reversed(versions):
                self._migrate_up(
                    engine, alembic_cfg, version.revision, with_data=True
                )

    def _skippable_migrations(self):
        # Placeholder migrations with empty upgrade() (pass).
        # They exist only to maintain the Alembic revision chain
        # after older migrations were squashed/removed.
        special = {
            "57539722e5cf",
            "22fb1af2d51e",
            "7b696fd94949",
            "62bcf2610c5d",
            "7a4fd0fc3f8c",
        }
        return special

    def _migrate_up(self, engine, config, version, with_data=False):
        """migrate up to a new version of the db.

        We allow for data insertion and post checks at every
        migration version with special _pre_upgrade_### and
        _check_### functions in the main test
        """
        self.migration_api.upgrade(version, config=config)
        self.assertEqual(version, self.migration_api.version(config))
        if with_data:
            check = getattr(self, f"_check_{version}", None)
            if version not in self._skippable_migrations():
                self.assertIsNotNone(
                    check,
                    f'DB Migration {version} does not have '
                    'a test. Please add one!',
                )
                check(engine, None)


class TestWalkVersions(base.TestCase, WalkVersionsMixin):
    def setUp(self):
        super().setUp()
        self.migration_api = mock.MagicMock()
        self.engine = mock.MagicMock()
        self.config = mock.MagicMock()
        self.versions = [mock.Mock(revision='2b2'), mock.Mock(revision='1a1')]

    def test_migrate_up(self):
        self.migration_api.version.return_value = '6a7f90fc3s8c'
        self._migrate_up(self.engine, self.config, '6a7f90fc3s8c')
        self.migration_api.upgrade.assert_called_with(
            '6a7f90fc3s8c', config=self.config
        )
        self.migration_api.version.assert_called_with(self.config)


class CyborgMigrationsCheckers:
    def setUp(self):
        super().setUp()
        self.engine = enginefacade.writer.get_engine()
        self.config = migration._alembic_config()
        self.migration_api = migration
        (self.useFixture(fixtures.Timeout(MIGRATIONS_TIMEOUT, gentle=True)),)

    def test_walk_versions(self):
        self._walk_versions(self.engine, self.config)

    def _check_f50980397351(self, engine, data):
        accelerators = db_utils.get_table(engine, 'accelerators')
        acc_col_names = [c.name for c in accelerators.c]
        for col in (
            'id',
            'uuid',
            'name',
            'description',
            'project_id',
            'user_id',
            'device_type',
            'acc_type',
            'acc_capability',
            'vendor_id',
            'product_id',
            'remotable',
        ):
            self.assertIn(col, acc_col_names)

        deployables = db_utils.get_table(engine, 'deployables')
        dep_col_names = [c.name for c in deployables.c]
        for col in (
            'id',
            'uuid',
            'name',
            'parent_uuid',
            'root_uuid',
            'address',
            'host',
            'board',
            'vendor',
            'version',
            'type',
            'interface_type',
            'assignable',
            'instance_uuid',
            'availability',
            'accelerator_id',
        ):
            self.assertIn(col, dep_col_names)

        attributes = db_utils.get_table(engine, 'attributes')
        attr_col_names = [c.name for c in attributes.c]
        for col in (
            'id',
            'uuid',
            'deployable_id',
            'key',
            'value',
        ):
            self.assertIn(col, attr_col_names)

    def _check_d6f033d8fa5b(self, engine, data):
        quota_usages = db_utils.get_table(engine, 'quota_usages')
        qu_col_names = [c.name for c in quota_usages.c]
        for col in (
            'id',
            'project_id',
            'user_id',
            'resource',
            'in_use',
            'reserved',
            'until_refresh',
        ):
            self.assertIn(col, qu_col_names)

        reservations = db_utils.get_table(engine, 'reservations')
        res_col_names = [c.name for c in reservations.c]
        for col in (
            'id',
            'uuid',
            'usage_id',
            'project_id',
            'user_id',
            'resource',
            'delta',
            'expire',
        ):
            self.assertIn(col, res_col_names)

        res_idx_names = [idx.name for idx in reservations.indexes]
        self.assertIn('reservations_uuid_idx', res_idx_names)

    def _check_ede4e3f1a232(self, engine, data):
        expected_tables = [
            'devices',
            'deployables',
            'attributes',
            'controlpath_ids',
            'attach_handles',
            'device_profiles',
            'extended_accelerator_requests',
        ]
        for table_name in expected_tables:
            table = db_utils.get_table(engine, table_name)
            self.assertIsNotNone(table)

        devices = db_utils.get_table(engine, 'devices')
        dev_col_names = [c.name for c in devices.c]
        for col in ('id', 'uuid', 'type', 'vendor', 'model', 'hostname'):
            self.assertIn(col, dev_col_names)
        self.assertIsInstance(devices.c.type.type, sqlalchemy.types.Enum)

        deployables = db_utils.get_table(engine, 'deployables')
        dep_col_names = [c.name for c in deployables.c]
        for col in (
            'id',
            'uuid',
            'parent_id',
            'root_id',
            'name',
            'num_accelerators',
            'device_id',
        ):
            self.assertIn(col, dep_col_names)

        dp = db_utils.get_table(engine, 'device_profiles')
        dp_col_names = [c.name for c in dp.c]
        for col in ('id', 'uuid', 'name', 'profile_json'):
            self.assertIn(col, dp_col_names)

        extarqs = db_utils.get_table(engine, 'extended_accelerator_requests')
        ea_col_names = [c.name for c in extarqs.c]
        for col in (
            'id',
            'uuid',
            'state',
            'substate',
            'device_profile_id',
            'attach_handle_id',
            'deployable_id',
        ):
            self.assertIn(col, ea_col_names)

    def _check_589ff20545b7(self, engine, data):
        devices = db_utils.get_table(engine, 'devices')
        col_names = [column.name for column in devices.c]
        self.assertIn('type', col_names)
        self.assertIsInstance(devices.c.type.type, sqlalchemy.types.Enum)

    def _check_c1b5abada09c(self, engine, data):
        deployables = db_utils.get_table(engine, 'deployables')
        dep_col_names = [c.name for c in deployables.c]
        for col in ('rp_uuid', 'driver_name', 'bitstream_id'):
            self.assertIn(col, dep_col_names)

        extarqs = db_utils.get_table(engine, 'extended_accelerator_requests')
        ea_col_names = [c.name for c in extarqs.c]
        self.assertIn('device_profile_group_id', ea_col_names)
        self.assertIn('instance_uuid', ea_col_names)
        self.assertNotIn('device_instance_uuid', ea_col_names)

        ea_idx_names = [idx.name for idx in extarqs.indexes]
        self.assertIn('extArqs_instance_uuid_idx', ea_idx_names)
        self.assertNotIn('extArqs_device_instance_uuid_idx', ea_idx_names)

    def _check_60d8ac91fd20(self, engine, data):
        dp = db_utils.get_table(engine, 'device_profiles')
        col_names = [c.name for c in dp.c]
        self.assertIn('description', col_names)

    def _check_7e6f1f107f2b(self, engine, data):
        devices = db_utils.get_table(engine, 'devices')
        self.assertIn('QAT', devices.c.type.type.enums)

    def _check_899cead40bc9(self, engine, data):
        devices = db_utils.get_table(engine, 'devices')
        self.assertIn('NIC', devices.c.type.type.enums)

    def _check_4cc1d79978fc(self, engine, data):
        devices = db_utils.get_table(engine, 'devices')
        self.assertIn('SSD', devices.c.type.type.enums)

    def _check_6c77bd6afea5(self, engine, data):
        devices = db_utils.get_table(engine, 'devices')
        col_names = [c.name for c in devices.c]
        self.assertIn('status', col_names)
        self.assertIsInstance(devices.c.status.type, sqlalchemy.types.Enum)

    def _check_9625668549b5(self, engine, data):
        devices = db_utils.get_table(engine, 'devices')
        col_names = [column.name for column in devices.c]
        self.assertIn('type', col_names)
        self.assertIsInstance(devices.c.type.type, sqlalchemy.types.Enum)
        expected_types = {
            'GPU',
            'FPGA',
            'AICHIP',
            'QAT',
            'NIC',
            'SSD',
            'MDEV',
            'PCI',
        }
        actual_types = set(devices.c.type.type.enums)
        self.assertEqual(expected_types, actual_types)

    def test_upgrade_and_version(self):
        with patch_with_engine(self.engine):
            self.migration_api.upgrade('head')
            self.assertIsNotNone(self.migration_api.version())

    def test_create_schema_and_version(self):
        with patch_with_engine(self.engine):
            self.migration_api.create_schema()
            self.assertIsNotNone(self.migration_api.version())

    def test_upgrade_and_create_schema(self):
        with patch_with_engine(self.engine):
            self.migration_api.upgrade('ede4e3f1a232')
            self.assertRaises(
                db_exc.DBMigrationError, self.migration_api.create_schema
            )

    def test_upgrade_twice(self):
        with patch_with_engine(self.engine):
            self.migration_api.upgrade('ede4e3f1a232')
            v1 = self.migration_api.version()
            self.migration_api.upgrade('head')
            v2 = self.migration_api.version()
            self.assertNotEqual(v1, v2)


class TestCyborgMigrationsMySQL(
    CyborgMigrationsCheckers,
    WalkVersionsMixin,
    test_fixtures.OpportunisticDBTestMixin,
    test_base.BaseTestCase,
):
    FIXTURE = test_fixtures.MySQLOpportunisticFixture


class TestMigrationsPostgreSQL(
    CyborgMigrationsCheckers,
    WalkVersionsMixin,
    test_fixtures.OpportunisticDBTestMixin,
    test_base.BaseTestCase,
):
    FIXTURE = test_fixtures.PostgresqlOpportunisticFixture
