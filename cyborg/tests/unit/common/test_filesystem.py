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

"""Unit tests for cyborg.common.filesystem."""

import errno
import pathlib

from unittest import mock

import fixtures

from cyborg.common import exception
from cyborg.common import filesystem
from cyborg.tests import base


class TestReadSys(base.TestCase):
    """Tests for filesystem.read_sys."""

    def setUp(self):
        super().setUp()
        self.tmpdir = pathlib.Path(
            self.useFixture(fixtures.TempDir()).path,
        )

    def test_read_absolute_path(self):
        target = self.tmpdir / 'attr'
        target.write_text('hello\n')
        self.assertEqual('hello\n', filesystem.read_sys(target))

    def test_read_relative_path_prepends_sys(self):
        with mock.patch.object(
            filesystem,
            'SYS',
            self.tmpdir,
        ):
            (self.tmpdir / 'class' / 'net').mkdir(
                parents=True,
            )
            attr = self.tmpdir / 'class' / 'net' / 'speed'
            attr.write_text('1000\n')
            result = filesystem.read_sys('class/net/speed')
            self.assertEqual('1000\n', result)

    def test_read_missing_file_raises_file_not_found(self):
        self.assertRaises(
            exception.FileNotFound,
            filesystem.read_sys,
            self.tmpdir / 'no_such_file',
        )

    @mock.patch('time.sleep', autospec=True)
    def test_read_retries_on_ebusy_then_succeeds(self, mock_sleep):
        target = self.tmpdir / 'busy_attr'
        target.write_text('value\n')
        ebusy = OSError(errno.EBUSY, 'Device busy')
        orig_read_text = pathlib.Path.read_text
        call_count = {'n': 0}

        def flaky_read(self_path, *a, **kw):
            call_count['n'] += 1
            if call_count['n'] <= 2:
                raise ebusy
            return orig_read_text(self_path, *a, **kw)

        with mock.patch.object(
            pathlib.Path,
            'read_text',
            flaky_read,
        ):
            result = filesystem.read_sys(target)

        self.assertEqual('value\n', result)
        self.assertEqual(2, mock_sleep.call_count)
        mock_sleep.assert_any_call(1)
        mock_sleep.assert_any_call(2)

    @mock.patch('time.sleep', autospec=True)
    def test_read_raises_device_busy_after_retries(
        self,
        mock_sleep,
    ):
        ebusy = OSError(errno.EBUSY, 'Device busy')
        with mock.patch.object(
            pathlib.Path,
            'read_text',
            side_effect=ebusy,
            autospec=True,
        ):
            self.assertRaises(
                exception.DeviceBusy,
                filesystem.read_sys,
                self.tmpdir / 'stuck',
            )
        self.assertEqual(
            filesystem.RETRY_LIMIT - 1,
            mock_sleep.call_count,
        )

    def test_read_value_error_raises_file_not_found(self):
        with mock.patch.object(
            pathlib.Path,
            'read_text',
            side_effect=ValueError('embedded null'),
            autospec=True,
        ):
            self.assertRaises(
                exception.FileNotFound,
                filesystem.read_sys,
                self.tmpdir / 'bad_path',
            )


class TestWriteSys(base.TestCase):
    """Tests for filesystem.write_sys."""

    def setUp(self):
        super().setUp()
        self.tmpdir = pathlib.Path(
            self.useFixture(fixtures.TempDir()).path,
        )

    def test_write_absolute_path(self):
        target = self.tmpdir / 'attr'
        target.write_text('')
        filesystem.write_sys(target, 'new_value')
        self.assertEqual('new_value', target.read_text())

    def test_write_missing_file_raises_file_not_found(self):
        self.assertRaises(
            exception.FileNotFound,
            filesystem.write_sys,
            self.tmpdir / 'no' / 'such' / 'file',
            'data',
        )

    @mock.patch('time.sleep', autospec=True)
    def test_write_retries_on_ebusy_then_succeeds(
        self,
        mock_sleep,
    ):
        target = self.tmpdir / 'busy_write'
        target.write_text('')
        ebusy = OSError(errno.EBUSY, 'Device busy')
        orig_write_text = pathlib.Path.write_text
        call_count = {'n': 0}

        def flaky_write(self_path, data, *a, **kw):
            call_count['n'] += 1
            if call_count['n'] <= 1:
                raise ebusy
            return orig_write_text(self_path, data, *a, **kw)

        with mock.patch.object(
            pathlib.Path,
            'write_text',
            flaky_write,
        ):
            filesystem.write_sys(target, 'written')

        self.assertEqual('written', target.read_text())
        self.assertEqual(1, mock_sleep.call_count)

    @mock.patch('time.sleep', autospec=True)
    def test_write_raises_device_busy_after_retries(
        self,
        mock_sleep,
    ):
        ebusy = OSError(errno.EBUSY, 'Device busy')
        with mock.patch.object(
            pathlib.Path,
            'write_text',
            side_effect=ebusy,
            autospec=True,
        ):
            self.assertRaises(
                exception.DeviceBusy,
                filesystem.write_sys,
                self.tmpdir / 'stuck',
                'data',
            )
        self.assertEqual(
            filesystem.RETRY_LIMIT - 1,
            mock_sleep.call_count,
        )

    def test_write_relative_path_prepends_sys(self):
        with mock.patch.object(
            filesystem,
            'SYS',
            self.tmpdir,
        ):
            (self.tmpdir / 'devices').mkdir()
            target = self.tmpdir / 'devices' / 'config'
            target.write_text('')
            filesystem.write_sys('devices/config', 'val')
            self.assertEqual('val', target.read_text())

    def test_write_value_error_raises_file_not_found(self):
        with mock.patch.object(
            pathlib.Path,
            'write_text',
            side_effect=ValueError('embedded null'),
            autospec=True,
        ):
            self.assertRaises(
                exception.FileNotFound,
                filesystem.write_sys,
                self.tmpdir / 'bad',
                'data',
            )


class TestRetryIfBusy(base.TestCase):
    """Tests for the retry_if_busy decorator."""

    @mock.patch('time.sleep', autospec=True)
    def test_non_busy_exception_not_retried(self, mock_sleep):
        @filesystem.retry_if_busy
        def always_fails():
            raise exception.FileNotFound(file_path='/fake')

        self.assertRaises(
            exception.FileNotFound,
            always_fails,
        )
        mock_sleep.assert_not_called()

    @mock.patch('time.sleep', autospec=True)
    def test_succeeds_without_retry(self, mock_sleep):
        @filesystem.retry_if_busy
        def ok():
            return 42

        self.assertEqual(42, ok())
        mock_sleep.assert_not_called()
