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

from oslo_config import cfg


nvme_group = cfg.OptGroup(
    name='nvme',
    title='NVMe device options',
    help='Options for NVMe devices managed by Cyborg.',
)

nvme_opts = [
    cfg.MultiStrOpt(
        'device_spec',
        default=[],
        help="""
List of NVMe devices for Cyborg to manage. Each entry is a JSON object
that filters devices by vendor, model, or PCI address. If this option is
not set, no NVMe devices are discovered.

You can use any combination of the following keys. Any key you leave out
will match all values for that field.

  vendor_id      -- PCI vendor ID (e.g. "1c5f")
  product_id     -- PCI product/model ID (e.g. "0540")
  address        -- PCI address glob (e.g. "0000:0a:00.*") or per-field regex dict
  clear_action   -- what to do when cleaning up: auto, sanitize, or zero
  clear_strategy -- how to erase: auto, crypto, or block

Multiple entries are allowed and act as an OR: a device is managed if it
matches any one entry.

Examples::

  # All NVMe devices from a specific vendor
  device_spec = {"vendor_id": "1c5f"}

  # A specific model from a specific vendor
  device_spec = {"vendor_id": "1c5f", "product_id": "0540"}

  # Devices on a PCI slot, erased with crypto-erase on cleanup
  device_spec = {"address": "0000:0a:00.*", "clear_strategy": "crypto"}

  # Explicit sanitize command with crypto-erase strategy
  device_spec = {"vendor_id": "1c5f", "clear_action": "sanitize", "clear_strategy": "crypto"}

  # Match by per-field regex address
  device_spec = {"address": {"bus": "0a", "slot": "00", "function": "[0-3]"}}

  # Manage devices from two vendors at once
  device_spec = {"vendor_id": "1c5f"}
  device_spec = {"vendor_id": "8086", "product_id": "0b60"}
""",
    ),
    cfg.IntOpt(
        'cleanup_timeout',
        default=900,
        min=60,
        help='Timeout in seconds for NVMe cleanup. Default 15 min.',
    ),
]


def register_opts(conf):
    conf.register_group(nvme_group)
    conf.register_opts(nvme_opts, group=nvme_group)


def list_opts():
    return {nvme_group: nvme_opts}
