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
    cfg.StrOpt('mysql_engine',
               default='InnoDB',
               help=_('MySQL engine to use.'))
]

opt_group = cfg.OptGroup(name='database',
                         title='Options for the database service')


def register_opts(conf):
    conf.register_opts(opts, group=opt_group)


DB_OPTS = (opts)


def list_opts():
    return {
        opt_group: DB_OPTS
    }
