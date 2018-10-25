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

"""Utilities and helper functions."""

import six

from keystoneauth1 import exceptions as ks_exc
from keystoneauth1 import loading as ks_loading
from os_service_types import service_types
from oslo_concurrency import lockutils
from oslo_log import log

from cyborg.common import exception
import cyborg.conf


LOG = log.getLogger(__name__)


synchronized = lockutils.synchronized_with_prefix('cyborg-')
_SERVICE_TYPES = service_types.ServiceTypes()
CONF = cyborg.conf.CONF


def safe_rstrip(value, chars=None):
    """Removes trailing characters from a string if that does not make it empty

    :param value: A string value that will be stripped.
    :param chars: Characters to remove.
    :return: Stripped value.

    """
    if not isinstance(value, six.string_types):
        LOG.warning("Failed to remove trailing character. Returning "
                    "original object. Supplied object is not a string: "
                    "%s,", value)
        return value

    return value.rstrip(chars) or value


def get_ksa_adapter(service_type, ksa_auth=None, ksa_session=None,
                    min_version=None, max_version=None):
    """Construct a keystoneauth1 Adapter for a given service type.

    We expect to find a conf group whose name corresponds to the service_type's
    project according to the service-types-authority.  That conf group must
    provide at least ksa adapter options.  Depending how the result is to be
    used, ksa auth and/or session options may also be required, or the relevant
    parameter supplied.

    :param service_type: String name of the service type for which the Adapter
                         is to be constructed.
    :param ksa_auth: A keystoneauth1 auth plugin. If not specified, we attempt
                     to find one in ksa_session.  Failing that, we attempt to
                     load one from the conf.
    :param ksa_session: A keystoneauth1 Session.  If not specified, we attempt
                        to load one from the conf.
    :param min_version: The minimum major version of the adapter's endpoint,
                        intended to be used as the lower bound of a range with
                        max_version.
                        If min_version is given with no max_version it is as
                        if max version is 'latest'.
    :param max_version: The maximum major version of the adapter's endpoint,
                        intended to be used as the upper bound of a range with
                        min_version.
    :return: A keystoneauth1 Adapter object for the specified service_type.
    :raise: ConfGroupForServiceTypeNotFound If no conf group name could be
            found for the specified service_type.
    """
    # Get the conf group corresponding to the service type.
    confgrp = _SERVICE_TYPES.get_project_name(service_type)
    if not confgrp or not hasattr(CONF, confgrp):
        # Try the service type as the conf group.  This is necessary for e.g.
        # placement, while it's still part of the nova project.
        # Note that this might become the first thing we try if/as we move to
        # using service types for conf group names in general.
        confgrp = service_type
        if not confgrp or not hasattr(CONF, confgrp):
            raise exception.ConfGroupForServiceTypeNotFound(stype=service_type)

    # Ensure we have an auth.
    # NOTE(efried): This could be None, and that could be okay - e.g. if the
    # result is being used for get_endpoint() and the conf only contains
    # endpoint_override.
    if not ksa_auth:
        if ksa_session and ksa_session.auth:
            ksa_auth = ksa_session.auth
        else:
            ksa_auth = ks_loading.load_auth_from_conf_options(CONF, confgrp)

    if not ksa_session:
        ksa_session = ks_loading.load_session_from_conf_options(
            CONF, confgrp, auth=ksa_auth)

    return ks_loading.load_adapter_from_conf_options(
        CONF, confgrp, session=ksa_session, auth=ksa_auth,
        min_version=min_version, max_version=max_version)


def get_endpoint(ksa_adapter):
    """Get the endpoint URL represented by a keystoneauth1 Adapter.

    This method is equivalent to what

        ksa_adapter.get_endpoint()

    should do, if it weren't for a panoply of bugs.

    :param ksa_adapter: keystoneauth1.adapter.Adapter, appropriately set up
                        with an endpoint_override; or service_type, interface
                        (list) and auth/service_catalog.
    :return: String endpoint URL.
    :raise EndpointNotFound: If endpoint discovery fails.
    """
    # TODO(efried): This will be unnecessary once bug #1707993 is fixed.
    # (At least for the non-image case, until 1707995 is fixed.)
    if ksa_adapter.endpoint_override:
        return ksa_adapter.endpoint_override
    # TODO(efried): Remove this once bug #1707995 is fixed.
    if ksa_adapter.service_type == 'image':
        try:
            # LOG.warning(ksa_adapter.__dict__)
            return ksa_adapter.get_endpoint_data().catalog_url
        except AttributeError:
            # ksa_adapter.auth is a _ContextAuthPlugin, which doesn't have
            # get_endpoint_data.  Fall through to using get_endpoint().
            pass
    # TODO(efried): The remainder of this method reduces to
    # TODO(efried):     return ksa_adapter.get_endpoint()
    # TODO(efried): once bug #1709118 is fixed.
    # NOTE(efried): Id9bd19cca68206fc64d23b0eaa95aa3e5b01b676 may also do the
    #               trick, once it's in a ksa release.
    # The EndpointNotFound exception happens when _ContextAuthPlugin is in play
    # because its get_endpoint() method isn't yet set up to handle interface as
    # a list.  (It could also happen with a real auth if the endpoint isn't
    # there; but that's covered below.)
    try:
        return ksa_adapter.get_endpoint()
    except ks_exc.EndpointNotFound:
        pass

    interfaces = list(ksa_adapter.interface)
    for interface in interfaces:
        ksa_adapter.interface = interface
        try:
            return ksa_adapter.get_endpoint()
        except ks_exc.EndpointNotFound:
            pass
    raise ks_exc.EndpointNotFound(
        "Could not find requested endpoint for any of the following "
        "interfaces: %s" % interfaces)
