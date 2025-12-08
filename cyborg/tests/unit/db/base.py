# Copyright 2017 Huawei Technologies Co.,LTD.
# All Rights Reserved.
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

"""Cyborg DB test base class."""

import os
import sqlite3
import tempfile

import alembic.migration as alembic_migration
from alembic.script import ScriptDirectory
import fixtures
from oslo_config import cfg
from oslo_db.sqlalchemy import enginefacade
from oslo_db.sqlalchemy import test_fixtures

from cyborg.db import api as dbapi
from cyborg.db.sqlalchemy import api as sqlalchemy_api
from cyborg.db.sqlalchemy import migration
from cyborg.db.sqlalchemy import models
from cyborg.tests import base
from cyborg.tests.unit.db_lock_fixture import DatabaseWriteLock


CONF = cfg.CONF


class DbTestCase(base.TestCase):

    def setUp(self):
        super(DbTestCase, self).setUp()

        # Create a temporary directory for SQLite temp files;
        # NestedTempfile patches tempfile to use it as the default.
        self.useFixture(fixtures.NestedTempfile())

        # File-backed SQLite so each thread gets its own connection.
        fd, dbfile_path = tempfile.mkstemp(
            prefix="cyborg_test_", suffix=".db")
        os.close(fd)
        CONF.set_override(
            "connection", "sqlite:///%s" % dbfile_path,
            group="database")

        # WAL mode: readers don't block writers, writer doesn't
        # block readers.
        with sqlite3.connect(dbfile_path) as conn:
            conn.execute("PRAGMA journal_mode=WAL")

        # Fresh enginefacade per test, replacing the app-level one.
        local_enginefacade = enginefacade.transaction_context()
        local_enginefacade.configure(
            connection=CONF.database.connection,
            sqlite_synchronous=CONF.database.sqlite_synchronous)
        self.useFixture(
            test_fixtures.ReplaceEngineFacadeFixture(
                sqlalchemy_api.main_context_manager,
                local_enginefacade))

        # Build schema from models directly, bypassing Alembic's env.py
        # which would create its own engine via the global enginefacade.
        engine = local_enginefacade.writer.get_engine()
        models.Base.metadata.create_all(engine)
        alembic_cfg = migration._alembic_config()
        script = ScriptDirectory.from_config(alembic_cfg)
        with engine.connect() as conn:
            context = alembic_migration.MigrationContext.configure(conn)
            context.stamp(script, 'head')
            conn.commit()

        # SQLite only supports one writer; serialize write txns.
        self.useFixture(DatabaseWriteLock())

        self.dbapi = dbapi.get_instance()
