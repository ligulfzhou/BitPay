#!/usr/bin/env python
# -*- coding: utf-8 -*-

import random
import pickle
import datetime
import logging
import bitcoin    # python-bitcoinlib
import electrum
# bitcoin.SelectParams('testnet')

from lib import utils
from decimal import Decimal
from tornado import httputil
from tornado.options import options
from bip32utils import BIP32Key
from bitcoin.wallet import CBitcoinAddress
from bitcoin.core.script import CScript

ORDER_LASTS = 15 * 60


if options.network != 'mainnet':
    bitcoin.SelectParams('testnet')
    electrum.bitcoin.NetworkConstants.set_testnet()


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

    def _get_xpub_value(self, network='main'):
        # if network == 'main':
        #     return 'xpub6F4nfP15Zd4755DYXpkJeHw8WydnhJxa7qo5BGzUWTbT1sULndMnVgRSmRqdfAEaWBFTfUYf6SK6pZjFdG12qcfjxDuQcTsJ7gY2F71yd1U'
        # return 'tpubDF6EXmfY6frNALcSJHDYLD14vZ6CdUvuppD7Ck1MDUjt5cWuCbiUjsnfK7c6fwHcX3a5s6Mba2dT7GHETCJWP1VwefQJQV7LspTKaEPNscv'
        # mention wish know payment dune picture level catalog parade flock hawk depend
        if options.network == 'mainnet':
            return 'xpub6F4nfP15Zd4755DYXpkJeHw8WydnhJxa7qo5BGzUWTbT1sULndMnVgRSmRqdfAEaWBFTfUYf6SK6pZjFdG12qcfjxDuQcTsJ7gY2F71yd1U'
        return 'tpubDFSRBcpmGu1ZLsQPz1jPrDGVr6jSghTdfUPNXq3crNMLmA93rrCse86H1TvRBfBpJ5nNH44XdY99WkDs27rGj4831peiHzXXhe8S15axBR5'

    def _get_address(self):
        index = self._get_childkey_index_ctl()
        xpub = self._get_xpub_value_ctl()
        bip32 = BIP32Key.fromExtendedKey(xpub)
        return bip32.ChildKey(index).Address()

    def get_order(self, order_id):
        key = self.get_order_key_ctl(order_id)
        v = self.ctrl.rs.get(key)
        if v:
            return pickle.loads(v)

        order = self.api.get_order(order_id)
        if order:
            self.ctrl.rs.set(key, pickle.dumps(order), ORDER_LASTS)
        return order

    def gen_order(self, data={}):
        order_id = data['order_id']
        order = self.get_order_ctl(order_id)
        if order:
            raise

        address = self._get_address_ctl()
        data.update({
            'bitaddr': address
        })
        order = self.api.add_order(data)
        if order:
            key = self.get_order_key_ctl(order['order_id'])
            self.ctrl.rs.set(key, pickle.dumps(order), ORDER_LASTS)
        return order

    def get_orders_of_last_fifteen_minutes(self):
        key = self.get_latest_orders_key_ctl()
        orders = self.ctrl.rs.lrange(key, 0, -1)
        if orders:
            orders = [pickle.loads(i) for i in orders]
            return orders

        dt = datetime.datetime.now() - datetime.timedelta(seconds=15*60)
        orders = self.api.get_latest_orders(dt)
        if orders:
            orders_json = [pickle.dumps(order) for order in orders]
            pipe = self.ctrl.rs.pipeline()
            pipe.delete(key)
            pipe.rpush(key, *orders)
        return orders

    def update_order(self, order_id, data={}):
        assert data

        key = self.get_order_key_ctl(order_id)
        self.api.update_order(order_id, data)
        self.ctrl.rs.delete(key)

    def get_script_from_address(self, address):
        # nversion = 0 if network == 'main' else 111  # https://github.com/petertodd/python-bitcoinlib/blob/2cd65b79a3e722f77c71cd26a6f805e62d3ada09/bitcoin/__init__.py#L31
        # bitcoin.SelectParams('mainnet' if network == 'main' else 'testnet')  # https://github.com/petertodd/python-bitcoinlib/blob/2cd65b79a3e722f77c71cd26a6f805e62d3ada09/bitcoin/__init__.py#L64
        # a = CBitcoinAddress.from_bytes(address.encode(), nversion)
        # script = a.to_scriptPubKey()
        # return script

        # if options.network != 'mainnet':
        #     electrum.bitcoin.NetworkConstants.set_testnet()
        return electrum.bitcoin.address_to_script(address)

    def get_address_from_script(self, script):
        address = CBitcoinAddress.from_scriptPubKey(CScript(script))
        return address

