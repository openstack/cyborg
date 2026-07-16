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

import alembic.migration as alembic_migration

from alembic.script import ScriptDirectory

from cyborg.db.sqlalchemy import migration
from cyborg.tests import base
from cyborg.tests.local_fixtures import db_fixture


class DbTestCase(base.TestCase):
    def setUp(self):
        super().setUp()
        db_fix = self.useFixture(db_fixture.DatabaseFixture())
        self.dbapi = db_fix.dbapi

        # Stamp Alembic to head so migration-aware tests see the
        # correct version.
        alembic_cfg = migration._alembic_config()
        script = ScriptDirectory.from_config(alembic_cfg)
        with db_fix.engine.connect() as conn:
            context = alembic_migration.MigrationContext.configure(conn)
            context.stamp(script, 'head')
            conn.commit()
