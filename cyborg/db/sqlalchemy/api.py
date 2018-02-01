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

"""SQLAlchemy storage backend."""

import threading

from oslo_db import api as oslo_db_api
from oslo_db import exception as db_exc
from oslo_db.sqlalchemy import enginefacade
from oslo_db.sqlalchemy import utils as sqlalchemyutils
from oslo_log import log
from oslo_utils import strutils
from oslo_utils import uuidutils
from sqlalchemy.orm.exc import NoResultFound

from cyborg.common import exception
from cyborg.common.i18n import _
from cyborg.db import api
from cyborg.db.sqlalchemy import models


_CONTEXT = threading.local()
LOG = log.getLogger(__name__)


def get_backend():
    """The backend is this module itself."""
    return Connection()


def _session_for_read():
    return enginefacade.reader.using(_CONTEXT)


def _session_for_write():
    return enginefacade.writer.using(_CONTEXT)


def model_query(context, model, *args, **kwargs):
    """Query helper for simpler session usage.

    :param context: Context of the query
    :param model: Model to query. Must be a subclass of ModelBase.
    :param args: Arguments to query. If None - model is used.

    Keyword arguments:

    :keyword project_only:
      If set to True, then will do query filter with context's project_id.
      if set to False or absent, then will not do query filter with context's
      project_id.
    :type project_only: bool
    """

    if kwargs.pop("project_only", False):
        kwargs["project_id"] = context.tenant

    with _session_for_read() as session:
        query = sqlalchemyutils.model_query(
            model, session, args, **kwargs)
        return query


def add_identity_filter(query, value):
    """Adds an identity filter to a query.

    Filters results by ID, if supplied value is a valid integer.
    Otherwise attempts to filter results by UUID.

    :param query: Initial query to add filter to.
    :param value: Value for filtering results by.
    :return: Modified query.
    """
    if strutils.is_int_like(value):
        return query.filter_by(id=value)
    elif uuidutils.is_uuid_like(value):
        return query.filter_by(uuid=value)
    else:
        raise exception.InvalidIdentity(identity=value)


def _paginate_query(context, model, limit, marker, sort_key, sort_dir, query):
    sort_keys = ['id']
    if sort_key and sort_key not in sort_keys:
        sort_keys.insert(0, sort_key)
    try:
        query = sqlalchemyutils.paginate_query(query, model, limit, sort_keys,
                                               marker=marker,
                                               sort_dir=sort_dir)
    except db_exc.InvalidSortKey:
        raise exception.InvalidParameterValue(
            _('The sort_key value "%(key)s" is an invalid field for sorting')
            % {'key': sort_key})
    return query.all()


class Connection(api.Connection):
    """SqlAlchemy connection."""

    def __init__(self):
        pass

    def accelerator_create(self, context, values):
        if not values.get('uuid'):
            values['uuid'] = uuidutils.generate_uuid()

        accelerator = models.Accelerator()
        accelerator.update(values)

        with _session_for_write() as session:
            try:
                session.add(accelerator)
                session.flush()
            except db_exc.DBDuplicateEntry:
                raise exception.AcceleratorAlreadyExists(uuid=values['uuid'])
            return accelerator

    def accelerator_get(self, context, uuid):
        query = model_query(
            context,
            models.Accelerator).filter_by(uuid=uuid)
        try:
            return query.one()
        except NoResultFound:
            raise exception.AcceleratorNotFound(uuid=uuid)

    def accelerator_list(self, context, limit, marker, sort_key, sort_dir,
                         project_only):
        query = model_query(context, models.Accelerator,
                            project_only=project_only)
        return _paginate_query(context, models.Accelerator, limit, marker,
                               sort_key, sort_dir, query)

    def accelerator_update(self, context, uuid, values):
        if 'uuid' in values:
            msg = _("Cannot overwrite UUID for an existing Accelerator.")
            raise exception.InvalidParameterValue(err=msg)

        try:
            return self._do_update_accelerator(context, uuid, values)
        except db_exc.DBDuplicateEntry as e:
            if 'name' in e.columns:
                raise exception.DuplicateAcceleratorName(name=values['name'])

    @oslo_db_api.retry_on_deadlock
    def _do_update_accelerator(self, context, uuid, values):
        with _session_for_write():
            query = model_query(context, models.Accelerator)
            query = add_identity_filter(query, uuid)
            try:
                ref = query.with_lockmode('update').one()
            except NoResultFound:
                raise exception.AcceleratorNotFound(uuid=uuid)

            ref.update(values)
        return ref

    @oslo_db_api.retry_on_deadlock
    def accelerator_delete(self, context, uuid):
        with _session_for_write():
            query = model_query(context, models.Accelerator)
            query = add_identity_filter(query, uuid)
            count = query.delete()
            if count != 1:
                raise exception.AcceleratorNotFound(uuid=uuid)

    def deployable_create(self, context, values):
        if not values.get('uuid'):
            values['uuid'] = uuidutils.generate_uuid()

        deployable = models.Deployable()
        deployable.update(values)

        with _session_for_write() as session:
            try:
                session.add(deployable)
                session.flush()
            except db_exc.DBDuplicateEntry:
                raise exception.DeployableAlreadyExists(uuid=values['uuid'])
            return deployable

    def deployable_get(self, context, uuid):
        query = model_query(
            context,
            models.Deployable).filter_by(uuid=uuid)
        try:
            return query.one()
        except NoResultFound:
            raise exception.DeployableNotFound(uuid=uuid)

    def deployable_get_by_host(self, context, host):
        query = model_query(
            context,
            models.Deployable).filter_by(host=host)
        return query.all()

    def deployable_list(self, context):
        query = model_query(context, models.Deployable)
        return query.all()

    def deployable_update(self, context, uuid, values):
        if 'uuid' in values:
            msg = _("Cannot overwrite UUID for an existing Deployable.")
            raise exception.InvalidParameterValue(err=msg)

        try:
            return self._do_update_deployable(context, uuid, values)
        except db_exc.DBDuplicateEntry as e:
            if 'name' in e.columns:
                raise exception.DuplicateDeployableName(name=values['name'])

    @oslo_db_api.retry_on_deadlock
    def _do_update_deployable(self, context, uuid, values):
        with _session_for_write():
            query = model_query(context, models.Deployable)
            query = add_identity_filter(query, uuid)
            try:
                ref = query.with_lockmode('update').one()
            except NoResultFound:
                raise exception.DeployableNotFound(uuid=uuid)

            ref.update(values)
        return ref

    @oslo_db_api.retry_on_deadlock
    def deployable_delete(self, context, uuid):
        with _session_for_write():
            query = model_query(context, models.Deployable)
            query = add_identity_filter(query, uuid)
            query.update({'root_uuid': None})
            count = query.delete()
            if count != 1:
                raise exception.DeployableNotFound(uuid=uuid)
