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

import logging
import warnings

import fixtures

from oslotest import log
from sqlalchemy import exc as sqla_exc


class NullHandler(logging.Handler):
    """Format the record to detect formatting errors, then discard it."""

    def handle(self, record):
        self.format(record)

    def emit(self, record):
        pass


class Logging(log.ConfigureLogging):
    def __init__(self):
        super().__init__()
        if self.level is None:
            self.level = logging.INFO

    def setUp(self):
        super().setUp()
        if self.level > logging.DEBUG:
            handler = NullHandler()
            self.useFixture(fixtures.LogHandler(handler, nuke_handlers=False))
            handler.setLevel(logging.DEBUG)


class WarningsFixture(fixtures.Fixture):
    def setUp(self):
        super().setUp()
        self._original_warning_filters = warnings.filters[:]
        warnings.simplefilter("once", DeprecationWarning)
        warnings.filterwarnings(
            'ignore',
            message="Policy .* failed scope check",
            category=UserWarning,
        )
        warnings.filterwarnings('error', message=".*invalid UUID.*")
        warnings.filterwarnings('error', category=sqla_exc.SAWarning)
        warnings.filterwarnings(
            'ignore', category=sqla_exc.SADeprecationWarning
        )
        warnings.filterwarnings(
            'error', module='cyborg', category=sqla_exc.SADeprecationWarning
        )
        self.addCleanup(self._reset_warning_filters)

    def _reset_warning_filters(self):
        warnings.filters[:] = self._original_warning_filters
