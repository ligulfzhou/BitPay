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


class PayPageHandler(BaseHandler):

    def get(self):
        try:
            order_id = self.get_argument('order_id')
        except Exception as e:
            logging.error(e)
            raise utils.APIError(errcode=10001)

        order = ctrl.api.get_order_ctl(order_id)
        self.render('test.tpl', order=order)
