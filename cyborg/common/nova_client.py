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

from cyborg.common import exception
from cyborg.common import utils
from oslo_log import log as logging

LOG = logging.getLogger(__name__)


class NovaAPI(object):
    def __init__(self):
        self.nova_client = utils.get_sdk_adapter('compute')
        # TODO(Sundar): change the version to 2.82 once Nova patches merge.
        self.nova_client.default_microversion = 'latest'

    def _get_acc_changed_event(self, instance_uuid, dev_profile_name, status):
        return {'name': 'accelerator-requests-bound',
                'server_uuid': instance_uuid,
                'tag': dev_profile_name,
                'status': status}

    def _send_event(self, event):
        url = "/os-server-external-events"
        body = {"events": [event]}
        response = self.nova_client.post(url, json=body)
        # NOTE(Sundar): Response status should always be 200/207. See
        # https://review.opendev.org/#/c/698037/
        if response.status_code == 200:
            LOG.info("Sucessfully sent event to Nova, event: %(event)s",
                     {"event": event})
            return True, response
        elif response.status_code == 207:
            # NOTE(Sundar): If Nova returns per-event code of 422, that
            # is due to a race condition where Nova has not associated
            # the instance with a host yet. See
            # https://bugs.launchpad.net/nova/+bug/1855752
            err_event = response.json()['events'][0]  # Only 1 event in resp
            if err_event['code'] == 422:
                LOG.info('Ignoring Nova notification error that the '
                         'instance %s is not yet associated with a host.',
                         err_event['server_uuid'])
                return True, response

        # Unexpected return code from Nova
        return False, response

    def notify_binding(self, instance_uuid, dev_profile_name, status):
        """Notify Nova that ARQ bindings are resolved for a given instance.

        :param instance_uuid: UUID of the instance whose ARQs are resolved
        :param dev_profile_name: Device profile name (tag for the event)
        :param status: 'completed' or 'failed', i.e.,
             cyborg.constants.ARQ_BIND_STATUS_FINISH or
             cyborg.constants.ARQ_BIND_STATUS_FAILED
        :raises: exception, if Nova notification fails
        """
        event = self._get_acc_changed_event(instance_uuid, dev_profile_name,
                                            status)
        result, response = self._send_event(event)
        if not result:
            LOG.error("Failed to notify Nova service.")
            msg = ('Failed to send event %s: HTTP %d: %s' %
                   (event, response.status_code, response.text))
            raise exception.NovaAPIConnectFailure(msg=msg)
