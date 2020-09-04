# Copyright (c) 2019 Intel, Inc.
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


# This is the version 2 API
BASE_VERSION = 2


# Here goes a short log of changes in every version.
# Refer to cyborg/api/rest_api-version-history.rst for a detailed
# explanation of what each version contains.
#
# v2.0: Initial minor version.
# v2.1: Add project_id for arq patch
MINOR_0_INITIAL_VERSION = 0
MINOR_1_PROJECT_ID = 1


# When adding another version, update:
# - MINOR_MAX_VERSION
# - cyborg/api/rest_api-version-history.rst with a detailed
#   explanation of what changed in the new version


MINOR_MAX_VERSION = MINOR_1_PROJECT_ID

# String representations of the minor and maximum versions
_MIN_VERSION_STRING = '{}.{}'.format(BASE_VERSION, MINOR_0_INITIAL_VERSION)
_MAX_VERSION_STRING = '{}.{}'.format(BASE_VERSION, MINOR_MAX_VERSION)


def service_type_string():
    return 'accelerator'


def min_version_string():
    """Returns the minimum supported API version (as a string)"""
    return _MIN_VERSION_STRING


def max_version_string():
    """Returns the maximum supported API version (as a string).

    If the service is pinned, the maximum API version is the pinned
    version. Otherwise, it is the maximum supported API version.

    """
    return _MAX_VERSION_STRING
