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

"""Unit tests for MdevDeviceSpec."""

from cyborg.accelerator.drivers.mdev import devspec
from cyborg.common import exception
from cyborg.tests import base


class TestMdevDeviceSpec(base.TestCase):
    """Tests for MdevDeviceSpec construction and validation."""

    def test_basic_construction(self):
        """Spec created from valid fields."""
        spec = devspec.MdevDeviceSpec(
            address='0000:06:00.0',
            mdev_type='nvidia-319',
        )
        self.assertEqual('0000:06:00.0', spec.address)
        self.assertEqual('nvidia-319', spec.mdev_type)

    def test_max_instances_stored(self):
        """max_instances is stored as given."""
        spec = devspec.MdevDeviceSpec(
            address='0000:06:00.0',
            mdev_type='nvidia-319',
            max_instances=4,
        )
        self.assertEqual(4, spec.max_instances)

    def test_zero_max_instances(self):
        """Zero max_instances is stored as zero."""
        spec = devspec.MdevDeviceSpec(
            address='0000:06:00.0',
            mdev_type='nvidia-319',
            max_instances=0,
        )
        self.assertEqual(0, spec.max_instances)

    def test_max_instances_absent(self):
        """Missing max_instances defaults to None."""
        spec = devspec.MdevDeviceSpec(
            address='0000:06:00.0',
            mdev_type='nvidia-319',
        )
        self.assertIsNone(spec.max_instances)

    def test_resource_class_stored(self):
        """Custom resource_class is stored as-is."""
        spec = devspec.MdevDeviceSpec(
            address='0000:06:00.0',
            mdev_type='nvidia-319',
            resource_class='CUSTOM_MY_VGPU',
        )
        self.assertEqual('CUSTOM_MY_VGPU', spec.resource_class)

    def test_resource_class_normalized(self):
        """resource_class without the CUSTOM_ prefix is normalized."""
        spec = devspec.MdevDeviceSpec(
            address='0000:06:00.0',
            mdev_type='nvidia-319',
            resource_class='my-vgpu',
        )
        self.assertEqual('CUSTOM_MY_VGPU', spec.resource_class)

    def test_resource_class_absent(self):
        """Missing resource_class defaults to None."""
        spec = devspec.MdevDeviceSpec(
            address='0000:06:00.0',
            mdev_type='nvidia-319',
        )
        self.assertIsNone(spec.resource_class)

    def test_traits_stored(self):
        """Already-normalized traits are kept unchanged."""
        spec = devspec.MdevDeviceSpec(
            address='0000:06:00.0',
            mdev_type='nvidia-319',
            traits=['CUSTOM_FAST', 'CUSTOM_GPU'],
        )
        self.assertEqual(
            ['CUSTOM_FAST', 'CUSTOM_GPU'],
            spec.traits,
        )

    def test_traits_normalized(self):
        """Traits without the CUSTOM_ prefix are normalized."""
        spec = devspec.MdevDeviceSpec(
            address='0000:06:00.0',
            mdev_type='nvidia-319',
            traits=['my-fast-trait'],
        )
        self.assertEqual(['CUSTOM_MY_FAST_TRAIT'], spec.traits)

    def test_traits_absent(self):
        """Missing traits defaults to empty list."""
        spec = devspec.MdevDeviceSpec(
            address='0000:06:00.0',
            mdev_type='nvidia-319',
        )
        self.assertEqual([], spec.traits)


class TestMdevDeviceSpecMatch(base.TestCase):
    """Tests for devspec.MdevDeviceSpec.match()."""

    def test_exact_match(self):
        """Exact address and type matches."""
        spec = devspec.MdevDeviceSpec(
            address='0000:06:00.0',
            mdev_type='nvidia-319',
        )
        self.assertTrue(
            spec.match('0000:06:00.0', 'nvidia-319'),
        )

    def test_exact_no_match_address(self):
        """Different address does not match."""
        spec = devspec.MdevDeviceSpec(
            address='0000:06:00.0',
            mdev_type='nvidia-319',
        )
        self.assertFalse(
            spec.match('0000:07:00.0', 'nvidia-319'),
        )

    def test_exact_no_match_type(self):
        """Different type does not match."""
        spec = devspec.MdevDeviceSpec(
            address='0000:06:00.0',
            mdev_type='nvidia-319',
        )
        self.assertFalse(
            spec.match('0000:06:00.0', 'nvidia-320'),
        )

    def test_wildcard_address(self):
        """Wildcard address matches any address."""
        spec = devspec.MdevDeviceSpec(
            address='*',
            mdev_type='nvidia-319',
        )
        self.assertTrue(
            spec.match('0000:06:00.0', 'nvidia-319'),
        )
        self.assertTrue(
            spec.match('0000:07:00.0', 'nvidia-319'),
        )

    def test_wildcard_address_wrong_type(self):
        """Wildcard address with wrong type does not match."""
        spec = devspec.MdevDeviceSpec(
            address='*',
            mdev_type='nvidia-319',
        )
        self.assertFalse(
            spec.match('0000:06:00.0', 'nvidia-320'),
        )


