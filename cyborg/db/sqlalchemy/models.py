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

"""SQLAlchemy models for accelerator service."""

from oslo_db import options as db_options
from oslo_db.sqlalchemy import models
from oslo_utils import timeutils
import six.moves.urllib.parse as urlparse
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import Column, String, Integer, Boolean, ForeignKey, Index
from sqlalchemy import Text
from sqlalchemy import schema
from sqlalchemy import DateTime
from sqlalchemy import orm

from cyborg.common import paths
from cyborg.conf import CONF


_DEFAULT_SQL_CONNECTION = 'sqlite:///' + paths.state_path_def('cyborg.sqlite')
db_options.set_defaults(CONF, connection=_DEFAULT_SQL_CONNECTION)


def table_args():
    engine_name = urlparse.urlparse(CONF.database.connection).scheme
    if engine_name == 'mysql':
        return {'mysql_engine': CONF.database.mysql_engine,
                'mysql_charset': "utf8"}
    return None


class CyborgBase(models.TimestampMixin, models.ModelBase):
    metadata = None

    def as_dict(self):
        d = {}
        for c in self.__table__.columns:
            d[c.name] = self[c.name]
        return d

    @staticmethod
    def delete_values():
        return {'deleted': True,
                'deleted_at': timeutils.utcnow()}

    def delete(self, session):
        """Delete this object."""
        updated_values = self.delete_values()
        self.update(updated_values)
        self.save(session=session)
        return updated_values


Base = declarative_base(cls=CyborgBase)


class Accelerator(Base):
    """Represents the accelerators."""

    __tablename__ = 'accelerators'
    __table_args__ = (
        schema.UniqueConstraint('uuid', name='uniq_accelerators0uuid'),
        table_args()
    )

    id = Column(Integer, primary_key=True)
    uuid = Column(String(36), nullable=False)
    name = Column(String(255), nullable=False)
    description = Column(String(255), nullable=True)
    project_id = Column(String(36), nullable=True)
    user_id = Column(String(36), nullable=True)
    device_type = Column(String(255), nullable=False)
    acc_type = Column(String(255), nullable=True)
    acc_capability = Column(String(255), nullable=True)
    vendor_id = Column(String(255), nullable=False)
    product_id = Column(String(255), nullable=False)
    remotable = Column(Integer, nullable=False)


class Deployable(Base):
    """Represents the deployables."""

    __tablename__ = 'deployables'
    __table_args__ = (
        schema.UniqueConstraint('uuid', name='uniq_deployables0uuid'),
        Index('deployables_parent_uuid_idx', 'parent_uuid'),
        Index('deployables_root_uuid_idx', 'root_uuid'),
        Index('deployables_accelerator_id_idx', 'accelerator_id'),
        table_args()
    )

    id = Column(Integer, primary_key=True)
    uuid = Column(String(36), nullable=False)
    name = Column(String(255), nullable=False)
    parent_uuid = Column(String(36),
                         ForeignKey('deployables.uuid'), nullable=True)
    root_uuid = Column(String(36),
                       ForeignKey('deployables.uuid'), nullable=True)
    address = Column(String(255), nullable=False)
    host = Column(String(255), nullable=False)
    board = Column(String(255), nullable=False)
    vendor = Column(String(255), nullable=False)
    version = Column(String(255), nullable=False)
    type = Column(String(255), nullable=False)
    interface_type = Column(String(255), nullable=False)
    assignable = Column(Boolean, nullable=False)
    instance_uuid = Column(String(36), nullable=True)
    availability = Column(String(255), nullable=False)
    accelerator_id = Column(Integer,
                            ForeignKey('accelerators.id', ondelete="CASCADE"),
                            nullable=False)


class Attribute(Base):
    __tablename__ = 'attributes'
    __table_args__ = (
        schema.UniqueConstraint('uuid', name='uniq_attributes0uuid'),
        Index('attributes_deployable_id_idx', 'deployable_id'),
        table_args()
    )

    id = Column(Integer, primary_key=True)
    uuid = Column(String(36), nullable=False)
    deployable_id = Column(Integer,
                           ForeignKey('deployables.id', ondelete="CASCADE"),
                           nullable=False)
    key = Column(Text, nullable=False)
    value = Column(Text, nullable=False)


class QuotaUsage(Base):
    """Represents the current usage for a given resource."""

    __tablename__ = 'quota_usages'
    __table_args__ = (
        Index('ix_quota_usages_project_id', 'project_id'),
        Index('ix_quota_usages_user_id', 'user_id'),
    )
    id = Column(Integer, primary_key=True)

    project_id = Column(String(255))
    user_id = Column(String(255))
    resource = Column(String(255), nullable=False)

    in_use = Column(Integer, nullable=False)
    reserved = Column(Integer, nullable=False)

    @property
    def total(self):
        return self.in_use + self.reserved

    until_refresh = Column(Integer)


class Reservation(Base):
    """Represents a resource reservation for quotas."""

    __tablename__ = 'reservations'
    __table_args__ = (
        Index('ix_reservations_project_id', 'project_id'),
        Index('reservations_uuid_idx', 'uuid'),
        Index('ix_reservations_user_id', 'user_id'),
    )
    id = Column(Integer, primary_key=True, nullable=False)
    uuid = Column(String(36), nullable=False)

    usage_id = Column(Integer, ForeignKey('quota_usages.id'), nullable=False)

    project_id = Column(String(255))
    user_id = Column(String(255))
    resource = Column(String(255))

    delta = Column(Integer, nullable=False)
    expire = Column(DateTime)

    usage = orm.relationship(
        "QuotaUsage",
        foreign_keys=usage_id,
        primaryjoin=usage_id == QuotaUsage.id)
