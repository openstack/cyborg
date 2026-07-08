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


"""
Cyborg generic mdev driver implementation.

Discovers mdev-capable parent PCI devices and their supported
mdev types via :class:`mdev.MdevBusManager`, builds Cyborg driver
objects for reporting to Placement based on ``[mdev] device_spec``
configuration parsed through :class:`devspec.MdevDeviceSpec`.
"""

from typing import Any

import os_resource_classes as orc

from oslo_log import log as logging
from oslo_serialization import jsonutils

import cyborg.conf

from cyborg.accelerator.bus_managers import mdev
from cyborg.accelerator.common import utils
from cyborg.accelerator.drivers import driver
from cyborg.accelerator.drivers.mdev import devspec
from cyborg.common import constants
from cyborg.objects.driver_objects import driver_attach_handle
from cyborg.objects.driver_objects import driver_attribute
from cyborg.objects.driver_objects import driver_controlpath_id
from cyborg.objects.driver_objects import driver_deployable
from cyborg.objects.driver_objects import driver_device


LOG = logging.getLogger(__name__)
CONF = cyborg.conf.CONF


class GenericMdevDriver(driver.GenericDriver):
    """Generic driver for mediated devices.

    Discovers mdev-capable parent devices and their supported
    types based on the ``[mdev] device_spec`` configuration,
    then reports them to Cyborg as accelerator resources.

    :param bus_manager: Optional :class:`mdev.MdevBusManager`
        instance. If ``None``, a default instance is created.
    """

    def __init__(
        self,
        *args: Any,
        bus_manager: mdev.MdevBusManager | None = None,
        **kwargs: Any,
    ):
        self._bus_manager: mdev.MdevBusManager = (
            bus_manager or mdev.MdevBusManager()
        )

    def _generate_attribute_list(
        self,
        rc: str,
        traits: list[str],
    ) -> list[driver_attribute.DriverAttribute]:
        """Build driver attribute list for a deployable.

        :param rc: Resource class string.
        :param traits: List of trait strings.
        :returns: List of
            :class:`~cyborg.objects.driver_objects.\
driver_attribute.DriverAttribute` objects.
        """
        attr_list = []
        driver_attr = driver_attribute.DriverAttribute()
        driver_attr.key = 'rc'
        driver_attr.value = rc
        attr_list.append(driver_attr)
        for index, trait in enumerate(traits):
            driver_attr = driver_attribute.DriverAttribute(
                key='trait' + str(index),
                value=trait,
            )
            attr_list.append(driver_attr)
        return attr_list

    def _generate_attach_handle(
        self,
        pci_address: str,
        type_name: str,
        num: int,
    ) -> driver_attach_handle.DriverAttachHandle:
        """Build a single mdev attach handle.

        :param pci_address: PCI address of the parent device.
        :param type_name: mdev type name.
        :param num: Instance number for the type_mark.
        :returns: A
            :class:`~cyborg.objects.driver_objects.\
driver_attach_handle.DriverAttachHandle` object.
        """
        driver_ah = driver_attach_handle.DriverAttachHandle()
        driver_ah.in_use = False
        driver_ah.attach_type = constants.AH_TYPE_MDEV
        type_mark = type_name + '_' + str(num)
        driver_ah.attach_info = utils.mdev_str_to_json(
            pci_address,
            type_name,
            type_mark,
        )
        return driver_ah

    def _get_resource_class(self, spec, type_name):
        """Determine the Placement resource class.

        Uses the ``resource_class`` override from the spec if
        present, otherwise generates
        ``CUSTOM_MDEV_<TYPE_NAME>``.

        :param spec: Matching :class:`devspec.MdevDeviceSpec`.
        :param type_name: mdev type name
            (e.g. ``'nvidia-319'``).
        :returns: Resource class string.
        """
        if not spec.resource_class:
            return orc.normalize_name('MDEV_' + type_name)
        return spec.resource_class

    def _get_traits(self, spec):
        """Build trait list for a deployable.

        Always includes ``OWNER_CYBORG``, plus any additional
        traits from the spec, each normalized via os_traits.

        :param spec: Matching :class:`devspec.MdevDeviceSpec`.
        :returns: A list of trait strings.
        """
        return [constants.OWNER_CYBORG] + spec.traits

    def _get_num_accelerators(self, spec, available, created):
        """Calculate the number of accelerators to report.

        :param spec: Matching :class:`devspec.MdevDeviceSpec`.
        :param available: Available instances from sysfs.
        :param created: Created instances from sysfs.
        :returns: Number of accelerators, capped by
            ``max_instances`` if set in the spec.
        """
        total = available + created
        if spec.max_instances is not None:
            return min(total, spec.max_instances)
        return total

    def _generate_deployable(
        self,
        pci_address: str,
        mdev_type: mdev.MdevType,
        spec: devspec.MdevDeviceSpec,
        hostname: str,
    ) -> driver_deployable.DriverDeployable:
        """Build a deployable for one mdev type on a parent.

        :param pci_address: PCI address of the parent device.
        :param mdev_type: :class:`mdev.MdevType` from
            :meth:`mdev.MdevBusManager.get_mdev_types`.
        :param spec: Matching :class:`devspec.MdevDeviceSpec`.
        :param hostname: Compute host name for naming.
        :returns: A
            :class:`~cyborg.objects.driver_objects.\
driver_deployable.DriverDeployable`.
        """
        type_name = mdev_type.type_name
        available = mdev_type.available_instances
        created = mdev_type.created_instances

        num_accelerators = self._get_num_accelerators(
            spec,
            available,
            created,
        )
        rc = self._get_resource_class(spec, type_name)
        traits = self._get_traits(spec)

        driver_dep = driver_deployable.DriverDeployable()
        driver_dep.attribute_list = self._generate_attribute_list(rc, traits)
        driver_dep.name = hostname + '_' + pci_address + '_' + type_name
        driver_dep.driver_name = 'mdev'
        driver_dep.num_accelerators = num_accelerators
        driver_dep.attach_handle_list = []
        for num in range(num_accelerators):
            driver_dep.attach_handle_list.append(
                self._generate_attach_handle(
                    pci_address,
                    type_name,
                    num,
                ),
            )
        return driver_dep

    def _generate_controlpath_id(
        self,
        pci_address: str,
    ) -> driver_controlpath_id.DriverControlPathID:
        """Build control path ID for a parent PCI device.

        :param pci_address: PCI address of the parent device.
        :returns: A
            :class:`~cyborg.objects.driver_objects.\
driver_controlpath_id.DriverControlPathID` object.
        """
        driver_cpid = driver_controlpath_id.DriverControlPathID()
        driver_cpid.cpid_type = "PCI"
        driver_cpid.cpid_info = utils.pci_str_to_json(
            pci_address,
        )
        return driver_cpid

    def _generate_driver_device(
        self,
        parent: mdev.MdevParentDevice,
        dep_list: list[driver_deployable.DriverDeployable],
    ) -> driver_device.DriverDevice:
        """Build a DriverDevice for a parent PCI device.

        :param parent: The parent device dataclass from
            :meth:`mdev.MdevBusManager.discover`.
        :param dep_list: Pre-built list of DriverDeployable
            objects, one per matching mdev type.
        :returns: A
            :class:`~cyborg.objects.driver_objects.\
driver_device.DriverDevice` object.
        """
        pci_address = parent.address
        device = driver_device.DriverDevice()
        device.vendor = parent.vendor
        device.model = parent.model
        device.std_board_info = jsonutils.dumps({'pci_address': pci_address})
        device.vendor_board_info = ''
        device.type = constants.DEVICE_MDEV
        device.stub = False
        device.controlpath_id = self._generate_controlpath_id(pci_address)
        device.deployable_list = dep_list
        return device

    def update(
        self,
        control_path: str,
        image_path: str,
    ) -> bool:
        return True

    def get_stats(self) -> dict[str, Any]:
        return {}

    def discover(
        self,
    ) -> list[driver_device.DriverDevice]:
        """Discover mdev devices based on configuration.

        Reads ``[mdev] device_spec`` entries, parses them into
        :class:`devspec.MdevDeviceSpec` objects, discovers matching
        parent PCI devices and their mdev types, and returns
        a list of DriverDevice objects.

        :returns: List of
            :class:`~cyborg.objects.driver_objects.\
driver_device.DriverDevice` objects.
        """
        specs = devspec.MdevDeviceSpec.from_config_list(CONF.mdev.device_spec)
        if not specs:
            return []

        pci_filter, type_filter = devspec.MdevDeviceSpec.build_filters(specs)

        parents = self._bus_manager.discover(
            pci_filter=pci_filter,
        )
        LOG.info('Discovered %d mdev parent device(s)', len(parents))

        device_list = []
        hostname = CONF.host
        for parent in parents:
            pci_address = parent.address
            mdev_types = self._bus_manager.get_mdev_types(
                pci_address,
                type_filter=type_filter,
            )
            dep_list = []
            for mdev_type in mdev_types:
                spec = devspec.MdevDeviceSpec.find_spec(
                    specs,
                    pci_address,
                    mdev_type.type_name,
                )
                if not spec:
                    continue
                dep_list.append(
                    self._generate_deployable(
                        pci_address,
                        mdev_type,
                        spec,
                        hostname,
                    ),
                )
            if dep_list:
                device_list.append(
                    self._generate_driver_device(
                        parent,
                        dep_list,
                    ),
                )

        LOG.info('mdev device_list: %s', device_list)
        return device_list
