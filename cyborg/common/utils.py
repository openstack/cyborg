# Copyright 2017 Huawei Technologies Co.,LTD.
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

"""Utilities and helper functions."""

from concurrent.futures import ThreadPoolExecutor as CFThreadPoolExecutor
from functools import wraps
import queue
import time
import traceback

from keystoneauth1 import exceptions as ks_exc
from keystoneauth1 import loading as ks_loading
from openstack import connection
from openstack import exceptions as sdk_exc
from os_service_types import service_types
from oslo_concurrency import lockutils
from oslo_log import log

from cyborg.common import exception
from cyborg.common.i18n import _
import cyborg.conf


LOG = log.getLogger(__name__)

synchronized = lockutils.synchronized_with_prefix('cyborg-')
_SERVICE_TYPES = service_types.ServiceTypes()
CONF = cyborg.conf.CONF


def safe_rstrip(value, chars=None):
    """Removes trailing characters from a string if that does not make it empty

    :param value: A string value that will be stripped.
    :param chars: Characters to remove.
    :return: Stripped value.

    """
    if not isinstance(value, str):
        LOG.warning("Failed to remove trailing character. Returning "
                    "original object. Supplied object is not a string: "
                    "%s,", value)
        return value

    return value.rstrip(chars) or value


def get_ksa_adapter(service_type, ksa_auth=None, ksa_session=None,
                    min_version=None, max_version=None):
    """Construct a keystoneauth1 Adapter for a given service type.

    We expect to find a conf group whose name corresponds to the service_type's
    project according to the service-types-authority.  That conf group must
    provide at least ksa adapter options.  Depending how the result is to be
    used, ksa auth and/or session options may also be required, or the relevant
    parameter supplied.

    :param service_type: String name of the service type for which the Adapter
                         is to be constructed.
    :param ksa_auth: A keystoneauth1 auth plugin. If not specified, we attempt
                     to find one in ksa_session.  Failing that, we attempt to
                     load one from the conf.
    :param ksa_session: A keystoneauth1 Session.  If not specified, we attempt
                        to load one from the conf.
    :param min_version: The minimum major version of the adapter's endpoint,
                        intended to be used as the lower bound of a range with
                        max_version.
                        If min_version is given with no max_version it is as
                        if max version is 'latest'.
    :param max_version: The maximum major version of the adapter's endpoint,
                        intended to be used as the upper bound of a range with
                        min_version.
    :return: A keystoneauth1 Adapter object for the specified service_type.
    :raise: ConfGroupForServiceTypeNotFound If no conf group name could be
            found for the specified service_type.
    """
    # Get the conf group corresponding to the service type.
    confgrp = _SERVICE_TYPES.get_project_name(service_type)
    if not confgrp or not hasattr(CONF, confgrp):
        # Try the service type as the conf group.  This is necessary for e.g.
        # placement, while it's still part of the nova project.
        # Note that this might become the first thing we try if/as we move to
        # using service types for conf group names in general.
        confgrp = service_type
        if not confgrp or not hasattr(CONF, confgrp):
            raise exception.ConfGroupForServiceTypeNotFound(stype=service_type)

    # Ensure we have an auth.
    # NOTE(efried): This could be None, and that could be okay - e.g. if the
    # result is being used for get_endpoint() and the conf only contains
    # endpoint_override.
    if not ksa_auth:
        if ksa_session and ksa_session.auth:
            ksa_auth = ksa_session.auth
        else:
            ksa_auth = ks_loading.load_auth_from_conf_options(CONF, confgrp)

    if not ksa_session:
        ksa_session = ks_loading.load_session_from_conf_options(
            CONF, confgrp, auth=ksa_auth)

    return ks_loading.load_adapter_from_conf_options(
        CONF, confgrp, session=ksa_session, auth=ksa_auth,
        min_version=min_version, max_version=max_version)


