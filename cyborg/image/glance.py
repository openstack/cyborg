# Copyright 2010 OpenStack Foundation
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

"""Implementation of an image service that uses Glance as the backend."""

import inspect
import os
import re
import stat
import time

import glanceclient
import glanceclient.exc

from keystoneauth1 import loading as ks_loading
from oslo_log import log as logging
from oslo_utils import excutils

import cyborg.conf

from cyborg import service_auth
from cyborg.common import exception
from cyborg.common import utils


LOG = logging.getLogger(__name__)
CONF = cyborg.conf.CONF

_SESSION = None


def _session_and_auth(context):
    # Session is cached, but auth needs to be pulled from context each time.
    global _SESSION

    if not _SESSION:
        _SESSION = ks_loading.load_session_from_conf_options(
            CONF, cyborg.conf.glance.glance_group.name
        )

    auth = service_auth.get_auth_plugin(context)

    return _SESSION, auth


def _glanceclient_from_endpoint(context, endpoint, version):
    sess, auth = _session_and_auth(context)

    return glanceclient.Client(
        version,
        session=sess,
        auth=auth,
        endpoint_override=endpoint,
        global_request_id=context.global_id,
    )


def _endpoint_from_image_ref(image_href):
    """Return the image_ref and guessed endpoint from an image url.

    :param image_href: href of an image
    :returns: a tuple of the form (image_id, endpoint_url)
    """
    parts = image_href.split('/')
    image_id = parts[-1]
    # the endpoint is everything in the url except the last 3 bits
    # which are version, 'images', and image_id
    endpoint = '/'.join(parts[:-3])
    return (image_id, endpoint)


def get_api_server(context):
    """Get the service endpoint."""
    sess, auth = _session_and_auth(context)
    ksa_adap = utils.get_ksa_adapter(
        cyborg.conf.glance.DEFAULT_SERVICE_TYPE,
        ksa_auth=auth,
        ksa_session=sess,
        min_version='2.0',
        max_version='2.latest',
    )
    endpoint = utils.get_endpoint(ksa_adap)
    if endpoint:
        # NOTE(mriedem): Due to python-glanceclient bug 1707995 we have
        # to massage the endpoint URL otherwise it won't work properly.
        # We can't use glanceclient.common.utils.strip_version because
        # of bug 1748009.
        endpoint = re.sub(r'/v\d+(\.\d+)?/?$', '/', endpoint)

    return endpoint


class GlanceClientWrapper:
    """Glance client wrapper class that implements retries."""

    def __init__(self, context=None, endpoint=None):
        version = 2
        if endpoint is not None:
            self.client = self._create_static_client(
                context, endpoint, version
            )
        else:
            self.client = None
        self.api_server = None

    def _create_static_client(self, context, endpoint, version):
        """Create a client that we'll use for every call."""
        self.api_server = str(endpoint)
        return _glanceclient_from_endpoint(context, endpoint, version)

    def _create_onetime_client(self, context, version):
        """Create a client that will be used for one call."""
        if self.api_server is None:
            self.api_server = get_api_server(context)
        return _glanceclient_from_endpoint(context, self.api_server, version)

    def call(self, context, version, method, *args, **kwargs):
        """Call a glance client method.  If we get a connection error,
        retry the request according to CONF.glance.num_retries.
        """
        retry_excs = (
            glanceclient.exc.HTTPServiceUnavailable,
            glanceclient.exc.InvalidEndpoint,
            glanceclient.exc.CommunicationError,
        )
        num_attempts = 1 + CONF.glance.num_retries

        for attempt in range(1, num_attempts + 1):
            client = self.client or self._create_onetime_client(
                context, version
            )
            try:
                controller = getattr(
                    client, kwargs.pop('controller', 'images')
                )
                result = getattr(controller, method)(*args, **kwargs)
                if inspect.isgenerator(result):
                    # Convert generator results to a list, so that we can
                    # catch any potential exceptions now and retry the call.
                    return list(result)
                return result
            except retry_excs as e:
                if attempt < num_attempts:
                    extra = "retrying"
                else:
                    extra = 'done trying'

                LOG.exception(
                    "Error contacting glance server "
                    "'%(server)s' for '%(method)s', "
                    "%(extra)s.",
                    {
                        'server': self.api_server,
                        'method': method,
                        'extra': extra,
                    },
                )
                if attempt == num_attempts:
                    raise exception.GlanceConnectionFailed(
                        server=str(self.api_server), reason=str(e)
                    )
                time.sleep(1)


