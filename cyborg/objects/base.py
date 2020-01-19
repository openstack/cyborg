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

"""Cyborg common internal object model"""

import netaddr
from oslo_log import log as logging
from oslo_utils import versionutils
from oslo_versionedobjects import base as object_base

from cyborg import objects
from cyborg.objects import fields as object_fields


LOG = logging.getLogger(__name__)


class CyborgObjectRegistry(object_base.VersionedObjectRegistry):
    def registration_hook(self, cls, index):
        # NOTE(jroll): blatantly stolen from nova
        # NOTE(danms): This is called when an object is registered,
        # and is responsible for maintaining cyborg.objects.$OBJECT
        # as the highest-versioned implementation of a given object.
        version = versionutils.convert_version_to_tuple(cls.VERSION)
        if not hasattr(objects, cls.obj_name()):
            setattr(objects, cls.obj_name(), cls)
        else:
            cur_version = versionutils.convert_version_to_tuple(
                getattr(objects, cls.obj_name()).VERSION)
            if version >= cur_version:
                setattr(objects, cls.obj_name(), cls)


class CyborgObject(object_base.VersionedObject):
    """Base class and object factory.

    This forms the base of all objects that can be remoted or instantiated
    via RPC. Simply defining a class that inherits from this base class
    will make it remotely instantiatable. Objects should implement the
    necessary "get" classmethod routines as well as "save" object methods
    as appropriate.
    """

    OBJ_SERIAL_NAMESPACE = 'cyborg_object'
    OBJ_PROJECT_NAMESPACE = 'cyborg'

    fields = {
        'created_at': object_fields.DateTimeField(nullable=True),
        'updated_at': object_fields.DateTimeField(nullable=True),
    }

    def as_dict(self):
        """Return the object represented as a dict.
        The returned object is JSON-serialisable.
        """

        def _attr_as_dict(field):
            """Return an attribute as a dict, handling nested objects."""
            attr = getattr(self, field)
            if isinstance(attr, CyborgObject):
                attr = attr.as_dict()
            return attr

        return {k: _attr_as_dict(k)
                for k in self.fields if self.obj_attr_is_set(k)}

    @staticmethod
    def _from_db_object(obj, db_obj):
        """Converts a database entity to a formal object.

        :param obj: An object of the class.
        :param db_obj: A DB model of the object
        :return: The object of the class with the database entity added
        """

        for field in obj.fields:
            obj[field] = db_obj[field]

        obj.obj_reset_changes()
        return obj

    @classmethod
    def _from_db_object_list(cls, db_objs, context):
        """Converts a list of database entities to a list of formal objects."""
        objs = []
        for db_obj in db_objs:
            objs.append(cls._from_db_object(cls(context), db_obj))
        return objs

    def obj_make_compatible(self, primitive, target_version):
        """Make an object representation compatible with a target version.

        This is responsible for taking the primitive representation of
        an object and making it suitable for the given target_version.
        This may mean converting the format of object attributes, removing
        attributes that have been added since the target version, etc.

        :param:primitive: The result of self.obj_to_primitive()
        :param:target_version: The version string requested by the recipient
                               of the object.
        """
        _log_backport(self, target_version)
        super(CyborgObject, self).obj_make_compatible(primitive,
                                                      target_version)


class CyborgObjectSerializer(object_base.VersionedObjectSerializer):
    # Base class to use for object hydration
    OBJ_BASE_CLASS = CyborgObject


CyborgObjectDictCompat = object_base.VersionedObjectDictCompat


class CyborgPersistentObject(object):
    """Mixin class for Persistent objects.

    This adds the fields that we use in common for most persistent objects.
    """
    fields = {
        'created_at': object_fields.DateTimeField(nullable=True),
        'updated_at': object_fields.DateTimeField(nullable=True),
        'deleted_at': object_fields.DateTimeField(nullable=True),
        'deleted': object_fields.BooleanField(default=False),
        }


class ObjectListBase(object_base.ObjectListBase):

    @classmethod
    def _obj_primitive_key(cls, field):
        return 'cyborg_object.%s' % field

    @classmethod
    def _obj_primitive_field(cls, primitive, field,
                             default=object_fields.UnspecifiedDefault):
        key = cls._obj_primitive_key(field)
        if default == object_fields.UnspecifiedDefault:
            return primitive[key]
        else:
            return primitive.get(key, default)


def obj_to_primitive(obj):
    """Recursively turn an object into a python primitive.

    A CyborgObject becomes a dict, and anything that implements ObjectListBase
    becomes a list.
    """
    if isinstance(obj, ObjectListBase):
        return [obj_to_primitive(x) for x in obj]
    elif isinstance(obj, CyborgObject):
        result = {}
        for key in obj.obj_fields:
            if obj.obj_attr_is_set(key) or key in obj.obj_extra_fields:
                result[key] = obj_to_primitive(getattr(obj, key))
        return result
    elif isinstance(obj, netaddr.IPAddress):
        return str(obj)
    elif isinstance(obj, netaddr.IPNetwork):
        return str(obj)
    else:
        return obj


def obj_equal_prims(obj_1, obj_2, ignore=None):
    """Compare two primitives for equivalence ignoring some keys.
    This operation tests the primitives of two objects for equivalence.
    Object primitives may contain a list identifying fields that have been
    changed - this is ignored in the comparison. The ignore parameter lists
    any other keys to be ignored.
    :param:obj1: The first object in the comparison
    :param:obj2: The second object in the comparison
    :param:ignore: A list of fields to ignore
    :returns: True if the primitives are equal ignoring changes
    and specified fields, otherwise False.
    """

    def _strip(prim, keys):
        if isinstance(prim, dict):
            for k in keys:
                prim.pop(k, None)
            for v in prim.values():
                _strip(v, keys)
        if isinstance(prim, list):
            for v in prim:
                _strip(v, keys)
        return prim

    if ignore is not None:
        keys = ['cyborg_object.changes'] + ignore
    else:
        keys = ['cyborg_object.changes']
    prim_1 = _strip(obj_1.obj_to_primitive(), keys)
    prim_2 = _strip(obj_2.obj_to_primitive(), keys)
    return prim_1 == prim_2


class DriverObjectBase(CyborgObject):
    @staticmethod
    def _from_db_object(obj, db_obj):
        fields = obj.fields
        fields.pop("updated_at")
        fields.pop("created_at")
        for field in fields:
            obj[field] = db_obj[field]

        obj.obj_reset_changes()
        return obj


def _log_backport(ovo, target_version):
    """Log backported versioned objects."""
    if target_version and target_version != ovo.VERSION:
        LOG.debug('Backporting %(obj_name)s from version %(src_vers)s '
                  'to version %(dst_vers)s',
                  {'obj_name': ovo.obj_name(),
                   'src_vers': ovo.VERSION,
                   'dst_vers': target_version})
