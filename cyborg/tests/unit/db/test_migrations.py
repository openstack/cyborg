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

from alembic import script
import contextlib
import fixtures
import sqlalchemy
from unittest import mock

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
    with mock.patch.object(enginefacade.writer,
                           'get_engine') as patch_engine:
        patch_engine.return_value = engine
        yield


class WalkVersionsMixin(object):
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
                self._migrate_up(engine, alembic_cfg,
                                 version.revision, with_data=True)

    def _skippable_migrations(self):
        # Some db scripts are not necessary to check
        special = []
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
            check = getattr(self, "_check_%s" % version, None)
            if version not in self._skippable_migrations():
                self.assertIsNotNone(check, ('DB Migration %i does not have '
                                     'a test. Please add one!') % version)


class TestWalkVersions(base.TestCase, WalkVersionsMixin):
    def setUp(self):
        super(TestWalkVersions, self).setUp()
        self.migration_api = mock.MagicMock()
        self.engine = mock.MagicMock()
        self.config = mock.MagicMock()
        self.versions = [mock.Mock(revision='2b2'), mock.Mock(revision='1a1')]

    def test_migrate_up(self):
        self.migration_api.version.return_value = '6a7f90fc3s8c'
        self._migrate_up(self.engine, self.config, '6a7f90fc3s8c')
        self.migration_api.upgrade.assert_called_with('6a7f90fc3s8c',
                                                      config=self.config)
        self.migration_api.version.assert_called_with(self.config)


class CyborgMigrationsCheckers(object):

    def setUp(self):
        super(CyborgMigrationsCheckers, self).setUp()
        self.engine = enginefacade.writer.get_engine()
        self.config = migration._alembic_config()
        self.migration_api = migration
        self.useFixture(fixtures.Timeout(MIGRATIONS_TIMEOUT,
                                         gentle=True)),

    def test_walk_versions(self):
        self._walk_versions(self.engine, self.config)

    def _check_589ff20545b7(self, engine, data):
        devices = db_utils.get_table(engine, 'devices')
        col_names = [column.name for column in devices.c]
        self.assertIn('type', col_names)
        self.assertIsInstance(devices.c.type.type,
                              sqlalchemy.types.Enum)

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
            self.assertRaises(db_exc.DBMigrationError,
                              self.migration_api.create_schema)

    def test_upgrade_twice(self):
        with patch_with_engine(self.engine):
            self.migration_api.upgrade('ede4e3f1a232')
            v1 = self.migration_api.version()
            self.migration_api.upgrade('head')
            v2 = self.migration_api.version()
            self.assertNotEqual(v1, v2)


class TestCyborgMigrationsMySQL(CyborgMigrationsCheckers,
                                WalkVersionsMixin,
                                test_fixtures.OpportunisticDBTestMixin,
                                test_base.BaseTestCase):
    FIXTURE = test_fixtures.MySQLOpportunisticFixture


class TestMigrationsPostgreSQL(CyborgMigrationsCheckers,
                               WalkVersionsMixin,
                               test_fixtures.OpportunisticDBTestMixin,
                               test_base.BaseTestCase):
    FIXTURE = test_fixtures.PostgresqlOpportunisticFixture