class TestMdevDeviceSpecFromConfig(base.TestCase):
    """Tests for devspec.MdevDeviceSpec.from_config()."""

    def test_valid_json(self):
        """Valid JSON string is parsed."""
        spec = devspec.MdevDeviceSpec.from_config(
            '{"address": "0000:06:00.0", "mdev_type": "nvidia-319"}'
        )
        self.assertEqual('0000:06:00.0', spec.address)
        self.assertEqual('nvidia-319', spec.mdev_type)

    def test_invalid_json_raises(self):
        """Invalid JSON raises exception."""
        self.assertRaises(
            exception.InvalidMdevDevSpecConfig,
            devspec.MdevDeviceSpec.from_config,
            'not-valid-json',
        )

    def test_non_object_json_raises(self):
        """JSON that is not an object fails schema validation."""
        self.assertRaises(
            exception.InvalidMdevDevSpecConfig,
            devspec.MdevDeviceSpec.from_config,
            '"not-a-dict"',
        )

    def test_array_json_raises(self):
        """A JSON array fails schema validation."""
        self.assertRaises(
            exception.InvalidMdevDevSpecConfig,
            devspec.MdevDeviceSpec.from_config,
            '[{"address": "0000:06:00.0", "mdev_type": "nvidia-319"}]',
        )

    def test_missing_address_raises(self):
        """Missing address fails schema validation."""
        self.assertRaises(
            exception.InvalidMdevDevSpecConfig,
            devspec.MdevDeviceSpec.from_config,
            '{"mdev_type": "nvidia-319"}',
        )

    def test_missing_mdev_type_raises(self):
        """Missing mdev_type fails schema validation."""
        self.assertRaises(
            exception.InvalidMdevDevSpecConfig,
            devspec.MdevDeviceSpec.from_config,
            '{"address": "0000:06:00.0"}',
        )

    def test_empty_address_raises(self):
        """Empty address string fails schema validation."""
        self.assertRaises(
            exception.InvalidMdevDevSpecConfig,
            devspec.MdevDeviceSpec.from_config,
            '{"address": "", "mdev_type": "nvidia-319"}',
        )

    def test_empty_mdev_type_raises(self):
        """Empty mdev_type string fails schema validation."""
        self.assertRaises(
            exception.InvalidMdevDevSpecConfig,
            devspec.MdevDeviceSpec.from_config,
            '{"address": "0000:06:00.0", "mdev_type": ""}',
        )

    def test_wildcard_mdev_type_raises(self):
        """Wildcard mdev_type fails schema validation."""
        self.assertRaises(
            exception.InvalidMdevDevSpecConfig,
            devspec.MdevDeviceSpec.from_config,
            '{"address": "0000:06:00.0", "mdev_type": "*"}',
        )

    def test_additional_properties_raises(self):
        """Unknown properties fail schema validation."""
        self.assertRaises(
            exception.InvalidMdevDevSpecConfig,
            devspec.MdevDeviceSpec.from_config,
            '{"address": "0000:06:00.0", "mdev_type": "nvidia-319",'
            ' "bogus": 1}',
        )

    def test_max_instances_parsed(self):
        """Integer max_instances is stored."""
        spec = devspec.MdevDeviceSpec.from_config(
            '{"address": "0000:06:00.0", "mdev_type": "nvidia-319",'
            ' "max_instances": 4}'
        )
        self.assertEqual(4, spec.max_instances)

    def test_string_max_instances_raises(self):
        """String max_instances fails schema validation."""
        self.assertRaises(
            exception.InvalidMdevDevSpecConfig,
            devspec.MdevDeviceSpec.from_config,
            '{"address": "0000:06:00.0", "mdev_type": "nvidia-319",'
            ' "max_instances": "8"}',
        )

    def test_invalid_max_instances_raises(self):
        """Non-numeric max_instances fails schema validation."""
        self.assertRaises(
            exception.InvalidMdevDevSpecConfig,
            devspec.MdevDeviceSpec.from_config,
            '{"address": "0000:06:00.0", "mdev_type": "nvidia-319",'
            ' "max_instances": "abc"}',
        )

    def test_negative_max_instances_raises(self):
        """Negative max_instances fails schema validation."""
        self.assertRaises(
            exception.InvalidMdevDevSpecConfig,
            devspec.MdevDeviceSpec.from_config,
            '{"address": "0000:06:00.0", "mdev_type": "nvidia-319",'
            ' "max_instances": -1}',
        )

    def test_traits_parsed(self):
        """Traits from JSON are normalized and stored."""
        spec = devspec.MdevDeviceSpec.from_config(
            '{"address": "0000:06:00.0", "mdev_type": "nvidia-319",'
            ' "traits": ["my-fast-trait"]}'
        )
        self.assertEqual(['CUSTOM_MY_FAST_TRAIT'], spec.traits)

    def test_resource_class_parsed(self):
        """resource_class from JSON is normalized and stored."""
        spec = devspec.MdevDeviceSpec.from_config(
            '{"address": "0000:06:00.0", "mdev_type": "nvidia-319",'
            ' "resource_class": "my-vgpu"}'
        )
        self.assertEqual('CUSTOM_MY_VGPU', spec.resource_class)

    def test_traits_as_string_raises(self):
        """Traits as a string fails schema validation."""
        self.assertRaises(
            exception.InvalidMdevDevSpecConfig,
            devspec.MdevDeviceSpec.from_config,
            '{"address": "0000:06:00.0", "mdev_type": "nvidia-319",'
            ' "traits": "CUSTOM_FAST"}',
        )

    def test_traits_as_null_raises(self):
        """Traits as null fails schema validation."""
        self.assertRaises(
            exception.InvalidMdevDevSpecConfig,
            devspec.MdevDeviceSpec.from_config,
            '{"address": "0000:06:00.0", "mdev_type": "nvidia-319",'
            ' "traits": null}',
        )


