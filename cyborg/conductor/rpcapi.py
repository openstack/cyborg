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


class RPCEndpoint(object):

    # Conductor functions exposed for external calls
    # Mostly called by the API?
    def __init__(self):
        pass

    # Returns a list of all accelerators managed by Cyborg
    def list_accelerators(self, ctxt):
        pass

    # Returns an accelerator from the DB
    def get_accelerator(self, ctxt, accelerator):
        pass

    # Deletes an accelerator from the DB and from the agent that hosts it
    def delete_accelerator(self, ctxt, accelerator):
        pass

    # Updates an accelerator both in the DB and on the agent that hosts it
    def update_accelerator(self, ctxt, accelerator):
        pass

    # Runs discovery on either a single agent or all agents
    def discover_accelerators(self, ctxt, agent_id=None):
        pass
