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

"""Cyborg command entry point initialization.

Initializes the oslo.service threading backend before any service is
started. All ``cyborg-*`` entry points import from ``cyborg.cmd``,
so this module runs before any service code.
"""

import oslo_i18n as i18n
import oslo_service.backend as service

service.init_backend(service.BackendType.THREADING)
i18n.install('cyborg')
