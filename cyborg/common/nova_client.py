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

from cyborg.conf import CONF
from openstack import connection
from oslo_log import log as logging

LOG = logging.getLogger(__name__)


class NovaAPI(object):
    def __init__(self):
        default_user = "devstack-admin"
        try:
            auth_user = CONF.compute.username
        except Exception:
            auth_user = default_user
        self.conn = connection.Connection(cloud=auth_user)
        self.nova_client = self.conn.compute

    def _get_acc_changed_event(self, instance_uuid, dev_profile_name, status):
        return [{'name': 'accelerator-requests-bound',
                 'server_uuid': instance_uuid,
                 'tag': dev_profile_name,
                 'status': status}
                ]

    def _send_events(self, events):
        url = "/os-server-external-events"
        body = {"events": events}
        response = self.nova_client.post(url, json=body)
        if response.ok:
            LOG.info("Sucessfully send events to Nova, events: %(events)s",
                     {"events": events})
            return True
        else:
            raise Exception(
                "Failed to send events %s: HTTP %d: %s" %
                (events, response.status_code, response.text))
            return False

    def notify_binding(self, instance_uuid, dev_profile_name, status):
        events = self._get_acc_changed_event(instance_uuid, dev_profile_name,
                                             status)
        result = self._send_events(events)
        if not result:
            LOG.error("Failed to notify Nova service.")
        return result
