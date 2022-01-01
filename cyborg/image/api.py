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

from cyborg.image import glance
from oslo_log import log

LOG = log.getLogger(__name__)


class API(object):

    """Responsible for exposing a relatively stable internal API for other
    modules in Cyborg to retrieve information about accelerator images.
    """

    def _get_session_and_image_id(self, context, id_or_uri):
        """Returns a tuple of (session, image_id). If the supplied `id_or_uri`
        is an image ID, then the default client session will be returned
        for the context's user, along with the image ID. If the supplied
        `id_or_uri` parameter is a URI, then a client session connecting to
        the URI's image service endpoint will be returned along with a
        parsed image ID from that URI.

        :param context: The `cyborg.context.Context` object for the request
        :param id_or_uri: A UUID identifier or an image URI to look up image
                          information for.
        """
        return glance.get_remote_image_service(context, id_or_uri)

    def download(self, context, id_or_uri, data=None, dest_path=None):
        """Transfer image bits from Glance or a known source location to the
        supplied destination filepath.

        :param context: The `cyborg.context.RequestContext` object for the
                        request
        :param id_or_uri: A UUID identifier or an image URI to look up image
                          information for.
        :param data: A file object to use in downloading image data.
        :param dest_path: Filepath to transfer image bits to.

        Note that because of the poor design of the
        `glance.ImageService.download` method, the function returns different
        things depending on what arguments are passed to it. If a data argument
        is supplied but no dest_path is specified (only done in the XenAPI virt
        driver's image.utils module) then None is returned from the method. If
        the data argument is not specified but a destination path *is*
        specified, then a writeable file handle to the destination path is
        constructed in the method and the image bits written to that file, and
        again, None is returned from the method. If no data argument is
        supplied and no dest_path argument is supplied (VMWare and XenAPI virt
        drivers), then the method returns an iterator to the image bits that
        the caller uses to write to wherever location it wants.

        I think the above points to just how hacky/wacky all of this code is,
        and the reason it needs to be cleaned up and standardized across the
        virt driver callers.
        """

        session, image_id = self._get_session_and_image_id(context, id_or_uri)
        return session.download(context, image_id, data=data,
                                dst_path=dest_path)
