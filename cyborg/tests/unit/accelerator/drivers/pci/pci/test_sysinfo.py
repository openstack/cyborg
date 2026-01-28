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

from unittest import mock

import cyborg
from cyborg.accelerator.drivers.pci.pci.driver import PCIDriver
from cyborg.accelerator.drivers.pci.pci import sysinfo
from cyborg.common import constants
from cyborg.tests import base

CONF = cyborg.conf.CONF

NVIDIA_PCI_LINE = (
    "0000:3b:00.0 3D controller [0302]: "
    "NVIDIA Corporation Device [10de:1eb8] (rev a1)")
INTEL_PCI_LINE = (
    "0000:00:00.0 Host bridge [0600]: "
    "Intel Corporation Device [8086:2020] (rev 07)")
UNKNOWN_VENDOR_LINE = (
    "0000:05:00.0 Network controller [0280]: "
    "Acme Corp Device [dead:beef] (rev 01)")
MALFORMED_LINE = "garbage data that does not match"

_MOCK_GET_PCI = (
    'cyborg.accelerator.drivers.pci.utils.get_pci_devices')


class TestSysinfo(base.DietTestCase):
    """Unit tests for sysinfo module helpers."""

    def _make_pci_dict(self, vendor_id='10de',
                       product_id='1eb8',
                       devices='0000:3b:00.0',
                       hostname='testhost'):
        return {
            'vendor_id': vendor_id,
            'product_id': product_id,
            'devices': devices,
            'hostname': hostname,
            'rc': constants.RESOURCES['PCI'],
            'traits': ['CUSTOM_PCI_NVIDIA',
                       'CUSTOM_PCI_PRODUCT_ID_1EB8'],
        }

    def test_match_standard_device(self):
        m = sysinfo.LSPCI_PATTERN.match(NVIDIA_PCI_LINE)
        self.assertIsNotNone(m)
        self.assertEqual('0000:3b:00.0', m.group('devices'))
        self.assertEqual('10de', m.group('vendor_id'))
        self.assertEqual('1eb8', m.group('product_id'))

    def test_match_uppercase_hex(self):
        line = (
            "0000:3B:00.0 3D controller [0302]: "
            "Device [10DE:1EB8] (rev a1)")
        m = sysinfo.LSPCI_PATTERN.match(line)
        self.assertIsNotNone(m)
        self.assertEqual('10DE', m.group('vendor_id'))
        self.assertEqual('1EB8', m.group('product_id'))

    def test_match_without_revision(self):
        line = (
            "0000:3b:00.0 3D controller [0302]: "
            "NVIDIA Corporation Device [10de:1eb8]")
        m = sysinfo.LSPCI_PATTERN.match(line)
        self.assertIsNotNone(m)
        self.assertEqual('10de', m.group('vendor_id'))

    def test_no_match_malformed(self):
        m = sysinfo.LSPCI_PATTERN.match(MALFORMED_LINE)
        self.assertIsNone(m)

    def test_no_match_empty(self):
        m = sysinfo.LSPCI_PATTERN.match('')
        self.assertIsNone(m)

    def test_known_vendor(self):
        result = sysinfo._get_traits('10de', '1eb8')
        traits = result['traits']
        self.assertIn('CUSTOM_PCI_NVIDIA', traits)
        self.assertIn('CUSTOM_PCI_PRODUCT_ID_1EB8', traits)

    def test_unknown_vendor_skips_vendor_trait(self):
        result = sysinfo._get_traits('dead', 'beef')
        traits = result['traits']
        self.assertIn('CUSTOM_PCI_PRODUCT_ID_BEEF', traits)
        # No vendor trait should be present
        vendor_traits = [
            t for t in traits if not t.startswith(
                'CUSTOM_PCI_PRODUCT_ID')]
        self.assertEqual([], vendor_traits)

    def test_product_id_uppercased(self):
        result = sysinfo._get_traits('dead', 'abcd')
        traits = result['traits']
        self.assertIn('CUSTOM_PCI_PRODUCT_ID_ABCD', traits)

    def test_known_vendor_driver_name(self):
        pci = self._make_pci_dict(vendor_id='10de')
        dep_list, num = sysinfo._generate_dep_list(pci)
        self.assertEqual(1, len(dep_list))
        self.assertEqual('NVIDIA', dep_list[0].driver_name)

    def test_unknown_vendor_fallback(self):
        pci = self._make_pci_dict(vendor_id='dead')
        dep_list, num = sysinfo._generate_dep_list(pci)
        self.assertEqual('DEAD', dep_list[0].driver_name)

    def test_deployable_name_format(self):
        pci = self._make_pci_dict(
            hostname='myhost', devices='0000:3b:00.0')
        dep_list, _num = sysinfo._generate_dep_list(pci)
        self.assertEqual(
            'myhost_0000:3b:00.0', dep_list[0].name)