def _get_conf_group(service_type):
    # Get the conf group corresponding to the service type.
    confgrp = _SERVICE_TYPES.get_project_name(service_type)
    if not confgrp or not hasattr(CONF, confgrp):
        raise exception.ConfGroupForServiceTypeNotFound(stype=service_type)
    return confgrp


def _get_auth_and_session(confgrp):
    ksa_auth = ks_loading.load_auth_from_conf_options(CONF, confgrp)
    return ks_loading.load_session_from_conf_options(
        CONF, confgrp, auth=ksa_auth)


def get_sdk_adapter(service_type, check_service=False):
    """Construct an openstacksdk-brokered Adapter for a given service type.
    We expect to find a conf group whose name corresponds to the service_type's
    project according to the service-types-authority.  That conf group must
    provide ksa auth, session, and adapter options.
    :param service_type: String name of the service type for which the Adapter
                         is to be constructed.
    :param check_service: If True, we will query the endpoint to make sure the
            service is alive, raising ServiceUnavailable if it is not.
    :return: An openstack.proxy.Proxy object for the specified service_type.
    :raise: ConfGroupForServiceTypeNotFound If no conf group name could be
            found for the specified service_type.
    :raise: ServiceUnavailable if check_service is True and the service is down
    """
    confgrp = _get_conf_group(service_type)
    sess = _get_auth_and_session(confgrp)
    try:
        conn = connection.Connection(
            session=sess, oslo_conf=CONF, service_types={service_type},
            strict_proxies=check_service)
    except sdk_exc.ServiceDiscoveryException as e:
        raise exception.ServiceUnavailable(
            _("The %(service_type)s service is unavailable: %(error)s") %
            {'service_type': service_type, 'error': str(e)})
    return getattr(conn, service_type)


def get_endpoint(ksa_adapter):
    """Get the endpoint URL represented by a keystoneauth1 Adapter.

    This method is equivalent to what

        ksa_adapter.get_endpoint()

    should do, if it weren't for a panoply of bugs.

    :param ksa_adapter: keystoneauth1.adapter.Adapter, appropriately set up
                        with an endpoint_override; or service_type, interface
                        (list) and auth/service_catalog.
    :return: String endpoint URL.
    :raise EndpointNotFound: If endpoint discovery fails.
    """
    # TODO(efried): This will be unnecessary once bug #1707993 is fixed.
    # (At least for the non-image case, until 1707995 is fixed.)
    if ksa_adapter.endpoint_override:
        return ksa_adapter.endpoint_override
    # TODO(efried): Remove this once bug #1707995 is fixed.
    if ksa_adapter.service_type == 'image':
        try:
            # LOG.warning(ksa_adapter.__dict__)
            return ksa_adapter.get_endpoint_data().catalog_url
        except AttributeError:
            # ksa_adapter.auth is a _ContextAuthPlugin, which doesn't have
            # get_endpoint_data.  Fall through to using get_endpoint().
            pass
    # TODO(efried): The remainder of this method reduces to
    # TODO(efried):     return ksa_adapter.get_endpoint()
    # TODO(efried): once bug #1709118 is fixed.
    # NOTE(efried): Id9bd19cca68206fc64d23b0eaa95aa3e5b01b676 may also do the
    #               trick, once it's in a ksa release.
    # The EndpointNotFound exception happens when _ContextAuthPlugin is in play
    # because its get_endpoint() method isn't yet set up to handle interface as
    # a list.  (It could also happen with a real auth if the endpoint isn't
    # there; but that's covered below.)
    try:
        return ksa_adapter.get_endpoint()
    except ks_exc.EndpointNotFound:
        pass

    interfaces = list(ksa_adapter.interface)
    for interface in interfaces:
        ksa_adapter.interface = interface
        try:
            return ksa_adapter.get_endpoint()
        except ks_exc.EndpointNotFound:
            pass
    raise ks_exc.EndpointNotFound(
        "Could not find requested endpoint for any of the following "
        "interfaces: %s" % interfaces)


