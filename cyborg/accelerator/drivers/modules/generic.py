# Copyright 2017 Lenovo, Inc.
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


"""
Cyborg Generic driver modules implementation.
"""

from cyborg.accelerator.common import exception
from oslo_log import log as logging

LOG = logging.getLogger(__name__)

# NOTE (crushil): REQUIRED_PROPERTIES needs to be filled out.
REQUIRED_PROPERTIES = {'create', 'get', 'list', 'update', 'delete'}
COMMON_PROPERTIES = REQUIRED_PROPERTIES


def _check_for_missing_params(info_dict, error_msg, param_prefix=''):
    missing_info = []
    for label, value in info_dict.items():
        if not value:
            missing_info.append(param_prefix + label)

    if missing_info:
        exc_msg = _("%(error_msg)s. Missing are: %(missing_info)s")
        raise exception.MissingParameterValue(
            exc_msg % {'error_msg': error_msg, 'missing_info': missing_info})


def _parse_driver_info(driver):
    info = driver.driver_info
    d_info = {k: info.get(k) for k in COMMON_PROPERTIES}
    error_msg = _("Cannot validate Generic Driver. Some parameters were"
                  " missing in the configuration file.")
    _check_for_missing_params(d_info, error_msg)
    return d_info


class GENERICDRIVER(object):

    def get_properties(self):
        """Return the properties of the generic driver.

        :returns: dictionary of <property name>:<property description> entries.
        """
        return COMMON_PROPERTIES

    def attach(self, accelerator, instance):

        def install(self, accelerator):
            pass

    def detach(self, accelerator, instance):

        def uninstall(self, accelerator):
            pass

        def delete(self):
            pass

    def discover(self):
        pass

    def list(self):
        pass

    def update(self, accelerator, **kwargs):
        pass
