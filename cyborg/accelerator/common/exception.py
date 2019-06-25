# Copyright 2017 Lenovo, Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License"); you may
# not use this file except in compliance with the License. You may obtain
# a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
# WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
# License for the specific language governing permissions and limitations
# under the License.

"""Accelerator base exception handling. """

import collections
from oslo_log import log as logging
from oslo_serialization import jsonutils
import six
from six.moves import http_client

from cyborg.common.i18n import _


LOG = logging.getLogger(__name__)


def _ensure_exception_kwargs_serializable(exc_class_name, kwargs):
    """Ensure that kwargs are serializable

    Ensure that all kwargs passed to exception constructor can be passed over
    RPC, by trying to convert them to JSON, or, as a last resort, to string.
    If it is not possible, unserializable kwargs will be removed, letting the
    receiver to handle the exception string as it is configured to.

    :param exc_class_name: an AcceleratorException class name.
    :param kwargs: a dictionary of keyword arguments passed to the exception
        constructor.
    :returns: a dictionary of serializable keyword arguments.
    """
    serializers = [(jsonutils.dumps, _('when converting to JSON')),
                   (six.text_type, _('when converting to string'))]
    exceptions = collections.defaultdict(list)
    serializable_kwargs = {}
    for k, v in kwargs.items():
        for serializer, msg in serializers:
            try:
                serializable_kwargs[k] = serializer(v)
                exceptions.pop(k, None)
                break
            except Exception as e:
                exceptions[k].append(
                    '(%(serializer_type)s) %(e_type)s: %(e_contents)s' %
                    {'serializer_type': msg, 'e_contents': e,
                     'e_type': e.__class__.__name__})
    if exceptions:
        LOG.error("One or more arguments passed to the %(exc_class)s "
                  "constructor as kwargs can not be serialized. The "
                  "serialized arguments: %(serialized)s. These "
                  "unserialized kwargs were dropped because of the "
                  "exceptions encountered during their "
                  "serialization:\n%(errors)s",
                  dict(errors=';\n'.join("%s: %s" % (k, '; '.join(v))
                                         for k, v in exceptions.items()),
                       exc_class=exc_class_name,
                       serialized=serializable_kwargs))
        # We might be able to actually put the following keys' values into
        # format string, but there is no guarantee, drop it just in case.
        for k in exceptions:
            del kwargs[k]
    return serializable_kwargs


class AcceleratorException(Exception):
    """Base Accelerator Exception

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

        self.kwargs = _ensure_exception_kwargs_serializable(
            self.__class__.__name__, kwargs)

        if 'code' not in self.kwargs:
            try:
                self.kwargs['code'] = self.code
            except AttributeError:
                pass

        if not message:
            if kwargs:
                message = self._msg_fmt % kwargs
            else:
                message = self._msg_fmt

        super(AcceleratorException, self).__init__(message)


class Invalid(AcceleratorException):
    _msg_fmt = _("Unacceptable parameters.")


class InvalidParameterValue(Invalid):
    _msg_fmt = "%(err)s"


class MissingParameterValue(InvalidParameterValue):
    _msg_fmt = "%(err)s"


class InvalidAccelerator(InvalidParameterValue):
    _msg_fmt = "%(err)s"
