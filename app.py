#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import sys

from tornado import web
from tornado.options import options
from tornado.httpserver import HTTPServer
from raven.contrib.tornado import AsyncSentryClient


class Application(web.Application):

    def __init__(self):
        handlers = [
            (r'/btc/prepay', 'handler.api.PrepayHandler'),
            (r'/btc/pay/query', 'handler.api.PayQueryHandler'),
            (r'/btc/page/deposit', 'handler.api.DepositPageHandler'),

            (r'/btc/payment/request/(.+)', 'handler.api.PaymentRequestHandler'),
            (r'/btc/payment/ack', 'handler.api.PaymentACKHandler'),

            (r'/btc/payment/demo', 'handler.api.DemoHandler'),
            (r'/btc/payment/demo/gen/order', 'handler.api.DemoGenOrderHandler'),
            (r'/btc/payment/demo/invoice/(.+)', 'handler.api.DemoInvoiceHandler'),
        ]

        settings = {
            'compress_response': True,
            'xsrf_cookies': False,
            'debug': options.debug,
            'static_path': os.path.join(sys.path[0], 'static'),
            'sentry_url': 'https://87991f331efb46adbc9a5a94ed9f0e43:d486c2d91c9a4dcebbc036e4958c3919@sentry.ktvsky.com/8' if not options.debug else '',
            'template_path': os.path.join(sys.path[0], 'tpl'),
        }
        web.Application.__init__(self, handlers, **settings)


def run():
    application = Application()
    # application.sentry_client = AsyncSentryClient(application.settings['sentry_url'])
    http_server = HTTPServer(application, xheaders=True)
    http_server.listen(options.port)
    print('Running on port %d' % options.port)

