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

"""
Main abstraction layer for retrieving and storing information about accelerator
images used by the cyborg agent layer.
"""

from oslo_log import log

from cyborg.image import glance


LOG = log.getLogger(__name__)


class API:
    """Responsible for exposing a relatively stable internal API for other
    modules in Cyborg to retrieve information about accelerator images.
    """

    def _get_session_and_image_id(self, context, id_or_uri):
        """Returns a tuple of (image_service, image_id).

        If the supplied `id_or_uri` is a URI, only the image UUID is
        extracted; the configured catalog endpoint is always used.

        :param context: The `cyborg.context.Context` object for the request
        :param id_or_uri: A UUID identifier or an image URI to look up image
                          information for.
        """
        return glance.get_remote_image_service(context, id_or_uri)

    def download(self, context, id_or_uri, data=None, dest_path=None):
        """Transfer image bits from Glance to the supplied destination.

        :param context: The `cyborg.context.RequestContext` object for the
                        request
        :param id_or_uri: A UUID identifier or an image URI to look up image
                          information for.
        :param data: A file object to use in downloading image data.
        :param dest_path: Filepath to transfer image bits to.
        """

        session, image_id = self._get_session_and_image_id(context, id_or_uri)
        return session.download(
            context, image_id, data=data, dst_path=dest_path
        )
