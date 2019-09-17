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

from oslo_config import cfg

from cyborg.conf import agent
from cyborg.conf import api
from cyborg.conf import database
from cyborg.conf import default
from cyborg.conf import glance
from cyborg.conf import keystone
from cyborg.conf import nova
from cyborg.conf import placement
from cyborg.conf import service_token

CONF = cfg.CONF

api.register_opts(CONF)
agent.register_opts(CONF)
database.register_opts(CONF)
default.register_opts(CONF)
service_token.register_opts(CONF)
glance.register_opts(CONF)
keystone.register_opts(CONF)
nova.register_opts(CONF)
placement.register_opts(CONF)
