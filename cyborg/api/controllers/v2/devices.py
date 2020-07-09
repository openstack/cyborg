# Copyright 2019 Intel, Inc.
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

import pecan
import wsme
from wsme import types as wtypes

from oslo_log import log

from cyborg.api.controllers import base
from cyborg.api.controllers import link
from cyborg.api.controllers import types
from cyborg.api import expose
from cyborg.common import authorize_wsgi
from cyborg import objects

LOG = log.getLogger(__name__)


class Device(base.APIBase):
    """API representation of a device.

    This class enforces type checking and value constraints, and converts
    between the internal object model and the API representation.
    """
    uuid = types.uuid
    """The UUID of the device"""

    type = wtypes.text
    """The type of the device"""

    vendor = wtypes.text
    """The vendor of the device"""

    model = wtypes.text
    """The model of the device"""

    std_board_info = wtypes.text
    """The standard board info of the device"""

    vendor_board_info = wtypes.text
    """The vendor board info of the device"""

    hostname = wtypes.text
    """The hostname of the device"""

    links = wsme.wsattr([link.Link], readonly=True)
    """A list containing a self link"""

    def __init__(self, **kwargs):
        super(Device, self).__init__(**kwargs)
        self.fields = []
        for field in objects.Device.fields:
            self.fields.append(field)
            setattr(self, field, kwargs.get(field, wtypes.Unset))

    @classmethod
    def convert_with_links(cls, obj_device):
        api_device = cls(**obj_device.as_dict())
        api_device.links = [
            link.Link.make_link('self', pecan.request.public_url,
                                'devices', api_device.uuid)
            ]
        return api_device


class DeviceCollection(base.APIBase):
    """API representation of a collection of devices."""

    devices = [Device]
    """A list containing Device objects"""

    @classmethod
    def convert_with_links(cls, devices):
        collection = cls()
        collection.devices = [Device.convert_with_links(device)
                              for device in devices]
        return collection


class DevicesController(base.CyborgController):
    """REST controller for Devices."""

    @authorize_wsgi.authorize_wsgi("cyborg:device", "get_one")
    @expose.expose(Device, wtypes.text)
    def get_one(self, uuid):
        """Get a single device by UUID.
        :param uuid: uuid of a device.
        """
        context = pecan.request.context
        device = objects.Device.get(context, uuid)
        return Device.convert_with_links(device)

    @authorize_wsgi.authorize_wsgi("cyborg:device", "get_all", False)
    @expose.expose(DeviceCollection, wtypes.text, wtypes.text, wtypes.text,
                   wtypes.ArrayType(types.FilterType))
    def get_all(self, type=None, vendor=None, hostname=None, filters=None):
        """Retrieve a list of devices.
        :param type: type of a device.
        :param vendor: vendor ID of a device.
        :param hostname: the hostname of a compute node where the device
        locates.
        :param filters: a filter of FilterType to get device list by filter.
        """
        filters_dict = {}
        if type:
            filters_dict["type"] = type
        if vendor:
            filters_dict["vendor"] = vendor
        if hostname:
            filters_dict["hostname"] = hostname
        if filters:
            for filter in filters:
                filters_dict.update(filter.as_dict())
        context = pecan.request.context
        obj_devices = objects.Device.list(context, filters=filters_dict)
        LOG.info('[devices:get_all] Returned: %s', obj_devices)
        return DeviceCollection.convert_with_links(obj_devices)
