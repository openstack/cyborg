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


class _TestPhysicalFunctionObject(DbTestCase):
    @property
    def fake_physical_function(self):
        db_pf = fake_physical_function.fake_db_physical_function(id=1)
        return db_pf

    @property
    def fake_virtual_function(self):
        db_vf = fake_virtual_function.fake_db_virtual_function(id=3)
        return db_vf

    @property
    def fake_accelerator(self):
        db_acc = fake_accelerator.fake_db_accelerator(id=2)
        return db_acc

    def test_create(self):
        db_pf = self.fake_physical_function
        db_acc = self.fake_accelerator
        acc = objects.Accelerator(context=self.context,
                                  **db_acc)
        acc.create(self.context)
        acc_get = objects.Accelerator.get(self.context, acc.uuid)
        pf = objects.PhysicalFunction(context=self.context,
                                      **db_pf)
        pf.accelerator_id = acc_get.id
        pf.create(self.context)

        self.assertEqual(db_pf['uuid'], pf.uuid)

    def test_get(self):
        db_pf = self.fake_physical_function
        db_acc = self.fake_accelerator
        acc = objects.Accelerator(context=self.context,
                                  **db_acc)
        acc.create(self.context)
        acc_get = objects.Accelerator.get(self.context, acc.uuid)
        pf = objects.PhysicalFunction(context=self.context,
                                      **db_pf)
        pf.accelerator_id = acc_get.id
        pf.create(self.context)
        pf_get = objects.PhysicalFunction.get(self.context, pf.uuid)
        self.assertEqual(pf_get.uuid, pf.uuid)

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

        query = {"vendor": pf['vendor']}
        pf_get_list = objects.PhysicalFunction.get_by_filter(self.context,
                                                             query)

        self.assertEqual(len(pf_get_list), 1)
        self.assertEqual(pf_get_list[0].uuid, pf.uuid)
        self.assertEqual(objects.PhysicalFunction, type(pf_get_list[0]))
        self.assertEqual(objects.VirtualFunction,
                         type(pf_get_list[0].virtual_function_list[0]))
        self.assertEqual(pf_get_list[0].virtual_function_list[0].uuid,
                         vf.uuid)

    def test_save(self):
        db_pf = self.fake_physical_function
        db_acc = self.fake_accelerator

        acc = objects.Accelerator(context=self.context,
                                  **db_acc)
        acc.create(self.context)
        acc_get = objects.Accelerator.get(self.context, acc.uuid)
        pf = objects.PhysicalFunction(context=self.context,
                                      **db_pf)
        pf.accelerator_id = acc_get.id
        pf.create(self.context)
        pf_get = objects.PhysicalFunction.get(self.context, pf.uuid)
        pf_get.host = 'test_save'

        pf_get.save(self.context)
        pf_get_2 = objects.PhysicalFunction.get(self.context, pf.uuid)
        self.assertEqual(pf_get_2.host, 'test_save')

    def test_destroy(self):
        db_pf = self.fake_physical_function
        db_acc = self.fake_accelerator
        acc = objects.Accelerator(context=self.context,
                                  **db_acc)
        acc.create(self.context)
        acc_get = objects.Accelerator.get(self.context, acc.uuid)
        pf = objects.PhysicalFunction(context=self.context,
                                      **db_pf)
        pf.accelerator_id = acc_get.id
        pf.create(self.context)
        pf_get = objects.PhysicalFunction.get(self.context, pf.uuid)
        self.assertEqual(db_pf['uuid'], pf_get.uuid)
        pf_get.destroy(self.context)
        self.assertRaises(exception.DeployableNotFound,
                          objects.PhysicalFunction.get, self.context,
                          pf_get['uuid'])

    def test_add_vf(self):
        db_pf = self.fake_physical_function
        db_vf = self.fake_virtual_function
        db_acc = self.fake_accelerator
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
        pf_get_2 = objects.PhysicalFunction.get(self.context, pf.uuid)

        self.assertEqual(db_vf['uuid'],
                         pf_get_2.virtual_function_list[0].uuid)


class TestPhysicalFunctionObject(test_objects._LocalTest,
                                 _TestPhysicalFunctionObject):
    def _test_save_objectfield_fk_constraint_fails(self, foreign_key,
                                                   expected_exception):

        error = db_exc.DBReferenceError('table', 'constraint', foreign_key,
                                        'key_table')
        # Prevent lazy-loading any fields, results in InstanceNotFound
        pf = fake_physical_function.physical_function_obj(self.context)
        fields_with_save_methods = [field for field in pf.fields
                                    if hasattr(pf, '_save_%s' % field)]
        for field in fields_with_save_methods:
            @mock.patch.object(pf, '_save_%s' % field)
            @mock.patch.object(pf, 'obj_attr_is_set')
            def _test(mock_is_set, mock_save_field):
                mock_is_set.return_value = True
                mock_save_field.side_effect = error
                pf.obj_reset_changes(fields=[field])
                pf._changed_fields.add(field)
                self.assertRaises(expected_exception, pf.save)
                pf.obj_reset_changes(fields=[field])
            _test()