class TestDiscoverPcis(base.TestCase):
    """Integration tests for _discover_pcis() / discover()."""

    def setUp(self):
        super(TestDiscoverPcis, self).setUp()
        self.set_defaults(host='fake-pci-host', debug=True)

    def _set_whitelist(self, specs):
        """Set pci passthrough_whitelist from a list of JSON strings.

        :param specs: list of JSON-encoded whitelist entries,
            e.g. ['{"vendor_id":"10de"}']
        """
        self.config(
            passthrough_whitelist=specs,
            group='pci')

    @mock.patch(_MOCK_GET_PCI, autospec=True)
    def test_discover_single_known_device(self, mock_pci):
        mock_pci.return_value = (NVIDIA_PCI_LINE, '')
        self._set_whitelist(['{"vendor_id":"10de"}'])
        devs = sysinfo._discover_pcis()
        self.assertEqual(1, len(devs))
        dev = devs[0]
        dev_dict = dev.as_dict()
        self.assertEqual('10de', dev_dict['vendor'])
        self.assertEqual('1eb8', dev_dict['model'])
        self.assertEqual(constants.DEVICE_GPU, dev_dict['type'])
        # Check controlpath_id
        cpid = dev_dict['controlpath_id']
        self.assertEqual('PCI', cpid['cpid_type'])
        # Check deployable
        dep = dev_dict['deployable_list'][0]
        dep_dict = dep.as_dict()
        self.assertEqual(
            'fake-pci-host_0000:3b:00.0', dep_dict['name'])
        self.assertEqual('NVIDIA', dep_dict['driver_name'])
        self.assertEqual(1, dep_dict['num_accelerators'])
        # Check attach handle
        ah = dep_dict['attach_handle_list'][0].as_dict()
        self.assertEqual(constants.AH_TYPE_PCI,
                         ah['attach_type'])
        self.assertFalse(ah['in_use'])
        # Check attributes contain traits
        attrs = dep_dict['attribute_list']
        attr_data = [a.as_dict() for a in attrs]
        attr_keys = [a['key'] for a in attr_data]
        self.assertIn('rc', attr_keys)
        trait_vals = [a['value'] for a in attr_data
                      if a['key'].startswith('trait')]
        self.assertIn('CUSTOM_PCI_NVIDIA', trait_vals)
        self.assertIn('CUSTOM_PCI_PRODUCT_ID_1EB8', trait_vals)

    @mock.patch(_MOCK_GET_PCI, autospec=True)
    def test_discover_unknown_vendor_device(self, mock_pci):
        mock_pci.return_value = (UNKNOWN_VENDOR_LINE, '')
        self._set_whitelist(['{"vendor_id":"dead"}'])
        devs = sysinfo._discover_pcis()
        self.assertEqual(1, len(devs))
        dev_dict = devs[0].as_dict()
        self.assertEqual('dead', dev_dict['vendor'])
        dep_dict = dev_dict['deployable_list'][0].as_dict()
        self.assertEqual('DEAD', dep_dict['driver_name'])
        # No vendor trait, only product trait
        attrs = dep_dict['attribute_list']
        attr_data = [a.as_dict() for a in attrs]
        trait_vals = [a['value'] for a in attr_data
                      if a['key'].startswith('trait')]
        self.assertIn('CUSTOM_PCI_PRODUCT_ID_BEEF', trait_vals)
        # Ensure no vendor-specific trait is present
        vendor_traits = [
            t for t in trait_vals
            if not t.startswith('CUSTOM_PCI_PRODUCT_ID')]
        self.assertEqual([], vendor_traits)

    @mock.patch(_MOCK_GET_PCI, autospec=True)
    def test_discover_multiple_devices_filtered(self, mock_pci):
        stdout = '\n'.join([
            NVIDIA_PCI_LINE, INTEL_PCI_LINE, UNKNOWN_VENDOR_LINE])
        mock_pci.return_value = (stdout, '')
        self._set_whitelist(['{"vendor_id":"10de"}'])
        devs = sysinfo._discover_pcis()
        self.assertEqual(1, len(devs))
        self.assertEqual(
            '10de', devs[0].as_dict()['vendor'])

    @mock.patch(_MOCK_GET_PCI, autospec=True)
    def test_discover_empty_output(self, mock_pci):
        mock_pci.return_value = ('', '')
        self._set_whitelist(['{"vendor_id":"10de"}'])
        devs = sysinfo._discover_pcis()
        self.assertEqual([], devs)

    @mock.patch(_MOCK_GET_PCI, autospec=True)
    def test_discover_no_whitelist(self, mock_pci):
        mock_pci.return_value = (NVIDIA_PCI_LINE, '')
        # passthrough_whitelist defaults to []
        devs = sysinfo._discover_pcis()
        self.assertEqual([], devs)

    @mock.patch(_MOCK_GET_PCI, autospec=True)
    def test_discover_malformed_lines_skipped(self, mock_pci):
        stdout = '\n'.join([
            MALFORMED_LINE, '', NVIDIA_PCI_LINE, MALFORMED_LINE])
        mock_pci.return_value = (stdout, '')
        self._set_whitelist(['{"vendor_id":"10de"}'])
        devs = sysinfo._discover_pcis()
        self.assertEqual(1, len(devs))
        self.assertEqual(
            '10de', devs[0].as_dict()['vendor'])

    @mock.patch(_MOCK_GET_PCI, autospec=True)
    def test_discover_device_not_in_whitelist(self, mock_pci):
        mock_pci.return_value = (NVIDIA_PCI_LINE, '')
        self._set_whitelist(['{"vendor_id":"8086"}'])
        devs = sysinfo._discover_pcis()
        self.assertEqual([], devs)

    @mock.patch(_MOCK_GET_PCI, autospec=True)
    def test_discover_via_driver_class(self, mock_pci):
        mock_pci.return_value = (NVIDIA_PCI_LINE, '')
        self._set_whitelist(['{"vendor_id":"10de"}'])
        driver = PCIDriver()
        devs = driver.discover()
        self.assertEqual(1, len(devs))
        self.assertEqual(
            '10de', devs[0].as_dict()['vendor'])
