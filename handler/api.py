#!/usr/bin/env python
# -*- coding: utf-8 -*-

import time
import json
import random
import logging
import datetime
import hashlib
import random

from lib import utils
from proto import paymentrequest_pb2
from control import ctrl
from handler.base import BaseHandler
from tornado.options import options


class PrepayHandler(BaseHandler):

    def get_satoshi(self, price):
        return 10000

    def post(self):
        try:
            info = self.get_argument('info', '')
            price = int(self.get_argument('priec'))
            order_id = self.get_argument('order_id')
        except Exception as e:
            logging.error(e)
            raise utils.APIError

        order = ctrl.api.gen_order_ctl({
            'info': info,
            'price': price,
            'order_id': order_id,
            'satoshi': self.get_satoshi(price)
        })

        self.send_json({
            'order': order
        })

    def get(self):
        self.post()


class QueryHandler(BaseHandler):

    def get(self):
        try:
            order_id = self.get_argument('order_id')
        except Exception as e:
            logging.error(e)
            raise utils.APIError(errcode=10001)

        order = ctrl.api.get_order_ctl(order_id)
        self.send_json({
            'state': order['state']
        })


class DepositPageHandler(BaseHandler):

    def get(self):
        try:
            order_id = self.get_argument('order_id')
        except Exception as e:
            logging.error(e)
            raise utils.APIError(errcode=10001)

        order = ctrl.api.get_order_ctl(order_id)
        self.render('test.tpl', order=order)


class InvoiceHandler(BaseHandler):

    def get(self):
        try:
            order_id = self.get_argument('order_id')
        except Exception as e:
            logging.error(e)
            raise utils.APIError(errcode=10001)

        self.send_json()


class PaymentRequestHandler(BaseHandler):

    def get(self, order_id):
        try:
            order = ctrl.api.get_order_ctl(order_id)
            network = self.get_argument('network', 'main')

            assert network in ('main', 'test')
            assert order
        except Exception as e:
            logging.error(e)
            raise utils.APIError(errcode=10001)

        script = ctrl.api.get_script_from_address_ctl(order['bitaddr'], network)

        pd = paymentrequest_pb2.PaymentDetails()
        pd.outputs.add(amount=order['satoshi'], script=script)
        pd.time = int(datetime.datetime.now().timestamp())
        pd.payment_url = 'http://bitpay.ligulfzhou.com/btc/payment/ack?order_id=%s' % order_id
        pd.memo = 'test order'
        pd.merchant_data = 'merchant_data'.encode()
        pd.network = network

        pr = paymentrequest_pb2.PaymentRequest()
        pr.serialized_payment_details = pd.SerializeToString()

        headers={'Content-Type': 'application/bitcoin-paymentrequest'}
        self.write_with_headers(pr.SerializeToString(), headers)


class PaymentHandler(BaseHandler):

    def get(self):
        self.send_json()


class PaymentACKHandler(BaseHandler):

    def get(self):
        self.send_json()
