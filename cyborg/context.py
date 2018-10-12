# Copyright 2011 OpenStack Foundation
# Copyright 2010 United States Government as represented by the
# Administrator of the National Aeronautics and Space Administration.
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


from keystoneauth1.access import service_catalog as ksa_service_catalog
from keystoneauth1 import plugin
from oslo_context import context
from oslo_db.sqlalchemy import enginefacade
from oslo_utils import timeutils
import six


class _ContextAuthPlugin(plugin.BaseAuthPlugin):
    """A keystoneauth auth plugin that uses the values from the Context.

    Ideally we would use the plugin provided by auth_token middleware however
    this plugin isn't serialized yet so we construct one from the serialized
    auth data.
    """

    def __init__(self, auth_token, sc):
        super(_ContextAuthPlugin, self).__init__()

        self.auth_token = auth_token
        self.service_catalog = ksa_service_catalog.ServiceCatalogV2(sc)

    def get_token(self, *args, **kwargs):
        return self.auth_token

    def get_endpoint(self, session, service_type=None, interface=None,
                     region_name=None, service_name=None, **kwargs):
        return self.service_catalog.url_for(service_type=service_type,
                                            service_name=service_name,
                                            interface=interface,
                                            region_name=region_name)


@enginefacade.transaction_context_provider
class RequestContext(context.RequestContext):
    """Security context and request information.

    Represents the user taking a given action within the system.

    """

    def __init__(self, user_id=None, project_id=None, is_admin=None,
                 read_deleted="no", remote_address=None, timestamp=None,
                 quota_class=None, service_catalog=None,
                 user_auth_plugin=None, **kwargs):
        """:param read_deleted: 'no' indicates deleted records are hidden,
                'yes' indicates deleted records are visible,
                'only' indicates that *only* deleted records are visible.

           :param overwrite: Set to False to ensure that the greenthread local
                copy of the index is not overwritten.

           :param instance_lock_checked: This is not used and will be removed
                in a future release.

           :param user_auth_plugin: The auth plugin for the current request's
                authentication data.
        """
        if user_id:
            kwargs['user_id'] = user_id
        if project_id:
            kwargs['project_id'] = project_id

        super(RequestContext, self).__init__(is_admin=is_admin, **kwargs)

        self.read_deleted = read_deleted
        self.remote_address = remote_address
        if not timestamp:
            timestamp = timeutils.utcnow()
        if isinstance(timestamp, six.string_types):
            timestamp = timeutils.parse_strtime(timestamp)
        self.timestamp = timestamp

        if service_catalog:
            # Only include required parts of service_catalog
            self.service_catalog = [s for s in service_catalog
                                    if s.get('type') in ('image')]
        else:
            # if list is empty or none
            self.service_catalog = []

        self.user_auth_plugin = user_auth_plugin
        # if self.is_admin is None:
        #    self.is_admin = policy.check_is_admin(self)

    def get_auth_plugin(self):
        if self.user_auth_plugin:
            return self.user_auth_plugin
        else:
            return _ContextAuthPlugin(self.auth_token, self.service_catalog)


def get_context():
    """A helper method to get a blank context.

    Note that overwrite is False here so this context will not update the
    greenthread-local stored context that is used when logging.
    """
    return RequestContext(user_id=None,
                          project_id=None,
                          is_admin=False,
                          overwrite=False)


def get_admin_context(read_deleted="no"):
    # NOTE(alaski): This method should only be used when an admin context is
    # necessary for the entirety of the context lifetime. If that's not the
    # case please use get_context(), or create the RequestContext manually, and
    # use context.elevated() where necessary. Some periodic tasks may use
    # get_admin_context so that their database calls are not filtered on
    # project_id.
    return RequestContext(user_id=None,
                          project_id=None,
                          is_admin=True,
                          read_deleted=read_deleted,
                          overwrite=False)


def is_user_context(context):
    """Indicates if the request context is a normal user."""
    if not context:
        return False
    if context.is_admin:
        return False
    if not context.user_id or not context.project_id:
        return False
    return True


def require_context(ctxt):
    """Raise exception.Forbidden() if context is not a user or an
    admin context.
    """
    if not ctxt.is_admin and not is_user_context(ctxt):
        raise exception.Forbidden()


def authorize_project_context(context, project_id):
    """Ensures a request has permission to access the given project."""
    if is_user_context(context):
        if not context.project_id:
            raise exception.Forbidden()
        elif context.project_id != project_id:
            raise exception.Forbidden()


def authorize_user_context(context, user_id):
    """Ensures a request has permission to access the given user."""
    if is_user_context(context):
        if not context.user_id:
            raise exception.Forbidden()
        elif context.user_id != user_id:
            raise exception.Forbidden()