class TestMdevDeviceSpecFromConfigList(base.TestCase):
    """Tests for devspec.MdevDeviceSpec.from_config_list()."""

    def test_empty_list(self):
        """Empty list returns empty."""
        specs = devspec.MdevDeviceSpec.from_config_list([])
        self.assertEqual([], specs)

    def test_single_entry(self):
        """Single entry returns one spec."""
        specs = devspec.MdevDeviceSpec.from_config_list(
            [
                '{"address": "0000:06:00.0", "mdev_type": "nvidia-319"}',
            ]
        )
        self.assertEqual(1, len(specs))
        self.assertEqual('0000:06:00.0', specs[0].address)

    def test_deduplication_first_wins(self):
        """Duplicate key uses first entry and logs a warning."""
        with self.assertLogs(level='WARNING') as cm:
            specs = devspec.MdevDeviceSpec.from_config_list(
                [
                    '{"address": "0000:06:00.0",'
                    ' "mdev_type": "nvidia-319",'
                    ' "max_instances": 2}',
                    '{"address": "0000:06:00.0",'
                    ' "mdev_type": "nvidia-319",'
                    ' "max_instances": 5}',
                ]
            )
        self.assertEqual(1, len(specs))
        self.assertEqual(2, specs[0].max_instances)
        self.assertEqual(
            [
                'WARNING:cyborg.accelerator.drivers.mdev.devspec:'
                'Duplicate mdev device_spec for '
                '(address=0000:06:00.0, mdev_type=nvidia-319), '
                'keeping first entry',
            ],
            cm.output,
        )

    def test_json_list_value_expanded(self):
        """A JSON array value expands into multiple specs."""
        specs = devspec.MdevDeviceSpec.from_config_list(
            [
                '[{"address": "0000:06:00.0", "mdev_type": "nvidia-319"},'
                ' {"address": "0000:07:00.0", "mdev_type": "nvidia-320"}]',
            ]
        )
        self.assertEqual(2, len(specs))
        self.assertEqual(
            [
                ('0000:06:00.0', 'nvidia-319'),
                ('0000:07:00.0', 'nvidia-320'),
            ],
            [(s.address, s.mdev_type) for s in specs],
        )

    def test_mixed_single_and_list_values(self):
        """Single-object and array values can be mixed."""
        specs = devspec.MdevDeviceSpec.from_config_list(
            [
                '{"address": "0000:06:00.0", "mdev_type": "nvidia-319"}',
                '[{"address": "0000:07:00.0", "mdev_type": "nvidia-320"}]',
            ]
        )
        self.assertEqual(2, len(specs))
        self.assertEqual(
            [('0000:06:00.0', 'nvidia-319'), ('0000:07:00.0', 'nvidia-320')],
            [(s.address, s.mdev_type) for s in specs],
        )

    def test_empty_json_list_value(self):
        """An empty array value yields no specs."""
        specs = devspec.MdevDeviceSpec.from_config_list(['[]'])
        self.assertEqual([], specs)

    def test_json_list_invalid_entry_raises(self):
        """An invalid entry inside an array raises."""
        self.assertRaises(
            exception.InvalidMdevDevSpecConfig,
            devspec.MdevDeviceSpec.from_config_list,
            '[{"address": "0000:06:00.0", "mdev_type": "nvidia-319"},'
            ' {"address": "0000:07:00.0"}]',
        )

    def test_json_list_non_object_entry_raises(self):
        """A non-object entry inside an array raises."""
        self.assertRaises(
            exception.InvalidMdevDevSpecConfig,
            devspec.MdevDeviceSpec.from_config_list,
            '["not-an-object"]',
        )

    def test_deduplication_across_values(self):
        """Duplicates across single and array values are deduplicated."""
        with self.assertLogs(level='WARNING') as cm:
            specs = devspec.MdevDeviceSpec.from_config_list(
                [
                    '{"address": "0000:06:00.0", "mdev_type": "nvidia-319",'
                    ' "max_instances": 2}',
                    '[{"address": "0000:06:00.0", "mdev_type": "nvidia-319",'
                    ' "max_instances": 5}]',
                ]
            )
        self.assertEqual(1, len(specs))
        self.assertEqual(2, specs[0].max_instances)
        self.assertEqual(
            [
                'WARNING:cyborg.accelerator.drivers.mdev.devspec:'
                'Duplicate mdev device_spec for '
                '(address=0000:06:00.0, mdev_type=nvidia-319), '
                'keeping first entry',
            ],
            cm.output,
        )

    def test_same_address_different_type_raises(self):
        """Same address with different mdev types is rejected."""
        exc = self.assertRaises(
            exception.InvalidMdevDevSpecConfig,
            devspec.MdevDeviceSpec.from_config_list,
            [
                '{"address": "0000:06:00.0", "mdev_type": "nvidia-319"}',
                '{"address": "0000:06:00.0", "mdev_type": "nvidia-320"}',
            ],
        )
        self.assertIn('0000:06:00.0', str(exc))
        self.assertIn('nvidia-319', str(exc))
        self.assertIn('nvidia-320', str(exc))
        self.assertIn('one mdev type per PCI address', str(exc))

    def test_same_address_different_type_in_array_raises(self):
        """Address conflict inside an array value is rejected."""
        self.assertRaises(
            exception.InvalidMdevDevSpecConfig,
            devspec.MdevDeviceSpec.from_config_list,
            '[{"address": "0000:06:00.0", "mdev_type": "nvidia-319"},'
            ' {"address": "0000:06:00.0", "mdev_type": "nvidia-320"}]',
        )

    def test_wildcard_multiple_types_allowed(self):
        """Wildcard entries may use different mdev types."""
        specs = devspec.MdevDeviceSpec.from_config_list(
            [
                '{"address": "*", "mdev_type": "nvidia-319"}',
                '{"address": "*", "mdev_type": "nvidia-320"}',
            ]
        )
        self.assertEqual(2, len(specs))
        self.assertEqual(
            ['nvidia-319', 'nvidia-320'],
            sorted(s.mdev_type for s in specs),
        )

    def test_wildcard_and_specific_different_types_allowed(self):
        """Wildcard and specific entries may use different types."""
        specs = devspec.MdevDeviceSpec.from_config_list(
            [
                '{"address": "0000:06:00.0", "mdev_type": "nvidia-319"}',
                '{"address": "*", "mdev_type": "nvidia-320"}',
            ]
        )
        self.assertEqual(2, len(specs))
        self.assertEqual(
            [('*', 'nvidia-320'), ('0000:06:00.0', 'nvidia-319')],
            sorted((s.address, s.mdev_type) for s in specs),
        )


