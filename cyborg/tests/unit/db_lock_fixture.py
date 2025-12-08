# Copyright 2026 Red Hat, Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License"); you may
# not use this file except in compliance with the License. You may obtain
# a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
# WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
# License for the specific language governing permissions and limitations
# under the License.

"""Threading lock fixture for database write operations in Cyborg tests."""

import contextlib
import threading

import fixtures

from oslo_db.sqlalchemy import enginefacade


_DB_WRITE_LOCK = threading.Lock()


class DatabaseWriteLock(fixtures.Fixture):
    """Serialize writer transactions across threads in tests.

    SQLite supports only a single writer at a time. WAL mode allows
    concurrent readers, so only writer transactions need serialization.

    Patches _TransactionContextManager._transaction_scope to acquire
    a process-global lock around writer transactions.
    """

    def _setUp(self):
        original = (
            enginefacade._TransactionContextManager._transaction_scope)

        @contextlib.contextmanager
        def _locked_scope(tcm_self, context):
            if tcm_self._mode is enginefacade._WRITER:
                _DB_WRITE_LOCK.acquire()
                try:
                    with original(tcm_self, context) as resource:
                        yield resource
                finally:
                    _DB_WRITE_LOCK.release()
            else:
                with original(tcm_self, context) as resource:
                    yield resource

        self.useFixture(fixtures.MockPatchObject(
            enginefacade._TransactionContextManager,
            '_transaction_scope',
            _locked_scope))
