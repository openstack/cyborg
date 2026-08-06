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

"""Online data migrations for Cyborg."""

from openstack import exceptions as sdk_exc
from oslo_log import log as logging

from cyborg import context as cyborg_context
from cyborg.common import constants
from cyborg.common import utils
from cyborg.db import api as dbapi


LOG = logging.getLogger(__name__)

HEAL_BATCH_SIZE = 100

# Nova compute microversion for this module's GET /servers/{id} calls so the
# response shape used here (``tenant_id``) is stable. 2.82 also introduced the
# accelerator-request-bound external event Cyborg uses with Nova; deployments
# that integrate Cyborg with Nova are expected to support at least this level
# for those flows. This constant is not a general statement of the minimum
# Nova microversion Cyborg supports across all API usage.
NOVA_COMPUTE_MICROVERSION = '2.82'


def _get_nova_adapter():
    """Build an openstacksdk adapter for the compute service."""
    # NOTE(sean-k-mooney): Pass ``microversion=`` on each Nova request rather
    # than setting ``default_microversion`` on the adapter so every call's
    # contract is explicit. Extend this pattern to other Nova callers.
    return utils.get_sdk_adapter('compute')


def heal_arq_project_ids():
    """Back-fill project_id on ARQs by querying Nova for instance details.

    Finds all ARQs where project_id IS NULL and instance_uuid IS NOT NULL,
    looks up each instance in Nova to get its project_id, and updates
    the ARQ row.  Processes rows in batches of ``HEAL_BATCH_SIZE`` using
    marker-based pagination to bound memory usage.

    :returns: number of ARQs successfully migrated.
    """
    db = dbapi.get_instance()
    context = cyborg_context.get_admin_context()
    nova = _get_nova_adapter()
    migrated = 0
    instance_cache = {}
    marker = None

    while True:
        batch = db.extarq_list(
            context,
            project_id=dbapi.NULL_FILTER,
            instance_uuid=dbapi.NOT_NULL_FILTER,
            limit=HEAL_BATCH_SIZE,
            marker=marker,
        )
        if not batch:
            break

        LOG.info(
            'Processing batch of %d ARQ(s) with NULL project_id.', len(batch)
        )

        for arq in batch:
            instance_uuid = arq['instance_uuid']
            if instance_uuid in instance_cache:
                project_id = instance_cache[instance_uuid]
            else:
                try:
                    response = nova.get(
                        '/servers/%s' % instance_uuid,
                        microversion=NOVA_COMPUTE_MICROVERSION,
                    )
                    server = response.json().get('server', {})
                    # NOTE(sean-k-mooney): If Nova exposes project_id on the
                    # server representation at a stable microversion, prefer it
                    # over tenant_id.
                    project_id = server.get('tenant_id', None)
                    if not project_id:
                        LOG.warning(
                            'Instance %s returned an unexpected response '
                            'shape for ARQ %s; skipping.',
                            instance_uuid,
                            arq['uuid'],
                        )
                        continue
                    instance_cache[instance_uuid] = project_id
                except sdk_exc.ResourceNotFound:
                    LOG.error(
                        'Instance %s not found in Nova.  ARQ %s '
                        'references a deleted instance and should be '
                        'cleaned up manually.',
                        instance_uuid,
                        arq['uuid'],
                    )
                    continue
                except sdk_exc.HttpException:
                    LOG.warning(
                        'Failed to look up instance %s for ARQ %s; skipping.',
                        instance_uuid,
                        arq['uuid'],
                    )
                    continue

            try:
                db.extarq_update(
                    context, arq['uuid'], {'project_id': project_id}
                )
                migrated += 1
                LOG.info(
                    'Healed ARQ %s: set project_id=%s', arq['uuid'], project_id
                )
            except Exception:
                LOG.warning(
                    'Failed to update ARQ %s with project_id=%s',
                    arq['uuid'],
                    project_id,
                )

        marker = batch[-1]['id']

        if len(batch) < HEAL_BATCH_SIZE:
            break

    LOG.info('Migrated %d ARQ(s).', migrated)
    return migrated


def _device_state_from_attach_handles(context, db, device_id):
    """Derive the correct device_state by inspecting attach handle usage.

    Walks the device -> deployable -> attach_handle hierarchy and returns
    DEVICE_STATE_ALLOCATED if any attach handle is currently in use,
    or DEVICE_STATE_AVAILABLE if none are.
    """
    deployables = db.deployable_get_by_filters(
        context, {'device_id': device_id}
    )
    for dep in deployables:
        # Stop at the first deployable that has an in-use attach handle.
        if db.attach_handle_get_by_filters(
            context, {'deployable_id': dep['id'], 'in_use': True}
        ):
            return constants.DEVICE_STATE_ALLOCATED
    return constants.DEVICE_STATE_AVAILABLE


def backfill_device_state(context=None, max_count=50):
    """Backfill NULL device_state for existing devices.

    For each device with device_state IS NULL:
    - Has in-use attach handles -> device_state = 'allocated'
    - No in-use attach handles -> device_state = 'available'

    Loops internally until all NULL rows are processed.

    :returns: (total_found, total_done) tuple
    """
    db = dbapi.get_instance()
    if context is None:
        context = cyborg_context.get_admin_context()

    total_found = 0
    total_done = 0

    while True:
        devices = db.device_list_by_filters(
            context,
            {'device_state': dbapi.NULL_FILTER},
            limit=max_count,
        )
        if not devices:
            break

        done = 0
        for db_dev in devices:
            try:
                new_state = _device_state_from_attach_handles(
                    context, db, db_dev['id']
                )
                db.device_update(
                    context, db_dev['uuid'], {'device_state': new_state}
                )
                done += 1
            except Exception:
                LOG.warning(
                    'Failed to backfill device_state for device %s',
                    db_dev['uuid'],
                    exc_info=True,
                )

        total_found += len(devices)
        total_done += done
        LOG.info(
            'Backfilled device_state on %d/%d devices.', done, len(devices)
        )

        if done == 0:
            LOG.warning(
                'No progress backfilling device_state in batch of %d '
                'device(s); stopping.',
                len(devices),
            )
            break

        if len(devices) < max_count:
            break

    return total_found, total_done
