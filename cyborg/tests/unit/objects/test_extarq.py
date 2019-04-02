# Copyright 2019 Beijing Lenovo Software Ltd.
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

import mock

from testtools.matchers import HasLength
from cyborg import objects
from cyborg.tests.unit.db import base
from cyborg.tests.unit.db import utils


class TestExtARQObject(base.DbTestCase):

    def setUp(self):
        super(TestExtARQObject, self).setUp()
        self.fake_arq = utils.get_test_arq()

    def test_get(self):
        uuid = self.fake_arq['uuid']
        with mock.patch.object(self.dbapi, 'extarq_get',
                               autospec=True) as mock_extarq_get:
            mock_extarq_get.return_value = self.fake_arq
            extarq = objects.ExtARQ.get(self.context, uuid)
            mock_extarq_get.assert_called_once_with(self.context, uuid)
            self.assertEqual(self.context, extarq._context)

    def test_list(self):
        with mock.patch.object(self.dbapi, 'extarq_list',
                               autospec=True) as mock_get_list:
            mock_get_list.return_value = [self.fake_arq]
            extarqs = objects.ExtARQ.list(self.context, 1, None, None, None)
            self.assertEqual(1, mock_get_list.call_count)
            self.assertThat(extarqs, HasLength(1))
            self.assertIsInstance(extarqs[0], objects.ExtARQ)
            self.assertEqual(self.context, extarqs[0]._context)

    def test_create(self):
        with mock.patch.object(self.dbapi, 'extarq_create',
                               autospec=True) as mock_extarq_create:
            mock_extarq_create.return_value = self.fake_arq
            extarq = objects.ExtARQ(self.context, **self.fake_arq)
            extarq.arq = objects.ARQ(self.context, **self.fake_arq)
            extarq.create(self.context)
            mock_extarq_create.assert_called_once_with(self.context,
                                                       self.fake_arq)
            self.assertEqual(self.context, extarq._context)

    def test_destroy(self):
        uuid = self.fake_arq['uuid']
        with mock.patch.object(self.dbapi, 'extarq_get',
                               autospec=True) as mock_extarq_get:
            mock_extarq_get.return_value = self.fake_arq
            with mock.patch.object(self.dbapi, 'extarq_delete',
                                   autospec=True) as mock_extarq_delete:
                extarq = objects.ExtARQ.get(self.context, uuid)
                extarq.destroy(self.context)
                mock_extarq_delete.assert_called_once_with(self.context, uuid)
                self.assertEqual(self.context, extarq._context)

    def test_save(self):
        uuid = self.fake_arq['uuid']
        with mock.patch.object(self.dbapi, 'extarq_get',
                               autospec=True) as mock_extarq_get:
            mock_extarq_get.return_value = self.fake_arq
            with mock.patch.object(self.dbapi, 'extarq_update',
                                   autospec=True) as mock_extarq_update:
                extarq = objects.ExtARQ.get(self.context, uuid)
                arq = extarq.arq
                arq.hostname = 'newtestnode1'
                fake_arq_updated = self.fake_arq
                fake_arq_updated['hostname'] = arq.hostname
                mock_extarq_update.return_value = fake_arq_updated
                extarq.save(self.context)
                mock_extarq_get.assert_called_once_with(self.context, uuid)
                mock_extarq_update.assert_called_once_with(
                    self.context, uuid,
                    {'hostname': 'newtestnode1'})
                self.assertEqual(self.context, extarq._context)
