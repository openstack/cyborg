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

"""Cyborg base exception handling.

SHOULD include dedicated exception logging.

"""

from oslo_log import log
import six
from six.moves import http_client

from cyborg.common.i18n import _
from cyborg.conf import CONF


LOG = log.getLogger(__name__)


class CyborgException(Exception):
    """Base Cyborg Exception

    To correctly use this class, inherit from it and define
    a '_msg_fmt' property. That message will get printf'd
    with the keyword arguments provided to the constructor.

    If you need to access the message from an exception you should use
    six.text_type(exc)

    """
    _msg_fmt = _("An unknown exception occurred.")
    code = http_client.INTERNAL_SERVER_ERROR
    headers = {}
    safe = False

    def __init__(self, message=None, **kwargs):
        self.kwargs = kwargs

        if 'code' not in self.kwargs:
            try:
                self.kwargs['code'] = self.code
            except AttributeError:
                pass

        if not message:
            try:
                message = self._msg_fmt % kwargs
            except Exception:
                # kwargs doesn't match a variable in self._msg_fmt
                # log the issue and the kwargs
                LOG.exception('Exception in string format operation')
                for name, value in kwargs.items():
                    LOG.error("%s: %s" % (name, value))

                if CONF.fatal_exception_format_errors:
                    raise
                else:
                    # at least get the core self._msg_fmt out if something
                    # happened
                    message = self._msg_fmt

        super(CyborgException, self).__init__(message)

    def __str__(self):
        """Encode to utf-8 then wsme api can consume it as well."""
        if not six.PY3:
            return unicode(self.args[0]).encode('utf-8')

        return self.args[0]

    def __unicode__(self):
        """Return a unicode representation of the exception message."""
        return unicode(self.args[0])


class ConfigInvalid(CyborgException):
    _msg_fmt = _("Invalid configuration file. %(error_msg)s")


class AcceleratorAlreadyExists(CyborgException):
    _msg_fmt = _("Accelerator with uuid %(uuid)s already exists.")


class DeployableAlreadyExists(CyborgException):
    _msg_fmt = _("Deployable with uuid %(uuid)s already exists.")


class Invalid(CyborgException):
    _msg_fmt = _("Invalid parameters.")
    code = http_client.BAD_REQUEST


class InvalidIdentity(Invalid):
    _msg_fmt = _("Expected a uuid/id but received %(identity)s.")


class InvalidUUID(Invalid):
    _msg_fmt = _("Expected a uuid but received %(uuid)s.")


class InvalidJsonType(Invalid):
    _msg_fmt = _("%(value)s is not JSON serializable.")


# Cannot be templated as the error syntax varies.
# msg needs to be constructed when raised.
class InvalidParameterValue(Invalid):
    _msg_fmt = _("%(err)s")


class PatchError(Invalid):
    _msg_fmt = _("Couldn't apply patch '%(patch)s'. Reason: %(reason)s")


class NotAuthorized(CyborgException):
    _msg_fmt = _("Not authorized.")
    code = http_client.FORBIDDEN


class HTTPForbidden(NotAuthorized):
    _msg_fmt = _("Access was denied to the following resource: %(resource)s")


class NotFound(CyborgException):
    _msg_fmt = _("Resource could not be found.")
    code = http_client.NOT_FOUND


class AcceleratorNotFound(NotFound):
    _msg_fmt = _("Accelerator %(uuid)s could not be found.")


class DeployableNotFound(NotFound):
    _msg_fmt = _("Deployable %(uuid)s could not be found.")


class InvalidDeployType(CyborgException):
    _msg_fmt = _("Deployable have an invalid type")


class Conflict(CyborgException):
    _msg_fmt = _('Conflict.')
    code = http_client.CONFLICT


class DuplicateAcceleratorName(Conflict):
    _msg_fmt = _("An accelerator with name %(name)s already exists.")


class DuplicateDeployableName(Conflict):
    _msg_fmt = _("A deployable with name %(name)s already exists.")


class PlacementEndpointNotFound(NotFound):
    message = _("Placement API endpoint not found")


class PlacementResourceProviderNotFound(NotFound):
    message = _("Placement resource provider not found %(resource_provider)s.")


class PlacementInventoryNotFound(NotFound):
    message = _("Placement inventory not found for resource provider "
                "%(resource_provider)s, resource class %(resource_class)s.")


class PlacementInventoryUpdateConflict(Conflict):
    message = _("Placement inventory update conflict for resource provider "
                "%(resource_provider)s, resource class %(resource_class)s.")


class ObjectActionError(CyborgException):
    _msg_fmt = _('Object action %(action)s failed because: %(reason)s')


class AttributeNotFound(NotFound):
    _msg_fmt = _("Attribute %(uuid)s could not be found.")


class AttributeInvalid(CyborgException):
    _msg_fmt = _("Attribute is invalid")


class AttributeAlreadyExists(CyborgException):
    _msg_fmt = _("Attribute with uuid %(uuid)s already exists.")
