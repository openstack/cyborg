# Copyright 2019 Huawei Technologies Co.,LTD.
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

import mock

from testtools.matchers import HasLength
from cyborg import objects
from cyborg.tests.unit.db import base
from cyborg.tests.unit.db import utils
from cyborg.tests.unit import fake_device
from cyborg.tests.unit import fake_deployable
from cyborg.tests.unit import fake_attribute
from cyborg.tests.unit.objects import test_objects
from cyborg.tests.unit.db.base import DbTestCase
from cyborg.common import exception


class _TestDeployableObject(DbTestCase):

    @property
    def fake_device(self):
        db_device = fake_device.fake_db_device(id=1)
        return db_device

    @property
    def fake_deployable(self):
        db_deploy = fake_deployable.fake_db_deployable(id=1)
        return db_deploy

    @property
    def fake_deployable2(self):
        db_deploy = fake_deployable.fake_db_deployable(id=2)
        return db_deploy

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
        db_device = self.fake_device
        device = objects.Device(context=self.context,
                                **db_device)
        device.create(self.context)
        device_get = objects.Device.get(self.context, device.uuid)
        db_dpl = self.fake_deployable
        dpl = objects.Deployable(context=self.context,
                                 **db_dpl)

        dpl.device_id = device_get.id
        dpl.create(self.context)

        self.assertEqual(db_dpl['uuid'], dpl.uuid)

    def test_get(self):
        db_device = self.fake_device
        device = objects.Device(context=self.context,
                                **db_device)
        device.create(self.context)
        device_get = objects.Device.get(self.context, device.uuid)
        db_dpl = self.fake_deployable
        dpl = objects.Deployable(context=self.context,
                                 **db_dpl)

        dpl.device_id = device_get.id
        dpl.create(self.context)
        dpl_get = objects.Deployable.get(self.context, dpl.uuid)
        self.assertEqual(dpl_get.uuid, dpl.uuid)

    def test_get_by_filter(self):
        db_device = self.fake_device
        device = objects.Device(context=self.context,
                                **db_device)
        device.create(self.context)
        device_get = objects.Device.get(self.context, device.uuid)
        db_dpl = self.fake_deployable
        dpl = objects.Deployable(context=self.context,
                                 **db_dpl)

        dpl.device_id = device_get.id
        dpl.create(self.context)
        query = {"uuid": dpl['uuid']}
        dpl_get_list = objects.Deployable.get_by_filter(self.context, query)

        self.assertEqual(dpl_get_list[0].uuid, dpl.uuid)

    def test_save(self):
        db_device = self.fake_device
        device = objects.Device(context=self.context,
                                **db_device)
        device.create(self.context)
        device_get = objects.Device.get(self.context, device.uuid)
        db_dpl = self.fake_deployable
        dpl = objects.Deployable(context=self.context,
                                 **db_dpl)

        dpl.device_id = device_get.id
        dpl.create(self.context)
        dpl.num_accelerators = 8
        dpl.save(self.context)
        dpl_get = objects.Deployable.get(self.context, dpl.uuid)
        self.assertEqual(dpl_get.num_accelerators, 8)

    def test_destroy(self):
        db_device = self.fake_device
        device = objects.Device(context=self.context,
                                **db_device)
        device.create(self.context)
        device_get = objects.Device.get(self.context, device.uuid)
        db_dpl = self.fake_deployable
        dpl = objects.Deployable(context=self.context,
                                 **db_dpl)

        dpl.device_id = device_get.id
        dpl.create(self.context)
        self.assertEqual(db_dpl['uuid'], dpl.uuid)
        dpl.destroy(self.context)
        self.assertRaises(exception.DeployableNotFound,
                          objects.Deployable.get, self.context,
                          dpl.uuid)

    def test_add_attribute(self):
        db_device = self.fake_device
        device = objects.Device(context=self.context,
                                **db_device)
        device.create(self.context)
        device_get = objects.Device.get(self.context, device.uuid)
        db_dpl = self.fake_deployable
        dpl = objects.Deployable(context=self.context,
                                 **db_dpl)

        dpl.device_id = device_get.id
        dpl.create(self.context)
        dpl_get = objects.Deployable.get(self.context, dpl.uuid)

        db_attr = self.fake_attribute

        dpl.add_attribute(self.context, db_attr['key'], db_attr['value'])
        dpl.save(self.context)

        dpl_get = objects.Deployable.get(self.context, dpl.uuid)
        self.assertEqual(len(dpl_get.attributes_list), 1)

    def test_delete_attribute(self):
        db_device = self.fake_device
        device = objects.Device(context=self.context,
                                **db_device)
        device.create(self.context)
        device_get = objects.Device.get(self.context, device.uuid)
        db_dpl = self.fake_deployable
        dpl = objects.Deployable(context=self.context,
                                 **db_dpl)

        dpl.device_id = device_get.id
        dpl.create(self.context)
        dpl_get = objects.Deployable.get(self.context, dpl.uuid)
        db_attr = self.fake_attribute
        dpl_get.add_attribute(self.context, db_attr['key'], db_attr['value'])
        dpl_get.save(self.context)
        dpl_get = objects.Deployable.get(self.context, dpl_get.uuid)
        self.assertEqual(len(dpl_get.attributes_list), 1)

        dpl_get.delete_attribute(self.context, dpl_get.attributes_list[0])
        self.assertEqual(len(dpl_get.attributes_list), 0)

    def test_get_by_filter_with_attributes(self):
        db_device = self.fake_device
        device = objects.Device(context=self.context,
                                **db_device)
        device.create(self.context)
        device_get = objects.Device.get(self.context, device.uuid)
        db_dpl = self.fake_deployable
        dpl = objects.Deployable(context=self.context,
                                 **db_dpl)

        dpl.device_id = device_get.id
        dpl.create(self.context)
        dpl_get = objects.Deployable.get(self.context, dpl.uuid)

        db_dpl2 = self.fake_deployable2
        dpl2 = objects.Deployable(context=self.context,
                                  **db_dpl2)
        dpl2.device_id = device_get.id
        dpl2.create(self.context)
        dpl2_get = objects.Deployable.get(self.context, dpl2.uuid)

        db_attr = self.fake_attribute

        db_attr2 = self.fake_attribute2

        db_attr3 = self.fake_attribute3

        dpl.add_attribute(self.context, 'attr_key', 'attr_val')
        dpl.save(self.context)

        dpl2.add_attribute(self.context, 'test_key', 'test_val')
        dpl2.add_attribute(self.context, 'test_key3', 'test_val3')
        dpl2.save(self.context)

        query = {"attr_key": "attr_val"}

        dpl_get_list = objects.Deployable.get_by_filter(self.context, query)
        self.assertEqual(len(dpl_get_list), 1)
        self.assertEqual(dpl_get_list[0].uuid, dpl.uuid)

        query = {"test_key": "test_val"}
        dpl_get_list = objects.Deployable.get_by_filter(self.context, query)
        self.assertEqual(len(dpl_get_list), 1)
        self.assertEqual(dpl_get_list[0].uuid, dpl2.uuid)

        query = {"test_key": "test_val", "test_key3": "test_val3"}
        dpl_get_list = objects.Deployable.get_by_filter(self.context, query)
        self.assertEqual(len(dpl_get_list), 1)
        self.assertEqual(dpl_get_list[0].uuid, dpl2.uuid)

        query = {"num_accelerators": 4, "test_key3": "test_val3"}
        dpl_get_list = objects.Deployable.get_by_filter(self.context, query)
        self.assertEqual(len(dpl_get_list), 1)
        self.assertEqual(dpl_get_list[0].uuid, dpl2.uuid)


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
