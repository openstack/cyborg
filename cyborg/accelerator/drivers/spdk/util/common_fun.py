"""
Utils for SPDK driver.
"""

import glob
import os
import re

from oslo_config import cfg
from oslo_log import log as logging

from cyborg.accelerator import configuration
from cyborg.accelerator.common import exception
from cyborg.accelerator.drivers.spdk.util.pyspdk.py_spdk import PySPDK
from cyborg.common.i18n import _
from pyspdk.nvmf_client import NvmfTgt
from pyspdk.vhost_client import VhostTgt

LOG = logging.getLogger(__name__)

accelerator_opts = [
    cfg.StrOpt('spdk_conf_file',
               default='/etc/cyborg/spdk.conf',
               help=_('SPDK conf file to be used for the SPDK driver')),

    cfg.StrOpt('accelerator_servers',
               default=['vhost', 'nvmf', 'iscsi'],
               help=_('A list of accelerator servers to enable by default')),

    cfg.StrOpt('spdk_dir',
               default='/home/wewe/spdk',
               help=_('The SPDK directory is /home/{user_name}/spdk')),

    cfg.StrOpt('device_type',
               default='NVMe',
               help=_('Backend device type is NVMe by default')),

    cfg.BoolOpt('remoteable',
                default=False,
                help=_('Remoteable is false by default'))
]

CONF = cfg.CONF
CONF.register_opts(accelerator_opts, group=configuration.SHARED_CONF_GROUP)

config = configuration.Configuration(accelerator_opts)
config.append_config_values(accelerator_opts)
SERVERS = config.safe_get('accelerator_servers')
SERVERS_PATTERN = re.compile("|".join(["(%s)" % s for s in SERVERS]))
SPDK_SERVER_APP_DIR = os.path.join(config.safe_get('spdk_dir'), 'app/')


def discover_servers():
    """Discover backend servers according to the CONF

    :returns: server list.
    """
    servers = set()
    for p in glob.glob1(SPDK_SERVER_APP_DIR, "*"):
        m = SERVERS_PATTERN.match(p)
        if m:
            servers.add(m.group())
    return list(servers)


def delete_bdev(py, accelerator, name):
    """Delete a blockdev

    :param py: py_client.
    :param accelerator: accelerator.
    :param name: Blockdev name to be deleted.
    """
    acc_client = get_accelerator_client(py, accelerator)
    acc_client.delete_bdev(name)


def kill_instance(py, accelerator, sig_name):
    """Send signal to instance

    :param py: py_client.
    :param accelerator: accelerator.
    :param sig_name: signal will be sent to server.
    """
    acc_client = get_accelerator_client(py, accelerator)
    acc_client.kill_instance(sig_name)


def construct_aio_bdev(py, accelerator, filename, name, block_size):
    """Add a bdev with aio backend

    :param py: py_client.
    :param accelerator: accelerator.
    :param filename: Path to device or file (ex: /dev/sda).
    :param name: Block device name.
    :param block_size: Block size for this bdev.
    :return: name.
    """
    acc_client = get_accelerator_client(py, accelerator)
    acc_client.construct_aio_bdev(filename, name, block_size)
    return name


def construct_error_bdev(py, accelerator, basename):
    """Add a bdev with error backend

    :param py: py_client.
    :param accelerator: accelerator.
    :param basename: Path to device or file (ex: /dev/sda).
    """
    acc_client = get_accelerator_client(py, accelerator)
    acc_client.construct_error_bdev(basename)


def construct_nvme_bdev(py,
                        accelerator,
                        name,
                        trtype,
                        traddr,
                        adrfam,
                        trsvcid,
                        subnqn
                        ):
    """Add a bdev with nvme backend

    :param py: py_client.
    :param accelerator: accelerator.
    :param name: Name of the bdev.
    :param trtype: NVMe-oF target trtype: e.g., rdma, pcie.
    :param traddr: NVMe-oF target address: e.g., an ip address
    or BDF.
    :param adrfam: NVMe-oF target adrfam: e.g., ipv4, ipv6, ib,
    fc, intra_host.
    :param trsvcid: NVMe-oF target trsvcid: e.g., a port number.
    :param subnqn: NVMe-oF target subnqn.
    :return: name.
    """
    acc_client = get_accelerator_client(py, accelerator)
    acc_client.construct_nvme_bdev(name,
                                   trtype,
                                   traddr,
                                   adrfam,
                                   trsvcid,
                                   subnqn
                                   )
    return name


def construct_null_bdev(py,
                        accelerator,
                        name,
                        total_size,
                        block_size
                        ):
    """Add a bdev with null backend

    :param py: py_client.
    :param accelerator: accelerator.
    :param name: Block device name.
    :param total_size: Size of null bdev in MB (int > 0).
    :param block_size: Block size for this bdev.
    :return: name.
    """
    acc_client = get_accelerator_client(py, accelerator)
    acc_client.construct_null_bdev(name, total_size, block_size)
    return name


def get_py_client(server):
    """Get the py_client instance

    :param server: server.
    :return: Boolean.
    :raise: InvalidAccelerator.
    """
    if server in SERVERS:
        py = PySPDK(server)
        return py
    else:
        msg = (_("Could not find %s accelerator") % server)
        raise exception.InvalidAccelerator(msg)


def check_for_setup_error(py, server):
    """Check server's status

    :param py: py_client.
    :param server: server.
    :return: Boolean.
    :raise: AcceleratorException.
    """
    if py.is_alive():
        return True
    else:
        msg = (_("%s accelerator is down") % server)
        raise exception.AcceleratorException(msg)


def get_accelerator_client(py, accelerator):
    """Get the specific client that communicates with server

    :param py: py_client.
    :param accelerator: accelerator.
    :return: acc_client.
    :raise: InvalidAccelerator.
    """
    acc_client = None
    if accelerator == 'vhost':
        acc_client = VhostTgt(py)
        return acc_client
    elif accelerator == 'nvmf':
        acc_client = NvmfTgt(py)
        return acc_client
    else:
        exc_msg = (_("accelerator_client %(acc_client) is missing")
                   % acc_client)
        raise exception.InvalidAccelerator(exc_msg)
