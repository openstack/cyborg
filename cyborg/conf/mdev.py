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


mdev_group = cfg.OptGroup(
    name='mdev',
    title='Mediated device options',
    help="""Options for configuring mediated (mdev) devices.

This group allows operators to specify which mediated devices
Cyborg should manage and report to Placement.
    """,
)

mdev_opts = [
    cfg.MultiStrOpt(
        'device_spec',
        default=[],
        help="""
Specifications for mediated devices to manage.

Each value is a JSON object describing a class of mdev
devices to discover and report to Placement. The following
keys are supported:

- ``address`` (required): PCI address of the parent device,
  e.g. ``"0000:06:00.0"``. Use ``"*"`` to match all parent
  devices.
- ``mdev_type`` (required): mdev type name, e.g.
  ``"nvidia-319"``. Must be a specific type; wildcards are
  not supported.
- ``max_instances`` (optional): integer cap on the number
  of instances reported to Placement.
- ``resource_class`` (optional): custom Placement resource
  class name. If omitted, a default is derived from the
  mdev type name.
- ``traits`` (optional): list of additional Placement trait
  strings to set on the resource provider.

A PCI address can only be configured with a single mdev type:
configuring the same address with more than one
mdev type is a fatal configuration error. The ``"*"``
wildcard address is exempt from this rule, but most hardware
only supports one active mdev type per parent device.

A value may also be a JSON array of such objects, which can be
more convenient when generating the configuration with
templates::

    [mdev]
    device_spec = {"address": "0000:06:00.0", "mdev_type": "nvidia-319"}
    device_spec = [{"address": "*", "mdev_type": "nvidia-320", "max_instances": 8}, {"address": "0000:07:00.0", "mdev_type": "nvidia-320"}]
""",
    ),
]


def register_opts(conf):
    conf.register_group(mdev_group)
    conf.register_opts(mdev_opts, group=mdev_group)


def list_opts():
    return {
        mdev_group: mdev_opts,
    }
