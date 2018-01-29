#!/usr/bin/env python
# -*- coding: utf-8 -*-

import random
import logging

from tornado.options import options
from sqlalchemy import create_engine
from sqlalchemy.orm import scoped_session, sessionmaker

from settings import BITPAY_DB
from mysql.api import APIModel


def create_session(engine):
    if not engine:
        return None
    session = scoped_session(sessionmaker(bind=engine))
    return session()


class Database(object):

    def __init__(self):
        self.schema = 'mysql://%s:%s@%s:%d/%s?charset=utf8'
        self.session = {
            'm': {},
            's': {}
        }
        self.kwargs = {
            'pool_recycle': 3600,
            'echo': options.debug,
            'echo_pool': options.debug
        }

        self.init_session()
        self.api = APIModel(self)

    def _session(self, user, passwd, host, port, db, master=True):
        schema = self.schema % (user, passwd, host, port, db)
        engine = create_engine(schema, **self.kwargs)
        session = create_session(engine)
        print('%s: %s' % ('master' if master else 'slave', schema))
        return session

    def init_session(self):
        for db, value in BITPAY_DB.items():
            self.session['s'][db] = []

            master = value.get('master')
            session = self._session(master['user'], master['pass'], master['host'], master['port'], db)
            self.session['m'][db] = session
            slaves = value.get('slaves')

            for slave in slaves:
                session = self._session(slave['user'], slave['pass'], slave['host'], slave['port'], db, master=False)
                self.session['s'][db].append(session)

    def get_session(self, db, master=False):
        if not master:
            sessions = self.session['s'][db]
            if len(sessions) > 0:
                session = random.choice(sessions)
                return session
        session = self.session['m'][db]
        return session

    @classmethod
    def instance(cls):
        name = 'singleton'
        if not hasattr(cls, name):
            setattr(cls, name, cls())
        return getattr(cls, name)

    def close(self):

        def shut(ins):
            try:
                ins.commit()
            except:
                logging.error('MySQL server has gone away. ignore.')
            finally:
                ins.close()

        for db in BITPAY_DB:
            shut(self.session['m'][db])
            for session in self.session['s'][db]:
                shut(session)

# global, called by control
pdb = Database.instance()
