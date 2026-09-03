# Copyright (c) 2019 ZTE Corporation
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

from oslo_log import log as logging
from oslo_utils import versionutils
from oslo_versionedobjects import base as object_base

from cyborg.common import constants
from cyborg.common import data_migrations
from cyborg.db import api as dbapi
from cyborg.objects import base
from cyborg.objects import fields as object_fields


LOG = logging.getLogger(__name__)


@base.CyborgObjectRegistry.register
class Device(base.CyborgObject, object_base.VersionedObjectDictCompat):
    # Version 1.0: Initial version
    # Version 1.1: Add AICHIP type
    # Version 1.2: Add status field
    # Version 1.3: Add MDEV, PCI type
    # Version 1.4: Add NVME type
    # Version 1.5: Add device_state field
    VERSION = '1.5'

    dbapi = dbapi.get_instance()

    fields = {
        'id': object_fields.IntegerField(nullable=False),
        'uuid': object_fields.UUIDField(nullable=False),
        'type': object_fields.EnumField(
            valid_values=constants.DEVICE_TYPE, nullable=False
        ),
        'vendor': object_fields.StringField(nullable=False),
        'model': object_fields.StringField(nullable=False),
        'std_board_info': object_fields.StringField(nullable=True),
        'vendor_board_info': object_fields.StringField(nullable=True),
        'hostname': object_fields.StringField(nullable=False),
        'status': object_fields.EnumField(
            valid_values=constants.DEVICE_STATUS,
            nullable=False,
            default="enabled",
        ),
        'device_state': object_fields.EnumField(
            valid_values=constants.DEVICE_STATES,
            nullable=True,
        ),
    }

    @property
    def supports_cleaning(self):
        return self.type == constants.DEVICE_NVME

    def obj_make_compatible(self, primitive, target_version):
        super().obj_make_compatible(primitive, target_version)
        target_version = versionutils.convert_version_to_tuple(target_version)
        if target_version < (1, 5):
            primitive.pop('device_state', None)
        if target_version < (1, 4):
            base.raise_on_too_new_values(
                target_version,
                primitive,
                'type',
                (constants.DEVICE_NVME,),
            )
        if target_version < (1, 3):
            base.raise_on_too_new_values(
                target_version,
                primitive,
                'type',
                (constants.DEVICE_MDEV, constants.DEVICE_PCI),
            )
        if target_version < (1, 2):
            primitive.pop('status', None)
        if target_version < (1, 1):
            base.raise_on_too_new_values(
                target_version,
                primitive,
                'type',
                (constants.DEVICE_AICHIP,),
            )

    @classmethod
    def _from_db_object(cls, obj, db_obj):
        obj = super()._from_db_object(obj, db_obj)
        # Heal device_state on load for devices that pre-date the column.
        # Avoids relying solely on the backfill migration or conductor startup.
        if obj.device_state is None and obj._context is not None:
            try:
                new_state = data_migrations._device_state_from_attach_handles(
                    obj._context, obj.dbapi, obj.id
                )
                obj.device_state = new_state
                obj._save(
                    obj._context,
                    {'device_state': new_state},
                )
            except Exception:
                LOG.warning(
                    'Failed to heal device_state for device %s', obj.uuid
                )
        return obj

    def create(self, context):
        """Create a device record in the DB."""
        if 'device_state' not in self:
            self.device_state = constants.DEVICE_STATE_AVAILABLE
        values = self.obj_get_changes()
        db_device = self.dbapi.device_create(context, values)
        self._from_db_object(self, db_device)

    @classmethod
    def get(cls, context, uuid):
        """Find a DB Device and return an Obj Device."""
        db_device = cls.dbapi.device_get(context, uuid)
        obj_device = cls._from_db_object(cls(context), db_device)
        return obj_device

    @classmethod
    def list(cls, context, filters=None):
        """Return a list of Device objects."""
        if filters:
            sort_dir = filters.pop('sort_dir', 'desc')
            sort_key = filters.pop('sort_key', 'created_at')
            limit = filters.pop('limit', None)
            marker = filters.pop('marker_obj', None)
            db_devices = cls.dbapi.device_list_by_filters(
                context,
                filters,
                sort_dir=sort_dir,
                sort_key=sort_key,
                limit=limit,
                marker=marker,
            )
        else:
            db_devices = cls.dbapi.device_list(context)
        return cls._from_db_object_list(db_devices, context)

    def _save(self, context, updates):
        db_device = self.dbapi.device_update(context, self.uuid, updates)
        self.obj_reset_changes(updates.keys())
        return db_device

    def save(self, context):
        """Update a Device record in the DB."""
        updates = self.obj_get_changes()
        db_device = self._save(context, updates)
        self._from_db_object(self, db_device)

    def destroy(self, context):
        """Delete the Device from the DB."""
        self.dbapi.device_delete(context, self.uuid)
        self.obj_reset_changes()

    @classmethod
    def get_list_by_hostname(cls, context, hostname):
        """get device object list from the hostname. return [] if not
        exist.
        """
        dev_filter = {'hostname': hostname}
        device_obj_list = Device.list(context, dev_filter)
        return device_obj_list

    @classmethod
    def get_by_device_id(cls, context, device_id):
        """get device object by the device ID."""
        db_device = cls.dbapi.device_get_by_id(context, device_id)
        obj_device = cls._from_db_object(cls(context), db_device)
        return obj_device
