# Copyright (c) 2018 Intel.
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

"""
Track resources like FPGA GPU and QAT for a host.  Provides the
conductor with useful information about availability through the accelerator
model.
"""

from oslo_log import log as logging
from oslo_serialization import jsonutils
from stevedore import driver
from stevedore.extension import ExtensionManager

from cyborg.common import exception
from cyborg.common import utils
from cyborg.conf import CONF


LOG = logging.getLogger(__name__)

AGENT_RESOURCE_SEMAPHORE = "agent_resources"


class ResourceTracker:
    """Agent helper class for keeping track of resource usage as instances
    are built and destroyed.
    """

    def __init__(self, host, cond_api):
        self.host = host
        self.conductor_api = cond_api
        self.acc_drivers = {}
        self._initialize_drivers()

    def _initialize_drivers(self, enabled_drivers=None):
        """Load accelerator drivers; does not call init_host().

        Stores the loaded drivers on self.acc_drivers as a dict keyed by
        driver name, e.g. {'nvidia_gpu_driver': obj}; returns None.
        """
        acc_drivers = {}
        if not enabled_drivers:
            enabled_drivers = CONF.agent.enabled_drivers
        valid_drivers = ExtensionManager(
            namespace='cyborg.accelerator.driver'
        ).names()
        for d in enabled_drivers:
            if d not in valid_drivers:
                raise exception.InvalidDriver(name=d)
            acc_driver = driver.DriverManager(
                namespace='cyborg.accelerator.driver',
                name=d,
                invoke_on_load=True,
            ).driver
            # Driver init_host() runs later, after the RPC server is up.
            acc_drivers[d] = acc_driver
        self.acc_drivers = acc_drivers

    def init_host(self):
        """Initialize drivers and check their discovered devices at startup."""
        self.init_drivers()
        all_devices = self.discover_all()
        self.check_duplicate_devices(all_devices)

    def init_drivers(self):
        """Call init_host() on every driver; must run before discover_all()."""
        for name, acc_driver in self.acc_drivers.items():
            LOG.info('Calling init_host() for driver %s', name)
            acc_driver.init_host()

    def discover_all(self):
        """Return one discovery snapshot across all drivers keyed by name."""
        return {name: drv.discover() for name, drv in self.acc_drivers.items()}

    @staticmethod
    def _canonical_pci_address(cpid_info):
        """Return a serialization-independent BDF string for cpid_info.

        Drivers serialize cpid_info differently (key order, spacing), so
        comparing the raw JSON would miss duplicates describing the same
        device. Rebuild the canonical domain:bus:device.function form. Fall
        back to the raw value if cpid_info is not the expected BDF JSON.
        """
        try:
            info = jsonutils.loads(cpid_info)
            return '%(domain)s:%(bus)s:%(device)s.%(function)s' % info
        except (ValueError, TypeError, KeyError):
            return cpid_info

    def check_duplicate_devices(self, device_lists):
        """Reject duplicate PCI addresses in the discovery snapshot."""
        seen = {}
        # Flatten {driver: [devices]} into (driver_name, dev) pairs.
        pairs = (
            (driver_name, dev)
            for driver_name, devices in device_lists.items()
            for dev in devices
        )
        for driver_name, dev in pairs:
            addr = self._canonical_pci_address(dev.controlpath_id.cpid_info)
            if addr in seen:
                raise exception.InvalidConfiguration(
                    reason='Device %s claimed by both %s and %s'
                    % (addr, seen[addr], driver_name)
                )
            seen[addr] = driver_name

    @utils.synchronized(AGENT_RESOURCE_SEMAPHORE)
    def update_usage(self, context):
        """Update the resource usage periodically."""
        acc_list = []
        for acc_driver in self.acc_drivers.values():
            acc_list.extend(acc_driver.discover())
        # Call conductor_api here to diff and report acc data. Now, we actually
        # do not have the method report_data.
        try:
            self.conductor_api.report_data(context, self.host, acc_list)
        except exception.PlacementResourceProviderNotFound as e:
            LOG.error('Unable to report usage: %s', e)
