# Copyright (c) 2018 NEC, Corp.
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

import sys

from oslo_config import cfg
from oslo_upgradecheck import common_checks
from oslo_upgradecheck import upgradecheck

from cyborg import context as cyborg_context
from cyborg.common.i18n import _
from cyborg.db import api as dbapi


CONF = cfg.CONF


class Checks(upgradecheck.UpgradeCommands):
    """Various upgrade checks should be added as separate methods in this class
    and added to _upgrade_checks tuple.
    """

    def _check_device_state_backfill(self):
        context = cyborg_context.get_admin_context()
        db = dbapi.get_instance()
        try:
            devices = db.device_list_by_filters(
                context,
                {'device_state': dbapi.NULL_FILTER},
            )
        except Exception:
            return upgradecheck.Result(
                upgradecheck.Code.FAILURE,
                _(
                    'Unable to query device_state column. '
                    'Run: cyborg-dbsync upgrade'
                ),
            )
        null_count = len(devices)
        if null_count:
            return upgradecheck.Result(
                upgradecheck.Code.FAILURE,
                _(
                    '%d device(s) still have NULL device_state. '
                    'Run: cyborg-dbsync online_data_migrations'
                )
                % null_count,
            )
        return upgradecheck.Result(
            upgradecheck.Code.SUCCESS,
            _('All device_state values backfilled.'),
        )

    _upgrade_checks = (
        # Added in Victoria
        (
            _('Policy File JSON to YAML Migration'),
            (common_checks.check_policy_json, {'conf': CONF}),
        ),
        # Added in 2026.2
        (_('Device state backfill'), _check_device_state_backfill),
    )


def main():
    return upgradecheck.main(
        cfg.CONF, project='cyborg', upgrade_command=Checks()
    )


if __name__ == '__main__':
    sys.exit(main())
