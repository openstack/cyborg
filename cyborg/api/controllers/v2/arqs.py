# Copyright 2019 Intel, Inc.
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

import pecan
from six.moves import http_client
import wsme
from wsme import types as wtypes

from oslo_log import log

from cyborg.api.controllers import base
from cyborg.api.controllers import link
from cyborg.api.controllers import types
from cyborg.api import expose
from cyborg.common import exception
from cyborg.common import policy
from cyborg import objects

LOG = log.getLogger(__name__)


class ARQ(base.APIBase):
    """API representation of an ARQ.

    This class enforces type checking and value constraints, and converts
    between the internal object model and the API representation.
    """
    uuid = types.uuid
    """The UUID of the device profile"""

    state = wtypes.text  # obvious meanings
    device_profile_name = wtypes.text
    device_profile_group_id = wtypes.IntegerType()

    hostname = wtypes.text
    """The host name to which the ARQ is bound, if any"""

    device_rp_uuid = wtypes.text
    """The UUID of the bound device RP, if any"""

    instance_uuid = wtypes.text
    """The UUID of the instance associated with this ARQ, if any"""

    attach_handle_type = wtypes.text
    attach_handle_info = {wtypes.text: wtypes.text}

    links = wsme.wsattr([link.Link], readonly=True)
    """A list containing a self link"""

    def __init__(self, **kwargs):
        super(ARQ, self).__init__(**kwargs)
        self.fields = []
        for field in objects.ARQ.fields:
            self.fields.append(field)
            setattr(self, field, kwargs.get(field, wtypes.Unset))

    @classmethod
    def convert_with_links(cls, obj_arq):
        api_arq = cls(**obj_arq.as_dict())
        api_arq.links = [
            link.Link.make_link('self', pecan.request.public_url,
                                'accelerator_requests', api_arq.uuid)
            ]
        return api_arq


class ARQCollection(base.APIBase):
    """API representation of a collection of arqs."""

    arqs = [ARQ]
    """A list containing arq objects"""

    @classmethod
    def convert_with_links(cls, obj_arqs):
        collection = cls()
        collection.arqs = [ARQ.convert_with_links(obj_arq)
                           for obj_arq in obj_arqs]
        return collection


