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

from keystoneauth1 import loading as ks_loading
from oslo_config import cfg

from cyborg.conf import utils as confutils


DEFAULT_SERVICE_TYPE = 'image'

glance_group = cfg.OptGroup(
    'glance',
    title='Glance Options',
    help='Configuration options for the Image service',
)

glance_opts = [
    cfg.IntOpt(
        'num_retries',
        default=0,
        min=0,
        help="""
Enable glance operation retries.

Specifies the number of retries when uploading / downloading
an image to / from glance. 0 means no retries.
""",
    ),
]

deprecated_ksa_opts = {
    'insecure': [cfg.DeprecatedOpt('api_insecure', group=glance_group.name)],
    'cafile': [cfg.DeprecatedOpt('ca_file', group="ssl")],
    'certfile': [cfg.DeprecatedOpt('cert_file', group="ssl")],
    'keyfile': [cfg.DeprecatedOpt('key_file', group="ssl")],
}


def register_opts(conf):
    conf.register_group(glance_group)
    conf.register_opts(glance_opts, group=glance_group)

    confutils.register_ksa_opts(
        conf,
        glance_group,
        DEFAULT_SERVICE_TYPE,
        include_auth=False,
        deprecated_opts=deprecated_ksa_opts,
    )


def list_opts():
    return {
        glance_group: (
            glance_opts
            + ks_loading.get_session_conf_options()
            + confutils.get_ksa_adapter_opts(
                DEFAULT_SERVICE_TYPE, deprecated_opts=deprecated_ksa_opts
            )
        )
    }
