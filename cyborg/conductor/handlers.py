# -*- coding: utf-8 -*-

#
# Licensed under the Apache License, Version 2.0 (the "License"); you may
# not use this file except in compliance with the License. You may obtain
# a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
# WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
# License for the specific language governing permissions and limitations
# under the License.


class NotificationEndpoint(object):
    # filter_rule = messaging.NotificationFilter(publisher_id='^cyborg.*')

    # We have an update from an agent and we need to add it to our in memory
    # cache of accelerator objects and schedule a flush to the database
    def update(self, ctxt, publisher_id, event_type, payload, metadata):
        print("Got update")
        return True

    # We have an info message from an agent, anything that wouldn't
    # go into the db but needs to be communicated goes here
    def info(self, ctxt, publisher_id, event_type, payload, metadata):
        print("Got info")
        return True

    # We have a warning from an agent, we may take some action
    def warn(self, ctxt, publisher_id, event_type, payload, metadata):
        print("Got warn")
        return True

    # We have an error from an agent, we must take some action
    def error(self, ctxt, publisher_id, event_type, payload, metadata):
        print("Got error")
        return True
