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

import os
import stat
import time

from keystoneauth1 import exceptions as ksa_exc
from keystoneauth1 import loading as ks_loading
from openstack import connection
from openstack import exceptions as sdk_exc
from oslo_log import log as logging
from oslo_utils import excutils

from cyborg import conf
from cyborg import service_auth
from cyborg.common import exception
from cyborg.common import utils


LOG = logging.getLogger(__name__)
CONF = conf.CONF

_SESSION = None


def _session_and_auth(context):
    # Session is cached, but auth needs to be pulled from context each time.
    global _SESSION

    if not _SESSION:
        _SESSION = ks_loading.load_session_from_conf_options(
            CONF, conf.glance.glance_group.name
        )

    auth = service_auth.get_auth_plugin(context)

    return _SESSION, auth


def _get_connection(context):
    """Create an openstacksdk Connection to the image service.

    Endpoint discovery is done via a keystoneauth Adapter so that ``[glance]``
    config options (``endpoint_override``, ``valid_interfaces``) are respected
    and version negotiation gets the explicit constraints it needs. The
    resolved endpoint is passed as ``image_endpoint_override`` and the API
    version is pinned to ``'2'``, bypassing the SDK's own ``from_conf``
    negotiation which fails because the ``[glance]`` config group registers
    dummy version opts. This follows the same pattern used by Ironic (see
    ``ironic/common/image_service.py``).
    """
    sess, auth = _session_and_auth(context)
    ksa_adap = utils.get_ksa_adapter(
        conf.glance.DEFAULT_SERVICE_TYPE,
        ksa_auth=auth,
        ksa_session=sess,
        min_version='2.0',
        max_version='2.latest',
    )
    endpoint = utils.get_endpoint(ksa_adap)

    # The Connection needs a session with auth baked in (unlike the
    # KSA adapter, which accepts auth separately).
    authed_sess = ks_loading.load_session_from_conf_options(
        CONF, conf.glance.glance_group.name, auth=auth
    )
    return connection.Connection(
        session=authed_sess,
        image_endpoint_override=endpoint,
        image_api_version='2',
    ).global_request(context.global_id)


class GlanceImageServiceV2:
    """Provides storage and retrieval of disk image objects within Glance."""

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

    def _download_data(self, context, image_id):
        """Download image data, retrying on connection failures.

        :returns: a streaming ``requests.Response``.
        :raises: ImageNotAuthorized, ResourceNotFound, ImageBadRequest,
                 GlanceConnectionFailed
        """
        num_attempts = 1 + CONF.glance.num_retries
        conn = _get_connection(context)

        for attempt in range(1, num_attempts + 1):
            try:
                resp = conn.image.download_image(image_id, stream=True)
            except sdk_exc.ForbiddenException:
                raise exception.ImageNotAuthorized(image_id=image_id)
            except sdk_exc.NotFoundException:
                raise exception.ResourceNotFound(
                    resource='Image',
                    msg='with uuid=%s' % image_id,
                )
            except sdk_exc.BadRequestException as e:
                raise exception.ImageBadRequest(
                    image_id=image_id, response=str(e)
                )
            except sdk_exc.HttpException as e:
                status = getattr(e, 'status_code', None)
                if status == 401:
                    raise exception.ImageNotAuthorized(image_id=image_id)
                if status == 503 and attempt < num_attempts:
                    LOG.exception("Error contacting glance server, retrying.")
                    time.sleep(1)
                    continue
                raise exception.GlanceConnectionFailed(
                    server='image service', reason=str(e)
                )
            except (sdk_exc.SDKException, ksa_exc.ConnectionError) as e:
                if attempt < num_attempts:
                    LOG.exception("Error contacting glance server, retrying.")
                    time.sleep(1)
                    continue
                raise exception.GlanceConnectionFailed(
                    server='image service', reason=str(e)
                )

            # The SDK may not raise on HTTP errors from the file download (GET
            # /v2/images/{id}/file) even though it does for the metadata fetch.
            # Check the status here so we don't silently stream an error body
            # as image data.
            status = resp.status_code
            if status >= 400:
                resp.close()
                if status in (401, 403):
                    raise exception.ImageNotAuthorized(image_id=image_id)
                if status == 404:
                    raise exception.ResourceNotFound(
                        resource='Image',
                        msg='with uuid=%s' % image_id,
                    )
                if status == 400:
                    raise exception.ImageBadRequest(
                        image_id=image_id, response='HTTP 400'
                    )
                if status == 503 and attempt < num_attempts:
                    LOG.error(
                        "Error contacting glance server (HTTP %s), retrying.",
                        status,
                    )
                    time.sleep(1)
                    continue
                raise exception.GlanceConnectionFailed(
                    server='image service',
                    reason='HTTP %s' % status,
                )

            return resp

    def download(self, context, image_id, data=None, dst_path=None):
        """Calls out to Glance for data and writes data."""
        resp = self._download_data(context, image_id)

        if resp.status_code == 204:
            resp.close()
            raise exception.ImageUnacceptable(
                image_id=image_id,
                reason='Image has no associated data',
            )

        close_file = False
        if data is None and dst_path:
            data = open(dst_path, 'wb')
            close_file = True

        if data is None:
            return resp

        try:
            for chunk in resp.iter_content(chunk_size=1024 * 1024):
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
                # persistent storage. This ensures that in the event of
                # a subsequent host crash we don't have running
                # instances using a corrupt backing file.
                data.flush()
                self._safe_fsync(data)
                data.close()


def get_remote_image_service(context, image_href):
    """Create an image_service and parse the id from the given image_href.

    The image_href param can be an href of the form
    'http://example.com:9292/v2/images/b8b2c6f7-7345-4e2f-afa2-eedaba9cbbe3',
    or just an id such as 'b8b2c6f7-7345-4e2f-afa2-eedaba9cbbe3'. If the
    image_href is a standalone id, then the default image service is returned.

    :param image_href: href that describes the location of an image
    :returns: a tuple of the form (image_service, image_id)
    """
    # NOTE(bcwaldon): If image_href doesn't look like a URI, assume its a
    # standalone image ID
    if '/' not in str(image_href):
        return get_default_image_service(), image_href

    # Extract the image id (last path component) from the URL.
    image_id = image_href.split('/')[-1]
    return GlanceImageServiceV2(), image_id


def get_default_image_service():
    return GlanceImageServiceV2()
