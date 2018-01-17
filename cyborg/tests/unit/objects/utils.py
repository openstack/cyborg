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

"""Cyborg object test utilities."""

from cyborg import objects
from cyborg.tests.unit.db import utils as db_utils


def get_test_accelerator(ctxt, **kw):
    """Return an Accelerator object with appropriate attributes.

    NOTE: The object leaves the attributes marked as changed, such
    that a create() could be used to commit it to the DB.
    """
    test_acc = db_utils.get_test_accelerator(**kw)
    obj_acc = objects.Accelerator(ctxt, **test_acc)
    return obj_acc


def create_test_accelerator(ctxt, **kw):
    """Create and return a test accelerator object.

    Create an accelerator in the DB and return an Accelerator object with
    appropriate attributes.
    """
    acc = get_test_accelerator(ctxt, **kw)
    acc.create(ctxt)
    return acc
