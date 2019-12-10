#!/usr/bin/env python
# -*- coding: utf-8 -*-

import time
import json
import random
import logging
import datetime
import hashlib
import random
import binascii

from Crypto.Hash import SHA256
from Crypto.Signature import PKCS1_v1_5
from Crypto.PublicKey import RSA

from lib import utils
from proto import paymentrequest_pb2
from control import ctrl
from handler.base import BaseHandler
from tornado.options import options
from settings import pems


class PayQueryHandler(BaseHandler):

    def get(self):
        try:
            order_id = self.get_argument('order_id')
        except Exception as e:
            logging.error(e)
            raise util.APIError(errcode=10001)

        # query order status
        order = ctrl.api.get_order(order_id)
        self.send_json({
            'order': order
        })


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
            raise utils.APIError(errcode=10001)

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

    def join_sign(self, pr):
        pr.signature = b''
        request_hash = SHA256.new(pr.SerializeToString())
        private_key = RSA.importKey(pems['privkey'])
        signer = PKCS1_v1_5.new(private_key)
        pr.signature = signer.sign(request_hash)
        return pr

    def get(self, order_id):
        try:
            order = ctrl.api.get_order_ctl(order_id)
            test = int(self.get_argument('test', 0))

            assert order
        except Exception as e:
            logging.error(e)
            raise utils.APIError(errcode=10001)

        script = ctrl.api.get_script_from_address_ctl(order['bitaddr'])
        if options.network != 'mainnet' and test:
            url = 'http://127.0.0.1:7890/btc/payment/ack?order_id=%s' % order_id
        else:
            url = 'https://bitpay.ligulfzhou.com/btc/payment/ack?order_id=%s' % order_id

        pd = paymentrequest_pb2.PaymentDetails()
        pd.outputs.add(amount=order['satoshi'], script=binascii.unhexlify(script))
        pd.time = int(datetime.datetime.now().timestamp())
        pd.payment_url = url
        pd.memo = 'test order'
        pd.merchant_data = 'merchant_data'.encode()
        pd.network = 'main' if options.network == 'mainnet' else 'test'

        x509 = paymentrequest_pb2.X509Certificates()
        x509.certificate.append(pems['fullchain'].encode())

        pr = paymentrequest_pb2.PaymentRequest()
        pr.serialized_payment_details = pd.SerializeToString()
        # pr.pki_data = x509.SerializeToString()
        # pr.pki_type = 'x509+sha256'
        # pr = self.join_sign(pr)

        headers={'Content-Type': 'application/bitcoin-paymentrequest', 'Accept': 'application/bitcoin-paymentrequest'}
        self.write_with_headers(pr.SerializeToString(), headers)


class PaymentACKHandler(BaseHandler):

    def post(self):
        try:
            pa = paymentrequest_pb2.PaymentACK()
            pa.payment.ParseFromString(self.request.body)
        except Exception as e:
            logging.error(e)
            raise utils.APIError(errcode=10001)

        pa.memo = 'payment received, we will process your payment soon'
        refund_address = ctrl.api.get_address_from_script_ctl(pa.payment.refund_to[0].script)

        headers = {'Content-Type' : 'application/bitcoin-payment', 'Accept' : 'application/bitcoin-paymentack'}
        self.write_with_headers(pa.SerializeToString(), headers)


class DemoHandler(BaseHandler):

    def get(self):
        self.render('demo.tpl')


class DemoGenOrderHandler(BaseHandler):

    def post(self):
        order = ctrl.api.gen_order_ctl({
            'info': 'information',
            'price': 1000,
            'order_id': str(int(datetime.datetime.now().timestamp())),
            'satoshi': random.randint(100, 10000)
        })
        self.send_json(order)


class DemoInvoiceHandler(BaseHandler):

    def get(self, order_id):
        try:
            order = ctrl.api.get_order_ctl(order_id)
        except Exception as e:
            logging.error(e)
            raise utils.APIError(errcode=10001)

        self.render('demo_invoice.tpl', order=order)

