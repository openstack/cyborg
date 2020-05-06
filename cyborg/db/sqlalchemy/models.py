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
from sqlalchemy import Boolean
from sqlalchemy import Column
from sqlalchemy import DateTime
from sqlalchemy import Enum
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import ForeignKey
from sqlalchemy import Index
from sqlalchemy import Integer
from sqlalchemy import orm
from sqlalchemy import schema
from sqlalchemy import String
from sqlalchemy import Text

from cyborg.common import constants
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


class Device(Base):
    """Represents the devices."""

    __tablename__ = 'devices'

    id = Column(Integer, primary_key=True)
    uuid = Column(String(36), nullable=False, unique=True)
    type = Column(Enum('GPU', 'FPGA', 'AICHIP', 'QAT',
                       name='device_type'), nullable=False)
    vendor = Column(String(255), nullable=False)
    model = Column(String(255), nullable=False)
    std_board_info = Column(Text, nullable=True)
    vendor_board_info = Column(Text, nullable=True)
    hostname = Column(String(255), nullable=False)


class Deployable(Base):
    """Represents the deployables."""

    __tablename__ = 'deployables'
    __table_args__ = (
        Index('deployables_parent_id_idx', 'parent_id'),
        Index('deployables_root_id_idx', 'root_id'),
        Index('deployables_device_id_idx', 'device_id'),
        table_args()
    )

    id = Column(Integer, primary_key=True)
    uuid = Column(String(36), nullable=False, unique=True)
    parent_id = Column(Integer, ForeignKey('deployables.id'), nullable=True)
    root_id = Column(Integer, ForeignKey('deployables.id'), nullable=True)
    name = Column(String(255), nullable=False)
    num_accelerators = Column(Integer, nullable=False)
    device_id = Column(Integer, ForeignKey('devices.id', ondelete="RESTRICT"),
                       nullable=False)
    # The resource provider UUID is nullable for 2 reasons:
    # A. on creation, till Placement is populated, this will be null.
    # B. Sub-deployables (such as in networked FPGA cards) will have
    #    this as null.
    rp_uuid = Column(String(36), nullable=True)
    # This is nullable because the parent deployable in a networked
    # FPGA card will have no driver. Only subdeployables have one.
    driver_name = Column(String(100), nullable=True)
    bitstream_id = Column(String(36), nullable=True)

    # TODO() Add programming_in_progress field


class Attribute(Base):
    __tablename__ = 'attributes'

    id = Column(Integer, primary_key=True)
    uuid = Column(String(36), nullable=False, unique=True)
    deployable_id = Column(Integer,
                           ForeignKey('deployables.id', ondelete="RESTRICT"),
                           nullable=False, index=True)
    key = Column(Text, nullable=False)
    value = Column(Text, nullable=False)


class ControlpathID(Base):
    """Identifier for the Device when driver reporting to agent, IDs is
    needed especially when multiple PFs exist in one Devices.
    """

    __tablename__ = 'controlpath_ids'

    id = Column(Integer, primary_key=True)
    uuid = Column(String(36), nullable=False, unique=True)
    device_id = Column(Integer,
                       ForeignKey('devices.id', ondelete="RESTRICT"),
                       nullable=False, index=True)
    cpid_type = Column(Enum('PCI', name='cpid_type'), nullable=False)
    cpid_info = Column(String(255), nullable=False)


class AttachHandle(Base):
    """Represents device's VFs and PFs which can be attached to a VM."""

    __tablename__ = 'attach_handles'
    __table_args__ = (
        Index('attach_handles_cpid_id_idx', 'cpid_id'),
        Index('attach_handles_deployable_id_idx', 'deployable_id'),
        table_args()
    )

    id = Column(Integer, primary_key=True)
    uuid = Column(String(36), nullable=False, unique=True)
    deployable_id = Column(Integer,
                           ForeignKey('deployables.id', ondelete="RESTRICT"),
                           nullable=False)
    cpid_id = Column(Integer,
                     ForeignKey('controlpath_ids.id', ondelete="RESTRICT"),
                     nullable=False)
    in_use = Column(Boolean, default=False)
    attach_type = Column(Enum(constants.AH_TYPE_PCI,
                              constants.AH_TYPE_MDEV,
                              constants.AH_TYPE_TEST_PCI,
                         name='attach_type'),
                         nullable=False)
    attach_info = Column(String(255), nullable=False)


class DeviceProfile(Base):
    """Represents users' specific requirements."""

    __tablename__ = 'device_profiles'
    __table_args__ = (
        schema.UniqueConstraint('uuid', 'name',
                                name='uniq_device_profiles0uuid0name'),
        table_args()
    )

    id = Column(Integer, primary_key=True)
    uuid = Column(String(36), nullable=False)
    name = Column(String(255), nullable=False, unique=True)
    profile_json = Column(Text, nullable=False)
    description = Column(Text, nullable=True)


class ExtArq(Base):
    """ExtArq is the abbreviation of ExtendedAcceleratorRequest, it represents
    extended nova requests for attach related operations.
    """

    __tablename__ = 'extended_accelerator_requests'
    __table_args__ = (
        Index('extArqs_project_id_idx', 'project_id'),
        Index('extArqs_device_profile_id_idx', 'device_profile_id'),
        Index('extArqs_device_rp_uuid_idx', 'device_rp_uuid'),
        Index('extArqs_instance_uuid_idx', 'instance_uuid'),
        Index('extArqs_attach_handle_id_idx', 'attach_handle_id'),
        Index('extArqs_deployable_id_idx', 'deployable_id'),
        table_args()
    )

    id = Column(Integer, primary_key=True)
    uuid = Column(String(36), nullable=False, unique=True)
    project_id = Column(String(255), nullable=True)
    state = Column(Enum(constants.ARQ_INITIAL,
                        constants.ARQ_BIND_STARTED,
                        constants.ARQ_BOUND,
                        constants.ARQ_BIND_FAILED,
                        constants.ARQ_UNBOUND,
                        constants.ARQ_DELETING),
                   nullable=False)
    device_profile_id = Column(Integer, ForeignKey('device_profiles.id',
                                                   ondelete="RESTRICT"),
                               nullable=False)
    device_profile_group_id = Column(Integer, nullable=False, default=0)
    hostname = Column(String(255), nullable=True)
    device_rp_uuid = Column(String(36), nullable=True)
    instance_uuid = Column(String(36), nullable=True)
    attach_handle_id = Column(Integer, ForeignKey('attach_handles.id',
                                                  ondelete="RESTRICT"),
                              nullable=True)
    # Cyborg Private Fields
    substate = Column(Enum('Initial', name='substate'), nullable=False,
                      default='Initial')
    deployable_id = Column(Integer,
                           ForeignKey('deployables.id', ondelete="RESTRICT"),
                           nullable=True)


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