class GlanceImageServiceV2:
    """Provides storage and retrieval of disk image objects within Glance."""

    def __init__(self, client=None):
        self._client = client or GlanceClientWrapper()

    @staticmethod
    def _safe_fsync(fh):
        """Performs os.fsync on a filehandle only if it is supported.

        fsync on a pipe, FIFO, or socket raises OSError with EINVAL.  This
        method discovers whether the target filehandle is one of these types
        and only performs fsync if it isn't.

        :param fh: Open filehandle (not a path or fileno) to maybe fsync.
        """
        fileno = fh.fileno()
        mode = os.fstat(fileno).st_mode
        # A pipe answers True to S_ISFIFO
        if not any(check(mode) for check in (stat.S_ISFIFO, stat.S_ISSOCK)):
            os.fsync(fileno)

    def download(self, context, image_id, data=None, dst_path=None):
        """Calls out to Glance for data and writes data."""
        try:
            image_chunks = self._client.call(context, 2, 'data', image_id)
        except (
            glanceclient.exc.HTTPForbidden,
            glanceclient.exc.HTTPUnauthorized,
        ):
            raise exception.ImageNotAuthorized(image_id=image_id)
        except glanceclient.exc.HTTPNotFound:
            raise exception.ResourceNotFound(
                resource='Image', msg='with uuid=%s' % image_id
            )
        except glanceclient.exc.HTTPBadRequest as e:
            raise exception.ImageBadRequest(image_id=image_id, response=str(e))

        if image_chunks.wrapped is None:
            raise exception.ImageUnacceptable(
                image_id=image_id,
                reason='Image has no associated data',
            )

        close_file = False
        if data is None and dst_path:
            data = open(dst_path, 'wb')
            close_file = True

        if data is None:
            return image_chunks
        else:
            try:
                for chunk in image_chunks:
                    data.write(chunk)
            except Exception as ex:
                with excutils.save_and_reraise_exception():
                    LOG.error(
                        "Error writing to %(path)s: %(exception)s",
                        {'path': dst_path, 'exception': ex},
                    )
            finally:
                if close_file:
                    # Ensure that the data is pushed all the way down to
                    # persistent storage. This ensures that in the event of a
                    # subsequent host crash we don't have running instances
                    # using a corrupt backing file.
                    data.flush()
                    self._safe_fsync(data)
                    data.close()


def get_remote_image_service(context, image_href):
    """Create an image_service and parse the id from the given image_href.

    The image_href param can be an href of the form
    'http://example.com:9292/v1/images/b8b2c6f7-7345-4e2f-afa2-eedaba9cbbe3',
    or just an id such as 'b8b2c6f7-7345-4e2f-afa2-eedaba9cbbe3'. If the
    image_href is a standalone id, then the default image service is returned.

    :param image_href: href that describes the location of an image
    :returns: a tuple of the form (image_service, image_id)

    """
    # NOTE(bcwaldon): If image_href doesn't look like a URI, assume its a
    # standalone image ID
    if '/' not in str(image_href):
        image_service = get_default_image_service()
        return image_service, image_href

    try:
        (image_id, endpoint) = _endpoint_from_image_ref(image_href)
        glance_client = GlanceClientWrapper(context=context, endpoint=endpoint)
    except ValueError:
        raise exception.InvalidImageRef(image_href=image_href)

    image_service = GlanceImageServiceV2(client=glance_client)
    return image_service, image_id


def get_default_image_service():
    return GlanceImageServiceV2()
