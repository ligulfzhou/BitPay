#!/usr/bin/env python
# -*- coding: utf-8 -*-

import time
import when
import json
import hashlib
import datetime
import logging

from settings import ERP, A_HOUR, DAREN, LOCK_TIME
from tornado import gen, httputil
from tornado.ioloop import IOLoop
from lib import utils


class FetchCtrl(object):

    def __init__(self, ctrl):
        self.ctrl = ctrl
        self.api = ctrl.pdb.api

    def __getattr__(self, name):
        return getattr(self.api, name)

    def get_rn_key(self, store_id, begintime, endtime):
        '''
        房型库存缓存KEY
        '''
        return 'rn_%s_%s_%s' % (store_id, begintime, endtime)

    def get_rps_key(self, store_id, date):
        '''
        房价缓存KEY
        '''
        return 'rps_%s_%s' % (store_id, utils.str_to_date(date).strftime('%Y-%m-%d'))

    def get_rt_key(self, store_id):
        '''
        房型缓存KEY
        '''
        return 'rt_%s' % store_id

    def get_recipe_key(self, kw):
        '''
        歌厅酒水缓存KEY
        '''
        return 'pub_recipe_%s' % kw

    def lock(self, key):
        pl = self.ctrl.rs.pipeline(transaction=False)
        state, _ = pl.setnx(key, 1).expire(key, LOCK_TIME).execute()
        return state

    def lock_key(self, key):
        '''
        lock key
        '''
        key = 'lock_%s' % key
        return self.lock_ctl(key)

    def signature(self, *args):
        sign_str = ''.join([str(arg) for arg in args])
        mysign = hashlib.md5(sign_str.encode()).hexdigest()
        return mysign

    def drop_cache_room_price(self, ktv_id, date):
        '''
        清空包房价格缓存
        '''
        date = datetime.datetime.strptime(date, '%Y-%m-%d')
        for o in range(10):
            key = self.get_rps_key_ctl(ktv_id, date.strftime('%Y-%m-%d'))
            self.ctrl.rs.delete(key)
            date = date + datetime.timedelta(days=1)

        self.ctrl.rs.delete(self.get_rt_key_ctl(ktv_id))

    def get_all_ktv_type_ids(self, ktv_id):
        key = 'pub_recipe_type_%s'%ktv_id
        types = self.ctrl.rs.lrange(key, 0, -1)
        types = [eval(t.decode()) for t in types]
        return [i['id'] for i in types]

    def drop_cache_recipe(self, ktv_id):
        '''
        清空酒水缓存
        '''
        # keys = self.ctrl.rs.keys('pub_recipe_%s_*'%ktv_id)
        keys = []
        type_ids = self.get_all_ktv_type_ids_ctl(ktv_id)
        if type_ids:
            ks = ['pub_recipe_%s_%s' % (ktv_id, tid) for tid in type_ids]
            keys.extend(ks)

        keys.append('pub_recipe_type_%s'%ktv_id)
        keys.append('pub_recipe_%s'%ktv_id)
        for k in keys:
            self.ctrl.rs.delete(k)

    def drop_cache_card(self, ktv_id):
        self.ctrl.rs.delete('ktv_cards_%s'%ktv_id)
        self.ctrl.rs.delete('ktv_card_regulation_%s'%ktv_id)

    def filter_items(self, items, roomtypeids=[], key='roomTypeID'):
        if roomtypeids:
            return list(filter(lambda item: int(item[key]) in roomtypeids, items))
        return items

    def get_rt_cache(self, key, roomtypeids):
        '''
        读房型缓存
        '''
        rooms_str = self.ctrl.rs.get(key)
        if rooms_str:
            rooms = json.loads(rooms_str.decode())['list']
            return self.filter_items_ctl(rooms, roomtypeids, 'id')
        return []

    def get_rps_cache(self, key, roomtypeids):
        '''
        读房价缓存
        '''
        pstr = self.ctrl.rs.get(key)
        if pstr:
            resp = json.loads(pstr.decode())
            return self.filter_items_ctl(resp['list'], roomtypeids), resp.get('discout', '')
        return [], ''

    def get_rn_cache(self, key, roomtypeids):
        '''
        读房型库存缓存
        '''
        rooms_str = self.ctrl.rs.get(key)
        if rooms_str:
            rooms = json.loads(rooms_str.decode())['roomDetails']
            return self.filter_items_ctl(rooms, roomtypeids)
        return []

    @gen.coroutine
    def get_room_type(self, store_id, address, roomtypeids=[]):
        '''
        获取房型，1小时更新一次房型
        '''
        key = self.get_rt_key_ctl(store_id)
        cache = self.get_rt_cache_ctl(key, roomtypeids)
        if cache:
            return cache

        state = self.lock_key_ctl(key)
        if not state:
            startime = 0
            sleeptime = 0.1
            while startime <= LOCK_TIME:
                yield gen.sleep(sleeptime)
                cache = self.get_rt_cache_ctl(key, roomtypeids)
                if cache:
                    return cache
                startime += sleeptime
            raise utils.APIError(errcode=50000)

        sign = self.signature_ctl(ERP['app_secret'], store_id)
        req_url = httputil.url_concat(address + ERP['room_type_url'], {
            'appid': ERP['app_id'],
            'time': int(time.time()),
            'poiid': store_id,
            'ktvid': store_id,
            'sign': sign
        })

        request = utils.http_request(req_url)
        resp = yield utils.get_response(request)
        self.ctrl.rs.set(key, json.dumps(resp), 5*60)

        return self.filter_items_ctl(resp['list'], roomtypeids, 'id')

    @gen.coroutine
    def get_room_price(self, store_id, address, roomtypeids=[], date=''):
        '''
        获取某一天的房型价格，1小时更新一次房价
        '''
        key = self.get_rps_key_ctl(store_id, date)
        rps, discout = self.get_rps_cache_ctl(key, roomtypeids)
        if rps:
            return rps, discout

        state = self.lock_key_ctl(key)
        if not state:
            startime = 0
            sleeptime = 0.1
            while startime <= LOCK_TIME:
                yield gen.sleep(sleeptime)
                rps, discout = self.get_rps_cache_ctl(key, roomtypeids)
                if rps:
                    return rps, discout
                startime += sleeptime
            raise utils.APIError(errcode=50000)

        days = 1
        begin_date = utils.str_to_timestamp(date)
        sign = self.signature_ctl(ERP['app_secret'], begin_date, days)
        req_url = httputil.url_concat(address + ERP['room_price_url'], {
            'days': days,
            'appid': ERP['app_id'],
            'begindate': begin_date,
            'time': int(time.time()),
            'poiid': store_id,
            'ktvid': store_id,
            'sign': sign
        })
        request = utils.http_request(req_url)
        resp = yield utils.get_response(request)
        self.ctrl.rs.set(key, json.dumps(resp), 5*60)

        return self.filter_items_ctl(resp['list'], roomtypeids), resp.get('discout', '')

    @gen.coroutine
    def get_room_number(self, store_id, address, begintime, endtime, roomtypeids=[]):
        '''
        获取某个时间区间的包房库存
        '''
        key = self.get_rn_key_ctl(store_id, begintime, endtime)
        cache = self.get_rn_cache_ctl(key, roomtypeids)
        if cache:
            return cache

        state = self.lock_key_ctl(key)
        if not state:
            startime = 0
            sleeptime = 0.1
            while startime <= LOCK_TIME:
                yield gen.sleep(sleeptime)
                cache = self.get_rn_cache_ctl(key, roomtypeids)
                if cache:
                    return cache
                startime += sleeptime
            raise utils.APIError(errcode=50000)

        begin_time = utils.timestr_to_timestamp(begintime)
        end_time = utils.datetime_to_timestamp(endtime)
        sign = self.signature_ctl(ERP['app_secret'], begin_time, end_time)
        req_url = httputil.url_concat(address + ERP['room_type_num_url'], {
            'appid': ERP['app_id'],
            'begintime': begin_time,
            'endtime': end_time,
            'time': int(time.time()),
            'poiid': store_id,
            'ktvid': store_id,
            'sign': sign
        })
        request = utils.http_request(req_url)
        resp = yield utils.get_response(request)
        self.ctrl.rs.set(key, json.dumps(resp), 15)

        return self.filter_items_ctl(resp['roomDetails'], roomtypeids)

    def _get_recipe_cache(self, key, start, stop):
        if self.ctrl.rs.exists(key):
            pl = self.ctrl.rs.pipeline(transaction=False)
            recipes, total = pl.lrange(key, start, stop).llen(key).execute()
            recipes = [eval(recipe.decode()) for recipe in recipes]
            return recipes, total

        return [], 0

    @gen.coroutine
    def get_recipes_type(self, store_id, has_pn=True, page=1, page_size=10):
        '''
        获取酒水小类信息
        '''
        start, stop = utils.start_stop(has_pn, page, page_size)
        key = 'pub_recipe_type_%s' % store_id
        return self._get_recipe_cache_ctl(key, start, stop)

    @gen.coroutine
    def get_recipes_tid(self, store_id, tid, has_pn=True, page=1, page_size=10):
        '''
        根据小类获取酒水信息
        '''
        start, stop = utils.start_stop(has_pn, page, page_size)
        key = 'pub_recipe_%s_%s' %(store_id, tid)
        return self._get_recipe_cache_ctl(key, start, stop)

    @gen.coroutine
    def get_recipes(self, store_id, has_pn=True, page=1, page_size=10):
        '''
        获取酒水信息
        '''
        start, stop = utils.start_stop(has_pn, page, page_size)
        key = 'pub_recipe_%s' %store_id
        return self._get_recipe_cache_ctl(key, start, stop)

    @gen.coroutine
    def fetch_next_page(self, key, req_url):
        request = utils.http_request(req_url)
        recipes = yield utils.get_response(request)
        if recipes['lv']:
            pl = self.ctrl.rs.pipeline(transaction=False)
            pl.rpush(key, *recipes['lv']).expire(key, A_HOUR).execute()

    @gen.coroutine
    def lock_room(self, store_id, address, roomtypeid, itemid, app_key, cp_order_id, begintime, endtime, is_paid,
                  book_username, book_mobile, arrivetime, roomtype, hours, payfee, offpayfee, cp_payfee, app_name, remark, is_fix,
                  hasPackage, packageId, packagePrice, packagePayMoney, payType, cardNo, roomPayMoney, customerType='', price=0, v2=0,
                  prepayType=0, prepayMoney=0, recipeFeeRuleId=0):
        '''
        在线预订房间
        '''
        state = self.lock_key_ctl('br_%s_%s' % (app_key, cp_order_id))
        if not state:
            raise utils.APIError(errcode=50006)

        # 0元不用支付, 直接下单成功
        if int(cp_payfee*100)==0 or int(payType)==2:
            is_paid = 1

        today = str(when.today())
        sign = self.signature_ctl(ERP['app_secret'], book_mobile, today)
        body = {
            'appid': ERP['app_id'],
            'mark': app_name,
            'time': int(time.time()),
            'sign': sign,
            'orderId': cp_order_id,
            'refItemId': itemid,
            'refRoomTypeId': roomtypeid,
            'refDateId': '',
            'refPeriodId': '',
            'roomType': roomtype,
            'startTime': begintime,
            'endTime': endtime,
            'singHours': hours,
            'paid': is_paid,
            'mobileNo': book_mobile,
            'bookName': book_username,
            'bookDate': today,
            'arriveDate': arrivetime,
            'price': str(price) if v2 else str(payfee),
            'quantity': 1,
            'bookingremark': remark,
            'poiid': store_id,
            'ktvid': store_id,
            'totalPrice': str(price) if v2 else str(payfee),
            'payType': int(payType),
            'roomPayMoney': float(roomPayMoney),
            'cardNo': cardNo,
            'customerType': customerType,
            'prepayType': prepayType,
            'prepayMoney': prepayMoney,
            'recipeFeeRuleId': recipeFeeRuleId
        }

        if hasPackage:
            body.update({
                'hasPackage': int(hasPackage),
                'packageId': packageId,
                'packagePrice': float(packagePrice),
                'packagePayMoney': float(packagePayMoney),
            })

        request = utils.http_request(
            address + ERP['book_url'],
            method='POST',
            body=json.dumps(body),
            headers={'Content-Type': 'application/json'})

        resp = yield utils.get_response(request)

        ktv_order_id = resp['orderId']
        if not ktv_order_id:
            raise utils.APIError(errcode=10012)

        data = {
            'ktv_order_id': ktv_order_id.strip(),
            'cp_order_id': cp_order_id,
            'store_id': store_id,
            'room_type_id': roomtypeid,
            'room_type': roomtype,
            'book_begin_time': begintime,
            'book_end_time': endtime,
            'arrive_time': arrivetime,
            'book_user_name': book_username,
            'book_mobile': book_mobile,
            'is_paid': is_paid,
            'online_pay_fee': payfee,
            'offline_pay_fee': offpayfee,
            'app_key': app_key,
            'app_name': app_name,
            'cp_pay_fee': cp_payfee,
            'remark': remark,
            'is_fix': is_fix
        }

        pay_order = self.api.add_pay_order(**data)

        return pay_order

    @gen.coroutine
    def change_order(self, store_id, app_name, cp_order_id, address, app_key, ordertype=2):
        '''
        修改订单状态，0未支付，1支付成功，2订单取消
        '''
        # state = self.lock_key_ctl('cor_%s_%s' % (app_key, cp_order_id))
        # if not state:
        #     raise utils.APIError(errcode=50006)
        #
        # time_stamp = int(time.time())
        # sign = self.signature_ctl(ERP['app_secret'], time_stamp, cp_order_id, ordertype)
        # req_url = httputil.url_concat(address + ERP['change_order_url'], {
        #     'appid': ERP['app_id'],
        #     'time': time_stamp,
        #     'webbookingno': cp_order_id,
        #     'ordertype': ordertype,
        #     'mark': app_name,
        #     'poiid': store_id,
        #     'ktvid': store_id,
        #     'sign': sign
        # })
        # request = utils.http_request(req_url)
        # yield utils.get_response(request)

        self.ctrl.api.update_pay_order_ctl(app_key, cp_order_id, {
            'is_paid': ordertype
        })

    @gen.coroutine
    def order_recipe_by_room(self, store_id, cp_roid, payfee, offpayfee,
                     cp_payfee, app_key, app_name, recipe, room_info, phone, remark, cardno, paytype):
        '''
        通过房间名预订酒水小吃
        '''
        state = self.lock_key_ctl("ore_%s_%s"%(app_key, cp_roid))
        if not state:
            raise utils.APIError(errcode=50006)

        time_stamp = int(time.time())
        bookno = ''
        sign = self.signature_ctl(ERP['app_secret'], time_stamp, bookno, app_name, recipe)

        req_url = 'http://%d.ngrok.ktvsky.com/erp/orderrecipenew' % int(store_id)

        body = {
            'appid': ERP['app_id'],
            'time': time_stamp,
            'webno': cp_roid,
            'strrecipe': recipe,
            'mark': app_name,
            'price': str(payfee),
            'userid': '',
            'usename': '',
            'remark': remark,
            'roominfo':room_info,
            'phone':phone,
            'poiid': store_id,
            'ktvid': store_id,
            'bookno': bookno,
            'sign': sign,
            'paytype': int(paytype),
            'cardno': cardno,
            'paymoney': float(cp_payfee),
        }

        request = utils.http_request(req_url, method='POST', body=json.dumps(body), headers={'Content-Type': 'application/json'})
        resp = yield utils.get_response(request)

        ktv_roid = resp['orderno']
        if not ktv_roid:
            raise utils.APIError(errcode=10012)

        data = {
            'store_id': store_id,
            'ktv_roid': ktv_roid,
            'cp_roid': cp_roid,
            'online_pay_fee': payfee,
            'offline_pay_fee': offpayfee,
            'cp_pay_fee': cp_payfee,
            'app_key': app_key,
            'app_name': app_name,
            'room_info': room_info,
            'recipe': recipe
        }

        pay_order = self.api.add_recipe_order(**data)

        return pay_order

    @gen.coroutine
    def cancel_recipe(self, store_id, address, cp_roid, app_key, app_name, ordertype=2):
        '''
        取消酒水小吃订单
        '''
        state = self.lock_key_ctl("cre_%s_%s"%(app_key, cp_roid))
        if not state:
            raise utils.APIError(errcode=50006)

        time_stamp = int(time.time())
        sign = self.signature_ctl(ERP['app_secret'], time_stamp, cp_roid, ordertype)
        req_url = httputil.url_concat(address + ERP['recipe_change_url'], {
            'appid': ERP['app_id'],
            'webno': cp_roid,
            'ordertype': ordertype,
            'time': time_stamp,
            'mark': app_name,
            'poiid': store_id,
            'ktvid': store_id,
            'sign': sign
        })
        request = utils.http_request(req_url)
        yield utils.get_response(request)

        self.ctrl.api.update_recipe_order_ctl(app_key, cp_roid, {
            'is_paid': ordertype
        })

    @gen.coroutine
    def get_ktv(self, store_id):
        req_url = DAREN['service_url'] % store_id
        request = utils.http_request(req_url)
        resp = (yield utils.get_response(request))['result']
        ktv = {}
        if resp:
            ktv = resp['matches'][0]
        return ktv

    def publish_recipes(self, ktv_id, data):
        get_key = lambda x: self.get_recipe_key_ctl(x)
        self.drop_cache_recipe_ctl(ktv_id)

        all_recipes = []
        all_type = []
        pl = self.ctrl.rs.pipeline(transaction=False)
        for o in data:
            val = o.pop('list', '')
            logging.info('subtype %s is \n%s'%(o['id'], val))
            if val:
                all_type.append(o)
                key = get_key('%s_%s' % (ktv_id, o['id']))
                pl.rpush(key, *val)
                all_recipes.extend(val)

        key = get_key('type_%s' % ktv_id)
        logging.info('recipe type of %s is %s, all recipe is %s'%(ktv_id, all_type, all_recipes))
        if all_type:
            pl.rpush(key, *all_type)
        key = get_key(ktv_id)
        if all_recipes:
            pl.rpush(key, *all_recipes)
        pl.execute()
