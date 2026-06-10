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
"""Policy Authorize Engine For Cyborg."""

import functools
import sys

import pecan
import wsme

from oslo_concurrency import lockutils
from oslo_config import cfg
from oslo_policy import policy

from cyborg import policies
from cyborg.common import exception


_ENFORCER = None
CONF = cfg.CONF


@lockutils.synchronized('policy_enforcer', 'cyborg-')
def init_enforcer(
    policy_file=None,
    rules=None,
    default_rule=None,
    use_conf=True,
    suppress_deprecation_warnings=False,
):
    """Synchronously initializes the policy enforcer
    :param policy_file: Custom policy file to use, if none is specified,
                        `CONF.oslo_policy.policy_file` will be used.
    :param rules: Default dictionary / Rules to use. It will be
                  considered just in the first instantiation.
    :param default_rule: Default rule to use,
                         CONF.oslo_policy.policy_default_rule will
                         be used if none is specified.
    :param use_conf: Whether to load rules from config file.
    :param suppress_deprecation_warnings: Whether to suppress the
                                          deprecation warnings.
    """
    global _ENFORCER

    if _ENFORCER:
        return

    # NOTE: Register defaults for policy-in-code here so that they are
    # loaded exactly once - when this module-global is initialized.
    # Defining these in the relevant API modules won't work
    # because API classes lack singletons and don't use globals.
    _ENFORCER = policy.Enforcer(
        CONF,
        policy_file=policy_file,
        rules=rules,
        default_rule=default_rule,
        use_conf=use_conf,
    )
    if suppress_deprecation_warnings:
        _ENFORCER.suppress_deprecation_warnings = True
    _ENFORCER.register_defaults(policies.list_policies())


def get_enforcer():
    """Provides access to the single accelerator of policy enforcer."""
    if not _ENFORCER:
        init_enforcer()

    return _ENFORCER


# NOTE: We can't call these methods from within decorators because the
# 'target' and 'creds' parameter must be fetched from the call time
# context-local pecan.request magic variable, but decorators are compiled
# at module-load time.


def authorize(rule, target, creds, do_raise=False, *args, **kwargs):
    """A shortcut for policy.Enforcer.authorize()
    Checks authorization of a rule against the target and credentials, and
    raises an exception if the rule is not defined.
    """
    enforcer = get_enforcer()
    try:
        return enforcer.authorize(
            rule, target, creds, do_raise=do_raise, *args, **kwargs
        )
    except policy.InvalidScope:
        raise exception.HTTPForbidden(resource=rule)
    except policy.PolicyNotAuthorized:
        raise exception.HTTPForbidden(resource=rule)


# This decorator MUST appear first (the outermost decorator)
# on an API method for it to work correctly
def authorize_wsgi(api_name, act=None):
    """This is a decorator to simplify wsgi action policy rule check.
    :param api_name: The collection name to be evaluate.
    :param act: The function name of wsgi action.
    example:
        from cyborg.common import authorize_wsgi
        class AcceleratorController(rest.RestController):
            ....
            @authorize_wsgi.authorize_wsgi("cyborg:accelerator",
                                           "create")
            @wsme_pecan.wsexpose(Accelerator, body=types.jsontype,
                                 status_code=HTTPStatus.CREATED)
            def post(self, values):
                ...
    """

    def wrapper(fn):
        action = '%s:%s' % (api_name, act or fn.__name__)

        # In this authorize method, we return a dict data when authorization
        # fails or exception comes out. Maybe we can consider to use
        # wsme.api.Response in future.
        def return_error(resp_status):
            exception_info = sys.exc_info()
            orig_exception = exception_info[1]
            orig_code = getattr(orig_exception, 'code', None)
            pecan.response.status = orig_code or resp_status
            data = wsme.api.format_exception(
                exception_info, pecan.conf.get('wsme', {}).get('debug', False)
            )
            del exception_info
            return data

        @functools.wraps(fn)
        def handle(self, *args, **kwargs):
            context = pecan.request.context
            credentials = context.to_policy_values()
            credentials['is_admin'] = context.is_admin
            policy_target = {
                'project_id': context.project_id,
                'user_id': context.user_id,
            }

            try:
                authorize(action, policy_target, credentials, do_raise=True)
            except Exception:
                return return_error(403)

            return fn(self, *args, **kwargs)

        return handle

    return wrapper
