# Copyright 2017 Huawei Technologies Co.,LTD.
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

from cyborg.accelerator.drivers.spdk.nvmf.nvmf import NVMFDRIVER
from cyborg.accelerator.drivers.spdk.util import common_fun
from cyborg.accelerator.drivers.spdk.util.pyspdk.nvmf_client import NvmfTgt
from cyborg.tests import base


class TestNVMFDRIVER(base.TestCase):

    def setUp(self,):
        super(TestNVMFDRIVER, self).setUp()
        self.nvmf_driver = NVMFDRIVER()

    def tearDown(self):
        super(TestNVMFDRIVER, self).tearDown()
        self.vhost_driver = None

    @mock.patch.object(NVMFDRIVER, 'get_one_accelerator')
    def test_discover_accelerator(self, mock_get_one_accelerator):
        expect_accelerator = {
            'server': 'nvmf',
            'bdevs': [{"num_blocks": 131072,
                       "name": "nvme1",
                       "block_size": 512
                       }],
            'subsystems': [{"core": 0,
                            "nqn": "nqn.2018-01.org.nvmexpress.discovery",
                            "hosts": []
                            }]
        }
        alive = mock.Mock(return_value=False)
        self.nvmf_driver.py.is_alive = alive
        check_error = mock.Mock(return_value=False)
        common_fun.check_for_setup_error = check_error
        self.assertFalse(
            mock_get_one_accelerator.called,
            "Failed to discover_accelerator if py not alive."
        )
        alive = mock.Mock(return_value=True)
        self.nvmf_driver.py.is_alive = alive
        check_error = mock.Mock(return_value=True)
        common_fun.check_for_setup_error = check_error
        acce_client = NvmfTgt(self.nvmf_driver.py)
        bdevs_fake = [{"num_blocks": 131072,
                       "name": "nvme1",
                       "block_size": 512
                       }]
        bdev_list = mock.Mock(return_value=bdevs_fake)
        acce_client.get_bdevs = bdev_list
        subsystems_fake = [{"core": 0,
                            "nqn": "nqn.2018-01.org.nvmexpress.discovery",
                            "hosts": []
                            }]
        subsystem_list = mock.Mock(return_value=subsystems_fake)
        acce_client.get_nvmf_subsystems = subsystem_list
        accelerator_fake = {
            'server': self.nvmf_driver.SERVER,
            'bdevs': acce_client.get_bdevs(),
            'subsystems': acce_client.get_nvmf_subsystems()
        }
        success_send = mock.Mock(return_value=accelerator_fake)
        self.nvmf_driver.get_one_accelerator = success_send
        accelerator = self.nvmf_driver.discover_accelerator()
        self.assertEqual(accelerator, expect_accelerator)

    def test_accelerator_list(self):
        expect_accelerators = [{
            'server': 'nvmf',
            'bdevs': [{"num_blocks": 131072,
                       "name": "nvme1",
                       "block_size": 512
                       }],
            'subsystems':
                [{"core": 0,
                  "nqn": "nqn.2018-01.org.nvmexpress.discovery",
                  "hosts": []
                  }]
        },
            {
                'server': 'nvnf_tgt',
                'bdevs': [{"num_blocks": 131072,
                           "name": "nvme1",
                           "block_size": 512
                           }],
                'subsystems':
                    [{"core": 0,
                      "nqn": "nqn.2018-01.org.nvmexpress.discovery",
                      "hosts": []
                      }]
            }
        ]
        success_send = mock.Mock(return_value=expect_accelerators)
        self.nvmf_driver.get_all_accelerators = success_send
        self.assertEqual(self.nvmf_driver.accelerator_list(),
                         expect_accelerators)

    def test_install_accelerator(self):
        pass

    def test_uninstall_accelerator(self):
        pass

    def test_update(self):
        pass

    def test_attach_instance(self):
        pass

    def test_detach_instance(self):
        pass

    def test_delete_subsystem(self):
        pass

    def test_construct_subsystem(self):
        pass
