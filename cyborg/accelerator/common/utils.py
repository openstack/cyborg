# Copyright 2019 Intel, Inc.
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

import collections

from oslo_serialization import jsonutils


def pci_str_to_json(pci_address):
    dbs, func = pci_address.split('.')
    domain, bus, slot = dbs.split(':')
    keys = ["domain", "bus", "device", "function"]
    values = [domain, bus, slot, func]
    bdf_dict = dict(zip(keys, values))
    ordered_dict = collections.OrderedDict(sorted(bdf_dict.items()))
    bdf_json = jsonutils.dumps(ordered_dict)
    return bdf_json
