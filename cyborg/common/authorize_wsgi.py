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

from oslo_concurrency import lockutils
from oslo_config import cfg
from oslo_log import log
from oslo_policy import opts
from oslo_policy import policy
from oslo_versionedobjects import base as object_base
import pecan
import wsme

from cyborg.common import exception
from cyborg import policies


_ENFORCER = None
CONF = cfg.CONF
LOG = log.getLogger(__name__)


# TODO(gmann): Remove setting the default value of config policy_file
# once oslo_policy change the default value to 'policy.yaml'.
# https://github.com/openstack/oslo.policy/blob/a626ad12fe5a3abd49d70e3e5b95589d279ab578/oslo_policy/opts.py#L49
DEFAULT_POLICY_FILE = 'policy.yaml'
opts.set_defaults(CONF, DEFAULT_POLICY_FILE)


def pick_policy_file(policy_file):
    # TODO(gmann): We have changed the default value of
    # CONF.oslo_policy.policy_file option to 'policy.yaml' in Victoria
    # release. To avoid breaking any deployment relying on default
    # value, we need to add this is fallback logic to pick the old default
    # policy file (policy.yaml) if exist. We can to remove this fallback
    # logic sometime in future.
    if policy_file:
        return policy_file

    if CONF.oslo_policy.policy_file == DEFAULT_POLICY_FILE:
        location = CONF.get_location('policy_file', 'oslo_policy').location
        if CONF.find_file(CONF.oslo_policy.policy_file):
            return CONF.oslo_policy.policy_file
        elif location in [cfg.Locations.opt_default,
                          cfg.Locations.set_default]:
            old_default = 'policy.json'
            if CONF.find_file(old_default):
                return old_default
    # Return overridden value
    return CONF.oslo_policy.policy_file


@lockutils.synchronized('policy_enforcer', 'cyborg-')
def init_enforcer(policy_file=None, rules=None,
                  default_rule=None, use_conf=True,
                  suppress_deprecation_warnings=False):
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
        policy_file=pick_policy_file(policy_file),
        rules=rules,
        default_rule=default_rule,
        use_conf=use_conf)
    if suppress_deprecation_warnings:
        _ENFORCER.suppress_deprecation_warnings = True
    _ENFORCER.register_defaults(policies.list_policies())


def get_enforcer():
    """Provides access to the single accelerator of policy enforcer."""
    global _ENFORCER

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
        return enforcer.authorize(rule, target, creds, do_raise=do_raise,
                                  *args, **kwargs)
    except policy.PolicyNotAuthorized:
        raise exception.HTTPForbidden(resource=rule)


# This decorator MUST appear first (the outermost decorator)
# on an API method for it to work correctly
def authorize_wsgi(api_name, act=None, need_target=True):
    """This is a decorator to simplify wsgi action policy rule check.
    :param api_name: The collection name to be evaluate.
    :param act: The function name of wsgi action.
    :param need_target: Whether need target for authorization. Such as,
                        when create some resource , maybe target is not needed.
    example:
        from cyborg.common import authorize_wsgi
        class AcceleratorController(rest.RestController):
            ....
            @authorize_wsgi.authorize_wsgi("cyborg:accelerator",
                                           "create", False)
            @wsme_pecan.wsexpose(Accelerator, body=types.jsontype,
                                 status_code=HTTPStatus.CREATED)
            def post(self, values):
                ...
    """
    def wraper(fn):
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
                exception_info,
                pecan.conf.get('wsme', {}).get('debug', False)
            )
            del exception_info
            return data

        @functools.wraps(fn)
        def handle(self, *args, **kwargs):
            context = pecan.request.context
            credentials = context.to_policy_values()
            credentials['is_admin'] = context.is_admin
            if context.system_scope == 'all':
                credentials['system'] = True
            target = {}
            # maybe we can pass "_get_resource" to authorize_wsgi
            if need_target and hasattr(self, "_get_resource"):
                try:
                    resource = getattr(self, "_get_resource")(*args, **kwargs)
                    # just support object, other type will just keep target as
                    # empty, then follow authorize method will fail and throw
                    # an exception
                    if isinstance(resource,
                                  object_base.VersionedObjectDictCompat):
                        target = {'project_id': resource.project_id,
                                  'user_id': resource.user_id}
                except Exception:
                    return return_error(500)
            elif need_target:
                # if developer do not set _get_resource, just set target as
                # empty, then follow authorize method will fail and throw an
                # exception
                target = {}
            else:
                # for create method, before resource exsites, we can check the
                # the credentials with itself.
                target = {'project_id': context.project_id,
                          'user_id': context.user_id}

            try:
                authorize(action, target, credentials, do_raise=True)
            except Exception:
                return return_error(403)

            return fn(self, *args, **kwargs)

        return handle

    return wraper
