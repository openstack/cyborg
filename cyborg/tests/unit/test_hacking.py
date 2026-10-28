# Licensed under the Apache License, Version 2.0 (the "License"); you may
# not use this file except in compliance with the License. You may obtain
# a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
# WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
# License for the specific language governing permissions and limitations
# under the License.

import textwrap

from unittest import mock

import pycodestyle

from hacking import core

from cyborg.hacking import checks
from cyborg.tests import base


class HackingTestCase(base.TestCase):
    @mock.patch(
        'pycodestyle._checks',
        {'physical_line': {}, 'logical_line': {}, 'tree': {}},
    )
    def _run_check(self, code, checker, filename=None):
        pycodestyle.register_check(checker)
        lines = textwrap.dedent(code).strip().splitlines(True)
        checker = pycodestyle.Checker(filename=filename, lines=lines)
        with mock.patch('pycodestyle.StandardReport.get_file_results'):
            checker.check_all()
        checker.report._deferred_print.sort()
        return checker.report._deferred_print

    def _assert_has_errors(
        self, code, checker, expected_errors=None, filename=None
    ):
        actual_errors = [
            e[:3] for e in self._run_check(code, checker, filename)
        ]
        self.assertEqual(expected_errors or [], actual_errors)

    def _assert_has_no_errors(self, code, checker, filename=None):
        self._assert_has_errors(code, checker, filename=filename)

    def test_set_literal_attr_call(self):
        checker = checks.CheckSetLiteralInLogging
        code = """
            import logging
            LOG = logging.getLogger(__name__)
            LOG.info("%(fruit)s is ready", {"fruit", fruit})
        """
        self._assert_has_errors(
            code, checker, expected_errors=[(3, 31, "C300")]
        )

    def test_set_literal_log_method(self):
        checker = checks.CheckSetLiteralInLogging
        code = """
            import logging
            LOG = logging.getLogger(__name__)
            LOG.log(logging.INFO, "%(fruit)s", {"fruit", fruit})
        """
        self._assert_has_errors(
            code, checker, expected_errors=[(3, 35, "C300")]
        )

    def test_set_literal_module_call(self):
        checker = checks.CheckSetLiteralInLogging
        code = """
            import logging
            logging.info("%(fruit)s is ready", {"fruit", fruit})
        """
        self._assert_has_errors(
            code, checker, expected_errors=[(2, 35, "C300")]
        )

    def test_set_literal_multiple_placeholders(self):
        checker = checks.CheckSetLiteralInLogging
        code = """
            import logging
            LOG = logging.getLogger(__name__)
            LOG.info("%(a)s %(b)s", {"a", a, "b", b})
        """
        self._assert_has_errors(
            code, checker, expected_errors=[(3, 24, "C300")]
        )

    def test_set_literal_concat_format_string(self):
        checker = checks.CheckSetLiteralInLogging
        code = """
            import logging
            LOG = logging.getLogger(__name__)
            LOG.info("%(fruit)s" + " is ready", {"fruit", fruit})
        """
        self._assert_has_errors(
            code, checker, expected_errors=[(3, 36, "C300")]
        )

    def test_set_literal_multiline(self):
        checker = checks.CheckSetLiteralInLogging
        code = """
            import logging
            LOG = logging.getLogger(__name__)
            LOG.info(
                "%(fruit)s is ready",
                {"fruit", fruit},
            )
        """
        self._assert_has_errors(
            code, checker, expected_errors=[(5, 4, "C300")]
        )

    def test_dict_literal_no_error(self):
        checker = checks.CheckSetLiteralInLogging
        code = """
            import logging
            LOG = logging.getLogger(__name__)
            LOG.info("%(fruit)s is ready", {"fruit": fruit})
        """
        self._assert_has_no_errors(code, checker)

    def test_positional_placeholder_no_error(self):
        checker = checks.CheckSetLiteralInLogging
        code = """
            import logging
            LOG = logging.getLogger(__name__)
            LOG.info("items: %s", {a, b})
        """
        self._assert_has_no_errors(code, checker)

    def test_no_placeholders_no_error(self):
        checker = checks.CheckSetLiteralInLogging
        code = """
            import logging
            LOG = logging.getLogger(__name__)
            LOG.info("no placeholders", {"a", b})
        """
        self._assert_has_no_errors(code, checker)

    def test_variable_format_string_no_error(self):
        checker = checks.CheckSetLiteralInLogging
        code = """
            import logging
            LOG = logging.getLogger(__name__)
            msg = "%(fruit)s is ready"
            LOG.info(msg, {"fruit", fruit})
        """
        self._assert_has_no_errors(code, checker)

    def test_direct_class_import_first_party(self):
        checker = checks.CheckDirectClassImport
        code = """
            from cyborg.objects.device import Device
        """
        self._assert_has_errors(
            code, checker, expected_errors=[(1, 0, "C301")]
        )

    def test_direct_class_import_third_party(self):
        checker = checks.CheckDirectClassImport
        code = """
            from stevedore.extension import ExtensionManager
        """
        self._assert_has_errors(
            code, checker, expected_errors=[(1, 0, "C301")]
        )

    def test_direct_class_import_aliased(self):
        checker = checks.CheckDirectClassImport
        code = """
            from cyborg.agent.rpcapi import AgentAPI as rpc
        """
        self._assert_has_errors(
            code, checker, expected_errors=[(1, 0, "C301")]
        )

    def test_import_exception_submodule_no_error(self):
        # A submodule of a whitelisted module (sqlalchemy) is exempt too.
        checker = checks.CheckDirectClassImport
        code = """
            from sqlalchemy.orm.exc import NoResultFound
        """
        self._assert_has_no_errors(code, checker)

    def test_module_import_no_error(self):
        checker = checks.CheckDirectClassImport
        code = """
            from cyborg.objects import device
        """
        self._assert_has_no_errors(code, checker)

    def test_tox_import_exception_no_error(self):
        # collections.abc and typing are configured in
        # [hacking] import_exceptions.
        checker = checks.CheckDirectClassImport
        code = """
            from collections.abc import Mapping
            from typing import Optional
        """
        self._assert_has_no_errors(code, checker)

    def test_configured_import_exception_no_error(self):
        # A module made exempt via import_exceptions is not flagged.
        checker = checks.CheckDirectClassImport
        code = """
            from example_ext.widgets import FancyWidget
        """
        with mock.patch.object(core, 'IMPORT_EXCEPTIONS', ['example_ext']):
            self._assert_has_no_errors(code, checker)

    def test_sqlalchemy_dsl_import_no_error(self):
        checker = checks.CheckDirectClassImport
        code = """
            from sqlalchemy import Column
        """
        self._assert_has_no_errors(code, checker)

    def test_constant_import_error(self):
        # Constants are not modules, so importing them directly is flagged.
        checker = checks.CheckDirectClassImport
        code = """
            from cyborg.conf import CONF
            from cyborg.common.constants import ARQ_STATES_TRANSFORM_MATRIX
        """
        self._assert_has_errors(
            code, checker, expected_errors=[(1, 0, "C301"), (2, 0, "C301")]
        )

    def test_relative_import_no_error(self):
        checker = checks.CheckDirectClassImport
        code = """
            from . import base
        """
        self._assert_has_no_errors(code, checker)
