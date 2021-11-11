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

import copy
from http import HTTPStatus
import pecan
import re
import wsme
from wsme import types as wtypes

from oslo_log import log
from oslo_utils import uuidutils

from cyborg import api
from cyborg.api.controllers import base
from cyborg.api.controllers import link
from cyborg.api.controllers import types
from cyborg.api.controllers.v2 import versions
from cyborg.api import expose
from cyborg.common import authorize_wsgi
from cyborg.common import constants
from cyborg.common import exception
from cyborg.common.i18n import _
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

    """The UUID of the device profile"""
    uuid = types.uuid

    """The name of the device profile"""
    name = wtypes.text

    """The description of the device profile"""
    description = wtypes.text

    """The groups of the device profile"""
    groups = [types.jsontype]

    created_at = wtypes.datetime.datetime
    updated_at = wtypes.datetime.datetime

    """A list containing a self link"""
    links = wsme.wsattr([link.Link], readonly=True)

    def __init__(self, **kwargs):
        super(DeviceProfile, self).__init__(**kwargs)
        self.fields = []
        for field in objects.DeviceProfile.fields:
            self.fields.append(field)
            setattr(self, field, kwargs.get(field, wtypes.Unset))

    @classmethod
    def convert_with_links(cls, obj_devprof):
        api_devprof = cls(**obj_devprof.as_dict())
        api_devprof.links = [
            link.Link.make_link('self', pecan.request.public_url,
                                'device_profiles', api_devprof.uuid)
            ]
        return api_devprof

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

    """A list containing device profile objects"""
    device_profiles = [DeviceProfile]

    @classmethod
    def convert_with_links(cls, obj_devprofs):
        collection = cls()
        collection.device_profiles = [
            DeviceProfile.convert_with_links(obj_devprof)
            for obj_devprof in obj_devprofs]
        return collection

    def get_device_profiles(self, obj_devprofs):
        api_obj_devprofs = [
            self.get_device_profile(obj_devprof)
            for obj_devprof in obj_devprofs]
        return api_obj_devprofs


class DeviceProfilesController(base.CyborgController,
                               DeviceProfileCollection):
    """REST controller for Device Profiles."""

    @authorize_wsgi.authorize_wsgi("cyborg:device_profile", "create", False)
    @expose.expose(DeviceProfile, body=types.jsontype,
                   status_code=HTTPStatus.CREATED)
    def post(self, req_devprof_list):
        """Create one or more device_profiles.

        NOTE: Only one device profile supported in Train.

        :param devprof: a list of device_profiles.
         [{ "name": <string>,
           "groups": [ {"key1: "value1", "key2": "value2"} ]
           "uuid": <uuid> # optional
           "description": <description> # optional
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
        return DeviceProfile.convert_with_links(new_devprof)

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

        for group in groups:
            tmp_group = copy.deepcopy(group)
            for key, value in tmp_group.items():
                # check resource and trait prefix format
                if not re.match(GROUP_KEYS, key):
                    raise exception.InvalidParameterValue(
                        err="Device profile group keys must be of"
                            " the form %s" % GROUP_KEYS)
                # check trait name and it's value
                if key.startswith("trait:"):
                    inner_origin_trait = ":".join(key.split(":")[1:])
                    inner_trait = inner_origin_trait.strip(" ")
                    if not inner_trait.startswith('CUSTOM_'):
                        raise exception.InvalidParameterValue(
                            err="Unsupported trait name format %s, should "
                                "start with CUSTOM_" % inner_trait)
                    if value not in TRAIT_VALUES:
                        raise exception.InvalidParameterValue(
                            err="Unsupported trait value %s, the value must"
                                " be one among %s" % (value, TRAIT_VALUES))
                    # strip " " and update old group key.
                    if inner_origin_trait != inner_trait:
                        del group[key]
                        standard_key = "trait:" + inner_trait
                        group[standard_key] = value
                # check rc name and it's value
                if key.startswith("resources:"):
                    inner_origin_rc = ":".join(key.split(":")[1:])
                    inner_rc = inner_origin_rc.strip(" ")
                    if inner_rc not in constants.SUPPORT_RESOURCES and \
                        not inner_rc.startswith('CUSTOM_'):
                        raise exception.InvalidParameterValue(
                            err="Unsupported resource class %s" % inner_rc)
                    try:
                        int(value)
                    except ValueError:
                        raise exception.InvalidParameterValue(
                            err="Resources number %s is invalid" % value)
                    # strip " " and update old group key.
                    if inner_origin_rc != inner_rc:
                        del group[key]
                        standard_key = "resources:" + inner_rc
                        group[standard_key] = value

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

        return obj_devprofs

    @authorize_wsgi.authorize_wsgi("cyborg:device_profile", "get_all", False)
    @expose.expose(DeviceProfileCollection, wtypes.text)
    def get_all(self, name=None):
        """Retrieve a list of device profiles."""
        if name is not None:
            names = name.split(',')
        else:
            names = []
        LOG.info('[device_profiles] get_all. names=%s', names)
        api_obj_devprofs = self._get_device_profile_list(names)

        ret = DeviceProfileCollection.convert_with_links(api_obj_devprofs)
        LOG.info('[device_profiles] get_all returned: %s', ret)
        return ret

    @authorize_wsgi.authorize_wsgi("cyborg:device_profile", "get_one")
    @expose.expose('json', wtypes.text)
    def get_one(self, dp_uuid_or_name):
        """Retrieve a single device profile by uuid or name."""
        context = pecan.request.context
        if uuidutils.is_uuid_like(dp_uuid_or_name):
            LOG.info('[device_profiles] get_one. uuid=%s', dp_uuid_or_name)
            obj_devprof = objects.DeviceProfile.get_by_uuid(context,
                                                            dp_uuid_or_name)
        else:
            if api.request.version.minor >= versions.MINOR_2_DP_BY_NAME:
                LOG.info('[device_profiles] get_one. name=%s', dp_uuid_or_name)
                obj_devprof = \
                    objects.DeviceProfile.get_by_name(context,
                                                      dp_uuid_or_name)
            else:
                raise exception.NotAcceptable(_(
                    "Request not acceptable. The minimal required API "
                    "version should be %(base)s.%(opr)s") %
                    {'base': versions.BASE_VERSION,
                     'opr': versions.MINOR_2_DP_BY_NAME})
        if not obj_devprof:
            LOG.warning("Device profile with %s not found!", dp_uuid_or_name)
            raise exception.ResourceNotFound(
                resource='Device profile',
                msg='with %s' % dp_uuid_or_name)
        api_obj_devprof = self.get_device_profile(obj_devprof)

        ret = {"device_profile": api_obj_devprof}
        LOG.info('[device_profiles] get_one returned: %s', ret)
        # TODO(Sundar) Replace this with convert_with_links()
        return wsme.api.Response(ret, status_code=HTTPStatus.OK,
                                 return_type=wsme.types.DictType)

    @authorize_wsgi.authorize_wsgi("cyborg:device_profile", "delete")
    @expose.expose(None, wtypes.text, status_code=HTTPStatus.NO_CONTENT)
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
