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
from cyborg.common.i18n import _
from cyborg.common import utils
from oslo_log import log as logging

LOG = logging.getLogger(__name__)


class NovaAPI(object):
    def __init__(self):
        self.nova_client = utils.get_sdk_adapter('compute')
        self.nova_client.default_microversion = '2.82'

    def _get_acc_changed_events(self, instance_uuid, arq_bind_statuses):
        return [{'name': 'accelerator-request-bound',
                 'server_uuid': instance_uuid,
                 'tag': arq_uuid,
                 'status': arq_bind_status,
                 } for (arq_uuid, arq_bind_status) in arq_bind_statuses]

    def _send_events(self, events):
        """Send events to Nova external events API.

        :param events: List of events to send to Nova.
        :raises: exception.InvalidAPIResponse, on unexpected error
        """
        url = "/os-server-external-events"
        body = {"events": events}
        response = self.nova_client.post(url, json=body)
        # NOTE(Sundar): Response status should always be 200/207. See
        # https://review.opendev.org/#/c/698037/
        if response.status_code == 200:
            LOG.info("Sucessfully sent events to Nova, events: %(events)s",
                     {"events": events})
        elif response.status_code == 207:
            # NOTE(Sundar): If Nova returns per-event code of 422, that
            # is due to a race condition where Nova has not associated
            # the instance with a host yet. See
            # https://bugs.launchpad.net/nova/+bug/1855752
            events = [ev for ev in response.json()['events']]
            event_codes = {ev['code'] for ev in events}
            if len(event_codes) == 1:  # all events have same event code
                if event_codes == {422}:
                    LOG.info('Ignoring Nova notification error that the '
                             'instance %s is not yet associated with a host.',
                             events[0]['server_uuid'])
                else:
                    msg = _('Unexpected event code %(code)s '
                            'for instance %(inst)s')
                    msg = msg % {'code': event_codes[0],
                                 'inst': events[0]["server_uuid"]}
                    raise exception.InvalidAPIResponse(
                        service='Nova', api=url[1:], msg=msg)
            else:
                msg = _('All event responses are expected to '
                        'have the same event code. Instance: %(inst)s')
                msg = msg % {'inst': events[0]['server_uuid']}
                raise exception.InvalidAPIResponse(
                    service='Nova', api=url[1:], msg=msg)
        else:
            # Unexpected return code from Nova
            msg = _('Failed to send events %(ev)s: HTTP %(code)s: %(txt)s')
            msg = msg % {'ev': events,
                         'code': response.status_code,
                         'txt': response.text}
            raise exception.InvalidAPIResponse(
                service='Nova', api=url[1:], msg=msg)

    def notify_binding(self, instance_uuid, arq_bind_statuses):
        """Notify Nova that ARQ bindings are resolved for a given instance.

        :param instance_uuid: UUID of the instance whose ARQs are resolved
        :param arq_bind_statuses: List of (arq_state, arq_bind_status) tuples
        :returns: None
        """
        events = self._get_acc_changed_events(instance_uuid, arq_bind_statuses)
        self._send_events(events)
