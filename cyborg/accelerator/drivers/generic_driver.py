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
Cyborg Generic driver implementation.
"""
from modules import generic


class GenericDriver(object):
    """Abstract base class representing the generic driver for Cyborg.

    This class provides a reference implementation for a Cyborg driver.
    """

    def __init__(self):
        self.discover = generic.discover()
        self.list = generic.list()
        self.update = generic.update
        self.attach = generic.attach()
        self.detach = generic.detach()
