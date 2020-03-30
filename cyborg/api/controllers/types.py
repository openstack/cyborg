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

import inspect

from oslo_serialization import jsonutils
from oslo_utils import strutils
from oslo_utils import uuidutils
import wsme
from wsme import types as wtypes

from cyborg.common import exception
from cyborg.common.i18n import _


class FilterType(wtypes.UserType):
    """Query filter."""
    name = 'filtertype'
    basetype = wtypes.text

    _supported_fields = wtypes.Enum(wtypes.text, 'parent_uuid', 'root_uuid',
                                    'board', 'availability', 'interface_type',
                                    'instance_uuid', 'limit', 'marker',
                                    'sort_key', 'sort_dir', 'name')

    field = wsme.wsattr(_supported_fields, mandatory=True)
    value = wsme.wsattr(wtypes.text, mandatory=True)

    def __repr__(self):
        # for logging calls
        return '<Query %s %s>' % (self.field,
                                  self.value)

    @classmethod
    def sample(cls):
        return cls(field='interface_type',
                   value='pci')

    def as_dict(self):
        d = dict()
        d[getattr(self, 'field')] = getattr(self, 'value')
        return d

    @staticmethod
    def validate(filters):
        for filter in filters:
            if filter.field not in FilterType._supported_fields:
                msg = _("'%s' is an unsupported field for querying.")
                raise wsme.exc.ClientSideError(msg % filter.field)
        return filters


class UUIDType(wtypes.UserType):
    """A simple UUID type."""

    basetype = wtypes.text
    name = 'uuid'

    @staticmethod
    def validate(value):
        if not uuidutils.is_uuid_like(value):
            raise exception.InvalidUUID(uuid=value)
        return value

    @staticmethod
    def frombasetype(value):
        if value is None:
            return None
        return UUIDType.validate(value)


class JsonType(wtypes.UserType):
    """A simple JSON type."""

    basetype = wtypes.text
    name = 'json'

    @staticmethod
    def validate(value):
        try:
            jsonutils.dumps(value)
        except TypeError:
            raise exception.InvalidJsonType(value=value)
        else:
            return value

    @staticmethod
    def frombasetype(value):
        return JsonType.validate(value)


class BooleanType(wtypes.UserType):
    """A simple boolean type."""

    basetype = wtypes.text
    name = 'boolean'

    @staticmethod
    def validate(value):
        try:
            return strutils.bool_from_string(value, strict=True)
        except ValueError as e:
            # raise Invalid to return 400 (BadRequest) in the API
            raise exception.Invalid(e)

    @staticmethod
    def frombasetype(value):
        if value is None:
            return None
        return BooleanType.validate(value)


uuid = UUIDType()
jsontype = JsonType()
boolean = BooleanType()
integer = wtypes.IntegerType()


class JsonPatchType(wtypes.Base):
    """A complex type that represents a single json-patch operation."""

    path = wtypes.wsattr(wtypes.StringType(pattern=r'^(/[\w-]+)+$'),
                         mandatory=True)
    op = wtypes.wsattr(wtypes.Enum(str, 'add', 'replace', 'remove'),
                       mandatory=True)
    value = wtypes.wsattr(jsontype, default=wtypes.Unset)

    # The class of the objects being patched. Override this in subclasses.
    # Should probably be a subclass of cyborg.api.controllers.base.APIBase.
    _api_base = None

    # Attributes that are not required for construction, but which may not be
    # removed if set. Override in subclasses if needed.
    _extra_non_removable_attrs = set()

    # Set of non-removable attributes, calculated lazily.
    _non_removable_attrs = None

    @staticmethod
    def internal_attrs():
        """Returns a list of internal attributes.

        Internal attributes can't be added, replaced or removed. This
        method may be overwritten by derived class.

        """
        return ['/created_at', '/id', '/links', '/updated_at', '/uuid']

    @classmethod
    def non_removable_attrs(cls):
        """Returns a set of names of attributes that may not be removed.

        Attributes whose 'mandatory' property is True are automatically added
        to this set. To add additional attributes to the set, override the
        field _extra_non_removable_attrs in subclasses, with a set of the form
        {'/foo', '/bar'}.
        """
        if cls._non_removable_attrs is None:
            cls._non_removable_attrs = cls._extra_non_removable_attrs.copy()
            if cls._api_base:
                fields = inspect.getmembers(cls._api_base,
                                            lambda a: not inspect.isroutine(a))
                for name, field in fields:
                    if getattr(field, 'mandatory', False):
                        cls._non_removable_attrs.add('/%s' % name)
        return cls._non_removable_attrs

    @staticmethod
    def validate(patch):
        _path = '/' + patch.path.split('/')[1]
        if _path in patch.internal_attrs():
            msg = _("'%s' is an internal attribute and can not be updated")
            raise wsme.exc.ClientSideError(msg % patch.path)

        if patch.path in patch.non_removable_attrs() and patch.op == 'remove':
            msg = _("'%s' is a mandatory attribute and can not be removed")
            raise wsme.exc.ClientSideError(msg % patch.path)

        if patch.op != 'remove':
            if patch.value is wsme.Unset:
                msg = _("'add' and 'replace' operations need a value")
                raise wsme.exc.ClientSideError(msg)

        ret = {'path': patch.path, 'op': patch.op}
        if patch.value is not wsme.Unset:
            ret['value'] = patch.value
        return ret