class TestMdevDeviceSpecBuildFilters(base.TestCase):
    """Tests for devspec.MdevDeviceSpec.build_filters()."""

    def test_specific_addresses(self):
        """Specific addresses become sorted filter."""
        specs = devspec.MdevDeviceSpec.from_config_list(
            [
                '{"address": "0000:07:00.0", "mdev_type": "nvidia-319"}',
                '{"address": "0000:06:00.0", "mdev_type": "nvidia-320"}',
            ]
        )
        pci_filter, type_filter = devspec.MdevDeviceSpec.build_filters(specs)
        self.assertEqual(
            ['0000:06:00.0', '0000:07:00.0'],
            pci_filter,
        )
        self.assertEqual(
            ['nvidia-319', 'nvidia-320'],
            type_filter,
        )

    def test_wildcard_address(self):
        """Wildcard address produces ['*'] filter."""
        specs = devspec.MdevDeviceSpec.from_config_list(
            [
                '{"address": "*", "mdev_type": "nvidia-319"}',
            ]
        )
        pci_filter, type_filter = devspec.MdevDeviceSpec.build_filters(specs)
        self.assertEqual(['*'], pci_filter)
        self.assertEqual(['nvidia-319'], type_filter)

    def test_empty_specs(self):
        """Empty specs produce None filters."""
        pci_filter, type_filter = devspec.MdevDeviceSpec.build_filters([])
        self.assertIsNone(pci_filter)
        self.assertIsNone(type_filter)


