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

"""Shared file-backed SQLite fixture for unit and functional tests."""

import os
import sqlite3
import tempfile

import fixtures

from oslo_config import cfg
from oslo_db.sqlalchemy import enginefacade
from oslo_db.sqlalchemy import test_fixtures

from cyborg.db import api as dbapi
from cyborg.db.sqlalchemy import api as sqlalchemy_api
from cyborg.db.sqlalchemy import models
from cyborg.tests.local_fixtures.db_lock_fixture import DatabaseWriteLock


CONF = cfg.CONF


class DatabaseFixture(fixtures.Fixture):
    """File-backed SQLite database for one test run.

    Creates a temporary SQLite file with WAL mode enabled, replaces
    the application-level enginefacade, builds the schema from ORM
    models, and serializes writer transactions with DatabaseWriteLock.

    Attributes:
        dbapi: The database API instance for direct DB operations.
        engine: The SQLAlchemy engine backing this test database.
    """

    def _setUp(self):
        self.useFixture(fixtures.NestedTempfile())
        fd, dbfile_path = tempfile.mkstemp(prefix="cyborg_test_", suffix=".db")
        os.close(fd)
        self.addCleanup(os.unlink, dbfile_path)
        CONF.set_override(
            "connection", f"sqlite:///{dbfile_path}", group="database"
        )

        with sqlite3.connect(dbfile_path) as conn:
            conn.execute("PRAGMA journal_mode=WAL")

        local_ef = enginefacade.transaction_context()
        local_ef.configure(
            connection=CONF.database.connection,
            sqlite_synchronous=CONF.database.sqlite_synchronous,
        )
        self.useFixture(
            test_fixtures.ReplaceEngineFacadeFixture(
                sqlalchemy_api.main_context_manager, local_ef
            )
        )

        self.engine = local_ef.writer.get_engine()
        models.Base.metadata.create_all(self.engine)
        self.useFixture(DatabaseWriteLock())
        self.dbapi = dbapi.get_instance()
