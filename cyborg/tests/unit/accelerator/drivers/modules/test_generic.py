# Copyright 2017 Lenovo Inc.
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

"""Base classes for Generic Driver tests."""

import mock

from cyborg.accelerator.drivers.generic_driver import GenericDriver as generic
from cyborg.conductor.rpcapi import ConductorAPI as conductor_api

FAKE_CONTEXT = mock.MagicMock()


class GenericDriverTest():
    """Class for testing of generic driver
    """

    def setUp(self):
        super(GenericDriverTest, self).setUp()

    @mock.patch.object(conductor_api, 'accelerator_create')
    def test_create_accelerator(self, mock_acc_create):
        mock_acc_create.return_value = self.acc
        generic.create_accelerator(context=FAKE_CONTEXT)

        mock_acc_create.assert_called()

    @mock.patch.object(conductor_api, 'accelerator_list_one')
    def test_get_accelerator(self, mock_acc_get):
        mock_acc_get.return_value = self.acc
        generic.get_accelerator(context=FAKE_CONTEXT)

        mock_acc_get.assert_called()

    @mock.patch.object(conductor_api, 'accelerator_list_all')
    def test_list_accelerators(self, mock_acc_list):
        mock_acc_list.return_value = self.acc
        generic.list_accelerators(context=FAKE_CONTEXT)

        mock_acc_list.assert_called()

    @mock.patch.object(conductor_api, 'accelerator_update')
    def test_update_accelerator(self, mock_acc_update):
        mock_acc_update.return_value = self.acc
        generic.update_accelerator(context=FAKE_CONTEXT)

        mock_acc_update.assert_called()

    @mock.patch.object(conductor_api, 'accelerator_delete')
    def test_delete_accelerator(self, mock_acc_delete):
        mock_acc_delete.return_value = self.acc
        generic.delete_accelerator(context=FAKE_CONTEXT)

        mock_acc_delete.assert_called()