class _Singleton(type):
    """A metaclass that creates a Singleton base class when called."""

    _instances = {}

    def __call__(cls, *args, **kwargs):
        ins = cls._instances.get(cls)
        if not ins or (
            hasattr(ins, "_reset") and isinstance(ins, cls) and ins._reset()):
            cls._instances[cls] = super(
                _Singleton, cls).__call__(*args, **kwargs)

        return cls._instances[cls]


class Singleton(_Singleton('SingletonMeta', (object,), {})):
    """A class for Singleton pattern."""

    pass


class ThreadPoolExecutor(CFThreadPoolExecutor):
    """Derived from concurrent.futures.ThreadPoolExecutor"""

    def __init__(self, *args, **kwargs):
        """Initializes a new ThreadPoolExecutor instance.

        Args:
            max_workers: The maximum number of threads that can be used to
                execute the given calls.
            thread_name_prefix: An optional name prefix to give our threads.
            initializer: A callable used to initialize worker threads.
            initargs: A tuple of arguments to pass to the initializer.
        """
        super(ThreadPoolExecutor, self).__init__(*args, **kwargs)
        # NOTE(Shaohe): py37/38 will use SimpleQueue as _work_queue, it will
        # cause hang the main thread with eventlet.monkey_patch. Change it
        # to queue._PySimpleQueue
        if hasattr(queue, "SimpleQueue") and not isinstance(
            self._work_queue, queue._PySimpleQueue):
            self._work_queue = queue._PySimpleQueue()


class ThreadWorks(Singleton):
    """Passthrough method for ThreadPoolExecutor.

    It will also grab the context from the threadlocal store and add it to
    the store on the new thread.  This allows for continuity in logging the
    context when using this method to spawn a new thread.
    """

    def __init__(self, pool_size=CONF.thread_pool_size):
        """Singleton ThreadWorks init."""
        # Ref: https://pythonhosted.org/futures/
        # NOTE(Shaohe) We can let eventlet greening ThreadPoolExecutor
        # eventlet.patcher.monkey_patch(os=False, socket=True,
        #     select=True, thread=True)
        # futures = eventlet.import_patched('concurrent.futures')
        # ThreadPoolExecutor = futures.ThreadPoolExecutor
        self.executor = ThreadPoolExecutor(max_workers=pool_size)
        self.masters = {}

    def spawn(self, func, *args, **kwargs):
        """Put a job in thread pool."""
        LOG.debug("Add an async jobs. func: %s is with parameters args: %s, "
                  "kwargs: %s", func, args, kwargs)
        future = self.executor.submit(func, *args, **kwargs)
        return future

    def spawn_master(self, func, *args, **kwargs):
        """Start a new thread for a job."""
        executor = ThreadPoolExecutor()
        # TODO(Shaohe) every submit func should be wrapped with exception catch
        job = executor.submit(func, *args, **kwargs)
        LOG.debug("Spawn master job. func: %s is with parameters args: %s, "
                  "kwargs: %s", func, args, kwargs)
        # NOTE(Shaohe) shutdown should be after job submit
        executor.shutdown(wait=False)
        # TODO(Shaohe) we need to consider resouce collection such as the
        # follow code to recoder them with timestemp?
        # master = {tag: {
        #     "executor": executor,
        #     "job": f,
        #     "timestemp": time.time(),
        #     "timeout": timeout}}
        # self.masters.update(master)
        return job

    def _reset(self):
        return self.executor._shutdown

    def map(self, func, *iterables, **kwargs):
        """Batch for job function."""
        return self.executor.map(func, *iterables, **kwargs)

    @classmethod
    def get_workers_result(cls, fs=(), **kwargs):
        """get a jobs worker result.

        Waits workers util it finish or raise any Exception.
        It will cancel the rest if one job worker fails.
        If the future is cancelled before completing then CancelledError
        will be raised.

        Parameters:
            fs: the workers list spawn return.
            timeout: Wait workers timeout, it can be an int or float.
                     If the worker hasn't yet completed then this method
                     will wait up to timeout seconds. If the worker hasn't
                     completed in timeout seconds, then a
                     concurrent.futures.TimeoutError will be raised.
                     If timeout is not specified or None, there is no limit
                     to the wait time.
        return a generator which include:
            result: the value returned by the job workers.
            exception: the exception details raised from workers.
            state: The work state.
        """

        def future_iterator():
            # Yield must be hidden in closure so that the futures are submitted
            # before the first iterator value is required.
            try:
                # reverse to keep finishing order
                fs.reverse()
                while fs:
                    # Careful not to keep a reference to the popped future
                    f = None
                    if timeout is None:
                        f = fs.pop()
                        yield f.result(), f.exception(), f._state, None
                    else:
                        f = fs.pop()
                        yield (f.result(end_time - time.time()),
                               f.exception(), f._state, None)
            except Exception as e:
                err = traceback.format_exc()
                LOG.error("Error during check the worker status. Exception "
                          "info: %s", err)
                if f:
                    LOG.error("Error during check the worker status. "
                              "Exception info: %s, result: %s, state: %s. "
                              "Reason %s", f.exception(), f._result,
                              f._state, str(e))
                    yield f._result, f.exception(), f._state, err
            finally:
                # Do best to cancel remain jobs.
                if fs:
                    LOG.info("Cancel the remained pending jobs")
                for future in fs:
                    future.cancel()

        timeout = kwargs.get('timeout')
        if timeout is not None:
            end_time = timeout + time.time()
            LOG.info("Job timeout set as %s", timeout)
        fs = list(fs)

        return future_iterator()


