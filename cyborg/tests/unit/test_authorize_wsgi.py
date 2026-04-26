# Copyright 2026 Red Hat, Inc.
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

from unittest import mock

from cyborg.common import authorize_wsgi
from cyborg.tests import base


class TestAuthorizeWSGI(base.TestCase):
    def test_init_enforcer_warns_when_scope_enforcement_disabled(self):
        self.flags(enforce_scope=False, group='oslo_policy')
        authorize_wsgi.get_enforcer().clear()
        authorize_wsgi._ENFORCER = None
        self.addCleanup(setattr, authorize_wsgi, '_ENFORCER', None)

        with mock.patch.object(authorize_wsgi.LOG, 'warning') as mock_warning:
            authorize_wsgi.init_enforcer(suppress_deprecation_warnings=True)

        mock_warning.assert_called_once()
        self.assertIn(
            'oslo_policy.enforce_scope is disabled',
            mock_warning.call_args[0][0]
        )
