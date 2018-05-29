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

import os
import pecan

from oslo_config import cfg
from oslo_log import log
from paste import deploy

from cyborg.api import config
from cyborg.api import hooks
from cyborg.api import middleware
import cyborg.conf


CONF = cyborg.conf.CONF
LOG = log.getLogger(__name__)


def get_pecan_config():
    # Set up the pecan configuration
    filename = config.__file__.replace('.pyc', '.py')
    return pecan.configuration.conf_from_file(filename)


def setup_app(pecan_config=None, extra_hooks=None):
    if not pecan_config:
        pecan_config = get_pecan_config()

    app_hooks = [hooks.ConfigHook(),
                 hooks.ConductorAPIHook(),
                 hooks.ContextHook(pecan_config.app.acl_public_routes),
                 hooks.PublicUrlHook()]
    if extra_hooks:
        app_hooks.extend(extra_hooks)

    app_conf = dict(pecan_config.app)
    app = pecan.make_app(
        app_conf.pop('root'),
        force_canonical=getattr(pecan_config.app, 'force_canonical', True),
        hooks=app_hooks,
        wrap_app=middleware.ParsableErrorMiddleware,
        **app_conf
    )

    return app


def load_app():
    cfg_file = None
    cfg_path = CONF.api.api_paste_config
    if not os.path.isabs(cfg_path):
        cfg_file = CONF.find_file(cfg_path)
    elif os.path.exists(cfg_path):
        cfg_file = cfg_path

    if not cfg_file:
        raise cfg.ConfigFilesNotFoundError([CONF.api.api_paste_config])
    LOG.info("Full WSGI config used: %s", cfg_file)
    return deploy.loadapp("config:" + cfg_file)


def app_factory(global_config, **local_conf):
    return setup_app()
