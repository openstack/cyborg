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

"""Helpers for functional tests: WSGI app creation and test data seeding."""

from unittest import mock

import pecan.testing

from oslo_utils import uuidutils
from pecan import hooks

from cyborg import objects
from cyborg.api import hooks as cyborg_hooks


class FakeConductorAPIHook(hooks.PecanHook):
    """Provide a mock conductor_api to avoid RPC initialization."""

    def __init__(self):
        self.conductor_api = mock.MagicMock()

    def before(self, state):
        state.request.conductor_api = self.conductor_api


def make_app():
    """Build a WebTest-wrapped Pecan app for functional tests."""
    app_config = {
        'app': {
            'root': 'cyborg.api.controllers.root.RootController',
            'modules': ['cyborg.api'],
            'acl_public_routes': ['/', '/v2'],
        },
    }
    # Replace ConductorAPIHook with our fake so setup_app() avoids RPC.
    with mock.patch.object(
        cyborg_hooks, 'ConductorAPIHook', FakeConductorAPIHook
    ):
        return pecan.testing.load_test_app(app_config)


def seed_devices(context):
    """Create a test device with a deployable and attribute."""
    dev = objects.Device(
        context,
        uuid=uuidutils.generate_uuid(),
        type='FPGA',
        vendor='0xABCD',
        model='miss model info',
        std_board_info="{'device_id': '0xabcd', 'class': 'Fake class'}",
        vendor_board_info='fake_vendor_info',
        hostname='test-node-1',
        status='enabled',
    )
    dev.create(context)

    dep = objects.Deployable(
        context,
        uuid=uuidutils.generate_uuid(),
        name='test-deployable-0',
        num_accelerators=1,
        device_id=dev.id,
        rp_uuid=uuidutils.generate_uuid(),
        driver_name='fake',
    )
    dep.create(context)

    attr = objects.Attribute(
        context,
        uuid=uuidutils.generate_uuid(),
        deployable_id=dep.id,
        key='rc',
        value='CUSTOM_ACCELERATOR_FPGA',
    )
    attr.create(context)

    return {
        'device': dev,
        'deployable': dep,
        'attribute': attr,
    }


def seed_programable_deployable(context):
    """Create a device, deployable, and controlpath ID for programming.

    The program endpoint requires a controlpath ID associated with the
    device so it can locate the FPGA control path.
    """
    dev = objects.Device(
        context,
        uuid=uuidutils.generate_uuid(),
        type='FPGA',
        vendor='0xABCD',
        model='miss model info',
        std_board_info="{'device_id': '0xabcd', 'class': 'Fake class'}",
        vendor_board_info='fake_vendor_info',
        hostname='test-node-1',
        status='enabled',
    )
    dev.create(context)

    dep = objects.Deployable(
        context,
        uuid=uuidutils.generate_uuid(),
        name='test-deployable-0',
        num_accelerators=1,
        device_id=dev.id,
        rp_uuid=uuidutils.generate_uuid(),
        driver_name='fake',
    )
    dep.create(context)

    cpid = objects.ControlpathID(
        context,
        uuid=uuidutils.generate_uuid(),
        device_id=dev.id,
        cpid_type='PCI',
        cpid_info='{"domain":"0000","bus":"0c","device":"00","function":"0"}',
    )
    cpid.create(context)

    return {
        'device': dev,
        'deployable': dep,
        'controlpath_id': cpid,
    }


def seed_device_profiles(context):
    """Create two test device profiles.

    Group keys are chosen to match doc/api_samples/ so structural
    comparison passes for every list entry.
    """
    dp1 = objects.DeviceProfile(
        context,
        uuid=uuidutils.generate_uuid(),
        name='test-dp-1',
        description='test device profile',
        groups=[
            {
                'resources:FPGA': '1',
                'trait:CUSTOM_FPGA_INSPUR': 'required',
                'accel:bitstream_id': 'd5ca2f11-3108-4426-a11c-a959987565df',
            }
        ],
    )
    dp1.create(context)

    dp2 = objects.DeviceProfile(
        context,
        uuid=uuidutils.generate_uuid(),
        name='test-dp-2',
        description='second test device profile',
        groups=[
            {
                'resources:FPGA': '1',
                'trait:CUSTOM_FPGA_C260': 'required',
            }
        ],
    )
    dp2.create(context)

    return {'device_profile': dp1, 'device_profile_2': dp2}


def seed_arqs(context, db):
    """Create two test accelerator requests.

    The first ARQ is in Initial state.  The second is Bound with an
    attach handle, matching the two entries in the list sample.
    Seeding the bound ARQ requires a device, deployable, controlpath,
    and attach handle.
    """
    # Initial ARQ
    arq_obj = objects.ExtARQ(
        context,
        arq=objects.ARQ(
            context,
            uuid=uuidutils.generate_uuid(),
            device_profile_name='test-dp-1',
            device_profile_group_id=0,
            project_id=context.project_id,
        ),
    )
    arq_obj.create(context)

    # Bound ARQ — needs device -> deployable -> attach_handle chain
    dev = objects.Device(
        context,
        uuid=uuidutils.generate_uuid(),
        type='FPGA',
        vendor='0xABCD',
        model='miss model info',
        std_board_info='{}',
        vendor_board_info='{}',
        hostname='test-node-1',
        status='enabled',
    )
    dev.create(context)

    dep = objects.Deployable(
        context,
        uuid=uuidutils.generate_uuid(),
        name='test-bound-deployable',
        num_accelerators=1,
        device_id=dev.id,
        rp_uuid=uuidutils.generate_uuid(),
        driver_name='fake',
    )
    dep.create(context)

    cpid = objects.ControlpathID(
        context,
        uuid=uuidutils.generate_uuid(),
        device_id=dev.id,
        cpid_type='PCI',
        cpid_info='{}',
    )
    cpid.create(context)

    ah = objects.AttachHandle(
        context,
        uuid=uuidutils.generate_uuid(),
        deployable_id=dep.id,
        cpid_id=cpid.id,
        in_use=True,
        attach_type='TEST_PCI',
        attach_info='{"domain":"0000","bus":"0c",'
        '"device":"00","function":"0"}',
    )
    ah.create(context)

    # ExtARQ.create() forces state=Initial, so we create then
    # update state and bind fields via dbapi.
    bound_obj = objects.ExtARQ(
        context,
        arq=objects.ARQ(
            context,
            uuid=uuidutils.generate_uuid(),
            device_profile_name='test-dp-1',
            device_profile_group_id=0,
            project_id=context.project_id,
        ),
    )
    bound_obj.create(context)
    db.extarq_update(
        context,
        bound_obj.arq.uuid,
        {
            'state': 'Bound',
            'hostname': 'test-node-1',
            'device_rp_uuid': uuidutils.generate_uuid(),
            'instance_uuid': uuidutils.generate_uuid(),
            'attach_handle_id': ah.id,
            'deployable_id': dep.id,
        },
    )

    return {'arq': arq_obj.arq, 'bound_arq': bound_obj.arq}