class ARQsController(base.CyborgController):
    """REST controller for ARQs.

       For the relationship betweens ARQs and device profiles, see
       nova/nova/accelerator/cyborg.py.
    """

    def _get_devprof(self, context, devprof_name):
        """Get the contents of a device profile.
           Since this is just a read, it is ok for the API layer
           to do this, instead of the conductor.
        """
        try:
            obj_devprof = objects.DeviceProfile.get_by_name(context,
                                                            devprof_name)
            return obj_devprof
        except Exception:
            return None

    @policy.authorize_wsgi("cyborg:arq", "create", False)
    @expose.expose(ARQCollection, body=types.jsontype,
                   status_code=http_client.CREATED)
    def post(self, req):
        """Create one or more ARQs for a single device profile.
           Request body:
              { 'device_profile_name': <string> }
           Future:
              { 'device_profile_name': <string> # required
                'device_profile_group_id': <integer>, # opt, default=0
                'image_uuid': <glance-image-UUID>, #optional, for future
              }
           :param req: request body.
        """
        LOG.info("[arq] post req = (%s)", req)
        context = pecan.request.context
        devprof = None
        dp_name = req.get('device_profile_name')
        if dp_name is not None:
            devprof = self._get_devprof(context, dp_name)
            if devprof is None:
                raise exception.DeviceProfileNameNotFound(name=dp_name)
        else:
            raise exception.DeviceProfileNameNeeded()
        LOG.info('[arqs] post. device profile name=%s', dp_name)

        extarq_list = []
        for group_id, group in enumerate(devprof.groups):
            accel_resources = [
                int(val) for key, val in group.items()
                if key.startswith('resources')]
            # If/when we introduce non-accelerator resources, like
            # device-local memory, the key search above needs to be
            # made specific to accelerator resources only.
            num_accels = sum(accel_resources)
            arq_fields = {
                'device_profile_name': devprof.name,
                'device_profile_group_id': group_id,
            }
            for i in range(num_accels):
                obj_arq = objects.ARQ(context, **arq_fields)
                extarq_fields = {'arq': obj_arq}
                obj_extarq = objects.ExtARQ(context, **extarq_fields)
                # TODO(Sundar) The conductor must do all db writes
                new_extarq = obj_extarq.create(context, devprof.id)
                extarq_list.append(new_extarq)

        ret = ARQCollection.convert_with_links(
            [extarq.arq for extarq in extarq_list])
        LOG.info('[arqs] post returned: %s', ret)
        return ret

    @policy.authorize_wsgi("cyborg:arq", "get_one")
    @expose.expose(ARQ, wtypes.text)
    def get_one(self, uuid):
        """Get a single ARQ by UUID."""
        context = pecan.request.context
        extarq = objects.ExtARQ.get(context, uuid)
        return ARQ.convert_with_links(extarq.arq)

    @policy.authorize_wsgi("cyborg:arq", "get_all", False)
    @expose.expose(ARQCollection, wtypes.text, types.uuid)
    def get_all(self, bind_state=None, instance=None):
        """Retrieve a list of arqs."""
        # TODO(Sundar) Need to implement 'arq=uuid1,...' query parameter
        LOG.info('[arqs] get_all. bind_state:(%s), instance:(%s)',
                 bind_state or '', instance or '')
        context = pecan.request.context
        extarqs = objects.ExtARQ.list(context)
        arqs = [extarq.arq for extarq in extarqs]
        # TODO(Sundar): Optimize by doing the filtering in the db layer
        # Apply instance filter before state filter.
        if instance is not None:
            new_arqs = [arq for arq in arqs
                        if arq['instance_uuid'] == instance]
            arqs = new_arqs
        if bind_state is not None:
            if bind_state != 'resolved':
                raise exception.ARQInvalidState(state=bind_state)
            unbound_flag = False
            for arq in arqs:
                if (arq['state'] != 'Bound' and
                        arq['state'] != 'BindFailed'):
                    unbound_flag = True
            if instance is not None and unbound_flag:
                # Return HTTP code 'Locked'
                # TODO(Sundar) This should return HTTP code 423
                # if any ARQ for this instance is not resolved.
                LOG.warning('HTTP Response should be 423')
                pecan.response.status = http_client.LOCKED
                return None

        ret = ARQCollection.convert_with_links(arqs)
        LOG.info('[arqs:get_all] Returned: %s', ret)
        return ret

    @policy.authorize_wsgi("cyborg:arq", "delete", False)
    @expose.expose(None, wtypes.text, wtypes.text,
                   status_code=http_client.NO_CONTENT)
    def delete(self, arqs=None, instance=None):
        """Delete one or more ARQS.

        The request can be either one of these two forms:
            DELETE /v2/accelerator_requests?arqs=uuid1,uuid2,...
            DELETE /v2/accelerator_requests?instance=uuid

        :param arq: List of ARQ UUIDs
        :param instance: UUID of instance whose ARQs need to be deleted
        """
        context = pecan.request.context
        if (arqs and instance) or ((not arqs) and (not instance)):
            raise exception.ObjectActionError(
                action='delete',
                reason='Provide either an ARQ uuid list or an instance UUID')
        elif arqs:
            LOG.info("[arqs] delete. arqs=(%s)", arqs)
            arqlist = arqs.split(',')
            objects.ExtARQ.delete_by_uuid(context, arqlist)
        else:  # instance is not None
            LOG.info("[arqs] delete. instance=(%s)", instance)
            objects.ExtARQ.delete_by_instance(context, instance)

    def _validate_arq_patch(self, patch):
        """Validate a single patch for an ARQ.

        :param patch: a JSON PATCH document.
            The patch must be of the form [{..}], as specified in the
            value field of arq_uuid in patch() method below.
        :returns: dict of valid fields
        """
        valid_fields = {'hostname': None,
                        'device_rp_uuid': None,
                        'instance_uuid': None}
        if ((not all(p['op'] == 'add' for p in patch)) and
           (not all(p['op'] == 'remove' for p in patch))):
            raise exception.PatchError(
                reason='Every op must be add or remove')

        for p in patch:
            path = p['path'].lstrip('/')
            if path not in valid_fields.keys():
                reason = 'Invalid path in patch {}'.format(p['path'])
                raise exception.PatchError(reason=reason)
            if p['op'] == 'add':
                valid_fields[path] = p['value']
        not_found = [field for field, value in valid_fields.items()
                     if value is None]
        if patch[0]['op'] == 'add' and len(not_found) > 0:
            msg = ','.join(not_found)
            reason = 'Fields absent in patch {}'.format(msg)
            raise exception.PatchError(reason=reason)
        return valid_fields

    @policy.authorize_wsgi("cyborg:arq", "update", False)
    @expose.expose(None, body=types.jsontype,
                   status_code=http_client.ACCEPTED)
    def patch(self, patch_list):
        """Bind/Unbind one or more ARQs.

        Usage: curl -X PATCH .../v2/accelerator_requests
                 -d <patch_list> -H "Content-type: application/json"

        :param patch_list: A map from ARQ UUIDs to their JSON patches:
            {"$arq_uuid": [
                {"path": "/hostname", "op": ADD/RM, "value": "..."},
                {"path": "/device_rp_uuid", "op": ADD/RM, "value": "..."},
                {"path": "/instance_uuid", "op": ADD/RM, "value": "..."},
               ],
             "$arq_uuid": [...]
            }
            In particular, all and only these 3 fields must be present,
            and only 'add' or 'remove' ops are allowed.
        """
        LOG.info('[arqs] patch. list=(%s)', patch_list)
        context = pecan.request.context
        # Validate all patches before un/binding.
        valid_fields = {}
        for arq_uuid, patch in patch_list.items():
            valid_fields[arq_uuid] = self._validate_arq_patch(patch)

        # TODO(Sundar) Defer to conductor and do all concurently.
        objects.ExtARQ.apply_patch(context, patch_list, valid_fields)
