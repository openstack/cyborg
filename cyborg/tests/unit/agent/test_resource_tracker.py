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


"""Cyborg agent resource_tracker test cases."""
from cyborg.agent.resource_tracker import ResourceTracker
from cyborg.common import exception
from cyborg.conductor import rpcapi as cond_api
from cyborg.conf import CONF
from cyborg.tests import base


class TestResourceTracker(base.TestCase):
    """Test Agent ResourceTracker """

    def setUp(self):
        super(TestResourceTracker, self).setUp()
        self.host = CONF.host
        self.cond_api = cond_api.ConductorAPI()
        self.rt = ResourceTracker(self.host, self.cond_api)

    def test_update_usage(self):
        """Update the resource usage and stats after a change in an
        instance
        """
        # FIXME(Shaohe Feng) need add testcase. How to check the fpgas
        # has stored into DB by conductor correctly?
        pass

    def test_initialize_acc_drivers(self):
        enabled_drivers = ['intel_fpga_driver']
        self.rt._initialize_drivers(enabled_drivers=enabled_drivers)
        drivers = self.rt.acc_drivers
        self.assertEqual(len(drivers), len(enabled_drivers))

    def test_initialize_invalid_driver(self):
        enabled_drivers = ['invalid_driver']
        self.assertRaises(exception.InvalidDriver, self.rt._initialize_drivers,
                          enabled_drivers)
