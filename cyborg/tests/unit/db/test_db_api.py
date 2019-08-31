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

"""Unit tests for the DB api."""

import datetime

from oslo_utils import timeutils

from cyborg.db import api as dbapi
from cyborg.db.sqlalchemy import api as sqlalchemyapi
from cyborg.tests.unit.db import base


def _quota_reserve(context, project_id):
    """Create sample QuotaUsage and Reservation objects.

    There is no method db.quota_usage_create(), so we have to use
    db.quota_reserve() for creating QuotaUsage objects.

    Returns reservations uuids.

    """
    sqlalchemy_api = sqlalchemyapi.get_backend()
    resources = {}
    deltas = {}
    for i, resource in enumerate(('fpga', 'gpu')):
        deltas[resource] = i + 1
    return sqlalchemy_api.quota_reserve(
        context, resources, deltas,
        timeutils.utcnow(), timeutils.utcnow(),
        datetime.timedelta(days=1), project_id
    )


class DBAPIQuotaUsageTestCase(base.DbTestCase):

    """Tests for db.api.quota_usage_* methods."""

    def _test_quota_reserve(self):
        sqlalchemy_api = sqlalchemyapi.get_backend()
        reservations = _quota_reserve(self.context, 'project1')
        self.assertEqual(2, len(reservations))
        quota_usages = sqlalchemy_api._get_quota_usages(self.context,
                                                        'project1')
        result = {'project_id': "project1"}
        for k, v in quota_usages.items():
            result[v.resource] = dict(in_use=v.in_use, reserved=v.reserved)

        self.assertEqual({'project_id': 'project1',
                          'gpu': {'reserved': 2, 'in_use': 0},
                          'fpga': {'reserved': 1, 'in_use': 0}},
                         result)

    def _test__get_quota_usages(self):
        _quota_reserve(self.context, 'project1')
        sqlalchemy_api = sqlalchemyapi.get_backend()
        quota_usages = sqlalchemy_api._get_quota_usages(self.context,
                                                        'project1')

        self.assertEqual(['fpga', 'gpu'],
                         sorted(quota_usages.keys()))

    def _test__get_quota_usages_with_resources(self):
        _quota_reserve(self.context, 'project1')
        sqlalchemy_api = sqlalchemyapi.get_backend()
        quota_usage = sqlalchemy_api._get_quota_usages(
            self.context, 'project1', resources=['gpu'])

        self.assertEqual(['gpu'], list(quota_usage.keys()))


class DBAPIReservationTestCase(base.DbTestCase):

    """Tests for db.api.reservation_* methods."""

    def setUp(self):
        super(DBAPIReservationTestCase, self).setUp()
        self.values = {
            'uuid': 'sample-uuid',
            'project_id': 'project1',
            'resource': 'resource',
            'delta': 42,
            'expire': (timeutils.utcnow() +
                       datetime.timedelta(days=1)),
            'usage': {'id': 1}
        }

    def _test__get_reservation_resources(self):
        sqlalchemy_api = sqlalchemyapi.get_backend()
        reservations = _quota_reserve(self.context, 'project1')
        expected = ['fpga', 'gpu']
        resources = sqlalchemy_api._get_reservation_resources(
            self.context, reservations)
        self.assertEqual(expected, sorted(resources))

    def _test_reservation_commit(self):
        db_api = dbapi.get_instance()
        reservations = _quota_reserve(self.context, 'project1')
        expected = {'project_id': 'project1',
                    'fpga': {'reserved': 1, 'in_use': 0},
                    'gpu': {'reserved': 2, 'in_use': 0},
                    }
        quota_usages = db_api._get_quota_usages(self.context, 'project1')
        result = {'project_id': "project1"}
        for k, v in quota_usages.items():
            result[v.resource] = dict(in_use=v.in_use, reserved=v.reserved)

        self.assertEqual(expected, result)

        db_api.reservation_commit(self.context, reservations, 'project1')
        expected = {'project_id': 'project1',
                    'fpga': {'reserved': 0, 'in_use': 1},
                    'gpu': {'reserved': 0, 'in_use': 2},
                    }
        quota_usages = db_api._get_quota_usages(self.context, 'project1')
        result = {'project_id': "project1"}
        for k, v in quota_usages.items():
            result[v.resource] = dict(in_use=v.in_use,
                                      reserved=v.reserved)
        self.assertEqual(expected, result)
