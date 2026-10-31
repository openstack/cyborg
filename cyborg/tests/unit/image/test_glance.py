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

import io
import os
import tempfile

from unittest import mock

from keystoneauth1 import exceptions as ksa_exc
from openstack import exceptions as sdk_exc
from oslo_utils.fixture import uuidsentinel as uuids

from cyborg.common import exception
from cyborg.image import glance
from cyborg.tests import base


_CONN_PATH = 'cyborg.image.glance._get_connection'


class TestGetConnection(base.TestCase):
    @mock.patch('cyborg.image.glance.utils')
    @mock.patch('cyborg.image.glance.ks_loading')
    @mock.patch('cyborg.image.glance.service_auth')
    @mock.patch('cyborg.image.glance.connection.Connection')
    def test_creates_connection_with_context_auth(
        self, mock_conn_cls, mock_sa, mock_ksl, mock_utils
    ):
        ctx = mock.MagicMock()
        ctx.global_id = 'req-fake'
        mock_sa.get_auth_plugin.return_value = mock.sentinel.auth
        mock_utils.get_endpoint.return_value = 'http://glance:9292'

        glance._get_connection(ctx)

        mock_sa.get_auth_plugin.assert_called_once_with(ctx)
        mock_utils.get_ksa_adapter.assert_called_once_with(
            'image',
            ksa_auth=mock.sentinel.auth,
            ksa_session=mock.ANY,
            min_version='2.0',
            max_version='2.latest',
        )
        mock_conn_cls.assert_called_once_with(
            session=mock.ANY,
            image_endpoint_override='http://glance:9292',
            image_api_version='2',
        )
        mock_conn_cls.return_value.global_request.assert_called_once_with(
            'req-fake'
        )


