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
from cyborg.objects.driver_objects import driver_controlpath_id


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
        self._drivers_by_controlpath = {}
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

    def check_duplicate_devices(self, device_lists):
        """Reject duplicate device addresses in the discovery snapshot."""
        seen = {}
        # Flatten {driver: [devices]} into (driver_name, dev) pairs.
        pairs = (
            (driver_name, dev)
            for driver_name, devices in device_lists.items()
            for dev in devices
        )
        for driver_name, dev in pairs:
            addr = dev.controlpath_id.address
            if addr in seen:
                raise exception.InvalidConfiguration(
                    reason='Device %s claimed by both %s and %s'
                    % (addr, seen[addr], driver_name)
                )
            seen[addr] = driver_name

    def discover_devices(self):
        """Collect devices for reporting and map control paths to drivers.

        Keep the loaded driver instance that reported each device so
        the agent can dispatch device operations to the driver that
        owns them.

        A device must be managed by exactly one driver; duplicate
        claims are rejected by check_duplicate_devices(). On failure
        the stale ownership map is cleared so lookups fail closed.
        """
        device_lists = self.discover_all()
        try:
            self.check_duplicate_devices(device_lists)
        except exception.InvalidConfiguration:
            self._drivers_by_controlpath = {}
            raise
        devices_to_report = []
        owners = {}
        for driver_name, devices in device_lists.items():
            for device in devices:
                key = device.controlpath_id.address
                owners[key] = self.acc_drivers[driver_name]
            devices_to_report.extend(devices)
        self._drivers_by_controlpath = owners
        return devices_to_report

    @utils.synchronized(AGENT_RESOURCE_SEMAPHORE)
    def get_driver_for_controlpath(self, controlpath_id):
        """Return the loaded driver that reported a control path.

        Raise InvalidConfiguration if no enabled driver reports the path.
        """
        controlpath = driver_controlpath_id.DriverControlPathID(
            cpid_type=controlpath_id['cpid_type'],
            cpid_info=jsonutils.dumps(controlpath_id['cpid_info']),
        )
        key = controlpath.address
        selected_driver = self._drivers_by_controlpath.get(key)
        if selected_driver is None:
            raise exception.InvalidConfiguration(
                reason='No enabled driver discovered control path %s' % (key,)
            )
        return selected_driver

    @utils.synchronized(AGENT_RESOURCE_SEMAPHORE)
    def update_usage(self, context):
        """Update the resource usage periodically."""
        acc_list = self.discover_devices()
        # Call conductor_api here to diff and report acc data. Now, we actually
        # do not have the method report_data.
        try:
            self.conductor_api.report_data(context, self.host, acc_list)
        except exception.PlacementResourceProviderNotFound as e:
            LOG.error('Unable to report usage: %s', e)
