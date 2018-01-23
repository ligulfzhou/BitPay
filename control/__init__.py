#!/usr/bin/env python
# -*- coding: utf-8 -*-

from control.api import ApiCtrl
from control.cache import rs
from mysql import pdb

class Ctrl(object):

    def __init__(self):
        self.__method_ren()
        self.pdb = pdb
        self.rs = rs
        self.api = ApiCtrl(self)

    def __method_ren(self):
        '''
        重命名control下的函数名，防止命名冲突
        '''
        for std in globals():
            if std.find('Ctrl') == -1:
                continue

            cls = globals()[std]
            for func in dir(cls):
                if callable(getattr(cls, func)) and not func.startswith('__'):
                    setattr(cls, '%s_ctl' % func, getattr(cls, func))
                    delattr(cls, func)

# global, called by handler
ctrl = Ctrl()
