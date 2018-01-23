#!/usr/bin/env python
# -*- coding: utf-8 -*-

# redis
REDIS = {
    'host': '10.10.155.122',
    'port': 6379
}

# mysql
DB = 'bitpay'
BITPAY_DB = {
    DB: {
        'master': {
            'host': '127.0.0.1',
            'user': 'root',
            'pass': 'MYSQLzhouligang153',
            'port': 3306
        },
        'slaves': [
            {
                'host': '127.0.0.1',
                'user': 'root',
                'pass': 'MYSQLzhouligang153',
                'port': 3306
            }
        ]
    }
}

# error msg
ERR = {
    200: '请求成功',
    10001: '请求参数错误',
    50000: '系统错误'
}

# try to load debug settings
try:
    from tornado.options import options
    if options.debug:
        exec(compile(open('settings.debug.py')
             .read(), 'settings.debug.py', 'exec'))
except:
    pass
