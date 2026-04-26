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

from unittest import mock

from openstack import exceptions as sdk_exc
from oslo_utils.fixture import uuidsentinel as uuids

from cyborg.common import data_migrations
from cyborg.db import api as dbapi
from cyborg.tests import base


class TestHealArqProjectIds(base.TestCase):
    """Tests for Bug #2144056: back-fill project_id on existing ARQs."""

    _FILTER_KWARGS = dict(
        project_id=dbapi.NULL_FILTER,
        instance_uuid=dbapi.NOT_NULL_FILTER,
    )

    def _mock_nova_response(self, tenant_id):
        """Build a mock openstacksdk response for GET /servers/{uuid}."""
        resp = mock.MagicMock()
        resp.json.return_value = {
            'server': {'tenant_id': tenant_id},
        }
        return resp

    @mock.patch.object(data_migrations, '_get_nova_adapter', autospec=True)
    @mock.patch('cyborg.db.api.get_instance', autospec=True)
    def test_heal_bound_arqs_sets_project_id(self, mock_get_db, mock_get_nova):
        fake_arq = {
            'id': 1,
            'uuid': str(uuids.arq1),
            'project_id': None,
            'instance_uuid': str(uuids.instance1),
        }
        mock_db = mock.MagicMock()
        mock_db.extarq_list.return_value = [fake_arq]
        mock_get_db.return_value = mock_db

        mock_nova = mock.MagicMock()
        mock_nova.get.return_value = self._mock_nova_response(
            str(uuids.project_a)
        )
        mock_get_nova.return_value = mock_nova

        count = data_migrations.heal_arq_project_ids()

        self.assertEqual(1, count)
        mock_nova.get.assert_called_once_with(
            '/servers/%s' % str(uuids.instance1),
            microversion=data_migrations.NOVA_COMPUTE_MICROVERSION,
        )
        mock_db.extarq_list.assert_called_once_with(
            mock.ANY,
            limit=data_migrations.HEAL_BATCH_SIZE,
            marker=None,
            **self._FILTER_KWARGS,
        )
        mock_db.extarq_update.assert_called_once_with(
            mock.ANY,
            str(uuids.arq1),
            {'project_id': str(uuids.project_a)},
        )

    @mock.patch.object(data_migrations, '_get_nova_adapter', autospec=True)
    @mock.patch('cyborg.db.api.get_instance', autospec=True)
    def test_heal_no_arqs_to_heal(self, mock_get_db, mock_get_nova):
        mock_db = mock.MagicMock()
        mock_db.extarq_list.return_value = []
        mock_get_db.return_value = mock_db

        count = data_migrations.heal_arq_project_ids()

        self.assertEqual(0, count)
        mock_db.extarq_list.assert_called_once_with(
            mock.ANY,
            limit=data_migrations.HEAL_BATCH_SIZE,
            marker=None,
            **self._FILTER_KWARGS,
        )
        mock_db.extarq_update.assert_not_called()

    @mock.patch.object(data_migrations, '_get_nova_adapter', autospec=True)
    @mock.patch('cyborg.db.api.get_instance', autospec=True)
    def test_heal_handles_deleted_instance(self, mock_get_db, mock_get_nova):
        fake_arq = {
            'id': 1,
            'uuid': str(uuids.arq1),
            'project_id': None,
            'instance_uuid': str(uuids.deleted_instance),
        }
        mock_db = mock.MagicMock()
        mock_db.extarq_list.return_value = [fake_arq]
        mock_get_db.return_value = mock_db

        mock_nova = mock.MagicMock()
        mock_nova.get.side_effect = sdk_exc.ResourceNotFound
        mock_get_nova.return_value = mock_nova

        count = data_migrations.heal_arq_project_ids()

        self.assertEqual(0, count)
        mock_db.extarq_update.assert_not_called()

    @mock.patch.object(data_migrations, '_get_nova_adapter', autospec=True)
    @mock.patch('cyborg.db.api.get_instance', autospec=True)
    def test_heal_handles_nova_error(self, mock_get_db, mock_get_nova):
        fake_arq = {
            'id': 1,
            'uuid': str(uuids.arq1),
            'project_id': None,
            'instance_uuid': str(uuids.instance1),
        }
        mock_db = mock.MagicMock()
        mock_db.extarq_list.return_value = [fake_arq]
        mock_get_db.return_value = mock_db

        mock_nova = mock.MagicMock()
        mock_nova.get.side_effect = sdk_exc.HttpException
        mock_get_nova.return_value = mock_nova

        count = data_migrations.heal_arq_project_ids()

        self.assertEqual(0, count)
        mock_db.extarq_update.assert_not_called()

    @mock.patch.object(data_migrations, '_get_nova_adapter', autospec=True)
    @mock.patch('cyborg.db.api.get_instance', autospec=True)
    def test_heal_handles_malformed_nova_response(
        self, mock_get_db, mock_get_nova
    ):
        fake_arq = {
            'id': 1,
            'uuid': str(uuids.arq1),
            'project_id': None,
            'instance_uuid': str(uuids.instance1),
        }
        mock_db = mock.MagicMock()
        mock_db.extarq_list.return_value = [fake_arq]
        mock_get_db.return_value = mock_db

        mock_nova = mock.MagicMock()
        mock_nova.get.return_value = mock.MagicMock()
        mock_nova.get.return_value.json.return_value = {'server': {}}
        mock_get_nova.return_value = mock_nova

        count = data_migrations.heal_arq_project_ids()

        self.assertEqual(0, count)
        mock_db.extarq_update.assert_not_called()

    @mock.patch.object(data_migrations, '_get_nova_adapter', autospec=True)
    @mock.patch('cyborg.db.api.get_instance', autospec=True)
    def test_heal_caches_instance_lookups(self, mock_get_db, mock_get_nova):
        """Two ARQs for the same instance should only trigger one Nova call."""
        fake_arqs = [
            {
                'id': 1,
                'uuid': str(uuids.arq1),
                'project_id': None,
                'instance_uuid': str(uuids.instance1),
            },
            {
                'id': 2,
                'uuid': str(uuids.arq2),
                'project_id': None,
                'instance_uuid': str(uuids.instance1),
            },
        ]
        mock_db = mock.MagicMock()
        mock_db.extarq_list.return_value = fake_arqs
        mock_get_db.return_value = mock_db

        mock_nova = mock.MagicMock()
        mock_nova.get.return_value = self._mock_nova_response(
            str(uuids.project_a)
        )
        mock_get_nova.return_value = mock_nova

        count = data_migrations.heal_arq_project_ids()

        self.assertEqual(2, count)
        mock_nova.get.assert_called_once_with(
            '/servers/%s' % str(uuids.instance1),
            microversion=data_migrations.NOVA_COMPUTE_MICROVERSION,
        )

    @mock.patch.object(data_migrations, '_get_nova_adapter', autospec=True)
    @mock.patch('cyborg.db.api.get_instance', autospec=True)
    def test_heal_returns_count(self, mock_get_db, mock_get_nova):
        fake_arqs = [
            {
                'id': 1,
                'uuid': str(uuids.arq1),
                'project_id': None,
                'instance_uuid': str(uuids.instance1),
            },
            {
                'id': 2,
                'uuid': str(uuids.arq2),
                'project_id': None,
                'instance_uuid': str(uuids.instance2),
            },
        ]
        mock_db = mock.MagicMock()
        mock_db.extarq_list.return_value = fake_arqs
        mock_get_db.return_value = mock_db

        mock_nova = mock.MagicMock()
        mock_nova.get.side_effect = [
            self._mock_nova_response(str(uuids.project1)),
            self._mock_nova_response(str(uuids.project2)),
        ]
        mock_get_nova.return_value = mock_nova

        count = data_migrations.heal_arq_project_ids()

        self.assertEqual(2, count)
        self.assertEqual(2, mock_nova.get.call_count)
        for call in mock_nova.get.call_args_list:
            self.assertEqual(
                data_migrations.NOVA_COMPUTE_MICROVERSION,
                call.kwargs['microversion'],
            )

    @mock.patch.object(data_migrations, '_get_nova_adapter', autospec=True)
    @mock.patch('cyborg.db.api.get_instance', autospec=True)
    def test_heal_continues_on_partial_failure(
        self, mock_get_db, mock_get_nova
    ):
        """One deleted instance should not prevent healing other ARQs."""
        fake_arqs = [
            {
                'id': 1,
                'uuid': str(uuids.arq1),
                'project_id': None,
                'instance_uuid': str(uuids.deleted_instance),
            },
            {
                'id': 2,
                'uuid': str(uuids.arq2),
                'project_id': None,
                'instance_uuid': str(uuids.instance2),
            },
        ]
        mock_db = mock.MagicMock()
        mock_db.extarq_list.return_value = fake_arqs
        mock_get_db.return_value = mock_db

        mock_nova = mock.MagicMock()
        mock_nova.get.side_effect = [
            sdk_exc.ResourceNotFound,
            self._mock_nova_response(str(uuids.project2)),
        ]
        mock_get_nova.return_value = mock_nova

        count = data_migrations.heal_arq_project_ids()

        self.assertEqual(1, count)
        mock_db.extarq_update.assert_called_once_with(
            mock.ANY,
            str(uuids.arq2),
            {'project_id': str(uuids.project2)},
        )

    @mock.patch.object(data_migrations, '_get_nova_adapter', autospec=True)
    @mock.patch('cyborg.db.api.get_instance', autospec=True)
    def test_heal_paginates_in_batches(self, mock_get_db, mock_get_nova):
        """Verify marker-based pagination across multiple batches."""
        batch1 = [
            {
                'id': i + 1,
                'uuid': 'arq-%d' % (i + 1),
                'project_id': None,
                'instance_uuid': 'inst-%d' % (i + 1),
            }
            for i in range(data_migrations.HEAL_BATCH_SIZE)
        ]
        batch2 = [
            {
                'id': data_migrations.HEAL_BATCH_SIZE + 1,
                'uuid': str(uuids.arq_last),
                'project_id': None,
                'instance_uuid': str(uuids.instance_last),
            },
        ]

        mock_db = mock.MagicMock()
        mock_db.extarq_list.side_effect = [batch1, batch2]
        mock_get_db.return_value = mock_db

        mock_nova = mock.MagicMock()
        mock_nova.get.return_value = self._mock_nova_response(
            str(uuids.project_a)
        )
        mock_get_nova.return_value = mock_nova

        count = data_migrations.heal_arq_project_ids()

        self.assertEqual(data_migrations.HEAL_BATCH_SIZE + 1, count)
        for call in mock_nova.get.call_args_list:
            self.assertEqual(
                data_migrations.NOVA_COMPUTE_MICROVERSION,
                call.kwargs['microversion'],
            )
        self.assertEqual(2, mock_db.extarq_list.call_count)
        first_call, second_call = mock_db.extarq_list.call_args_list
        self.assertIsNone(first_call.kwargs.get('marker'))
        self.assertEqual(
            data_migrations.HEAL_BATCH_SIZE,
            second_call.kwargs['marker'],
        )


class TestNovaAdapterForHeal(base.TestCase):
    """Nova adapter used for ARQ project_id backfill."""

    @mock.patch('cyborg.common.data_migrations.utils.get_sdk_adapter')
    def test_get_nova_adapter_returns_compute_sdk_adapter(self, mock_get):
        mock_adapter = mock.MagicMock()
        mock_get.return_value = mock_adapter
        result = data_migrations._get_nova_adapter()
        mock_get.assert_called_once_with('compute')
        self.assertIs(result, mock_adapter)
