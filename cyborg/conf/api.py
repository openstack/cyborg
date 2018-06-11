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

from cyborg.common.i18n import _


opts = [
    cfg.HostAddressOpt('host_ip',
                       default='0.0.0.0',
                       help=_('The IP address on which cyborg-api listens.')),
    cfg.PortOpt('port',
                default=6666,
                help=_('The TCP port on which cyborg-api listens.')),
    cfg.IntOpt('api_workers',
               help=_('Number of workers for OpenStack Cyborg API service. '
                      'The default is equal to the number of CPUs available '
                      'if that can be determined, else a default worker '
                      'count of 1 is returned.')),
    cfg.BoolOpt('enable_ssl_api',
                default=False,
                help=_("Enable the integrated stand-alone API to service "
                       "requests via HTTPS instead of HTTP. If there is a "
                       "front-end service performing HTTPS offloading from "
                       "the service, this option should be False; note, you "
                       "will want to change public API endpoint to represent "
                       "SSL termination URL with 'public_endpoint' option.")),
    cfg.StrOpt('public_endpoint',
               help=_("Public URL to use when building the links to the API "
                      "resources (for example, \"https://cyborg.rocks:6666\")."
                      " If None the links will be built using the request's "
                      "host URL. If the API is operating behind a proxy, you "
                      "will want to change this to represent the proxy's URL. "
                      "Defaults to None.")),
    cfg.StrOpt('api_paste_config',
               default="api-paste.ini",
               help="Configuration file for WSGI definition of API."),
]

opt_group = cfg.OptGroup(name='api',
                         title='Options for the cyborg-api service')


API_OPTS = (opts)


def register_opts(conf):
    conf.register_group(opt_group)
    conf.register_opts(opts, group=opt_group)


def list_opts():
    return {
        opt_group: API_OPTS
    }
