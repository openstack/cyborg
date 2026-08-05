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

from oslo_log import log as logging

from cyborg.common import exception
from cyborg.common import utils
from cyborg.common.i18n import _


LOG = logging.getLogger(__name__)


class NovaAPI:
    def __init__(self):
        self.nova_client = utils.get_sdk_adapter('compute')
        self.nova_client.default_microversion = '2.82'

    def _get_acc_changed_events(self, instance_uuid, arq_bind_statuses):
        return [
            {
                'name': 'accelerator-request-bound',
                'server_uuid': instance_uuid,
                'tag': arq_uuid,
                'status': arq_bind_status,
            }
            for (arq_uuid, arq_bind_status) in arq_bind_statuses
        ]

    def _send_events(self, events):
        """Send events to Nova external events API.

        :param events: List of events to send to Nova.
        :raises: exception.InvalidAPIResponse, on unexpected error
        """
        url = "/os-server-external-events"
        body = {"events": events}
        response = self.nova_client.post(url, json=body)
        if response.status_code == 200:
            LOG.info(
                "Successfully sent events to Nova, events: %(events)s",
                {"events": events},
            )
        elif response.status_code == 207:
            resp_events = response.json()['events']
            event_codes = {ev['code'] for ev in resp_events}
            if len(event_codes) == 1 and event_codes == {422}:
                # LP#1855752: Nova returns 422 per-event when instance.host
                # is not yet set. This is expected for instant ARQ binds
                # because Cyborg notifies during the conductor's bind RPC,
                # before build_and_run_instance assigns the host. Nova
                # compute handles this via exit_wait_early: it polls Cyborg
                # for already-bound ARQs and skips the event wait.
                LOG.debug(
                    'Nova returned 422 for instance %s (host not yet '
                    'assigned). Expected for instant ARQ binds; Nova '
                    'compute will detect the bound state via polling.',
                    resp_events[0]['server_uuid'],
                )
            elif len(event_codes) == 1:
                msg = _('Unexpected event code %(code)s for instance %(inst)s')
                msg = msg % {
                    'code': event_codes.pop(),
                    'inst': resp_events[0]["server_uuid"],
                }
                raise exception.InvalidAPIResponse(
                    service='Nova', api=url[1:], msg=msg
                )
            else:
                msg = _(
                    'All event responses are expected to '
                    'have the same event code. Instance: %(inst)s'
                )
                msg = msg % {'inst': resp_events[0]['server_uuid']}
                raise exception.InvalidAPIResponse(
                    service='Nova', api=url[1:], msg=msg
                )
        else:
            msg = _('Failed to send events %(ev)s: HTTP %(code)s: %(txt)s')
            msg = msg % {
                'ev': events,
                'code': response.status_code,
                'txt': response.text,
            }
            raise exception.InvalidAPIResponse(
                service='Nova', api=url[1:], msg=msg
            )

    def notify_binding(self, instance_uuid, arq_bind_statuses):
        """Notify Nova that ARQ bindings are resolved for a given instance.

        :param instance_uuid: UUID of the instance whose ARQs are resolved
        :param arq_bind_statuses: List of (arq_uuid, arq_bind_status) tuples
        :returns: None
        """
        events = self._get_acc_changed_events(instance_uuid, arq_bind_statuses)
        self._send_events(events)
