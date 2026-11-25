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

"""Device specification for mediated (mdev) devices.

Provides :class:`MdevDeviceSpec`, which wraps a single
``[mdev] device_spec`` JSON entry, validating fields and
exposing typed accessors for address, mdev type, and
optional overrides (resource_class, traits, max_instances).
"""

import dataclasses

import jsonschema
import os_resource_classes as orc
import os_traits

from oslo_log import log as logging
from oslo_serialization import jsonutils

from cyborg.common import exception


LOG = logging.getLogger(__name__)

WILDCARD = '*'


@dataclasses.dataclass()
class MdevDeviceSpec:
    """Specification for a single ``[mdev] device_spec`` entry.

    Parses and validates a JSON dict from the configuration,
    exposing typed accessors for address, mdev type, and
    optional overrides. Driver-level policy (default resource
    class naming, owner traits, instance capping) belongs in
    the driver, not here.

    :param spec_dict: Parsed JSON dict with keys ``address``,
        ``mdev_type``, and optionally ``max_instances``,
        ``resource_class``, ``traits``.
    :raises exception.InvalidMdevDevSpecConfig: If required
        fields are missing or the dict is not valid.
    """

    # JSON schema for a single ``[mdev] device_spec`` entry.  Mirrors the
    # keys documented for the ``[mdev] device_spec`` configuration option.
    SCHEMA = {
        'type': 'object',
        'properties': {
            # PCI address of the parent device, or "*" for all parents.
            'address': {'type': 'string', 'minLength': 1},
            # mdev type name; wildcards are not supported.
            'mdev_type': {
                'type': 'string',
                'minLength': 1,
                'not': {'const': WILDCARD},
            },
            'max_instances': {'type': 'integer', 'minimum': 0},
            'resource_class': {'type': 'string', 'minLength': 1},
            'traits': {
                'type': 'array',
                'items': {'type': 'string', 'minLength': 1},
            },
        },
        'required': ['address', 'mdev_type'],
        'additionalProperties': False,
    }

    address: str
    mdev_type: str
    max_instances: int = None
    resource_class: str = None
    traits: list = dataclasses.field(default_factory=list)

    def __post_init__(self):
        if self.traits is not None:
            self._normalize_traits()

        if self.resource_class is not None:
            self._normalize_resource_class()

    def _normalize_resource_class(self):
        """Normalize the input resource_class."""
        self.resource_class = orc.normalize_name(
            self.resource_class.removeprefix(orc.CUSTOM_NAMESPACE)
        )

    def _normalize_traits(self):
        """Validate the input traits list."""
        traits = []
        for trait in self.traits:
            traits.append(
                os_traits.normalize_name(
                    trait.removeprefix(os_traits.CUSTOM_NAMESPACE)
                )
            )
        self.traits = traits

    def match(self, pci_address, type_name):
        """Check if this spec matches a device/type pair.

        :param pci_address: PCI address of the parent device.
        :param type_name: mdev type name.
        :returns: True if this spec matches the given pair.
        """
        addr_match = self.address == WILDCARD or self.address == pci_address
        return addr_match and self.mdev_type == type_name

    def __repr__(self):
        return (
            f'MdevDeviceSpec(address={self.address}, '
            f'mdev_type={self.mdev_type})'
        )

    @classmethod
    def from_config(cls, spec_str):
        """Parse a single JSON config string into a spec.

        :param spec_str: A JSON-encoded device_spec string
            holding a single JSON object.
        :returns: An :class:`MdevDeviceSpec` instance.
        :raises exception.InvalidMdevDevSpecConfig: If the
            JSON is invalid or required fields are missing.
        """
        try:
            spec_dict = jsonutils.loads(spec_str)
        except (ValueError, TypeError):
            raise exception.InvalidMdevDevSpecConfig(
                reason=f'Invalid mdev device_spec: {spec_str}'
            )
        return cls._from_dict(spec_dict, spec_str)

    @classmethod
    def _from_dict(cls, spec_dict, spec_str):
        """Validate a parsed device_spec dict and build a spec.

        :param spec_dict: Parsed JSON dict for a single entry.
        :param spec_str: Original config string, used in error
            messages.
        :returns: An :class:`MdevDeviceSpec` instance.
        :raises exception.InvalidMdevDevSpecConfig: If the dict
            fails schema validation.
        """
        try:
            jsonschema.validate(spec_dict, cls.SCHEMA)
        except jsonschema.exceptions.ValidationError as e:
            raise exception.InvalidMdevDevSpecConfig(
                reason=f'Invalid mdev device spec {spec_str}:{e.message}'
            )
        return cls(
            address=spec_dict['address'],
            mdev_type=spec_dict['mdev_type'],
            max_instances=spec_dict.get('max_instances'),
            resource_class=spec_dict.get('resource_class'),
            traits=spec_dict.get('traits', []),
        )

    @classmethod
    def from_config_list(cls, spec_strings):
        """Parse a list of JSON config strings into specs.

        Parses all ``[mdev] device_spec`` values.  Each value may
        hold a single JSON object or a JSON array of objects.
        Entries are deduplicated by ``(address, mdev_type)``:
        duplicates are user error, so they log a warning and the
        first entry wins.

        Like Nova, a PCI address can only be configured with a
        single mdev type.  Configuring the same address with more
        than one mdev type is a fatal configuration error.  The
        ``*`` wildcard address is exempt from this rule, so
        wildcard entries may use different mdev types.

        :param spec_strings: List of JSON-encoded strings.
        :returns: A list of :class:`MdevDeviceSpec` objects.
        :raises exception.InvalidMdevDevSpecConfig: If a value
            is invalid JSON, fails schema validation, or if the
            same PCI address is configured with more than one
            mdev type.
        """
        seen = {}
        type_by_address = {}
        for spec_str in spec_strings:
            try:
                parsed = jsonutils.loads(spec_str)
            except (ValueError, TypeError):
                raise exception.InvalidMdevDevSpecConfig(
                    reason=f'Invalid mdev device_spec: {spec_str}'
                )
            entries = parsed if isinstance(parsed, list) else [parsed]
            for entry in entries:
                spec = cls._from_dict(entry, spec_str)
                key = (spec.address, spec.mdev_type)
                if key in seen:
                    LOG.warning(
                        'Duplicate mdev device_spec for '
                        '(address=%s, mdev_type=%s), '
                        'keeping first entry',
                        spec.address,
                        spec.mdev_type,
                    )
                    continue
                if spec.address != WILDCARD:
                    known_type = type_by_address.setdefault(
                        spec.address,
                        spec.mdev_type,
                    )
                    if known_type != spec.mdev_type:
                        raise exception.InvalidMdevDevSpecConfig(
                            reason=(
                                f'multiple mdev types configured for '
                                f'PCI address {spec.address} '
                                f'({known_type}, {spec.mdev_type}): only '
                                f'one mdev type per PCI address is '
                                f'supported'
                            ),
                        )
                seen[key] = spec
        specs = list(seen.values())
        return specs

    @staticmethod
    def build_filters(specs):
        """Build PCI address and mdev type filters from specs.

        Extracts unique addresses and type names from the specs
        to create filter lists for
        :meth:`MdevBusManager.discover` and
        :meth:`MdevBusManager.get_mdev_types`.

        :param specs: List of :class:`MdevDeviceSpec` objects.
        :returns: Tuple of ``(pci_filter, type_filter)`` where
            each is a sorted list of strings, ``['*']`` for
            wildcard, or ``None`` if empty.
        """
        pci_addresses = {s.address for s in specs}
        mdev_types = {s.mdev_type for s in specs}

        if WILDCARD in pci_addresses:
            pci_filter = [WILDCARD]
        elif pci_addresses:
            pci_filter = sorted(pci_addresses)
        else:
            pci_filter = None

        type_filter = sorted(mdev_types) if mdev_types else None

        return pci_filter, type_filter

    @staticmethod
    def find_spec(specs, pci_address, type_name):
        """Find the best matching spec for a device/type pair.

        Iterates through specs and returns the first match.

        :param specs: List of :class:`MdevDeviceSpec` objects
        :param pci_address: PCI address of the parent device.
        :param type_name: mdev type name.
        :returns: The matching :class:`MdevDeviceSpec`, or
            ``None`` if no match is found.
        """
        for spec in specs:
            if spec.match(pci_address, type_name):
                return spec
        return None
