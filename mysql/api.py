#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import datetime
from sqlalchemy import Column
from sqlalchemy.dialects.mysql import INTEGER, VARCHAR, ENUM, TINYINT, DATE, DATETIME, DECIMAL, TIMESTAMP
from sqlalchemy.sql.expression import func, desc, asc, or_

from settings import DB, BITPAY_DB
from mysql.base import NotNullColumn, Base
from lib.decorator import model_to_dict, models_to_list


class Order(Base):
    __tablename__ = 'order'
    id = Column(INTEGER(11), primary_key=True)
    order_id = NotNullColumn(VARCHAR(64))
    price = NotNullColumn(INTEGER(24))
    bitaddr = NotNullColumn(VARCHAR(64))
    satoshi = NotNullColumn(INTEGER(24))
    state = NotNullColumn(TINYINT(1))
    info = NotNullColumn(VARCHAR(1024))


class APIModel(object):

    def __init__(self, pdb):
        self.pdb = pdb
        self.master = pdb.get_session(DB, master=True)
        self.slave = pdb.get_session(DB)

    @model_to_dict
    def add_order(self, data={}):
        o = Order(**data)
        self.master.add(o)
        self.master.commit()
        return o

    @model_to_dict
    def get_order(self, order_id):
        return self.slave.query(Order).filter_by(order_id=order_id).scalar()

    @models_to_list
    def get_latest_orders(self, dt, state=0):
        if isinstance(dt, datetime.datetime):
            dt = dt.strftime('%Y-%m-%d %X')
        return self.slave.query(Order).filter(Order.state==state, Order.create_time > dt).all()

    def update_order(self, order_id, data={}):
        assert data

        self.master.query(Order).filter_by(order_id=order_id).update(data)
        self.master.commit()

