#!/usr/bin/env python
# -*- coding: utf-8 -*-

import redis

from settings import REDIS

def get_redis_client(conf=REDIS):
    print('redis: %s' % conf['host'])
    return redis.StrictRedis(host=conf['host'], port=conf['port'])

rs = get_redis_client()

