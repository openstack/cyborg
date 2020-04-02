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

from cyborg.accelerator.drivers.spdk.util import common_fun
from cyborg.accelerator.drivers.spdk.util.pyspdk.vhost_client import VhostTgt
from cyborg.accelerator.drivers.spdk.vhost.vhost import VHOSTDRIVER
from cyborg.tests import base


class TestVHOSTDRIVER(base.TestCase):

    def setUp(self):
        super(TestVHOSTDRIVER, self).setUp()
        self.vhost_driver = VHOSTDRIVER()

    def tearDown(self):
        super(TestVHOSTDRIVER, self).tearDown()
        self.vhost_driver = None

    @mock.patch.object(VHOSTDRIVER, 'get_one_accelerator')
    def test_discover_accelerator(self, mock_get_one_accelerator):
        expect_accelerator = {
            'server': 'vhost',
            'bdevs': [{"num_blocks": 131072,
                       "name": "nvme1",
                       "block_size": 512
                       }],
            'scsi_devices': [],
            'luns': [{"claimed": True,
                      "name": "Malloc0"}],
            'interfaces': [{"core": 0,
                            "nqn": "nqn.2018-01.org.nvmexpress.discovery",
                            "hosts": []
                            }]
        }
        alive = mock.Mock(return_value=True)
        self.vhost_driver.py.is_alive = alive
        check_error = mock.Mock(return_value=True)
        common_fun.check_for_setup_error = check_error
        self.assertFalse(
            mock_get_one_accelerator.called,
            "Failed to discover_accelerator if py not alive."
        )
        acce_client = VhostTgt(self.vhost_driver.py)
        bdevs_fake = [{"num_blocks": 131072,
                       "name": "nvme1",
                       "block_size": 512
                       }]
        bdev_list = mock.Mock(return_value=bdevs_fake)
        acce_client.get_bdevs = bdev_list
        scsi_devices_fake = []
        scsi_device_list = mock.Mock(return_value=scsi_devices_fake)
        acce_client.get_scsi_devices = scsi_device_list
        luns_fake = [{"claimed": True,
                      "name": "Malloc0"}]
        lun_list = mock.Mock(return_value=luns_fake)
        acce_client.get_luns = lun_list
        interfaces_fake = \
            [{"core": 0,
              "nqn": "nqn.2018-01.org.nvmexpress.discovery",
              "hosts": []
              }]
        interface_list = mock.Mock(return_value=interfaces_fake)
        acce_client.get_interfaces = interface_list
        accelerator_fake = {
            'server': self.vhost_driver.SERVER,
            'bdevs': acce_client.get_bdevs(),
            'scsi_devices': acce_client.get_scsi_devices(),
            'luns': acce_client.get_luns(),
            'interfaces': acce_client.get_interfaces()
        }
        success_send = mock.Mock(return_value=accelerator_fake)
        self.vhost_driver.get_one_accelerator = success_send
        accelerator = self.vhost_driver.discover_accelerator()
        self.assertEqual(accelerator, expect_accelerator)

    def test_accelerator_list(self):
        expect_accelerators = [{
            'server': 'vhost',
            'bdevs': [{"num_blocks": 131072,
                       "name": "nvme1",
                       "block_size": 512
                       }],
            'scsi_devices': [],
            'luns': [{"claimed": True,
                      "name": "Malloc0"}],
            'interfaces': [{"core": 0,
                            "nqn": "nqn.2018-01.org.nvmexpress.discovery",
                            "hosts": []
                            }]
        },
            {
                'server': 'vhost_tgt',
                'bdevs': [{"num_blocks": 131072,
                           "name": "nvme1",
                           "block_size": 512
                           }],
                'scsi_devices': [],
                'luns': [{"claimed": True,
                          "name": "Malloc0"}],
                'interfaces': [{"core": 0,
                                "nqn": "nqn.2018-01.org.nvmexpress.discovery",
                                "hosts": []
                                }]
            }
        ]
        success_send = mock.Mock(return_value=expect_accelerators)
        self.vhost_driver.get_all_accelerators = success_send
        self.assertEqual(self.vhost_driver.accelerator_list(),
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

    def test_delete_ip_address(self):
        pass

    def test_add_ip_address(self):
        pass
