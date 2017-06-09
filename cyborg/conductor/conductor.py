# -*- coding: utf-8 -*-

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

import conf
import eventlet
import handlers
from oslo_config import cfg
from oslo_log import log as logging
import oslo_messaging as messaging
import rpcapi
import time

eventlet.monkey_patch()

CONF = cfg.CONF
conf.register_opts(CONF)

LOG = logging.getLogger(__name__)
logging.register_options(CONF)
logging.setup(CONF, 'Cyborg.Conductor')

url = messaging.TransportURL.parse(CONF, url=CONF.transport_url)
transport = messaging.get_notification_transport(CONF, url)

message_endpoints = [
    handlers.NotificationEndpoint
]
message_targets = [
    messaging.Target(topic='info'),
    messaging.Target(topic='update'),
    messaging.Target(topic='warn'),
    messaging.Target(topic='error')
]
rpc_targets = messaging.Target(topic='cyborg_control', server=CONF.server_id)
rpc_endpoints = [
    rpcapi.RPCEndpoint()
]
access_policy = messaging.ExplicitRPCAccessPolicy
rpc_server = messaging.get_rpc_server(transport,
                                      rpc_targets,
                                      rpc_endpoints,
                                      executor='eventlet',
                                      access_policy=access_policy)
pool = "listener-workers"
message_server = messaging.get_notification_listener(transport,
                                                     message_targets,
                                                     message_endpoints,
                                                     executor='eventlet',
                                                     allow_requeue=True)

try:
    message_server.start()
    rpc_server.start()
    print("Cyborg Conductor running")
    while True:
        time.sleep(1)
except KeyboardInterrupt:
    print("Stopping server")

message_server.stop()
rpc_server.stop()
message_server.wait()
rpc_server.wait()
