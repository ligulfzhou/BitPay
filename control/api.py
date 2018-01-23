#!/usr/bin/env python
# -*- coding: utf-8 -*-

import json
import random
import pickle
import datetime
import logging

from lib import utils
from decimal import Decimal
from tornado import httputil
from bip32utils import BIP32Key

ORDER_LASTS = 15 * 60


class ApiCtrl(object):

    def __init__(self, ctrl):
        self.ctrl = ctrl
        self.api = ctrl.pdb.api

    def __getattr__(self, name):
        return getattr(self.api, name)

    def get_order_key(self, order_id):
        return 'order_%s' % order_id

    def get_childkey_index_key(self):
        return 'child_key_index'

    def get_latest_orders_key(self):
        return 'latest_orders'

    def _get_childkey_index(self):
        key = self.get_childkey_index_key_ctl()
        index = self.ctrl.rs.incr(key)
        return int(index)

    def _get_xpub_value(self):
        return 'xpub6F4nfP15Zd4755DYXpkJeHw8WydnhJxa7qo5BGzUWTbT1sULndMnVgRSmRqdfAEaWBFTfUYf6SK6pZjFdG12qcfjxDuQcTsJ7gY2F71yd1U'

    def _get_address(self):
        index = self._get_childkey_index_ctl()
        xpub = self._get_xpub_value_ctl()
        bip32 = BIP32Key.fromExtendedKey(xpub)
        return bip32.ChildKey(index).Address()

    def get_order(self, order_id):
        key = self.get_order_key_ctl(order_id)
        v = self.ctrl.rs.get(key)
        if v:
            return json.loads(v)

        order = self.api.get_order(order_id)
        if order:
            self.ctrl.rs.set(key, json.dumps(order), ORDER_LASTS)
        return order

    def gen_order(self, data={}):
        order_id = data['order_id']
        order = self.get_order_ctl(order_id)
        if order:
            raise

        address = self._get_address()
        data.update({
            'bitaddr': address
        })
        order = self.api.add_order(data)
        if order:
            key = self.get_order_key_ctl(order['order_id'])
            self.ctrl.rs.set(key, json.dumps(order), ORDER_LASTS)
        return order

    def get_orders_of_last_fifteen_minutes(self):
        key = self.get_latest_orders_key_ctl()
        orders = self.ctrl.rs.lrange(key, 0, -1)
        if orders:
            orders = [json.loads(i) for i in orders]
            return orders

        dt = datetime.datetime.now() - datetime.timedelta(seconds=15*60)
        orders = self.api.get_latest_orders(dt)
        if orders:
            orders_json = [json.dumps(order) for order in orders]
            pipe = self.ctrl.rs.pipeline()
            pipe.delete(key)
            pipe.rpush(key, *orders)
        return orders

    def update_order(self, order_id, data={}):
        assert data

        key = self.get_order_key_ctl(order_id)
        self.api.update_order(order_id, data)
        self.ctrl.rs.delete(key)

