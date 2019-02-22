# Copyright 2018 Huawei Technologies Co.,LTD.
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

import contextlib
import copy
import datetime
import inspect
import os

import fixtures
import mock
from oslo_log import log
from oslo_utils import timeutils
from oslo_versionedobjects import base as ovo_base
from oslo_versionedobjects import exception as ovo_exc
from oslo_versionedobjects import fixture
import six

from oslo_context import context

from cyborg.common import exception
from cyborg import objects
from cyborg.objects import base
from cyborg.objects import fields
from cyborg import tests as test


LOG = log.getLogger(__name__)


class MyOwnedObject(base.CyborgPersistentObject, base.CyborgObject):
    VERSION = '1.0'
    fields = {'baz': fields.IntegerField()}


class MyObj(base.CyborgPersistentObject, base.CyborgObject,
            base.CyborgObjectDictCompat):
    VERSION = '1.6'
    fields = {'foo': fields.IntegerField(default=1),
              'bar': fields.StringField(),
              'missing': fields.StringField(),
              'readonly': fields.IntegerField(read_only=True),
              'rel_object': fields.ObjectField('MyOwnedObject', nullable=True),
              'rel_objects': fields.ListOfObjectsField('MyOwnedObject',
                                                       nullable=True),
              'mutable_default': fields.ListOfStringsField(default=[]),
              }

    @staticmethod
    def _from_db_object(context, obj, db_obj):
        self = MyObj()
        self.foo = db_obj['foo']
        self.bar = db_obj['bar']
        self.missing = db_obj['missing']
        self.readonly = 1
        self._context = context
        return self

    def obj_load_attr(self, attrname):
        setattr(self, attrname, 'loaded!')

    def query(cls, context):
        obj = cls(context=context, foo=1, bar='bar')
        obj.obj_reset_changes()
        return obj

    def marco(self):
        return 'polo'

    def _update_test(self):
        self.bar = 'updated'

    def save(self):
        self.obj_reset_changes()

    def refresh(self):
        self.foo = 321
        self.bar = 'refreshed'
        self.obj_reset_changes()

    def modify_save_modify(self):
        self.bar = 'meow'
        self.save()
        self.foo = 42
        self.rel_object = MyOwnedObject(baz=42)

    def obj_make_compatible(self, primitive, target_version):
        super(MyObj, self).obj_make_compatible(primitive, target_version)
        # NOTE(danms): Simulate an older version that had a different
        # format for the 'bar' attribute
        if target_version == '1.1' and 'bar' in primitive:
            primitive['bar'] = 'old%s' % primitive['bar']


class RandomMixInWithNoFields(object):
    """Used to test object inheritance using a mixin that has no fields."""
    pass


@base.CyborgObjectRegistry.register_if(False)
class TestSubclassedObject(RandomMixInWithNoFields, MyObj):
    fields = {'new_field': fields.StringField()}


class TestObjToPrimitive(test.base.TestCase):

    def test_obj_to_primitive_list(self):
        @base.CyborgObjectRegistry.register_if(False)
        class MyObjElement(base.CyborgObject):
            fields = {'foo': fields.IntegerField()}

            def __init__(self, foo):
                super(MyObjElement, self).__init__()
                self.foo = foo

        @base.CyborgObjectRegistry.register_if(False)
        class MyList(base.ObjectListBase, base.CyborgObject):
            fields = {'objects': fields.ListOfObjectsField('MyObjElement')}

        mylist = MyList()
        mylist.objects = [MyObjElement(1), MyObjElement(2), MyObjElement(3)]
        self.assertEqual([1, 2, 3],
                         [x['foo'] for x in base.obj_to_primitive(mylist)])

    def test_obj_to_primitive_dict(self):
        base.CyborgObjectRegistry.register(MyObj)
        myobj = MyObj(foo=1, bar='foo')
        self.assertEqual({'foo': 1, 'bar': 'foo'},
                         base.obj_to_primitive(myobj))

    def test_obj_to_primitive_recursive(self):
        base.CyborgObjectRegistry.register(MyObj)

        class MyList(base.ObjectListBase, base.CyborgObject):
            fields = {'objects': fields.ListOfObjectsField('MyObj')}

        mylist = MyList(objects=[MyObj(), MyObj()])
        for i, value in enumerate(mylist):
            value.foo = i
        self.assertEqual([{'foo': 0}, {'foo': 1}],
                         base.obj_to_primitive(mylist))

    def test_obj_to_primitive_with_ip_addr(self):
        @base.CyborgObjectRegistry.register_if(False)
        class TestObject(base.CyborgObject):
            fields = {'addr': fields.IPAddressField(),
                      'cidr': fields.IPNetworkField()}

        obj = TestObject(addr='1.2.3.4', cidr='1.1.1.1/16')
        self.assertEqual({'addr': '1.2.3.4', 'cidr': '1.1.1.1/16'},
                         base.obj_to_primitive(obj))


def compare_obj(test, obj, db_obj, subs=None, allow_missing=None,
                comparators=None):
    """Compare a CyborgObject and a dict-like database object.

    This automatically converts TZ-aware datetimes and iterates over
    the fields of the object.

    :param:test: The TestCase doing the comparison
    :param:obj: The CyborgObject to examine
    :param:db_obj: The dict-like database object to use as reference
    :param:subs: A dict of objkey=dbkey field substitutions
    :param:allow_missing: A list of fields that may not be in db_obj
    :param:comparators: Map of comparator functions to use for certain fields
    """

    if subs is None:
        subs = {}
    if allow_missing is None:
        allow_missing = []
    if comparators is None:
        comparators = {}

    for key in obj.fields:
        if key in allow_missing and not obj.obj_attr_is_set(key):
            continue
        obj_val = getattr(obj, key)
        db_key = subs.get(key, key)
        db_val = db_obj[db_key]
        if isinstance(obj_val, datetime.datetime):
            obj_val = obj_val.replace(tzinfo=None)

        if key in comparators:
            comparator = comparators[key]
            comparator(db_val, obj_val)
        else:
            test.assertEqual(db_val, obj_val)


class _BaseTestCase(test.base.TestCase):
    def setUp(self):
        super(_BaseTestCase, self).setUp()
        self.user_id = 'fake-user'
        self.project_id = 'fake-project'
        self.context = context.RequestContext(self.user_id, self.project_id)

        base.CyborgObjectRegistry.register(MyObj)
        base.CyborgObjectRegistry.register(MyOwnedObject)

    def compare_obj(self, obj, db_obj, subs=None, allow_missing=None,
                    comparators=None):
        compare_obj(self, obj, db_obj, subs=subs, allow_missing=allow_missing,
                    comparators=comparators)

    def str_comparator(self, expected, obj_val):
        """Compare an object field to a string in the db by performing
        a simple coercion on the object field value.
        """
        self.assertEqual(expected, str(obj_val))


class _LocalTest(_BaseTestCase):
    def setUp(self):
        super(_LocalTest, self).setUp()
