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

import http

from unittest import mock

from cyborg import context as cyborg_context
from cyborg.common import authorize_wsgi
from cyborg.common import exception
from cyborg.tests import base


class TestAuthorizeWSGI(base.TestCase):
    def test_authorize_wsgi_uses_request_context_target(self):
        context = cyborg_context.RequestContext(
            user_id='user-id',
            project_id='project-id',
            roles=['reader'],
            is_admin=False,
        )
        request = authorize_wsgi.pecan.Request.blank('/v2/test')
        request.context = context

        class TestController:
            # The decorator must not call the removed resource-target path.
            def _get_resource(self):
                raise AssertionError('_get_resource should not be called')

        def test_method(self):
            return 'ok'

        wrapped = authorize_wsgi.authorize_wsgi('cyborg:test', 'get_one')(
            test_method
        )

        with (
            mock.patch.object(authorize_wsgi.pecan, 'request', request),
            mock.patch.object(
                authorize_wsgi, 'authorize', autospec=True
            ) as auth,
        ):
            self.assertEqual('ok', wrapped(TestController()))

        auth.assert_called_once()
        rule, target, credentials = auth.call_args.args[:3]
        self.assertEqual('cyborg:test:get_one', rule)
        self.assertEqual(
            {'project_id': 'project-id', 'user_id': 'user-id'}, target
        )
        self.assertEqual(['reader'], credentials['roles'])
        self.assertIs(False, credentials['is_admin'])
        self.assertTrue(auth.call_args.kwargs['do_raise'])

    def test_authorize_wsgi_returns_403_when_policy_denied(self):
        context = cyborg_context.RequestContext(
            user_id='user-id',
            project_id='project-id',
            roles=['reader'],
            is_admin=False,
        )
        request = authorize_wsgi.pecan.Request.blank('/v2/test')
        request.context = context
        response = authorize_wsgi.pecan.Response()

        def test_method(self):
            return 'ok'

        wrapped = authorize_wsgi.authorize_wsgi('cyborg:device', 'disable')(
            test_method
        )

        with (
            mock.patch.object(authorize_wsgi.pecan, 'request', request),
            mock.patch.object(authorize_wsgi.pecan, 'response', response),
            mock.patch.object(
                authorize_wsgi,
                'authorize',
                autospec=True,
                side_effect=exception.HTTPForbidden(
                    resource='cyborg:device:disable'
                ),
            ),
        ):
            payload = wrapped(object())

        self.assertNotEqual('ok', payload)
        self.assertEqual(http.HTTPStatus.FORBIDDEN, response.status_int)
        self.assertIn('faultcode', payload)
        self.assertIn('faultstring', payload)
        self.assertIn('cyborg:device:disable', payload['faultstring'])
