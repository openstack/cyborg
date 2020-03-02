# Copyright 2019 Intel, Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License"); you may
# not use this file except in compliance with the License. You may obtain
# a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
# WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
# License for the specific language governing permissions and limitations
# under the License.


import copy

from oslo_serialization import jsonutils

from cyborg.accelerator.drivers.fake import FakeDriver
from cyborg.tests import base


class TestFakeDriver(base.TestCase):

    def setUp(self):
        super(TestFakeDriver, self).setUp()

    def tearDown(self):
        super(TestFakeDriver, self).tearDown()

    def _get_pci_bdfs(self, num_pci_bdfs):
        """Return a list of PCI BDFs, first for cpid, rest
        for attach handles.
        """
        pci_bdf_template = {
            'domain': '0000', 'bus': '0c', 'device': '00', }
        pci_bdf_list = []
        for fn in range(num_pci_bdfs):
            pci_bdf = copy.deepcopy(pci_bdf_template)
            pci_bdf['function'] = str(fn)
            pci_bdf_list.append(jsonutils.dumps(pci_bdf))
        return pci_bdf_list

    def _get_cpid_attach_handles(self):
        num_accelerators = 2  # keep it simple
        pci_bdf_list = self._get_pci_bdfs(num_accelerators + 1)
        cpid = {
            'cpid_type': 'PCI',
            'cpid_info': pci_bdf_list[0],
        }

        ah_template = {
            'attach_type': 'TEST_PCI',
            'in_use': False,
        }
        ah1 = copy.deepcopy(ah_template)
        ah1['attach_info'] = pci_bdf_list[1]
        ah2 = copy.deepcopy(ah_template)
        ah2['attach_info'] = pci_bdf_list[2]
        return cpid, [ah1, ah2]

    def _validate_attach_handle_list(self, ah_list):
        self.assertTrue(all(
            ah['attach_type'] == 'TEST_PCI' for ah in ah_list))
        self.assertTrue(all(ah['in_use'] is False for ah in ah_list))

        ah_bdfs = [jsonutils.loads(ah['attach_info']) for ah in ah_list]
        bdf_list = [(bdf['domain'], bdf['bus'],
                     bdf['device'], bdf['function']) for bdf in ah_bdfs]
        domains = [bdf[0] for bdf in bdf_list]
        buses = [bdf[1] for bdf in bdf_list]
        pci_devs = [bdf[2] for bdf in bdf_list]
        pci_fns = [bdf[3] for bdf in bdf_list]

        # Ensure BDFs are unique
        self.assertEqual(len(set(bdf_list)), len(bdf_list),
                         "BDFs must be unique.")
        self.assertEqual(
            len(set(domains)), 1,
            "PCI domains are expected to be same for #accelerators < 256.")
        self.assertEqual(
            len(set(buses)), 1,
            "PCI bus #s are expected to be same for #accelerators < 256.")

        self.assertTrue(
            all([0 <= int(pci_dev) < 32 for pci_dev in pci_devs]),
            "PCI device numbers must be between 0 and 31."
            )
        self.assertTrue(
            all([0 <= int(pci_fn) < 8 for pci_fn in pci_fns]),
            "PCI function numbers must be between 0 and 7."
            )

    def test_discover(self):
        cpid, ah_list = self._get_cpid_attach_handles()
        # This is an example device from the fake driver.
        # We set num_accelerators = 2 for simplicity.
        expected = {'vendor': '0xABCD',
                    'type': 'FPGA',
                    'model': 'miss model info',
                    'deployable_list':
                        [{'num_accelerators': 2,
                          'name': 'FakeDevice',
                          'attach_handle_list': ah_list,
                          },
                         ],
                    'controlpath_id': cpid,
                    }

        fake_drv = FakeDriver()
        devices = fake_drv.discover()
        self.assertEqual(1, len(devices))
        for field in ['vendor', 'type', 'model']:
            self.assertEqual(devices[0][field], expected[field])

        expected_cpid = expected['controlpath_id']
        cpid = devices[0]['controlpath_id']
        self.assertEqual(cpid['cpid_type'], expected_cpid['cpid_type'])
        self.assertEqual(
            jsonutils.loads(cpid['cpid_info']),
            jsonutils.loads(expected_cpid['cpid_info']))

        deployables = devices[0].deployable_list
        self.assertEqual(1, len(deployables))
        self.assertEqual('fake-mini_FakeDevice', deployables[0]['name'])
        self.assertGreater(deployables[0]['num_accelerators'], 1)

        # Since num_accelerators can change, we don't test for its value.
        ah_list = deployables[0]['attach_handle_list']
        self.assertEqual(deployables[0]['num_accelerators'], len(ah_list))
        self._validate_attach_handle_list(ah_list)

    def test_generate_attach_handles(self):
        fake_drv = FakeDriver()
        pci_addr = '{"domain":"0000","bus":"0c","device":"00","function":"0"}'
        pci = {'slot': pci_addr}
        num_accelerators = 255  # Largest value that will fit within a bus
        ah_list = fake_drv._generate_attach_handles(pci, num_accelerators)

        self.assertEqual(num_accelerators, len(ah_list))
        self._validate_attach_handle_list(ah_list)
