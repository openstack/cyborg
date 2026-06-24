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

"""Structural validation of API response samples in doc/api_samples/.

Each test hits a real Pecan/WSME endpoint backed by a SQLite database
and compares the response *structure* (keys and value types) against
the corresponding sample JSON file.  Values like UUIDs, timestamps,
and URLs are ignored — only shape matters.

Set GENERATE_SAMPLES=1 to overwrite sample files with actual responses.
"""

import os
import unittest

from cyborg.tests.functional.api import test_api_samples_base as base


SAMPLES_DIR = os.path.normpath(
    os.path.join(os.path.dirname(__file__), '../../../../doc/api_samples')
)


class TestDeviceSamples(base.ApiSampleTestBase):
    def setUp(self):
        super().setUp()
        self.uuids = self.seed_devices()

    def test_devices_list(self):
        self._check_sample(
            '/v2/devices',
            os.path.join(SAMPLES_DIR, 'devices', 'devices-list-resp.json'),
        )

    def test_devices_get_one(self):
        self._check_sample(
            f'/v2/devices/{self.uuids["device"]}',
            os.path.join(SAMPLES_DIR, 'devices', 'devices-getone-resp.json'),
        )


class TestDeployableSamples(base.ApiSampleTestBase):
    def setUp(self):
        super().setUp()
        self.uuids = self.seed_devices()

    def test_deployables_list(self):
        self._check_sample(
            '/v2/deployables',
            os.path.join(
                SAMPLES_DIR, 'deployables', 'deployables-list-resp.json'
            ),
        )

    def test_deployables_get_one(self):
        self._check_sample(
            f'/v2/deployables/{self.uuids["deployable"]}',
            os.path.join(
                SAMPLES_DIR, 'deployables', 'deployables-getone-resp.json'
            ),
        )


class TestDeviceProfileSamples(base.ApiSampleTestBase):
    def setUp(self):
        super().setUp()
        self.uuids = self.seed_device_profiles()

    def test_device_profiles_list(self):
        self._check_sample(
            '/v2/device_profiles',
            os.path.join(
                SAMPLES_DIR,
                'device_profiles',
                'device_profiles-list-resp.json',
            ),
        )

    def test_device_profiles_get_one(self):
        self._check_sample(
            f'/v2/device_profiles/{self.uuids["device_profile"]}',
            os.path.join(
                SAMPLES_DIR,
                'device_profiles',
                'device_profiles-getone-resp.json',
            ),
        )

    def test_device_profiles_get_one_v22(self):
        self._check_sample(
            f'/v2/device_profiles/{self.uuids["device_profile"]}',
            os.path.join(
                SAMPLES_DIR,
                'device_profiles',
                'v22',
                'device_profiles-getone-resp.json',
            ),
            extra_headers={'OpenStack-API-Version': 'accelerator 2.2'},
        )


class TestAttributeSamples(base.ApiSampleTestBase):
    def setUp(self):
        super().setUp()
        self.uuids = self.seed_devices()

    def test_attributes_list(self):
        self._check_sample(
            '/v2/attributes',
            os.path.join(
                SAMPLES_DIR, 'attributes', 'attributes-list-resp.json'
            ),
        )

    def test_attributes_get_one(self):
        self._check_sample(
            f'/v2/attributes/{self.uuids["attribute"]}',
            os.path.join(
                SAMPLES_DIR, 'attributes', 'attributes-getone-resp.json'
            ),
        )


class TestAcceleratorRequestSamples(base.ApiSampleTestBase):
    def setUp(self):
        super().setUp()
        self.uuids = self.seed_arqs()

    def test_arqs_list(self):
        self._check_sample(
            '/v2/accelerator_requests',
            os.path.join(
                SAMPLES_DIR,
                'accelerator_requests',
                'accelerator_requests-list-resp.json',
            ),
        )

    def test_arqs_get_one(self):
        self._check_sample(
            f'/v2/accelerator_requests/{self.uuids["arq"]}',
            os.path.join(
                SAMPLES_DIR,
                'accelerator_requests',
                'accelerator_requests-getone-resp.json',
            ),
        )


if __name__ == '__main__':
    unittest.main()