# info https://www.oreilly.com/library/view/python-cookbook/
# 0596001673/ch14s05.html
def format_tb(tb, limit=None):
    """Fromat traceback to a string list.

    Print the usual traceback information, followed by a listing of all the
    local variables in each frame.
    """
    if not tb:
        return []
    tbs = ['Traceback (most recent call last):\n']
    while 1:
        tbs = tbs + traceback.format_tb(tb, limit)
        if not tb.tb_next:
            break
        tb = tb.tb_next
    return tbs


def wrap_job_tb(msg="Reason: %s"):
    """Wrap a function with a is_job tag added, and catch Excetpion."""
    def _wrap_job_tb(method):
        @wraps(method)
        def _impl(self, *args, **kwargs):
            try:
                output = method(self, *args, **kwargs)
            except Exception as e:
                LOG.error(msg, str(e))
                LOG.error(traceback.format_exc())
                raise
            return output
        setattr(_impl, "is_job", True)
        return _impl
    return _wrap_job_tb


def factory_register(SuperClass, ClassName):
    """Register an concrete class to a factory Class."""
    def decorator(Class):
        # return Class
        if not hasattr(SuperClass, "_factory"):
            setattr(SuperClass, "_factory", {})
        SuperClass._factory[ClassName] = Class
        setattr(Class, "_factory_type", ClassName)
        return Class
    return decorator


class FactoryMixin(object):
    """A factory Mixin to create an concrete class."""

    @classmethod
    def factory(cls, typ, *args, **kwargs):
        """factory to create an concrete class."""
        f = getattr(cls, "_factory", {})
        sclass = f.get(typ, None)
        if sclass:
            LOG.info("Find %s of concrete %s by %s.",
                     sclass.__name__, cls.__name__, typ)
            return sclass
        for sclass in cls.__subclasses__():
            if typ == getattr(cls, "_factory_type", None):
                return sclass
        else:
            return cls
            LOG.info("Use default %s, do not find concrete class"
                     "by %s.", cls.__name__, typ)


def strtime(at):
    return at.strftime("%Y-%m-%dT%H:%M:%S.%f")
