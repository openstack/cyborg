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

"""Base classes for API tests."""

from oslo_config import cfg
import pecan
import pecan.testing

from cyborg.tests.unit.db import base


cfg.CONF.import_group('keystone_authtoken', 'keystonemiddleware.auth_token')


class BaseApiTest(base.DbTestCase):
    """Pecan controller functional testing class.

    Used for functional tests of Pecan controllers where you need to
    test your literal application and its integration with the
    framework.
    """

    PATH_PREFIX = ''

    def setUp(self):
        super(BaseApiTest, self).setUp()
        cfg.CONF.set_override("auth_version", "v3",
                              group='keystone_authtoken')
        cfg.CONF.set_override("admin_user", "admin",
                              group='keystone_authtoken')
        self.app = self._make_app()

        def reset_pecan():
            pecan.set_config({}, overwrite=True)

        self.addCleanup(reset_pecan)

    def _make_app(self):
        # Determine where we are so we can set up paths in the config
        root_dir = self.get_path()

        self.app_config = {
            'app': {
                'root': 'cyborg.api.controllers.root.RootController',
                'modules': ['cyborg.api'],
                'static_root': '%s/public' % root_dir,
                'template_path': '%s/api/templates' % root_dir,
                'acl_public_routes': ['/', '/v1/.*'],
            },
        }
        return pecan.testing.load_test_app(self.app_config)

    def _request_json(self, path, params, expect_errors=False, headers=None,
                      method="post", extra_environ=None, status=None):
        """Sends simulated HTTP request to Pecan test app.

        :param path: url path of target service
        :param params: content for wsgi.input of request
        :param expect_errors: Boolean value; whether an error is expected based
                              on request
        :param headers: a dictionary of headers to send along with the request
        :param method: Request method type. Appropriate method function call
                       should be used rather than passing attribute in.
        :param extra_environ: a dictionary of environ variables to send along
                              with the request
        :param status: expected status code of response
        """
        response = getattr(self.app, "%s_json" % method)(
            str(path),
            params=params,
            headers=headers,
            status=status,
            extra_environ=extra_environ,
            expect_errors=expect_errors
        )
        return response

    def post_json(self, path, params, expect_errors=False, headers=None,
                  extra_environ=None, status=None):
        """Sends simulated HTTP POST request to Pecan test app.

        :param path: url path of target service
        :param params: content for wsgi.input of request
        :param expect_errors: Boolean value; whether an error is expected based
                              on request
        :param headers: a dictionary of headers to send along with the request
        :param extra_environ: a dictionary of environ variables to send along
                              with the request
        :param status: expected status code of response
        """
        full_path = self.PATH_PREFIX + path
        return self._request_json(path=full_path, params=params,
                                  expect_errors=expect_errors,
                                  headers=headers, extra_environ=extra_environ,
                                  status=status, method="post")

    def gen_headers(self, context, **kw):
        """Generate a header for a simulated HTTP request to Pecan test app.

        :param context: context that store the client user information.
        :param kw: key word aguments, used to overwrite the context attribute.

        note: "is_public_api" is not in headers, it should be in environ
        variables to send along with the request. We can pass it by
        extra_environ when we call delete, get_json or other method request.
        """
        ct = context.to_dict()
        ct.update(kw)
        headers = {
            'X-User-Name': ct.get("user_name") or "user",
            'X-User-Id':
                ct.get("user") or "1d6d686bc2c949ddb685ffb4682e0047",
            'X-Project-Name': ct.get("project_name") or "project",
            'X-Project-Id':
                ct.get("tenant") or "86f64f561b6d4f479655384572727f70",
            'X-User-Domain-Id':
                ct.get("domain_id") or "bd5eeb7d0fb046daaf694b36f4df5518",
            'X-User-Domain-Name': ct.get("domain_name") or "no_domain",
            'X-Auth-Token':
                ct.get("auth_token") or "b9764005b8c145bf972634fb16a826e8",
            'X-Roles': ct.get("roles") or "cyborg"
        }

        return headers
