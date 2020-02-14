# Copyright 2019 Intel.
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

from io import BytesIO
import json
import requests
from requests import structures
from requests import utils
from unittest import mock

from testtools.matchers import HasLength

from cyborg.common import constants
from cyborg.common import exception
from cyborg import objects
from cyborg.tests.unit.db import base
from cyborg.tests.unit import fake_deployable
from cyborg.tests.unit import fake_extarq


class TestFPGAExtARQObject(base.DbTestCase):

    def setUp(self):
        super(TestFPGAExtARQObject, self).setUp()
        self.fake_fpga_db_extarqs = fake_extarq.get_fake_fpga_db_extarqs()
        self.fake_obj_fpga_extarqs = fake_extarq.get_fake_fpga_extarq_objs()
        classes = ["no_program", "bitstream_program",
                   "function_program", "bad_program"]
        self.class_fgpa_objects = dict(
            zip(classes, self.fake_obj_fpga_extarqs))
        self.class_fgpa_dbs = dict(
            zip(classes, self.fake_fpga_db_extarqs))
        self.bitstream_id = self.class_fgpa_objects["bitstream_program"][
            "device_profile_group"][constants.ACCEL_BITSTREAM_ID]
        self.function_id = self.class_fgpa_objects["function_program"][
            "device_profile_group"][constants.ACCEL_FUNCTION_ID]
        self.images_md = {
            "/images":
            [
                {"id": self.bitstream_id,
                 "tags": ["trait:CUSTOM_FPGA_INTEL"],
                 constants.ACCEL_FUNCTION_ID: self.function_id},
            ]
        }
        self.deployable_uuids = ['0acbf8d6-e02a-4394-aae3-57557d209498']
        self.bdf = {"domain": "0000", "bus": "00",
                    "device": "01", "function": "1"}
        self.cpid = {
            "id": 0,
            "uuid": "e4a66b0d-b377-40d6-9cdc-6bf7e720e596",
            "device_id": "1",
            "cpid_type": "PCI",
            "cpid_info": json.dumps(self.bdf).encode('utf-8')
        }

    def response(self, status_code=200, content='', headers=None,
                 reason=None, elapsed=0, request=None, stream=False):
        res = requests.Response()
        res.status_code = status_code
        if isinstance(content, (dict, list)):
            content = json.dumps(content).encode('utf-8')
        if isinstance(content, str):
            content = content.encode('utf-8')
        res._content = content
        res._content_consumed = content
        res.headers = structures.CaseInsensitiveDict(headers or {})
        res.encoding = utils.get_encoding_from_headers(res.headers)
        res.reason = reason
        res.request = request
        if hasattr(request, 'url'):
            res.url = request.url
            if isinstance(request.url, bytes):
                res.url = request.url.decode('utf-8')

        if stream:
            res.raw = BytesIO(content)
        else:
            res.raw = BytesIO(b'')
        # normally this closes the underlying connection,
        #  but we have nothing to free.
        res.close = lambda *args, **kwargs: None
        return res

    def images_get(self, url, *args, **kw):
        images = {"images": []}
        params = kw.get("params", {})
        bit_id = None
        res = None
        if url != "/images":
            bit_id = url.rsplit("/", 1)[-1]
            params["id"] = bit_id
        tags = kw.pop("tags", [])
        for image in self.images_md["/images"]:
            if tags <= image["tags"] and params.items() <= image.items():
                images["images"].append(image)
                res = self.response(content=image)
        return res if bit_id else self.response(content=images)

    @mock.patch('cyborg.objects.ExtARQ._from_db_object')
    def test_get_bitstream_id_return_None(self, mock_from_db_obj):
        db_extarq = self.fake_fpga_db_extarqs[0]
        uuid = db_extarq['uuid']
        mock_from_db_obj.return_value = self.fake_obj_fpga_extarqs[0]
        with mock.patch.object(
            self.dbapi, 'extarq_get') as mock_extarq_get:
            mock_extarq_get.return_value = db_extarq
            obj_extarq = objects.FPGAExtARQ.get(self.context, uuid)
            mock_extarq_get.assert_called_once_with(self.context, uuid)
            self.assertEqual(obj_extarq.arq.uuid, uuid)
            self.assertIsNone(obj_extarq._get_bitstream_id())

    @mock.patch('cyborg.objects.ExtARQ._from_db_object')
    def test_get_bitstream_id_return_UUID(self, mock_from_db_obj):
        db_extarq = self.fake_fpga_db_extarqs[1]
        bit_id = db_extarq['device_profile_group'][
            constants.ACCEL_BITSTREAM_ID]
        uuid = db_extarq['uuid']
        mock_from_db_obj.return_value = self.fake_obj_fpga_extarqs[1]
        with mock.patch.object(
            self.dbapi, 'extarq_get') as mock_extarq_get:
            mock_extarq_get.return_value = db_extarq
            obj_extarq = objects.FPGAExtARQ.get(self.context, uuid)
            mock_extarq_get.assert_called_once_with(self.context, uuid)
            self.assertEqual(obj_extarq.arq.uuid, uuid)
            self.assertEqual(obj_extarq._get_bitstream_id(), bit_id)

    @mock.patch('cyborg.objects.ExtARQ._from_db_object')
    def test_get_function_id_return_UUID(self, mock_from_db_obj):
        db_extarq = self.fake_fpga_db_extarqs[2]
        fun_id = db_extarq['device_profile_group'][constants.ACCEL_FUNCTION_ID]
        uuid = db_extarq['uuid']
        mock_from_db_obj.return_value = self.fake_obj_fpga_extarqs[2]
        with mock.patch.object(
            self.dbapi, 'extarq_get') as mock_extarq_get:
            mock_extarq_get.return_value = db_extarq
            obj_extarq = objects.FPGAExtARQ.get(self.context, uuid)
            mock_extarq_get.assert_called_once_with(self.context, uuid)
            self.assertEqual(obj_extarq.arq.uuid, uuid)
            self.assertEqual(obj_extarq._get_function_id(), fun_id)

    @mock.patch('cyborg.objects.ExtARQ._from_db_object_list')
    def test_list(self, mock_from_db_obj_list):
        db_extarqs = self.fake_fpga_db_extarqs
        mock_from_db_obj_list.return_value = self.fake_obj_fpga_extarqs
        with mock.patch.object(self.dbapi, 'extarq_list',
                               autospec=True) as mock_get_list:
            mock_get_list.return_value = db_extarqs
            obj_extarqs = objects.FPGAExtARQ.list(self.context)
            self.assertEqual(1, mock_get_list.call_count)
            self.assertThat(obj_extarqs, HasLength(4))
            self.assertIsInstance(obj_extarqs[0], objects.FPGAExtARQ)
            for i, obj_extarq in enumerate(obj_extarqs):
                self.assertEqual(obj_extarq.arq.uuid, db_extarqs[i]['uuid'])

    @mock.patch('openstack.connection.Connection')
    def test_get_bitstream_md_from_bitstream_id(self, mock_conn):
        mock_conn.return_value = type(
            "Connection", (object,),
            {"image": type("image", (object,), {"get": self.images_get})})
        obj_extarq = self.class_fgpa_objects["bitstream_program"]
        md = obj_extarq._get_bitstream_md_from_bitstream_id(self.bitstream_id)
        self.assertDictEqual(self.images_md["/images"][0], md)

    @mock.patch('openstack.connection.Connection')
    def test_get_bitstream_md_from_function_id(self, mock_conn):
        mock_conn.return_value = type(
            "Connection", (object,),
            {"image": type("image", (object,), {"get": self.images_get})})
        obj_extarq = self.class_fgpa_objects["function_program"]
        md = obj_extarq._get_bitstream_md_from_function_id(self.function_id)
        self.assertDictEqual(self.images_md["/images"][0], md)

    @mock.patch('openstack.connection.Connection')
    @mock.patch('cyborg.objects.ExtARQ.update_check_state')
    def test_needs_programming(self, mock_check_state, mock_conn):
        mock_conn.return_value = type(
            "Connection", (object,),
            {"image": type("image", (object,), {"get": self.images_get})})
        dep_uuid = self.deployable_uuids[0]
        fake_dep = fake_deployable.fake_deployable_obj(
            self.context, uuid=dep_uuid)

        # function_id is require
        obj_extarq = self.class_fgpa_objects["function_program"]
        need = obj_extarq._needs_programming(self.context, fake_dep)
        self.assertTrue(need)

        # bitstream_id is require
        obj_extarq = self.class_fgpa_objects["bitstream_program"]
        need = obj_extarq._needs_programming(self.context, fake_dep)
        self.assertTrue(need)

        # Both bitstream_id and function_id are require
        obj_extarq = self.class_fgpa_objects["bad_program"]
        self.assertRaises(
            exception.InvalidParameterValue, obj_extarq._needs_programming,
            self.context, fake_dep)

        # None of bitstream_id or function_id is require
        obj_extarq = self.class_fgpa_objects["no_program"]
        need = obj_extarq._needs_programming(self.context, fake_dep)
        self.assertFalse(need)

    @mock.patch('openstack.connection.Connection')
    @mock.patch('cyborg.objects.ExtARQ.update_check_state')
    def test_get_bitstream_md(self, mock_check_state, mock_conn):
        mock_conn.return_value = type(
            "Connection", (object,),
            {"image": type("image", (object,), {"get": self.images_get})})
        dep_uuid = self.deployable_uuids[0]
        fake_dep = fake_deployable.fake_deployable_obj(
            self.context, uuid=dep_uuid)

        # function_id is require
        obj_extarq = self.class_fgpa_objects["function_program"]
        bs_id = obj_extarq._get_bitstream_id()
        fun_id = obj_extarq._get_function_id()
        md = obj_extarq.get_bitstream_md(
            self.context, fake_dep, fun_id, bs_id)
        self.assertDictEqual(self.images_md["/images"][0], md)

        # bitstream_id is require
        obj_extarq = self.class_fgpa_objects["bitstream_program"]
        bs_id = obj_extarq._get_bitstream_id()
        fun_id = obj_extarq._get_function_id()
        md = obj_extarq.get_bitstream_md(
            self.context, fake_dep, fun_id, bs_id)
        self.assertDictEqual(self.images_md["/images"][0], md)

        # Both bitstream_id and function_id are require
        obj_extarq = self.class_fgpa_objects["bad_program"]
        bs_id = obj_extarq._get_bitstream_id()
        fun_id = obj_extarq._get_function_id()
        self.assertRaises(
            exception.InvalidParameterValue, obj_extarq.get_bitstream_md,
            self.context, fake_dep, fun_id, bs_id)

        # None of bitstream_id or function_id is require
        obj_extarq = self.class_fgpa_objects["no_program"]
        bs_id = obj_extarq._get_bitstream_id()
        fun_id = obj_extarq._get_function_id()
        md = obj_extarq.get_bitstream_md(
            self.context, fake_dep, fun_id, bs_id)
        self.assertIsNone(md)

    @mock.patch('openstack.connection.Connection')
    @mock.patch('cyborg.objects.ExtARQ.update_check_state')
    def test_need_extra_bind_job(self, mock_check_state, mock_conn):
        mock_conn.return_value = type(
            "Connection", (object,),
            {"image": type("image", (object,), {"get": self.images_get})})
        dep_uuid = self.deployable_uuids[0]
        fake_dep = fake_deployable.fake_deployable_obj(
            self.context, uuid=dep_uuid)

        # function_id is require
        obj_extarq = self.class_fgpa_objects["function_program"]
        need = obj_extarq._need_extra_bind_job(self.context, fake_dep)
        self.assertTrue(need)

        # bitstream_id is require
        obj_extarq = self.class_fgpa_objects["bitstream_program"]
        need = obj_extarq._need_extra_bind_job(self.context, fake_dep)
        self.assertTrue(need)

        # Both bitstream_id and function_id are require
        obj_extarq = self.class_fgpa_objects["bad_program"]
        self.assertRaises(
            exception.InvalidParameterValue, obj_extarq._need_extra_bind_job,
            self.context, fake_dep)

        # None of bitstream_id or function_id is require
        obj_extarq = self.class_fgpa_objects["no_program"]
        need = obj_extarq._need_extra_bind_job(self.context, fake_dep)
        self.assertFalse(need)

    @mock.patch('cyborg.agent.rpcapi.AgentAPI.fpga_program')
    @mock.patch('openstack.connection.Connection')
    @mock.patch('cyborg.objects.ExtARQ.update_check_state')
    @mock.patch('cyborg.objects.Deployable.get_cpid_list')
    def test_do_programming(self, mock_cpid_list, mock_check_state, mock_conn,
                            mock_program):
        dep_uuid = self.deployable_uuids[0]
        fake_dep = fake_deployable.fake_deployable_obj(
            self.context, uuid=dep_uuid)

        # function_id is require
        obj_extarq = self.class_fgpa_objects["function_program"]
        obj_extarq.arq.hostname = 'newtestnode1'
        fake_dep.driver_name = "intel_fpga"

        mock_cpid_list.return_value = [self.cpid]
        bs_id = obj_extarq._get_bitstream_id()
        obj_extarq._do_programming(self.context, fake_dep, bs_id)
        mock_program.assert_called_once_with(
            self.context, 'newtestnode1', self.cpid, bs_id, "intel_fpga")

    @mock.patch('cyborg.objects.ExtARQ.update_check_state')
    @mock.patch('cyborg.objects.Deployable.get_cpid_list')
    def test_do_programming_with_not_one_cp(self, mock_cpid_list,
                                            mock_check_state):
        dep_uuid = self.deployable_uuids[0]
        fake_dep = fake_deployable.fake_deployable_obj(
            self.context, uuid=dep_uuid)

        mock_cpid_list.return_value = []
        obj_extarq = self.class_fgpa_objects["function_program"]
        obj_extarq.arq.hostname = 'newtestnode1'
        fake_dep.driver_name = "intel_fpga"
        bs_id = obj_extarq._get_bitstream_id()
        self.assertRaises(exception.ExpectedOneObject,
                          obj_extarq._do_programming,
                          self.context,
                          fake_dep,
                          bs_id)

    @mock.patch('cyborg.common.placement_client.PlacementClient.'
                '__init__')
    @mock.patch('cyborg.common.placement_client.PlacementClient.'
                'add_traits_to_rp')
    @mock.patch('cyborg.common.placement_client.PlacementClient.'
                'delete_traits_with_prefixes')
    def test_update_placement(
        self, mock_delete_traits, mock_add_traits, mock_placement_init):
        mock_placement_init.return_value = None
        dep_uuid = self.deployable_uuids[0]
        fake_dep = fake_deployable.fake_deployable_obj(
            self.context, uuid=dep_uuid)

        # function_id is require
        obj_extarq = self.class_fgpa_objects["function_program"]
        obj_extarq.arq.hostname = 'newtestnode1'
        # fake_dep.driver_name = "intel_fpga"
        fun_id = obj_extarq._get_function_id()
        rp_uuid = obj_extarq.arq.device_rp_uuid
        obj_extarq._update_placement(
            self.context, fun_id, fake_dep.driver_name)

        function_id = fun_id.upper().replace('-', '_-')
        vendor = fake_dep.driver_name.upper()
        trait_names = ["_".join((
            constants.FPGA_FUNCTION_ID, vendor, function_id))]
        mock_add_traits.assert_called_once_with(rp_uuid, trait_names)
        mock_delete_traits.assert_called_once_with(
            self.context, rp_uuid, [constants.FPGA_FUNCTION_ID])

    @mock.patch('cyborg.agent.rpcapi.AgentAPI.fpga_program')
    @mock.patch('cyborg.objects.Deployable.get_cpid_list')
    @mock.patch('cyborg.objects.Deployable.update')
    @mock.patch('cyborg.common.placement_client.PlacementClient.'
                '__init__')
    @mock.patch('cyborg.common.placement_client.PlacementClient.'
                'add_traits_to_rp')
    @mock.patch('cyborg.common.placement_client.PlacementClient.'
                'delete_traits_with_prefixes')
    @mock.patch('openstack.connection.Connection')
    @mock.patch('cyborg.objects.ExtARQ.update_check_state')
    @mock.patch('cyborg.objects.ExtARQ.bind')
    def test_bind(
        self, mock_bind, mock_check_state, mock_conn, mock_delete_traits,
        mock_add_traits, mock_placement_init, mock_dp_update,
        mock_cpid_list, mock_program):

        mock_placement_init.return_value = None
        mock_conn.return_value = type(
            "Connection", (object,),
            {"image": type("image", (object,), {"get": self.images_get})})

        dep_uuid = self.deployable_uuids[0]
        fake_dep = fake_deployable.fake_deployable_obj(
            self.context, uuid=dep_uuid)

        mock_cpid_list.return_value = [self.cpid]

        # None of bitstream_id or function_id is require
        obj_extarq = self.class_fgpa_objects["no_program"]
        obj_extarq.bind(self.context, fake_dep)
        self.assertFalse(mock_program.called)
        self.assertFalse(mock_placement_init.called)
        self.assertFalse(mock_dp_update.called)
        mock_bind.assert_called_once_with(self.context, fake_dep)

        self.cpid["cpid_info"] = json.dumps(self.bdf).encode('utf-8')
        # function_id is require
        obj_extarq = self.class_fgpa_objects["function_program"]
        obj_extarq.bind(self.context, fake_dep)
        mock_bind.assert_called_with(self.context, fake_dep)
        self.assertEqual(mock_bind.call_count, 2)

        self.cpid["cpid_info"] = json.dumps(self.bdf).encode('utf-8')
        # bitstream_id is require
        obj_extarq = self.class_fgpa_objects["bitstream_program"]
        obj_extarq.bind(self.context, fake_dep)
        mock_bind.assert_called_with(self.context, fake_dep)
        self.assertEqual(mock_bind.call_count, 3)
