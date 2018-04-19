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
from cyborg.tests.unit import fake_physical_function
from cyborg.tests.unit import fake_virtual_function
from cyborg.tests.unit import fake_accelerator
from cyborg.tests.unit.objects import test_objects
from cyborg.tests.unit.db.base import DbTestCase


class _TestVirtualFunctionObject(DbTestCase):
    @property
    def fake_accelerator(self):
        db_acc = fake_accelerator.fake_db_accelerator(id=1)
        return db_acc

    @property
    def fake_virtual_function(self):
        db_vf = fake_virtual_function.fake_db_virtual_function(id=2)
        return db_vf

    @property
    def fake_physical_function(self):
        db_pf = fake_physical_function.fake_db_physical_function(id=3)
        return db_pf

    def test_create(self):
        db_acc = self.fake_accelerator
        db_vf = self.fake_virtual_function

        acc = objects.Accelerator(context=self.context,
                                  **db_acc)
        acc.create(self.context)
        acc_get = objects.Accelerator.get(self.context, acc.uuid)
        vf = objects.VirtualFunction(context=self.context,
                                     **db_vf)
        vf.accelerator_id = acc_get.id
        vf.create(self.context)

        self.assertEqual(db_vf['uuid'], vf.uuid)

    def test_get(self):
        db_vf = self.fake_virtual_function
        db_acc = self.fake_accelerator

        acc = objects.Accelerator(context=self.context,
                                  **db_acc)
        acc.create(self.context)
        acc_get = objects.Accelerator.get(self.context, acc.uuid)
        vf = objects.VirtualFunction(context=self.context,
                                     **db_vf)
        vf.accelerator_id = acc_get.id
        vf.create(self.context)
        vf_get = objects.VirtualFunction.get(self.context, vf.uuid)
        self.assertEqual(vf_get.uuid, vf.uuid)

    def test_get_by_filter(self):
        db_acc = self.fake_accelerator
        db_pf = self.fake_physical_function
        db_vf = self.fake_virtual_function
        acc = objects.Accelerator(context=self.context,
                                  **db_acc)
        acc.create(self.context)
        acc_get = objects.Accelerator.get(self.context, acc.uuid)
        pf = objects.PhysicalFunction(context=self.context,
                                      **db_pf)

        pf.accelerator_id = acc_get.id
        pf.create(self.context)
        pf_get = objects.PhysicalFunction.get(self.context, pf.uuid)
        vf = objects.VirtualFunction(context=self.context,
                                     **db_vf)
        vf.accelerator_id = pf_get.accelerator_id
        vf.create(self.context)
        vf_get = objects.VirtualFunction.get(self.context, vf.uuid)
        pf_get.add_vf(vf_get)
        pf_get.save(self.context)

        query = {"vendor": pf_get['vendor']}
        vf_get_list = objects.VirtualFunction.get_by_filter(self.context,
                                                            query)

        self.assertEqual(len(vf_get_list), 1)
        self.assertEqual(vf_get_list[0].uuid, vf.uuid)
        self.assertEqual(objects.VirtualFunction, type(vf_get_list[0]))
        self.assertEqual(1, 1)

    def test_get_by_filter2(self):
        db_acc = self.fake_accelerator

        db_pf = self.fake_physical_function
        db_vf = self.fake_virtual_function

        db_pf2 = self.fake_physical_function
        db_vf2 = self.fake_virtual_function
        acc = objects.Accelerator(context=self.context,
                                  **db_acc)
        acc.create(self.context)
        acc_get = objects.Accelerator.get(self.context, acc.uuid)
        pf = objects.PhysicalFunction(context=self.context,
                                      **db_pf)

        pf.accelerator_id = acc_get.id
        pf.create(self.context)
        pf_get = objects.PhysicalFunction.get(self.context, pf.uuid)
        pf2 = objects.PhysicalFunction(context=self.context,
                                       **db_pf2)

        pf2.accelerator_id = acc_get.id
        pf2.create(self.context)
        pf_get2 = objects.PhysicalFunction.get(self.context, pf2.uuid)
        query = {"uuid": pf2.uuid}

        pf_get_list = objects.PhysicalFunction.get_by_filter(self.context,
                                                             query)
        self.assertEqual(1, 1)

    def test_save(self):
        db_vf = self.fake_virtual_function
        db_acc = self.fake_accelerator

        acc = objects.Accelerator(context=self.context,
                                  **db_acc)
        acc.create(self.context)
        acc_get = objects.Accelerator.get(self.context, acc.uuid)
        vf = objects.VirtualFunction(context=self.context,
                                     **db_vf)
        vf.accelerator_id = acc_get.id
        vf.create(self.context)
        vf_get = objects.VirtualFunction.get(self.context, vf.uuid)
        vf_get.host = 'test_save'
        vf_get.save(self.context)
        vf_get_2 = objects.VirtualFunction.get(self.context, vf.uuid)
        self.assertEqual(vf_get_2.host, 'test_save')

    def test_destroy(self):
        db_vf = self.fake_virtual_function
        db_acc = self.fake_accelerator

        acc = objects.Accelerator(context=self.context,
                                  **db_acc)
        acc.create(self.context)
        acc_get = objects.Accelerator.get(self.context, acc.uuid)
        vf = objects.VirtualFunction(context=self.context,
                                     **db_vf)
        vf.accelerator_id = acc_get.id
        vf.create(self.context)
        vf_get = objects.VirtualFunction.get(self.context, vf.uuid)
        self.assertEqual(db_vf['uuid'], vf_get.uuid)
        vf_get.destroy(self.context)
        self.assertRaises(exception.DeployableNotFound,
                          objects.VirtualFunction.get, self.context,
                          vf_get['uuid'])


class TestVirtualFunctionObject(test_objects._LocalTest,
                                _TestVirtualFunctionObject):
    def _test_save_objectfield_fk_constraint_fails(self, foreign_key,
                                                   expected_exception):

        error = db_exc.DBReferenceError('table', 'constraint', foreign_key,
                                        'key_table')
        # Prevent lazy-loading any fields, results in InstanceNotFound
        vf = fake_virtual_function.virtual_function_obj(self.context)
        fields_with_save_methods = [field for field in vf.fields
                                    if hasattr(vf, '_save_%s' % field)]
        for field in fields_with_save_methods:
            @mock.patch.object(vf, '_save_%s' % field)
            @mock.patch.object(vf, 'obj_attr_is_set')
            def _test(mock_is_set, mock_save_field):
                mock_is_set.return_value = True
                mock_save_field.side_effect = error
                vf.obj_reset_changes(fields=[field])
                vf._changed_fields.add(field)
                self.assertRaises(expected_exception, vf.save)
                vf.obj_reset_changes(fields=[field])
            _test()
