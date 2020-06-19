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

from unittest import mock

from oslo_db import exception as db_exc

from cyborg.common import exception
from cyborg import objects
from cyborg.tests.unit.db.base import DbTestCase
from cyborg.tests.unit import fake_deployable
from cyborg.tests.unit import fake_device
from cyborg.tests.unit.objects import test_objects


class TestDeployableObject(DbTestCase):

    @property
    def fake_device(self):
        db_device = fake_device.get_fake_devices_as_dict()[0]
        return db_device

    @property
    def fake_deployable(self):
        db_deploy = fake_deployable.fake_db_deployable(id=1)
        return db_deploy

    @property
    def fake_deployable2(self):
        db_deploy = fake_deployable.fake_db_deployable(id=2)
        return db_deploy

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
        self.assertRaises(exception.ResourceNotFound,
                          objects.Deployable.get, self.context,
                          dpl.uuid)


class TestDeployableObject(test_objects._LocalTest,
                           TestDeployableObject):
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
