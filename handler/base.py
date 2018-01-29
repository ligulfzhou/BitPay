#!/usr/bin/env python
# -*- coding: utf-8 -*-

import re
import json
import logging
import hashlib
import traceback
import datetime

from decimal import Decimal
from tornado import web, gen
from tornado.options import options
from control import ctrl
from settings import ERR
from lib import utils
from raven.contrib.tornado import SentryMixin


class BaseHandler(web.RequestHandler, SentryMixin):

    def initialize(self):
        ctrl.pdb.close()

    def on_finish(self):
        ctrl.pdb.close()

    def json_format(self, obj):
        if isinstance(obj, datetime.datetime):
            return obj.strftime('%Y-%m-%d %H:%M:%S')
        if isinstance(obj, Decimal):
            return ('%.2f' % obj)

    def has_argument(self, name):
        return name in self.request.arguments

    def send_json(self, data={}, errcode=200, errmsg='', status_code=200, headers={}):
        res = {
            'errcode': errcode,
            'errmsg': errmsg if errmsg else ERR[errcode]
        }
        res.update(data)

        if errcode > 200:
            logging.error(res)

        json_str = json.dumps(res, default=self.json_format)

        if options.debug:
            logging.info('path: %s, arguments: %s, response: %s'%(self.request.path, self.request.arguments, json_str))
        jsonp = self.get_argument('jsonp', '')
        if jsonp:
            jsonp = re.sub(r'[^\w\.]', '', jsonp)
            self.set_header('Content-Type', 'text/javascript; charet=UTF-8')
            json_str = '%s(%s)' % (jsonp, json_str)
        else:
            self.set_header('Content-Type', 'application/json')

        if headers:
            [self.set_header(k, v) for k, v in headers.items()]

        self.set_status(status_code)
        self.write(json_str)
        self.finish()

    def write_with_headers(self, chunk, headers={}):
        if headers:
            [self.set_header(k, v) for k, v in headers.items()]

        # super(BaseHandler, self).write(chunk)
        self.write(chunk)


    def dict_args(self):
        _rq_args = self.request.arguments
        rq_args = dict([(k, _rq_args[k][0]) for k in _rq_args])
        return rq_args

    def write_error(self, status_code=200, **kwargs):
        if 'exc_info' in kwargs:
            err_object = kwargs['exc_info'][1]
            traceback.format_exception(*kwargs['exc_info'])

            if isinstance(err_object, utils.APIError):
                err_info = err_object.kwargs
                self.send_json(**err_info)
                return

        self.send_json(status_code=500, errcode=50001)
        # self.captureException(**kwargs)
