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

"""Bus manager for discovering mdev-capable devices via sysfs.

This module provides a reusable, driver-independent interface for
querying the Linux mdev (mediated device) bus. It reads sysfs entries
under ``/sys/class/mdev_bus/`` to enumerate parent PCI devices and
their supported mdev types.
"""

import dataclasses
import pathlib

from oslo_log import log as logging

from cyborg.common import exception
from cyborg.common import filesystem


LOG = logging.getLogger(__name__)

MDEV_BUS_SYSFS_PATH = '/sys/class/mdev_bus/'


@dataclasses.dataclass(frozen=True)
class MdevType:
    """A single mdev type exposed by a parent device."""

    type_name: str
    name: str
    available_instances: int
    created_instances: int
    device_api: str
    description: str


@dataclasses.dataclass(frozen=True)
class MdevParentDevice:
    """An mdev-capable PCI parent device."""

    address: str
    mdev_types: list[MdevType] = dataclasses.field(
        default_factory=list,
    )


class MdevBusManager:
    """Discovers mdev-capable parent devices and their types.

    Reads the sysfs mdev_bus tree to enumerate PCI devices that
    support mediated device creation and to retrieve details about
    each supported mdev type (name, available instances, device API,
    etc.).

    :param sysfs_path: Root path of the mdev_bus sysfs tree.
        Defaults to ``/sys/class/mdev_bus/``.  Can be overridden
        for testing with a temporary directory.
    """

    def __init__(self, sysfs_path: str | None = None):
        self.sysfs_path = pathlib.Path(
            sysfs_path or MDEV_BUS_SYSFS_PATH,
        )

    def discover_parent_devices(
        self,
        pci_filter: list[str] | None = None,
    ) -> list[MdevParentDevice]:
        """Enumerate mdev-capable PCI parent devices.

        :param pci_filter: Controls which devices are returned.

            * ``None`` -- return an empty list (opt-in discovery).
            * ``['*']`` -- return all parent devices found under
              the mdev_bus sysfs path.
            * A list of PCI addresses (e.g.
              ``['0000:06:00.0', '0000:07:00.0']``) -- return only
              devices whose address appears in the list.

        :returns: A list of :class:`MdevParentDevice` objects.
        """
        if not pci_filter:
            return []

        if not self.sysfs_path.is_dir():
            LOG.warning(
                'mdev_bus sysfs path does not exist: %s',
                self.sysfs_path,
            )
            return []

        try:
            all_devices = sorted(p.name for p in self.sysfs_path.iterdir())
        except OSError as e:
            LOG.error(
                'Failed to list mdev_bus sysfs path %s: %s',
                self.sysfs_path,
                e,
            )
            return []

        if pci_filter == ['*']:
            addresses = all_devices
        else:
            addresses = [d for d in all_devices if d in pci_filter]

        LOG.info(
            'Discovered %d mdev-capable parent device(s)',
            len(addresses),
        )
        return [MdevParentDevice(address=a) for a in addresses]

    def get_mdev_types(
        self,
        pci_address: str,
        type_filter: list[str] | None = None,
    ) -> list[MdevType]:
        """Retrieve supported mdev types for a parent device.

        :param pci_address: PCI address of the parent device
            (e.g. ``'0000:06:00.0'``).
        :param type_filter: Controls which types are returned.

            * ``None`` -- return an empty list (opt-in discovery).
            * ``['*']`` -- return all supported types.
            * A list of type names (e.g. ``['nvidia-319']``) --
              return only matching types.

        :returns: A list of :class:`MdevType` objects.
        """
        if not type_filter:
            return []

        types_path = self.sysfs_path / pci_address / 'mdev_supported_types'

        if not types_path.is_dir():
            LOG.warning(
                'mdev_supported_types path does not exist for device %s: %s',
                pci_address,
                types_path,
            )
            return []

        try:
            all_types = sorted(p.name for p in types_path.iterdir())
        except OSError as e:
            LOG.error(
                'Failed to list mdev_supported_types for device %s: %s',
                pci_address,
                e,
            )
            return []

        if type_filter == ['*']:
            type_names = all_types
        else:
            type_names = [t for t in all_types if t in type_filter]

        result = []
        for type_name in type_names:
            type_dir = types_path / type_name
            type_info = self._read_mdev_type(
                pci_address,
                type_name,
                type_dir,
            )
            if type_info is not None:
                result.append(type_info)

        return result

    def _read_mdev_type(
        self,
        pci_address: str,
        type_name: str,
        type_dir: pathlib.Path,
    ) -> MdevType | None:
        """Read attributes of a single mdev type from sysfs.

        :param pci_address: PCI address of the parent device.
        :param type_name: Name of the mdev type directory.
        :param type_dir: Path to the type directory.
        :returns: An :class:`MdevType` instance, or ``None``
            on read failure.
        """
        try:
            available = self._read_sysfs_attr(
                type_dir,
                'available_instances',
            )
            device_api = self._read_sysfs_attr(
                type_dir,
                'device_api',
            )
        except (exception.FileNotFound, exception.DeviceBusy) as e:
            LOG.error(
                'Failed to read required attribute for '
                'mdev type %s on device %s: %s',
                type_name,
                pci_address,
                e,
            )
            return None

        try:
            available_int = int(available)
        except ValueError:
            LOG.error(
                'Invalid available_instances value for '
                'mdev type %s on device %s: %r',
                type_name,
                pci_address,
                available,
            )
            return None

        name = self._read_sysfs_attr_optional(
            type_dir,
            'name',
        )
        description = self._read_sysfs_attr_optional(
            type_dir,
            'description',
        )

        created = self._count_created_instances(
            type_dir,
        )

        return MdevType(
            type_name=type_name,
            name=name,
            available_instances=available_int,
            created_instances=created,
            device_api=device_api,
            description=description,
        )

    @staticmethod
    def _read_sysfs_attr(
        directory: pathlib.Path,
        filename: str,
    ) -> str:
        """Read and strip a sysfs attribute file.

        :param directory: Directory containing the file.
        :param filename: Name of the file to read.
        :returns: The stripped file content as a string.
        :raises cyborg.common.exception.FileNotFound: If the
            file cannot be read.
        :raises cyborg.common.exception.DeviceBusy: If the
            file is busy after exhausting retries.
        """
        return filesystem.read_sys(directory / filename).strip()

    @staticmethod
    def _read_sysfs_attr_optional(
        directory: pathlib.Path,
        filename: str,
    ) -> str:
        """Read a sysfs attribute file, returning '' if absent.

        :param directory: Directory containing the file.
        :param filename: Name of the file to read.
        :returns: The stripped file content, or ``''`` if the file
            does not exist.
        """
        try:
            return filesystem.read_sys(
                directory / filename,
            ).strip()
        except (exception.FileNotFound, exception.DeviceBusy):
            return ''

    @staticmethod
    def _count_created_instances(
        type_dir: pathlib.Path,
    ) -> int:
        """Count mdev instances created for a given type.

        Each created mdev instance is represented as an entry
        inside the ``devices/`` subdirectory of the mdev type
        directory under ``mdev_supported_types/``.

        :param type_dir: Path to the mdev type directory
            (e.g. ``.../mdev_supported_types/nvidia-319``).
        :returns: The number of created instances (int).
        """
        devices_dir = type_dir / 'devices'
        if not devices_dir.is_dir():
            return 0
        try:
            return sum(1 for _ in devices_dir.iterdir())
        except OSError:
            return 0
