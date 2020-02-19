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

from cyborg.common import exception
from cyborg.tests import base


class TestException(base.TestCase):
    def _get_all_exception_classes(self):
        classes = []

        base_class = exception.CyborgException

        for name in dir(exception):
            item = getattr(exception, name)
            if item == base_class:
                continue
            elif type(item) != type:
                continue
            elif not issubclass(item, base_class):
                continue
            classes.append(item)

        return classes

    def test_all_exceptions(self):
        bad_classes = []
        for cls in self._get_all_exception_classes():
            parent = cls.mro()[1]
            if parent._msg_fmt == cls._msg_fmt:
                bad_classes.append(cls.__name__)

        self.assertEqual([], bad_classes,
                         'Exception classes %s do not '
                         'set _msg_fmt' % ', '.join(bad_classes))
