# -*- coding: utf-8 -*-

# Copyright 2016-2017 OpenStack Foundation
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

from sqlalchemy import Column, Integer, String
from sqlalchemy.ext.declarative import declarative_base
Base = declarative_base()


# A common internal acclerator object for internal use.
class Accelerator(Base):
    __tablename__ = 'accelerators'
    accelerator_id = Column(String, primary_key=True)
    device_type = Column(String)
    remoteable = Column(Integer)
    vender_id = Column(String)
    product_id = Column(String)

    def __init__(self, **kwargs):
        self.accelerator_id = kwargs['accelerator_id']
        self.device_type = kwargs['device_type']
        self.remoteable = kwargs['remoteable']
        self.vendor_id = kwargs['vendor_id']
        self.product_id = kwargs['product_id']
