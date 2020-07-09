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
import re
from six.moves import http_client
import wsme
from wsme import types as wtypes

from oslo_log import log
from oslo_utils import uuidutils

from cyborg.api.controllers import base
from cyborg.api.controllers import link
from cyborg.api.controllers import types
from cyborg.api import expose
from cyborg.common import authorize_wsgi
from cyborg.common import exception
from cyborg import objects
LOG = log.getLogger(__name__)

"""
The device profile object and db table has a profile_json field, which has
its own version apart from the device profile groups field. The reasoning
behind that was this structure may evolve more rapidly. Since then the
feedback has been to manage this with the API version itself, preferably
with microversions, rather than use a second version.

One problem with that is that we have to decide on a suitable db
representation for device profile groups, which form an array of
string pairs. The Cyborg community wishes to keep the number of
tables small and manageable.

As of now, the db layer for device profiles still uses the profile_json
field. But the API layer returns the device profile as it should be.
The objects layer does the conversion.
"""


class DeviceProfile(base.APIBase):
    """API representation of a device profile.

    This class enforces type checking and value constraints, and converts
    between the internal object model and the API representation of
    a device profile. See module notes above.
    """

    def get_device_profile(self, obj_devprof):
        api_obj = {}
        for field in ['name', 'description', 'uuid', 'groups']:
            api_obj[field] = obj_devprof[field]
        for field in ['created_at', 'updated_at']:
            api_obj[field] = str(obj_devprof[field])
        api_obj['links'] = [
            link.Link.make_link_dict('device_profiles', api_obj['uuid'])
            ]
        return api_obj


class DeviceProfileCollection(DeviceProfile):
    """API representation of a collection of device profiles."""

    def get_device_profiles(self, obj_devprofs):
        api_obj_devprofs = [
            self.get_device_profile(obj_devprof)
            for obj_devprof in obj_devprofs]
        return api_obj_devprofs


