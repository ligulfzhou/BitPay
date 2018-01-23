#!/usr/bin/env python
# -*- coding: utf-8 -*-

import when
import time
import json
import logging
import requests

from datetime import datetime
from decimal import Decimal
from tornado import web, httpclient
from tornado.httputil import url_concat
from tornado.options import options


httpclient.AsyncHTTPClient.configure('tornado.curl_httpclient.CurlAsyncHTTPClient', max_clients=300)

def dict_filter(target, attr=()):
    result = dict()
    for p in attr:
        if type(p) is dict:
            key = list(p.keys())[0]
            value = list(p.values())[0]
            result[value] = target[key] if key in target else ''
        elif p in target:
            result[p] = target[p]
    return result


class APIError(web.HTTPError):
    '''
    自定义API异常
    '''
    def __init__(self, status_code=200, *args, **kwargs):
        super(APIError, self).__init__(status_code, *args, **kwargs)
        self.kwargs = kwargs

def http_request(url, connect_timeout=10, request_timeout=10, **kwargs):
    if 'ngrok' in url:
        kwargs.update(dict(auth_username='ktvsky', auth_password='ktvsky5166'))

    return httpclient.HTTPRequest(url=url, connect_timeout=connect_timeout, request_timeout=request_timeout, **kwargs)

def get_async_client():
    http_client = httpclient.AsyncHTTPClient()
    return http_client

async def get_response(request):
    http_client = get_async_client()
    try:
        response = await http_client.fetch(request)
        logging.info(20*'*')
        logging.info('%s\trequest_time=%s\nheader=%s\nbody=%s\nresp=%s' % (request.url, response.request_time, request.headers, request.body, response.body.decode()))
        resp = json.loads(response.body.decode())
        return json.loads(resp)
    except Exception as e:
        logging.error(e)
        raise APIError(errcode=50000)


async def fetch(http_client, request):
    r = await http_client.fetch(request)
    logging.info('\treq_url=%s\trequest_time=%s' % (r.effective_url, r.request_time))
    logging.info('\tbody=%s' % (r.body))
    return r

async def fetch_api(url, method='GET', params={}, body={}, raw=0):
    url = url_concat(url, params)
    client = get_async_client()
    request = httpclient.HTTPRequest(url=url, method=method, body=None if method=='GET' else json.dumps(body),
                                     connect_timeout=10, request_timeout=10)
    try:
        response = await client.fetch(request)
        response = response.body.decode()
        if raw:
            return response
        response = json.loads(response)
        return response
    except Exception as e:
        logging.error(e)
        logging.error('url: %s, method: %s, params: %s, body: %s'%(url, method, params, body))
        raise
