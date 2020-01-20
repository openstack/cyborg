# Copyright 2017 Huawei Technologies Co.,LTD.
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

"""Base classes for storage engines."""

import abc

from oslo_config import cfg
from oslo_db import api as db_api
import six


_BACKEND_MAPPING = {'sqlalchemy': 'cyborg.db.sqlalchemy.api'}
IMPL = db_api.DBAPI.from_config(cfg.CONF,
                                backend_mapping=_BACKEND_MAPPING,
                                lazy=True)


def get_instance():
    """Return a DB API instance."""
    return IMPL


@six.add_metaclass(abc.ABCMeta)
class Connection(object):
    """Base class for storage system connections."""

    @abc.abstractmethod
    def __init__(self):
        """Constructor."""

    # device
    @abc.abstractmethod
    def device_create(self, context, values):
        """Create a new device when device is inserted into the host."""

    @abc.abstractmethod
    def device_get(self, context, uuid):
        """Get requested device."""

    @abc.abstractmethod
    def device_list(self, context, limit=None, marker=None,
                    sort_key=None, sort_dir=None):
        """Get requested list of devices."""

    @abc.abstractmethod
    def device_list_by_filters(self, context,
                               filters, sort_key='created_at',
                               sort_dir='desc', limit=None,
                               marker=None, columns_to_join=None):
        """Get requested devices by filters."""

    @abc.abstractmethod
    def device_update(self, context, uuid, values):
        """Update a device."""

    @abc.abstractmethod
    def device_delete(self, context, uuid):
        """Delete a device when device is removed from the host."""

    # device_profile
    @abc.abstractmethod
    def device_profile_create(self, context, values):
        """Create a new device_profile."""

    @abc.abstractmethod
    def device_profile_get_by_uuid(self, context, uuid):
        """Get requested device_profile by uuid."""

    @abc.abstractmethod
    def device_profile_get_by_id(self, context, id):
        """Get requested device_profile by id."""

    @abc.abstractmethod
    def device_profile_get(self, context, name):
        """Get requested device_profile by name."""

    @abc.abstractmethod
    def device_profile_list(self, context):
        """Get requested list of device_profiles."""

    @abc.abstractmethod
    def device_profile_list_by_filters(self, context,
                                       filters, sort_key='created_at',
                                       sort_dir='desc', limit=None,
                                       marker=None, columns_to_join=None):
        """Get requested list of device_profiles by filters."""

    @abc.abstractmethod
    def device_profile_update(self, context, uuid, values):
        """Update a device_profile."""

    @abc.abstractmethod
    def device_profile_delete(self, context, uuid):
        """Delete a device_profile."""

    # deployable
    @abc.abstractmethod
    def deployable_create(self, context, values):
        """Create a new deployable."""

    @abc.abstractmethod
    def deployable_get(self, context, uuid):
        """Get requested deployable."""

    @abc.abstractmethod
    def deployable_list(self, context):
        """Get requested list of deployables."""

    @abc.abstractmethod
    def deployable_update(self, context, uuid, values):
        """Update a deployable."""

    @abc.abstractmethod
    def deployable_delete(self, context, uuid):
        """Delete a deployable."""

    @abc.abstractmethod
    def deployable_get_by_filters(self, context,
                                  filters, sort_key='created_at',
                                  sort_dir='desc', limit=None,
                                  marker=None, columns_to_join=None):
        """Get requested deployable by filters."""

    @abc.abstractmethod
    def deployable_get_by_rp_uuid(self, context, rp_uuid):
        """Get requested deployable by resource provider UUID."""

    # attributes
    @abc.abstractmethod
    def attribute_create(self, context, values):
        """Create a new attribute."""

    @abc.abstractmethod
    def attribute_get(self, context, uuid):
        """Get requested attribute."""

    @abc.abstractmethod
    def attribute_get_by_deployable_id(self, context, deployable_id):
        """Get requested attribute by attribute id."""

    @abc.abstractmethod
    def attribute_get_by_filter(self, context, filters):
        """Get requested attribute by kv pair and attribute id."""

    @abc.abstractmethod
    def attribute_update(self, context, uuid, key, value):
        """Update an attribute's key value pair."""

    @abc.abstractmethod
    def attribute_delete(self, context, uuid):
        """Delete an attribute."""

    # quota
    @abc.abstractmethod
    def quota_reserve(self, context, resources, deltas, expire,
                      until_refresh, max_age, project_id=None,
                      is_allocated_reserve=False):
        """Check quotas and create appropriate reservations."""

    @abc.abstractmethod
    def reservation_commit(self, context, reservations, project_id=None):
        """Check quotas and create appropriate reservations."""

    # extarq
    @abc.abstractmethod
    def extarq_create(self, context, values):
        """Create a new extarq."""

    @abc.abstractmethod
    def extarq_delete(self, context, uuid):
        """Delete an extarq."""

    @abc.abstractmethod
    def extarq_update(self, context, uuid, values, state_scope=None):
        """Update an extarq."""

    @abc.abstractmethod
    def extarq_list(self, context, uuid_range=None):
        """Get requested list of extarqs."""

    @abc.abstractmethod
    def extarq_get(self, context, uuid, lock=False):
        """Get requested extarq."""

    # attach_handle
    @abc.abstractmethod
    def attach_handle_create(self, context, values):
        """Create a new attach_handle"""

    @abc.abstractmethod
    def attach_handle_get_by_uuid(self, context, uuid):
        """Get requested attach_handle"""

    @abc.abstractmethod
    def attach_handle_get_by_id(self, context, id):
        """Get requested attach_handle"""

    @abc.abstractmethod
    def attach_handle_get_by_filters(self, context,
                                     filters, sort_key='created_at',
                                     sort_dir='desc', limit=None,
                                     marker=None, columns_to_join=None):
        """Get requested deployable by filters."""

    @abc.abstractmethod
    def attach_handle_list(self, context):
        """Get requested list of attach_handles"""

    @abc.abstractmethod
    def attach_handle_delete(self, context, uuid):
        """Delete an attach_handle"""

    @abc.abstractmethod
    def attach_handle_update(self, context, uuid, values):
        """Update an attach_handle"""

    # control_path_id
    @abc.abstractmethod
    def control_path_create(self, context, values):
        """Create a new control path id"""

    @abc.abstractmethod
    def control_path_get_by_uuid(self, context, uuid):
        """Get requested control path id"""

    @abc.abstractmethod
    def control_path_get_by_filters(self, context,
                                    filters, sort_key='created_at',
                                    sort_dir='desc', limit=None,
                                    marker=None, columns_to_join=None):
        """Get requested deployable by filters."""

    @abc.abstractmethod
    def control_path_list(self, context):
        """Get requested list of control path ids"""

    @abc.abstractmethod
    def control_path_delete(self, context, uuid):
        """Delete a control path id"""

    @abc.abstractmethod
    def control_path_update(self, context, uuid, values):
        """Update a control path id"""