class DeviceProfilesController(base.CyborgController,
                               DeviceProfileCollection):
    """REST controller for Device Profiles."""

    @authorize_wsgi.authorize_wsgi("cyborg:device_profile", "create", False)
    @expose.expose('json', body=types.jsontype,
                   status_code=http_client.CREATED)
    def post(self, req_devprof_list):
        """Create one or more device_profiles.

        NOTE: Only one device profile supported in Train.

        :param devprof: a list of device_profiles.
         [{ "name": <string>,
           "groups": [ {"key1: "value1", "key2": "value2"} ]
           "uuid": <uuid> # optional
         }]
         :returns: The list of created device profiles
        """
        # TODO(Sundar) Support more than one devprof per request, if needed

        LOG.info("[device_profiles] POST request = (%s)", req_devprof_list)
        if len(req_devprof_list) != 1:
            raise exception.InvalidParameterValue(
                err="Only one device profile allowed "
                    "per POST request for now.")
        req_devprof = req_devprof_list[0]
        self._validate_post_request(req_devprof)

        context = pecan.request.context
        obj_devprof = objects.DeviceProfile(context, **req_devprof)

        new_devprof = pecan.request.conductor_api.device_profile_create(
            context, obj_devprof)
        ret = self.get_device_profile(new_devprof)
        return wsme.api.Response(ret, status_code=http_client.CREATED,
                                 return_type=wsme.types.DictType)

    def _validate_post_request(self, req_devprof):
        NAME = "^[a-zA-Z0-9-_]+$"
        keys = '|'.join(["resources:", "trait:", "accel:"])
        GROUP_KEYS = "^(%s)" % keys
        TRAIT_VALUES = ["required", "forbidden"]

        name = req_devprof.get("name")
        if not name:
            raise exception.DeviceProfileNameNeeded()
        elif not re.match(NAME, name):
            raise exception.InvalidParameterValue(
                err="Device profile name must be of the form %s" % NAME)

        groups = req_devprof.get("groups")
        if not groups:
            raise exception.DeviceProfileGroupsExpected()
        else:
            for group in groups:
                for key, value in group.items():
                    if not re.match(GROUP_KEYS, key):
                        raise exception.InvalidParameterValue(
                            err="Device profile group keys must be of "
                                " the form %s" % GROUP_KEYS)
                    if key.startswith("trait:") and value not in TRAIT_VALUES:
                        raise exception.InvalidParameterValue(
                            err="Device profile trait values must be one "
                                "among %s" % TRAIT_VALUES)

    def _get_device_profile_list(self, names=None, uuid=None):
        """Get a list of API objects representing device profiles."""

        context = pecan.request.context
        obj_devprofs = objects.DeviceProfile.list(context)
        if names:
            new_obj_devprofs = [devprof for devprof in obj_devprofs
                                if devprof['name'] in names]
            obj_devprofs = new_obj_devprofs
        elif uuid is not None:
            new_obj_devprofs = [devprof for devprof in obj_devprofs
                                if devprof['uuid'] == uuid]
            obj_devprofs = new_obj_devprofs

        api_obj_devprofs = self.get_device_profiles(obj_devprofs)

        return api_obj_devprofs

    @authorize_wsgi.authorize_wsgi("cyborg:device_profile", "get_all", False)
    @expose.expose('json', wtypes.text)
    def get_all(self, name=None):
        """Retrieve a list of device profiles."""
        if name is not None:
            names = name.split(',')
        else:
            names = []
        LOG.info('[device_profiles] get_all. names=%s', names)
        api_obj_devprofs = self._get_device_profile_list(names)

        ret = {"device_profiles": api_obj_devprofs}
        LOG.info('[device_profiles] get_all returned: %s', ret)
        # TODO(Sundar) Replace this with convert_with_links()
        return wsme.api.Response(ret, status_code=http_client.OK,
                                 return_type=wsme.types.DictType)

    @authorize_wsgi.authorize_wsgi("cyborg:device_profile", "get_one")
    @expose.expose('json', wtypes.text)
    def get_one(self, uuid):
        """Retrieve a single device profile by uuid."""
        LOG.info('[device_profiles] get_one. uuid=%s', uuid)
        api_obj_devprofs = self._get_device_profile_list(uuid=uuid)
        if len(api_obj_devprofs) == 0:
            raise exception.ResourceNotFound(
                resource='Device profile',
                msg='with uuid %s' % uuid)

        count = len(api_obj_devprofs)
        if count != 1:  # Should never happen because names are unique
            raise exception.ExpectedOneObject(obj='device profile',
                                              count=count)
        ret = {"device_profile": api_obj_devprofs[0]}
        LOG.info('[device_profiles] get_one returned: %s', ret)
        # TODO(Sundar) Replace this with convert_with_links()
        return wsme.api.Response(ret, status_code=http_client.OK,
                                 return_type=wsme.types.DictType)

    @authorize_wsgi.authorize_wsgi("cyborg:device_profile", "delete")
    @expose.expose(None, wtypes.text, status_code=http_client.NO_CONTENT)
    def delete(self, value):
        """Delete one or more device_profiles.

        URL: /device_profiles/{uuid} OR /device_profiles?value=foo,bar

        :param value: This should be one of these two:
            - UUID of a device_profile.
            - Comma-delimited list of device profile names.
        """
        context = pecan.request.context
        if uuidutils.is_uuid_like(value):
            uuid = value
            LOG.info('[device_profiles] delete uuid=%s', uuid)
            obj_devprof = objects.DeviceProfile.get_by_uuid(context, uuid)
            pecan.request.conductor_api.device_profile_delete(
                context, obj_devprof)
        else:
            names = value.split(",")
            LOG.info('[device_profiles] delete names=(%s)', names)
            for name in names:
                obj_devprof = objects.DeviceProfile.get_by_name(context, name)
                pecan.request.conductor_api.device_profile_delete(
                    context, obj_devprof)
