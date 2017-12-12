# Copyright 2017 Huawei Technologies Co.,LTD.
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

"""Cyborg db test utilities."""


def get_test_accelerator(**kw):
    return {
        'name': kw.get('name', 'name'),
        'description': kw.get('description', 'description'),
        'device_type': kw.get('device_type', 'device_type'),
        'acc_type': kw.get('acc_type', 'acc_type'),
        'acc_capability': kw.get('acc_capability', 'acc_capability'),
        'vendor_id': kw.get('vendor_id', 'vendor_id'),
        'product_id': kw.get('product_id', 'product_id'),
        'remotable': kw.get('remotable', 1),
        'project_id': kw.get('project_id', 'b492a6fb12964ae3bd291ce585107d48'),
        'user_id': kw.get('user_id', '7009409e21614d1db1ef7a8c5ee101d8'),
    }
