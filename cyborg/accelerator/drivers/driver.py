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

import abc


class GenericDriver(object, metaclass=abc.ABCMeta):

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
