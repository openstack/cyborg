"""
Cyborg SPDK driver modules implementation.
"""

from oslo_log import log as logging
LOG = logging.getLogger(__name__)


class SPDKDRIVER(object):
    """SPDKDRIVER

        This is just a virtual SPDK drivers interface.
        SPDK-based app server should implement their specific drivers.
    """
    @classmethod
    def create(cls, server, *args, **kwargs):
        for subclass in cls.__subclasses__():
            if server == subclass.SERVER:
                return subclass(*args, **kwargs)
        raise LookupError("Could not find the driver for server %s" % server)

    def __init__(self, *args, **kwargs):
        super(SPDKDRIVER, self).__init__()

    def discover_accelerator(self):
        """Discover a backend accelerator

        :return: accelerator list.
        """
        raise NotImplementedError('Subclasses must implement this method.')

    def install_accelerator(self, driver_id, driver_type):
        """install a backend accelerator

        :param driver_id: driver id.
        :param driver_type: driver type.

        :raise: NotImplementedError.
        """
        raise NotImplementedError('Subclasses must implement this method.')

    def uninstall_accelerator(self, driver_id, driver_type):
        """uninstall a backend accelerator

        :param driver_id: driver id.
        :param driver_type: driver type.

        :raise: NotImplementedError.
        """
        raise NotImplementedError('Subclasses must implement this method.')

    def accelerator_list(self):
        """Discover a backend accelerator list

        :return: accelerator list.
        :raise: NotImplementedError.
        """
        raise NotImplementedError('Subclasses must implement this method.')

    def update(self, driver_type, **kwargs):
        """update

        :param driver_type: driver type.
        :param kwargs: kwargs.
        :raise: NotImplementedError.
        """
        raise NotImplementedError('Subclasses must implement this method.')

    def attach_instance(self, instance_id):
        """attach a backend instance

        :param instance_id: instance id.
        :return: instance.
        :raise: NotImplementedError.
        """
        raise NotImplementedError('Subclasses must implement this method.')

    def detach_instance(self, instance_id):
        """detach a backend instance

        :param instance_id: instance id.
        :return: instance.
        :raise: NotImplementedError.
        """
        raise NotImplementedError('Subclasses must implement this method.')
