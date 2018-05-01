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
from cyborg.tests.unit import fake_attribute
from cyborg.tests.unit import fake_deployable
from cyborg.tests.unit import fake_accelerator
from cyborg.tests.unit.objects import test_objects
from cyborg.tests.unit.db.base import DbTestCase


class _TestDeployableObject(DbTestCase):
    @property
    def fake_deployable(self):
        db_deploy = fake_deployable.fake_db_deployable(id=1)
        return db_deploy

    @property
    def fake_accelerator(self):
        db_acc = fake_accelerator.fake_db_accelerator(id=2)
        return db_acc

    @property
    def fake_attribute(self):
        db_attr = fake_attribute.fake_db_attribute(id=2)
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
        dpl_get = objects.Deployable.get(self.context, dpl.uuid)

        db_attr = self.fake_attribute
        attr = objects.Attribute(context=self.context,
                                 **db_attr)
        attr.deployable_id = dpl_get.id
        attr.create(self.context)

        self.assertEqual(db_attr['uuid'], attr.uuid)

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

        db_attr = self.fake_attribute
        attr = objects.Attribute(context=self.context,
                                 **db_attr)
        attr.deployable_id = dpl_get.id
        attr.create(self.context)
        attr_get = objects.Attribute.get(self.context, attr.uuid)

        self.assertEqual(db_attr['uuid'], attr_get.uuid)

    def test_get_by_deployable_uuid(self):
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
        attr_get = objects.Attribute.get_by_deployable_id(
            self.context, dpl_get.id)[0]

        self.assertEqual(db_attr['uuid'], attr_get.uuid)

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
        dpl_get = objects.Deployable.get(self.context, dpl.uuid)

        db_attr = self.fake_attribute
        attr = objects.Attribute(context=self.context,
                                 **db_attr)
        attr.deployable_id = dpl_get.id
        attr.create(self.context)
        attr_get = objects.Attribute.get(self.context, attr.uuid)
        attr_get.set_key_value_pair("test_key", "test_val")
        attr_get.save(self.context)
        attr_get_2 = objects.Attribute.get(self.context, attr_get.uuid)
        self.assertEqual(attr_get_2.key, "test_key")
        self.assertEqual(attr_get_2.value, "test_val")

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
        dpl_get = objects.Deployable.get(self.context, dpl.uuid)

        db_attr = self.fake_attribute
        attr = objects.Attribute(context=self.context,
                                 **db_attr)
        attr.deployable_id = dpl_get.id
        attr.create(self.context)
        self.assertEqual(db_attr['uuid'], attr.uuid)

        attr.destroy(self.context)
        self.assertRaises(exception.AttributeNotFound,
                          objects.Attribute.get, self.context,
                          attr.uuid)

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
        dpl_get = objects.Deployable.get(self.context, dpl.uuid)

        db_attr = self.fake_attribute
        attr = objects.Attribute(context=self.context,
                                 **db_attr)
        attr.deployable_id = dpl_get.id
        attr.create(self.context)
        attr_filter = {"key": "attr_key", "value": "attr_val"}
        attr_get = objects.Attribute.get_by_filter(
            self.context, attr_filter)[0]

        self.assertEqual(db_attr['uuid'], attr_get.uuid)

        attr_filter = {"key": "attr_key", "value": "attr_val2"}
        attr_get_list = objects.Attribute.get_by_filter(
            self.context, attr_filter)
        self.assertEqual(len(attr_get_list), 0)
