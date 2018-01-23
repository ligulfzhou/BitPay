#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import sys

from tornado import web
from tornado.options import options
from tornado.httpserver import HTTPServer
from raven.contrib.tornado import AsyncSentryClient


URLS = [
    (r'/btc/prepay', 'handler.api.PrepayHandler'),
    (r'/btc/invoice', 'handler.api.PayPageHandler'),
]


class Application(web.Application):

    def __init__(self):
        settings = {
            'compress_response': True,
            'xsrf_cookies': False,
            'debug': options.debug,
            'static_path': os.path.join(sys.path[0], 'static'),
            'sentry_url': 'https://87991f331efb46adbc9a5a94ed9f0e43:d486c2d91c9a4dcebbc036e4958c3919@sentry.ktvsky.com/8' if not options.debug else ''
        }
        web.Application.__init__(self, **settings)

        for spec in URLS:
            host = '.*$'
            handlers = spec[1:]
            self.add_handlers(host, handlers)


def run():
    application = Application()
    application.sentry_client = AsyncSentryClient(application.settings['sentry_url'])
    http_server = HTTPServer(application, xheaders=True)
    http_server.listen(options.port)
    print('Running on port %d' % options.port)
