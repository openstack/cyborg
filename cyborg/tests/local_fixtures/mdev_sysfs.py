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

"""Fixture that projects MdevParentDevice dataclasses into a fake sysfs."""

import pathlib

import fixtures


class MdevSysfsFixture(fixtures.Fixture):
    """Create a fake mdev_bus sysfs tree from dataclass objects.

    :param devices: :class:`MdevParentDevice` instances to
        materialise under the temporary sysfs root.
    """

    def __init__(self, devices=None):
        super().__init__()
        self.devices = devices or []

    def setUp(self):
        super().setUp()
        self._tmpdir = self.useFixture(fixtures.TempDir())
        self.path = self._tmpdir.path
        for parent in self.devices:
            self._create_device(parent)

    def _create_device(self, parent):
        parent_dir = pathlib.Path(self.path) / parent.address
        parent_dir.mkdir(parents=True, exist_ok=True)
        for mtype in parent.mdev_types:
            self._create_mdev_type(parent_dir, mtype)

    @staticmethod
    def _create_mdev_type(parent_dir, mtype):
        type_dir = parent_dir / 'mdev_supported_types' / mtype.type_name
        type_dir.mkdir(parents=True, exist_ok=True)
        (type_dir / 'name').write_text(mtype.name)
        (type_dir / 'available_instances').write_text(
            str(mtype.available_instances),
        )
        (type_dir / 'device_api').write_text(mtype.device_api)
        if mtype.description:
            (type_dir / 'description').write_text(
                mtype.description,
            )
        if mtype.created_instances > 0:
            devices_dir = type_dir / 'devices'
            devices_dir.mkdir(exist_ok=True)
            for i in range(mtype.created_instances):
                uuid = f'00000000-0000-0000-0000-{i:012d}'
                (devices_dir / uuid).touch()
