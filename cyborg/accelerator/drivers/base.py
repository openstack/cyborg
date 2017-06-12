# Copyright 2017 Lenovo, Inc.
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
"""
Abstract base classes for drivers.
"""

import abc
import six


@six.add_metaclass(abc.ABCMeta)
class BaseDriver(object):
    """Base class for all drivers.

    Defines the abstract base class for generic and vendor drivers.
    """

    standard_interfaces = ('discover', 'list', 'update', 'attach', 'detach')

    discover = None
    """`Standard` attribute for discovering drivers.

    A reference to an instance of :class:DiscoverInterface.
    """

    list = None
    """`Core` attribute for listing drivers.

    A reference to an instance of :class:ListInterface.
    """

    update = None
    """`Standard` attribute to update drivers.

    A reference to an instance of :class:UpdateInterface.
    """

    attach = None
    """`Standard` attribute to attach accelerator to an instance.

    A reference to an instance of :class:AttachInterface.
    """

    detach = None
    """`Standard` attribute to detach accelerator to an instance.

    A reference to an instance of :class:AttachInterface.
    """

    def __init__(self):
        pass

    @property
    def all_interfaces(self):
        return (list(self.standard_interfaces))

    def get_properties(self):
        """Gets the properties of the driver.

        :returns: dictionary of <property name>:<property description> entries.
        """

        properties = {}
        for iface_name in self.all_interfaces:
            iface = getattr(self, iface_name, None)
            if iface:
                properties.update(iface.get_properties())
        return properties