class TestGlanceImageServiceV2(base.TestCase):
    def setUp(self):
        super().setUp()
        self.service = glance.GlanceImageServiceV2()
        self.image_id = str(uuids.image)

    def _mock_response(self, status_code=200, content=b'data'):
        resp = mock.MagicMock()
        resp.status_code = status_code
        resp.iter_content.return_value = iter([content])
        return resp

    @mock.patch(_CONN_PATH)
    def test_download_to_path(self, mock_get_conn):
        resp = self._mock_response()
        mock_get_conn.return_value.image.download_image.return_value = resp
        with tempfile.NamedTemporaryFile(delete=False) as tmp:
            tmp_path = tmp.name
        try:
            self.service.download(
                self.context, self.image_id, dst_path=tmp_path
            )
            with open(tmp_path, 'rb') as f:
                self.assertEqual(b'data', f.read())
        finally:
            os.unlink(tmp_path)

    @mock.patch(_CONN_PATH)
    def test_download_to_fileobj(self, mock_get_conn):
        resp = self._mock_response()
        mock_get_conn.return_value.image.download_image.return_value = resp
        buf = io.BytesIO()
        self.service.download(self.context, self.image_id, data=buf)
        self.assertEqual(b'data', buf.getvalue())

    @mock.patch(_CONN_PATH)
    def test_download_stream_returned(self, mock_get_conn):
        resp = self._mock_response()
        mock_get_conn.return_value.image.download_image.return_value = resp
        result = self.service.download(self.context, self.image_id)
        self.assertIs(resp, result)

    @mock.patch(_CONN_PATH)
    def test_download_no_data_raises(self, mock_get_conn):
        resp = self._mock_response(status_code=204)
        mock_get_conn.return_value.image.download_image.return_value = resp
        self.assertRaises(
            exception.ImageUnacceptable,
            self.service.download,
            self.context,
            self.image_id,
        )
        resp.close.assert_called_once()

    @mock.patch(_CONN_PATH)
    def test_download_forbidden(self, mock_get_conn):
        mock_get_conn.return_value.image.download_image.side_effect = (
            sdk_exc.ForbiddenException()
        )
        self.assertRaises(
            exception.ImageNotAuthorized,
            self.service.download,
            self.context,
            self.image_id,
        )

    @mock.patch(_CONN_PATH)
    def test_download_unauthorized(self, mock_get_conn):
        exc = sdk_exc.HttpException()
        exc.status_code = 401
        mock_get_conn.return_value.image.download_image.side_effect = exc
        self.assertRaises(
            exception.ImageNotAuthorized,
            self.service.download,
            self.context,
            self.image_id,
        )

    @mock.patch(_CONN_PATH)
    def test_download_not_found(self, mock_get_conn):
        mock_get_conn.return_value.image.download_image.side_effect = (
            sdk_exc.NotFoundException()
        )
        self.assertRaises(
            exception.ResourceNotFound,
            self.service.download,
            self.context,
            self.image_id,
        )

    @mock.patch(_CONN_PATH)
    def test_download_bad_request(self, mock_get_conn):
        mock_get_conn.return_value.image.download_image.side_effect = (
            sdk_exc.BadRequestException()
        )
        self.assertRaises(
            exception.ImageBadRequest,
            self.service.download,
            self.context,
            self.image_id,
        )

    @mock.patch(_CONN_PATH)
    def test_download_file_response_auth_error(self, mock_get_conn):
        """401/403 on the file download raise ImageNotAuthorized."""
        for status in (401, 403):
            resp = self._mock_response(status_code=status)
            mock_get_conn.return_value.image.download_image.return_value = resp
            self.assertRaises(
                exception.ImageNotAuthorized,
                self.service.download,
                self.context,
                self.image_id,
            )
            resp.close.assert_called_once()

    @mock.patch(_CONN_PATH)
    def test_download_file_response_503_retries(self, mock_get_conn):
        """A 503 on the file download should be retried."""
        self.flags(num_retries=1, group='glance')
        bad_resp = self._mock_response(status_code=503)
        good_resp = self._mock_response()
        conn = mock_get_conn.return_value
        conn.image.download_image.side_effect = [bad_resp, good_resp]

        result = self.service.download(self.context, self.image_id)
        self.assertIs(good_resp, result)
        self.assertEqual(2, conn.image.download_image.call_count)
        bad_resp.close.assert_called_once()

    @mock.patch(_CONN_PATH)
    def test_download_http_500_no_retry(self, mock_get_conn):
        self.flags(num_retries=1, group='glance')
        exc = sdk_exc.HttpException()
        exc.status_code = 500
        conn = mock_get_conn.return_value
        conn.image.download_image.side_effect = exc

        self.assertRaises(
            exception.GlanceConnectionFailed,
            self.service.download,
            self.context,
            self.image_id,
        )
        conn.image.download_image.assert_called_once()

    @mock.patch(_CONN_PATH)
    def test_download_retries_on_http_503(self, mock_get_conn):
        self.flags(num_retries=1, group='glance')
        exc = sdk_exc.HttpException()
        exc.status_code = 503
        resp = self._mock_response()
        conn = mock_get_conn.return_value
        conn.image.download_image.side_effect = [exc, resp]

        result = self.service.download(self.context, self.image_id)
        self.assertIs(resp, result)
        self.assertEqual(2, conn.image.download_image.call_count)
        mock_get_conn.assert_called_once()

    @mock.patch(_CONN_PATH)
    def test_download_retries_exhausted(self, mock_get_conn):
        self.flags(num_retries=1, group='glance')
        exc = sdk_exc.HttpException()
        exc.status_code = 503
        conn = mock_get_conn.return_value
        conn.image.download_image.side_effect = exc

        self.assertRaises(
            exception.GlanceConnectionFailed,
            self.service.download,
            self.context,
            self.image_id,
        )
        self.assertEqual(2, conn.image.download_image.call_count)
        mock_get_conn.assert_called_once()

    @mock.patch(_CONN_PATH)
    def test_download_retries_on_sdk_exception(self, mock_get_conn):
        self.flags(num_retries=1, group='glance')
        resp = self._mock_response()
        conn = mock_get_conn.return_value
        conn.image.download_image.side_effect = [sdk_exc.SDKException(), resp]

        result = self.service.download(self.context, self.image_id)
        self.assertIs(resp, result)
        mock_get_conn.assert_called_once()

    @mock.patch(_CONN_PATH)
    def test_download_retries_on_connect_failure(self, mock_get_conn):
        self.flags(num_retries=1, group='glance')
        resp = self._mock_response()
        conn = mock_get_conn.return_value
        conn.image.download_image.side_effect = [
            ksa_exc.ConnectFailure('refused'),
            resp,
        ]

        result = self.service.download(self.context, self.image_id)
        self.assertIs(resp, result)
        mock_get_conn.assert_called_once()


class TestSafeFsync(base.TestCase):
    def test_fsync_regular_file(self):
        with tempfile.NamedTemporaryFile() as tmp:
            glance.GlanceImageServiceV2._safe_fsync(tmp)

    def test_fsync_skips_pipe(self):
        r, w = os.pipe()
        try:
            with os.fdopen(w, 'wb') as wf:
                glance.GlanceImageServiceV2._safe_fsync(wf)
        finally:
            os.close(r)


class TestGetRemoteImageService(base.TestCase):
    def test_plain_uuid(self):
        svc, image_id = glance.get_remote_image_service(
            self.context, str(uuids.img)
        )
        self.assertIsInstance(svc, glance.GlanceImageServiceV2)
        self.assertEqual(str(uuids.img), image_id)

    def test_url_extracts_id(self):
        url = 'http://glance:9292/v2/images/%s' % uuids.img
        svc, image_id = glance.get_remote_image_service(self.context, url)
        self.assertIsInstance(svc, glance.GlanceImageServiceV2)
        self.assertEqual(str(uuids.img), image_id)