class TestMdevDeviceSpecFindSpec(base.TestCase):
    """Tests for devspec.MdevDeviceSpec.find_spec()."""

    def _make_specs(self, spec_strings):
        return devspec.MdevDeviceSpec.from_config_list(spec_strings)

    def test_first_matching_spec_wins(self):
        """find_spec returns the first spec that matches."""
        specs = self._make_specs(
            [
                '{"address": "0000:06:00.0",'
                ' "mdev_type": "nvidia-319",'
                ' "max_instances": 4}',
                '{"address": "*", "mdev_type": "nvidia-319",'
                ' "max_instances": 99}',
            ]
        )
        spec = devspec.MdevDeviceSpec.find_spec(
            specs,
            '0000:06:00.0',
            'nvidia-319',
        )
        self.assertIsNotNone(spec)
        self.assertEqual(4, spec.max_instances)

    def test_wildcard_address_matches_as_fallback(self):
        """Wildcard address spec matches when no exact entry is listed."""
        specs = self._make_specs(
            [
                '{"address": "*", "mdev_type": "nvidia-319",'
                ' "max_instances": 99}',
            ]
        )
        spec = devspec.MdevDeviceSpec.find_spec(
            specs,
            '0000:07:00.0',
            'nvidia-319',
        )
        self.assertIsNotNone(spec)
        self.assertEqual(99, spec.max_instances)

    def test_no_match_returns_none(self):
        """No matching spec returns None."""
        specs = self._make_specs(
            [
                '{"address": "0000:06:00.0", "mdev_type": "nvidia-319"}',
            ]
        )
        spec = devspec.MdevDeviceSpec.find_spec(
            specs,
            '0000:07:00.0',
            'nvidia-320',
        )
        self.assertIsNone(spec)


class TestMdevDeviceSpecRepr(base.TestCase):
    """Tests for devspec.MdevDeviceSpec.__repr__()."""

    def test_repr(self):
        """repr includes address and mdev_type."""
        spec = devspec.MdevDeviceSpec(
            address='0000:06:00.0',
            mdev_type='nvidia-319',
        )
        result = repr(spec)
        self.assertIn('0000:06:00.0', result)
        self.assertIn('nvidia-319', result)
        self.assertIn('MdevDeviceSpec', result)
