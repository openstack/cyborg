# Copyright 2018 Intel, Inc.
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

import datetime
from oslo_config import cfg
from oslo_log import log as logging
from oslo_utils import timeutils

from cyborg.common import exception
from cyborg import db as db_api

LOG = logging.getLogger(__name__)

quota_opts = [
    cfg.IntOpt('reservation_expire',
               default=86400,
               help='Number of seconds until a reservation expires'),
    cfg.IntOpt('until_refresh',
               default=0,
               help='Count of reservations until usage is refreshed'),
    cfg.StrOpt('quota_driver',
               default="cyborg.quota.DbQuotaDriver",
               help='Default driver to use for quota checks'),
    cfg.IntOpt('quota_fpgas',
               default=10,
               help='Total amount of fpga allowed per project'),
    cfg.IntOpt('quota_gpus',
               default=10,
               help='Total amount of storage allowed per project'),
    cfg.IntOpt('max_age',
               default=0,
               help='Number of seconds between subsequent usage refreshes')
    ]

CONF = cfg.CONF
CONF.register_opts(quota_opts)


class QuotaEngine(object):
    """Represent the set of recognized quotas."""

    def __init__(self, quota_driver_class=None):
        """Initialize a Quota object."""

        self._resources = {}
        self._driver = DbQuotaDriver()

    def register_resource(self, resource):
        """Register a resource."""
        self._resources[resource.name] = resource

    def register_resources(self, resources):
        """Register a list of resources."""
        for resource in resources:
            self.register_resource(resource)

    def reserve(self, context, deltas, expire=None, project_id=None):
        """Check quotas and reserve resources.

        For counting quotas--those quotas for which there is a usage
        synchronization function--this method checks quotas against
        current usage and the desired deltas.  The deltas are given as
        keyword arguments, and current usage and other reservations
        are factored into the quota check.

        This method will raise a QuotaResourceUnknown exception if a
        given resource is unknown or if it does not have a usage
        synchronization function.

        If any of the proposed values is over the defined quota, an
        OverQuota exception will be raised with the sorted list of the
        resources which are too high.  Otherwise, the method returns a
        list of reservation UUIDs which were created.

        :param context: The request context, for access checks.
        :param expire: An optional parameter specifying an expiration
                       time for the reservations.  If it is a simple
                       number, it is interpreted as a number of
                       seconds and added to the current time; if it is
                       a datetime.timedelta object, it will also be
                       added to the current time.  A datetime.datetime
                       object will be interpreted as the absolute
                       expiration time.  If None is specified, the
                       default expiration time set by
                       --default-reservation-expire will be used (this
                       value will be treated as a number of seconds).
        :param project_id: Specify the project_id if current context
                           is admin and admin wants to impact on
                           common user's project.
        """
        if not project_id:
            project_id = context.project_id
        reservations = self._driver.reserve(context, self._resources, deltas,
                                            expire=expire,
                                            project_id=project_id)

        LOG.debug("Created reservations %s", reservations)

        return reservations

    def commit(self, context, reservations, project_id=None):
        """Commit reservations.

        :param context: The request context, for access checks.
        :param reservations: A list of the reservation UUIDs, as
                             returned by the reserve() method.
        :param project_id: Specify the project_id if current context
                           is admin and admin wants to impact on
                           common user's project.
        """
        project_id = context.project_id
        try:
            self._driver.commit(context, reservations, project_id=project_id)
        except Exception:
            # NOTE(Vek): Ignoring exceptions here is safe, because the
            # usage resynchronization and the reservation expiration
            # mechanisms will resolve the issue.  The exception is
            # logged, however, because this is less than optimal.
            LOG.exception("Failed to commit reservations %s", reservations)

    def rollback(self, context, reservations, project_id=None):
        pass


class DbQuotaDriver(object):
    """Driver to perform check to enforcement of quotas.

    Also allows to obtain quota information.
    The default driver utilizes the local database.
    """
    dbapi = db_api.get_instance()

    def reserve(self, context, resources, deltas, expire=None,
                project_id=None):
        # Set up the reservation expiration
        if expire is None:
            expire = CONF.reservation_expire
        if isinstance(expire, int):
            expire = datetime.timedelta(seconds=expire)
        if isinstance(expire, datetime.timedelta):
            expire = timeutils.utcnow() + expire
        if not isinstance(expire, datetime.datetime):
            raise exception.InvalidReservationExpiration(expire=expire)

        # If project_id is None, then we use the project_id in context
        if project_id is None:
            project_id = context.project_id

        return self._reserve(context, resources, deltas, expire,
                             project_id)

    def _reserve(self, context, resources, deltas, expire, project_id):
        return self.dbapi.quota_reserve(context, resources, deltas, expire,
                                        CONF.until_refresh, CONF.max_age,
                                        project_id=project_id)

    def commit(self, context, reservations, project_id=None):
        """Commit reservations.

        :param context: The request context, for access checks.
        :param reservations: A list of the reservation UUIDs, as
                             returned by the reserve() method.
        :param project_id: Specify the project_id if current context
                           is admin and admin wants to impact on
                           common user's project.
        """

        try:
            self.dbapi.reservation_commit(context, reservations,
                                          project_id=project_id)
        except Exception:
            # NOTE(Vek): Ignoring exceptions here is safe, because the
            # usage resynchronization and the reservation expiration
            # mechanisms will resolve the issue.  The exception is
            # logged, however, because this is less than optimal.
            LOG.exception("Failed to commit reservations %s", reservations)


QUOTAS = QuotaEngine()
