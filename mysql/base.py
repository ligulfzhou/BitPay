#!/usr/bin/env python
# -*- coding: utf-8 -*-

from sqlalchemy import Column
from functools import partial
from sqlalchemy.ext.declarative import declarative_base, declared_attr
from sqlalchemy.dialects.mysql import TIMESTAMP, DATETIME

NotNullColumn = partial(Column, nullable=False, server_default='')

class declare_base(object):

    create_time = NotNullColumn(DATETIME, server_default='CURRENT_TIMESTAMP')
    update_time = NotNullColumn(TIMESTAMP, server_default='CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP')

    @declared_attr
    def __table_args__(cls):
        return {
            'mysql_engine': 'InnoDB',
            'mysql_charset': 'utf8'
        }

Base = declarative_base(cls=declare_base)

