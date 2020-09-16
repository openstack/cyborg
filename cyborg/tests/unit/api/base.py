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
from oslo_context import context
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

    def flags(self, **kw):
        """Override flag variables for a test."""
        group = kw.pop('group', None)
        for k, v in kw.items():
            cfg.CONF.set_override(k, v, group)

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

    def gen_context(self, value, **kwargs):
        ct = context.RequestContext.from_dict(value, **kwargs)
        return ct

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
        if ct.get("is_admin"):
            role = "admin"
        else:
            role = "user"
        headers = {
            'X-User-Name': ct.get("user_name") or "user",
            'X-User-Id':
                ct.get("user") or "1d6d686bc2c949ddb685ffb4682e0047",
            'X-Project-Name': ct.get("project_name") or "no_project_name",
            'X-Project-Id':
                ct.get("tenant") or "86f64f561b6d4f479655384572727f70",
            'X-User-Domain-Id':
                ct.get("domain_id") or "bd5eeb7d0fb046daaf694b36f4df5518",
            'X-User-Domain-Name': ct.get("domain_name") or "no_domain",
            'X-Auth-Token':
                ct.get("auth_token") or "b9764005b8c145bf972634fb16a826e8",
            'X-Roles': ct.get("roles") or role,
        }
        if ct.get('system_scope') == 'all':
            headers.update({'Openstack-System-Scope': 'all'})
        return headers

    def get_json(self, path, expect_errors=False, headers=None,
                 extra_environ=None, q=None, return_json=True, **params):
        """Sends simulated HTTP GET request to Pecan test app.

        :param path: url path of target service
        :param expect_errors: Boolean value; whether an error is expected based
                              on request
        :param headers: a dictionary of headers to send along with the request
        :param extra_environ: a dictionary of environ variables to send along
                              with the request
        :param q: list of queries consisting of: field, value, op, and type
                  keys
        :param path_prefix: prefix of the url path
        :param params: content for wsgi.input of request
        """
        full_path = self.PATH_PREFIX + path
        q = q or []
        query_params = {
            'q.field': [],
            'q.value': [],
            'q.op': [],
            }
        for query in q:
            for name in ['field', 'op', 'value']:
                query_params['q.%s' % name].append(query.get(name, ''))
        all_params = {}
        all_params.update(params)
        if q:
            all_params.update(query_params)
        response = self.app.get(full_path,
                                params=all_params,
                                headers=headers,
                                extra_environ=extra_environ,
                                expect_errors=expect_errors)
        if return_json and not expect_errors:
            response = response.json
        return response

    def patch_json(self, path, params, expect_errors=False, headers=None,
                   extra_environ=None, status=None):
        """Sends simulated HTTP PATCH request to Pecan test app.

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
                                  status=status, method="patch")

    def delete(self, path, expect_errors=False, headers=None,
               extra_environ=None, status=None):
        """Sends simulated HTTP DELETE request to Pecan test app.

        :param path: url path of target service
        :param expect_errors: Boolean value; whether an error is expected based
                              on request
        :param headers: a dictionary of headers to send along with the request
        :param extra_environ: a dictionary of environ variables to send along
                              with the request
        :param status: expected status code of response
        """
        full_path = self.PATH_PREFIX + path
        response = self.app.delete(full_path,
                                   headers=headers,
                                   status=status,
                                   extra_environ=extra_environ,
                                   expect_errors=expect_errors)
        return response
