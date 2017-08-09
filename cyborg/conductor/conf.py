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
import uuid

default_opts = [
    cfg.StrOpt('transport_url',
               default='',
               help='Transport url for messating, copy from transport_url= in \
                     your Nova config default section'),
    cfg.StrOpt('database_url',
               default='',
               help='Database url for storage, copy from connection= in your \
                     Nova db config section'),
    cfg.StrOpt('server_id',
               default=uuid.uuid4(),
               help='Unique ID for this conductor instance'),
]


def register_opts(conf):
    conf.register_opts(default_opts, group='cyborg')
