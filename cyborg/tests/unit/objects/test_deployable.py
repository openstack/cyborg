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

import datetime

import mock
import netaddr
from oslo_db import exception as db_exc
from oslo_serialization import jsonutils
from oslo_utils import timeutils
from oslo_context import context

from cyborg import db
from cyborg.common import exception
from cyborg import objects
from cyborg.objects import base
from cyborg import tests as test
from cyborg.tests.unit import fake_accelerator
from cyborg.tests.unit import fake_deployable
from cyborg.tests.unit import fake_attribute
from cyborg.tests.unit.objects import test_objects
from cyborg.tests.unit.db.base import DbTestCase


class _TestDeployableObject(DbTestCase):
    @property
    def fake_deployable(self):
        db_deploy = fake_deployable.fake_db_deployable(id=1)
        return db_deploy

    @property
    def fake_deployable2(self):
        db_deploy = fake_deployable.fake_db_deployable(id=2)
        return db_deploy

    @property
    def fake_accelerator(self):
        db_acc = fake_accelerator.fake_db_accelerator(id=2)
        return db_acc

    @property
    def fake_attribute(self):
        db_attr = fake_attribute.fake_db_attribute(id=2)
        return db_attr

    @property
    def fake_attribute2(self):
        db_attr = fake_attribute.fake_db_attribute(id=3)
        return db_attr

    @property
    def fake_attribute3(self):
        db_attr = fake_attribute.fake_db_attribute(id=4)
        return db_attr

    def test_create(self):
        db_acc = self.fake_accelerator
        acc = objects.Accelerator(context=self.context,
                                  **db_acc)
        acc.create(self.context)
        acc_get = objects.Accelerator.get(self.context, acc.uuid)
        db_dpl = self.fake_deployable
        dpl = objects.Deployable(context=self.context,
                                 **db_dpl)

        dpl.accelerator_id = acc_get.id
        dpl.create(self.context)

        self.assertEqual(db_dpl['uuid'], dpl.uuid)

    def test_get(self):
        db_acc = self.fake_accelerator
        acc = objects.Accelerator(context=self.context,
                                  **db_acc)
        acc.create(self.context)
        acc_get = objects.Accelerator.get(self.context, acc.uuid)
        db_dpl = self.fake_deployable
        dpl = objects.Deployable(context=self.context,
                                 **db_dpl)

        dpl.accelerator_id = acc_get.id
        dpl.create(self.context)
        dpl_get = objects.Deployable.get(self.context, dpl.uuid)
        self.assertEqual(dpl_get.uuid, dpl.uuid)

    def test_get_by_filter(self):
        db_acc = self.fake_accelerator
        acc = objects.Accelerator(context=self.context,
                                  **db_acc)
        acc.create(self.context)
        acc_get = objects.Accelerator.get(self.context, acc.uuid)
        db_dpl = self.fake_deployable
        dpl = objects.Deployable(context=self.context,
                                 **db_dpl)

        dpl.accelerator_id = acc_get.id
        dpl.create(self.context)
        query = {"uuid": dpl['uuid']}
        dpl_get_list = objects.Deployable.get_by_filter(self.context, query)

        self.assertEqual(dpl_get_list[0].uuid, dpl.uuid)

    def test_save(self):
        db_acc = self.fake_accelerator
        acc = objects.Accelerator(context=self.context,
                                  **db_acc)
        acc.create(self.context)
        acc_get = objects.Accelerator.get(self.context, acc.uuid)
        db_dpl = self.fake_deployable
        dpl = objects.Deployable(context=self.context,
                                 **db_dpl)

        dpl.accelerator_id = acc_get.id
        dpl.create(self.context)
        dpl.host = 'test_save'
        dpl.save(self.context)
        dpl_get = objects.Deployable.get(self.context, dpl.uuid)
        self.assertEqual(dpl_get.host, 'test_save')

    def test_destroy(self):
        db_acc = self.fake_accelerator
        acc = objects.Accelerator(context=self.context,
                                  **db_acc)
        acc.create(self.context)
        acc_get = objects.Accelerator.get(self.context, acc.uuid)
        db_dpl = self.fake_deployable
        dpl = objects.Deployable(context=self.context,
                                 **db_dpl)

        dpl.accelerator_id = acc_get.id
        dpl.create(self.context)
        self.assertEqual(db_dpl['uuid'], dpl.uuid)
        dpl.destroy(self.context)
        self.assertRaises(exception.DeployableNotFound,
                          objects.Deployable.get, self.context,
                          dpl.uuid)

    def test_add_attribute(self):
        db_acc = self.fake_accelerator
        acc = objects.Accelerator(context=self.context,
                                  **db_acc)
        acc.create(self.context)
        acc_get = objects.Accelerator.get(self.context, acc.uuid)

        db_dpl = self.fake_deployable
        dpl = objects.Deployable(context=self.context,
                                 **db_dpl)
        dpl.accelerator_id = acc_get.id
        dpl.create(self.context)
        dpl_get = objects.Deployable.get(self.context, dpl.uuid)

        db_attr = self.fake_attribute
        attr = objects.Attribute(context=self.context,
                                 **db_attr)
        attr.deployable_id = dpl_get.id
        attr.create(self.context)

        dpl.add_attribute(attr)
        dpl.save(self.context)

        dpl_get = objects.Deployable.get(self.context, dpl.uuid)
        self.assertEqual(len(dpl_get.attributes_list), 1)
        self.assertEqual(dpl_get.attributes_list[0].id, attr.id)

    def test_delete_attribute(self):
        db_acc = self.fake_accelerator
        acc = objects.Accelerator(context=self.context,
                                  **db_acc)
        acc.create(self.context)
        acc_get = objects.Accelerator.get(self.context, acc.uuid)

        db_dpl = self.fake_deployable
        dpl = objects.Deployable(context=self.context,
                                 **db_dpl)
        dpl.accelerator_id = acc_get.id
        dpl.create(self.context)
        dpl_get = objects.Deployable.get(self.context, dpl.uuid)
        db_attr = self.fake_attribute
        attr = objects.Attribute(context=self.context,
                                 **db_attr)
        attr.deployable_id = dpl_get.id
        attr.create(self.context)
        dpl_get.add_attribute(attr)
        dpl_get.save(self.context)
        dpl_get = objects.Deployable.get(self.context, dpl_get.uuid)
        self.assertEqual(len(dpl_get.attributes_list), 1)
        self.assertEqual(dpl_get.attributes_list[0].id, attr.id)

        dpl_get.delete_attribute(self.context, dpl_get.attributes_list[0])
        self.assertEqual(len(dpl_get.attributes_list), 0)
        self.assertRaises(exception.AttributeNotFound,
                          objects.Attribute.get, self.context,
                          attr.uuid)

    def test_get_by_filter_with_attributes(self):
        db_acc = self.fake_accelerator
        acc = objects.Accelerator(context=self.context,
                                  **db_acc)
        acc.create(self.context)
        acc_get = objects.Accelerator.get(self.context, acc.uuid)

        db_dpl = self.fake_deployable
        dpl = objects.Deployable(context=self.context,
                                 **db_dpl)
        dpl.accelerator_id = acc_get.id
        dpl.create(self.context)
        dpl_get = objects.Deployable.get(self.context, dpl.uuid)

        db_dpl2 = self.fake_deployable2
        dpl2 = objects.Deployable(context=self.context,
                                  **db_dpl2)
        dpl2.accelerator_id = acc_get.id
        dpl2.create(self.context)
        dpl2_get = objects.Deployable.get(self.context, dpl2.uuid)

        db_attr = self.fake_attribute
        attr = objects.Attribute(context=self.context,
                                 **db_attr)
        attr.deployable_id = dpl_get.id
        attr.create(self.context)

        db_attr2 = self.fake_attribute2
        attr2 = objects.Attribute(context=self.context,
                                  **db_attr2)
        attr2.deployable_id = dpl2_get.id
        attr2.create(self.context)

        db_attr3 = self.fake_attribute3
        attr3 = objects.Attribute(context=self.context,
                                  **db_attr3)
        attr3.deployable_id = dpl2_get.id
        attr3.create(self.context)

        dpl.add_attribute(attr)
        dpl.save(self.context)

        dpl2.add_attribute(attr2)
        dpl2.save(self.context)

        dpl2.add_attribute(attr3)
        dpl2.save(self.context)

        query = {"attr_key": "attr_val"}

        dpl_get_list = objects.Deployable.get_by_filter(self.context, query)
        self.assertEqual(len(dpl_get_list), 2)
        self.assertEqual(dpl_get_list[0].uuid, dpl.uuid)

        attr2.set_key_value_pair("test_key", "test_val")
        attr2.save(self.context)

        attr3.set_key_value_pair("test_key3", "test_val3")
        attr3.save(self.context)

        query = {"test_key": "test_val"}
        dpl_get_list = objects.Deployable.get_by_filter(self.context, query)
        self.assertEqual(len(dpl_get_list), 1)
        self.assertEqual(dpl_get_list[0].uuid, dpl2.uuid)

        query = {"test_key": "test_val", "test_key3": "test_val3"}
        dpl_get_list = objects.Deployable.get_by_filter(self.context, query)
        self.assertEqual(len(dpl_get_list), 1)
        self.assertEqual(dpl_get_list[0].uuid, dpl2.uuid)

        query = {"host": "host_name", "test_key3": "test_val3"}
        dpl_get_list = objects.Deployable.get_by_filter(self.context, query)
        self.assertEqual(len(dpl_get_list), 1)
        self.assertEqual(dpl_get_list[0].uuid, dpl2.uuid)

    def test_get_by_host(self):
        dep1 = self.fake_deployable
        dep2 = self.fake_deployable2
        fake_hostname = 'host_name'
        dep_obj1 = objects.Deployable(context=self.context,
                                      **dep1)
        dep_obj2 = objects.Deployable(context=self.context,
                                      **dep2)
        dep_obj1.create(self.context)
        dep_obj2.create(self.context)

        dep_obj1.save(self.context)
        dep_obj2.save(self.context)
        dep_objs = objects.Deployable.get_by_host(self.context, fake_hostname)
        self.assertEqual(dep_objs[0].host, fake_hostname)
        self.assertEqual(dep_objs[1].host, fake_hostname)


class TestDeployableObject(test_objects._LocalTest,
                           _TestDeployableObject):
    def _test_save_objectfield_fk_constraint_fails(self, foreign_key,
                                                   expected_exception):

        error = db_exc.DBReferenceError('table', 'constraint', foreign_key,
                                        'key_table')
        # Prevent lazy-loading any fields, results in InstanceNotFound
        deployable = fake_deployable.fake_deployable_obj(self.context)
        fields_with_save_methods = [field for field in deployable.fields
                                    if hasattr(deployable, '_save_%s' % field)]
        for field in fields_with_save_methods:
            @mock.patch.object(deployable, '_save_%s' % field)
            @mock.patch.object(deployable, 'obj_attr_is_set')
            def _test(mock_is_set, mock_save_field):
                mock_is_set.return_value = True
                mock_save_field.side_effect = error
                deployable.obj_reset_changes(fields=[field])
                deployable._changed_fields.add(field)
                self.assertRaises(expected_exception, deployable.save)
                deployable.obj_reset_changes(fields=[field])
            _test()
