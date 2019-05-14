import abc
import six


@six.add_metaclass(abc.ABCMeta)
class GenericDriver(object):

    @abc.abstractmethod
    def discover(self):
        """Discover a specified accelerator.

        :return: the list of driver device objs
        """
        pass

    @abc.abstractmethod
    def update(self, control_path, image_path):
        """Update the device firmware with specific image.

        :param control_path: the image update control path of device.
        :param image_path: The image path of the firmware binary.

        :return: True if update successfully otherwise False
        """
        pass

    @abc.abstractmethod
    def get_stats(self):
        """Collects device stats.

        It is used to collect information from the device about the device
        capabilities. Such as performance info like temprature, power, volt,
        packet_count info.

        :return: The stats info of the device. The format should follow the
        current Cyborg device-deploy-accelerator model
        """
        pass
