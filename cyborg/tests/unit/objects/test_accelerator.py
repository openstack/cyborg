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
from cyborg.tests.unit.objects import test_objects
from cyborg.tests.unit.db.base import DbTestCase


class _TestAcceleratorObject(DbTestCase):
    @property
    def fake_accelerator(self):
        db_acc = fake_accelerator.fake_db_accelerator(id=2)
        return db_acc

    @mock.patch.object(db.api.Connection, 'accelerator_create')
    def test_create(self, mock_create):
        mock_create.return_value = self.fake_accelerator
        acc = objects.Accelerator(context=self.context,
                                  **mock_create.return_value)
        acc.create(self.context)

        self.assertEqual(self.fake_accelerator['id'], acc.id)

    @mock.patch.object(db.api.Connection, 'accelerator_get')
    def test_get(self, mock_get):
        mock_get.return_value = self.fake_accelerator
        acc = objects.Accelerator(context=self.context,
                                  **mock_get.return_value)
        acc.create(self.context)
        acc_get = objects.Accelerator.get(self.context, acc['uuid'])
        self.assertEqual(acc_get.uuid, acc.uuid)

    @mock.patch.object(db.api.Connection, 'accelerator_update')
    def test_save(self, mock_save):
        mock_save.return_value = self.fake_accelerator
        acc = objects.Accelerator(context=self.context,
                                  **mock_save.return_value)
        acc.create(self.context)
        acc.name = 'test_save'
        acc.save(self.context)
        acc_get = objects.Accelerator.get(self.context, acc['uuid'])
        self.assertEqual(acc_get.name, 'test_save')

    @mock.patch.object(db.api.Connection, 'accelerator_delete')
    def test_destroy(self, mock_destroy):
        mock_destroy.return_value = self.fake_accelerator
        acc = objects.Accelerator(context=self.context,
                                  **mock_destroy.return_value)
        acc.create(self.context)
        self.assertEqual(self.fake_accelerator['id'], acc.id)
        acc.destroy(self.context)
        self.assertRaises(exception.AcceleratorNotFound,
                          objects.Accelerator.get, self.context,
                          acc['uuid'])


class TestAcceleratorObject(test_objects._LocalTest,
                            _TestAcceleratorObject):
    def _test_save_objectfield_fk_constraint_fails(self, foreign_key,
                                                   expected_exception):

        error = db_exc.DBReferenceError('table', 'constraint', foreign_key,
                                        'key_table')
        # Prevent lazy-loading any fields, results in InstanceNotFound
        accelerator = fake_accelerator.fake_accelerator_obj(self.context)
        fields_with_save_methods = [field for field in accelerator.fields
                                    if hasattr(accelerator,
                                               '_save_%s' % field)]
        for field in fields_with_save_methods:
            @mock.patch.object(accelerator, '_save_%s' % field)
            @mock.patch.object(accelerator, 'obj_attr_is_set')
            def _test(mock_is_set, mock_save_field):
                mock_is_set.return_value = True
                mock_save_field.side_effect = error
                accelerator.obj_reset_changes(fields=[field])
                accelerator._changed_fields.add(field)
                self.assertRaises(expected_exception, accelerator.save)
                accelerator.obj_reset_changes(fields=[field])
            _test()
