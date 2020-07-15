# -*- mode: python -*-
# -*- encoding: utf-8 -*-
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
#

"""WSGI script for cyborg-api.

Script for running cyborg-api under Apache2.
"""

import sys

from oslo_config import cfg
import oslo_i18n as i18n
from oslo_log import log

from cyborg.api import app
from cyborg.common import service


def init_application():
    CONF = cfg.CONF
    # NOTE(hberaud): Call reset to ensure the ConfigOpts object doesn't
    # already contain registered options if the app is reloaded.
    CONF.reset()

    i18n.install('cyborg')

    service.prepare_service(sys.argv)

    LOG = log.getLogger(__name__)
    LOG.debug("Configuration:")
    CONF.log_opt_values(LOG, log.DEBUG)

    return app.load_app()
