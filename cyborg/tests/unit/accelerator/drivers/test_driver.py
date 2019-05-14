import six

from cyborg.tests import base
from cyborg.accelerator.drivers.driver import GenericDriver


class WellDoneDriver(GenericDriver):
    def discover(self):
        pass

    def update(self, control_path, image_path):
        pass

    def get_stats(self):
        pass


class NotCompleteDriver(GenericDriver):
    def discover(self):
        pass


class TestGenericDriver(base.TestCase):

    def test_generic_driver(self):
        driver = WellDoneDriver()
        # Can't instantiate abstract class NotCompleteDriver with
        # abstract methods get_stats, update
        result = self.assertRaises(TypeError, NotCompleteDriver)
        self.assertIn("Can't instantiate abstract class",
                      six.text_type(result))
