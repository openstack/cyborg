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

"""Helpers for reading and writing sysfs files.

Ported from ``nova.filesystem`` to provide robust sysfs access with
automatic retry on EBUSY (errno 16), which real hardware can return
intermittently when the kernel device model is busy.
"""

import errno
import functools
import pathlib
import time

from oslo_log import log as logging

from cyborg.common import exception


LOG = logging.getLogger(__name__)
SYS = pathlib.Path('/sys')
RETRY_LIMIT = 5


def retry_if_busy(func):
    """Retry *func* with linear back-off when it raises DeviceBusy."""

    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        for attempt in range(RETRY_LIMIT):
            try:
                return func(*args, **kwargs)
            except exception.DeviceBusy as e:
                count = attempt + 1
                if count < RETRY_LIMIT:
                    LOG.debug(
                        '%s: sleeping %d second(s) before retrying',
                        e,
                        count,
                    )
                    time.sleep(count)
                    continue
                raise

    return wrapper


@retry_if_busy
def read_sys(path):
    """Read a sysfs file, retrying on EBUSY.

    :param path: Absolute or relative path. Relative paths are
        resolved under ``/sys``.
    :returns: The raw file content as a string.
    :raises cyborg.common.exception.FileNotFound: If the file
        cannot be read (permission denied, missing, etc.).
    :raises cyborg.common.exception.DeviceBusy: If the file is
        busy after exhausting retries.
    """
    full_path = pathlib.Path(path)
    if not full_path.is_absolute():
        full_path = SYS / full_path
    try:
        return full_path.read_text()
    except OSError as exc:
        if exc.errno == errno.EBUSY:
            raise exception.DeviceBusy(file_path=str(full_path)) from exc
        raise exception.FileNotFound(file_path=str(full_path)) from exc
    except ValueError as exc:
        raise exception.FileNotFound(file_path=str(full_path)) from exc


@retry_if_busy
def write_sys(path, data):
    """Write to a sysfs file, retrying on EBUSY.

    :param path: Absolute or relative path. Relative paths are
        resolved under ``/sys``.
    :param data: The string data to write.
    :raises cyborg.common.exception.FileNotFound: If the file
        cannot be written (permission denied, missing, etc.).
    :raises cyborg.common.exception.DeviceBusy: If the file is
        busy after exhausting retries.
    """
    full_path = pathlib.Path(path)
    if not full_path.is_absolute():
        full_path = SYS / full_path
    try:
        full_path.write_text(data)
    except OSError as exc:
        if exc.errno == errno.EBUSY:
            raise exception.DeviceBusy(file_path=str(full_path)) from exc
        raise exception.FileNotFound(file_path=str(full_path)) from exc
    except ValueError as exc:
        raise exception.FileNotFound(file_path=str(full_path)) from exc
