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

import os
from unittest import mock

from oslo_config import cfg
from oslo_config import fixture as config_fixture
from oslo_context import context
from oslo_db import options
from oslo_log import log
from oslo_utils import excutils
from oslotest import base

import contextlib
import eventlet
import testtools

from cyborg.common import config as cyborg_config
from cyborg.tests import post_mortem_debug
from cyborg.tests.unit import policy_fixture


CONF = cfg.CONF
options.set_defaults(cfg.CONF)
try:
    log.register_options(CONF)
except cfg.ArgsAlreadyParsedError:
    pass


class TestCase(base.BaseTestCase):
    """Test case base class for all unit tests."""

    def setUp(self):
        super(TestCase, self).setUp()
        self.context = context.get_admin_context()
        self._set_config()
        self.policy = self.useFixture(policy_fixture.PolicyFixture())

    def _set_config(self):
        self.cfg_fixture = self.useFixture(config_fixture.Config(cfg.CONF))
        self.config(use_stderr=False,
                    fatal_exception_format_errors=True)
        self.set_defaults(host='fake-mini',
                          debug=True)
        self.set_defaults(connection="sqlite://",
                          sqlite_synchronous=False,
                          group='database')
        cyborg_config.parse_args([], default_config_files=[])

    def config(self, **kw):
        """Override config options for a test."""
        self.cfg_fixture.config(**kw)

    def set_defaults(self, **kw):
        """Set default values of config options."""
        group = kw.pop('group', None)
        for o, v in kw.items():
            self.cfg_fixture.set_default(o, v, group=group)

    def get_path(self, project_file=None):
        """Get the absolute path to a file. Used for testing the API.

        :param project_file: File whose path to return. Default: None.
        :returns: path to the specified file, or path to project root.
        """
        root = os.path.abspath(
            os.path.join(os.path.dirname(__file__), '..', '..')
            )
        if project_file:
            return os.path.join(root, project_file)
        else:
            return root


# Test worker cannot survive eventlet's Timeout exception, which effectively
# kills the whole worker, with all test cases scheduled to it. This metaclass
# makes all test cases convert Timeout exceptions into unittest friendly
# failure mode (self.fail).
class DietTestCase(base.BaseTestCase):
    """Same great taste, less filling.

    BaseTestCase is responsible for doing lots of plugin-centric setup
    that not all tests require (or can tolerate).  This class provides
    only functionality that is common across all tests.
    """

    def setUp(self):
        super(DietTestCase, self).setUp()

        options.set_defaults(cfg.CONF, connection='sqlite://')

        debugger = os.environ.get('OS_POST_MORTEM_DEBUGGER')
        if debugger:
            self.addOnException(post_mortem_debug.get_exception_handler(
                debugger))

        self.addCleanup(mock.patch.stopall)

        self.addOnException(self.check_for_systemexit)
        self.orig_pid = os.getpid()

    def addOnException(self, handler):

        def safe_handler(*args, **kwargs):
            try:
                return handler(*args, **kwargs)
            except Exception:
                with excutils.save_and_reraise_exception(reraise=False) as ctx:
                    self.addDetail('Failure in exception handler %s' % handler,
                                   testtools.content.TracebackContent(
                                       (ctx.type_, ctx.value, ctx.tb), self))

        return super(DietTestCase, self).addOnException(safe_handler)

    def check_for_systemexit(self, exc_info):
        if isinstance(exc_info[1], SystemExit):
            if os.getpid() != self.orig_pid:
                # Subprocess - let it just exit
                raise
            # This makes sys.exit(0) still a failure
            self.force_failure = True

    @contextlib.contextmanager
    def assert_max_execution_time(self, max_execution_time=5):
        with eventlet.Timeout(max_execution_time, False):
            yield
            return
        self.fail('Execution of this test timed out')

    def assertOrderedEqual(self, expected, actual):
        expect_val = self.sort_dict_lists(expected)
        actual_val = self.sort_dict_lists(actual)
        self.assertEqual(expect_val, actual_val)

    def sort_dict_lists(self, dic):
        for key, value in dic.items():
            if isinstance(value, list):
                dic[key] = sorted(value)
            elif isinstance(value, dict):
                dic[key] = self.sort_dict_lists(value)
        return dic

    def assertDictSupersetOf(self, expected_subset, actual_superset):
        """Checks that actual dict contains the expected dict.

        After checking that the arguments are of the right type, this checks
        that each item in expected_subset is in, and matches, what is in
        actual_superset. Separate tests are done, so that detailed info can
        be reported upon failure.
        """
        if not isinstance(expected_subset, dict):
            self.fail("expected_subset (%s) is not an instance of dict" %
                      type(expected_subset))
        if not isinstance(actual_superset, dict):
            self.fail("actual_superset (%s) is not an instance of dict" %
                      type(actual_superset))
        for k, v in expected_subset.items():
            self.assertIn(k, actual_superset)
            self.assertEqual(v, actual_superset[k],
                             "Key %(key)s expected: %(exp)r, actual %(act)r" %
                             {'key': k, 'exp': v, 'act': actual_superset[k]})
