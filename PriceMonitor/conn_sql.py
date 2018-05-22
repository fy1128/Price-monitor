#!/usr/bin/env python3
# coding=utf-8
from gevent import monkey  # IMPORT: must import gevent at first
monkey.patch_all()
import logging
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from create_db import Base, User, Monitor, SmartPhone_9987653655
import datetime
import math
from CONFIG import DISCOUNT_LIMIT, ALERT_EXT


class Sql(object):

    engine = create_engine('sqlite:///db_demo.db', echo=True)
    # engine = create_engine('mysql+pymysql://root:root@localhost/pricemonitor?charset=utf8&autocommit=true')
    Base.metadata.bind = engine
    DBSession = sessionmaker(bind=engine)
    session = DBSession()

    def read_all_not_updated_item(self, update_time):
        time_now = datetime.datetime.now()
        need_item = []
        all_items = self.session.query(Monitor).filter_by(enable=1).all()
        for item in all_items:

            time_delta = (time_now - item.update_time).days * 86400 + (time_now - item.update_time).seconds
            logging.info('%s\'s time delta: %s', item.item_id, time_delta)
            if time_delta >= update_time:
                item = dict(item.__dict__)
                item.pop('_sa_instance_state', None)
                need_item.append(item)
        return need_item

    def check_item_need_to_remind(self, prev_items = None, curr_items = None):
        monitor_items = []
        alert_items = []
        if curr_items is None:
            items = self.session.query(Monitor).all()
        else:
            items = curr_items

        notice_items = {}
        if prev_items is not None:
            alert_ext = ALERT_EXT.lower().split(',')
            curr_items = {item['item_id']: item if isinstance(item, dict) else item.__dict__ for item in items}
            for item in prev_items:
                item_id = item['item_id']
                item['ext'] = item['ext'] if isinstance(item['ext'], dict) else {}
                curr_item = curr_items[item_id]
                if curr_item['updated'] == 0:
                    continue

                # do not continue if out of stock
                stock = curr_item['ext']['stock']
                if not stock or stock == 34:
                    continue

                user = self.session.query(User).filter_by(column_id=item['user_id'])
                #monitor_items[item_id] = []
                
                # fields of item to be return
                base_item = [user[0].email,
                            curr_item['item_name'] if curr_item['item_name'] is not False else item['item_name'],
                            curr_item['subtitle'] if curr_item['subtitle'] is not False else '抓取子标题失败',
                            item['item_price'], curr_item['item_price'], 
                            curr_item['user_price'], curr_item['item_id'], curr_item['column_id'],
                            curr_item['highest_price'] if curr_item['highest_price'] is not None else '',
                            curr_item['lowest_price'] if curr_item['lowest_price'] is not None else '',
                            []]
                
                if item['discount'] and float(item['discount']) <= DISCOUNT_LIMIT:
                    alert_items.append([user[0].email, curr_item['item_name'], curr_item['subtitle'], item['item_price'], curr_item['item_price'],
                                        curr_item['discount'], curr_item['item_id'], curr_item['column_id'], curr_item['highest_price'], curr_item['lowest_price']])

                if item['user_price']:
                    if curr_item['item_price'] and item['item_price'] is not None and float(curr_item['item_price']) != float(item['item_price']) and float(item['user_price']) > float(curr_item['item_price']):  # User-defined monitor price items
                        base_item[10].append('降')

                if 'name' in alert_ext:
                    if curr_item['item_name'] and item['item_name'] != curr_item['item_name']:
                        base_item[10].append('变')

                if 'stock' in alert_ext:
                    prev_stock = item['ext']['stock'] if 'stock' in item['ext'] else None
                    if prev_stock != stock:
                        base_item[10].append('货')

                if 'coupon' in alert_ext:
                    coupon = curr_item['ext']['coupon']
                    prev_coupon = item['ext']['coupon'] if 'coupon' in item['ext'] else None
                    if coupon and len(coupon) > 0 and prev_coupon != coupon:
                        base_item[10].append('券')
                
                if 'promo' in alert_ext:
                    promo = curr_item['ext']['promo']
                    prev_promo = item['ext']['promo'] if 'promo' in item['ext'] else None
                    if promo and len(promo) > 0 and prev_promo != promo:
                        base_item[10].append('促')

                if len(base_item[10]) > 0:
                    monitor_items.append(base_item)

        # append the previous items failed to send mail
        items_need_mail = self.session.query(Monitor).filter_by(status=1).limit(10)
        for item in items_need_mail:
            user = self.session.query(User).filter_by(column_id=item.user_id)
            monitor_items.append([user[0].email,
                                item.item_name if item.item_name is not None else '',
                                item.subtitle if item.subtitle is not None else '',
                                item.last_price, item.item_price, 
                                item.user_price, item.item_id, item.column_id,
                                item.highest_price if item.highest_price is not None else '',
                                item.lowest_price if item.lowest_price is not None else '',
                                []])
            
        return monitor_items, alert_items

    def check_cate_item_need_to_remind(self):
        # TODO: use cate_name parameter
        alert_items = []
        items = self.session.query(SmartPhone_9987653655).filter_by(status=1).all()
        for item in items:
            if item.discount and float(item.discount) <= DISCOUNT_LIMIT:
                alert_items.append([item.item_name, item.item_price, item.discount,
                                    item.item_id, item.column_id, item.last_price, item.subtitle])
                item.status = 0  # set status to 0 for avoiding to send duplicate mails
        return alert_items

    def check_cate_user_mail(self, cate_name):
        user_mails = []
        # TODO: extract cate_name from category string
        users = self.session.query(User).filter_by(category=cate_name).all()
        for user in users:
            user_mails.append(user.email)
        return user_mails

    def write_cate_item(self, item_info):  # item_id, item_name, item_price, subtitle
        if item_info[2] == '暂无报价':  # never store no price item
            return
        time_now = datetime.datetime.now()
        exist = self.session.query(SmartPhone_9987653655).filter_by(item_id=item_info[0]).all()
        if len(exist):  # item already exists in category database
            logging.info('Item id %s already exists in database, update information', item_info[0])
            exist[0].item_name = item_info[1]
            exist[0].subtitle = item_info[3]
            exist[0].update_time = time_now
            if exist[0].item_price != item_info[2]:  # if new price, calculate discount and last_price
                exist[0].status = 1  # set status to 1 for send new alert mail
                exist[0].last_price = exist[0].item_price
                exist[0].item_price = item_info[2]
                logging.debug('last price: {} {}, price: {} {}'.format(type(exist[0].last_price), exist[0].last_price,
                                                                       type(item_info[2]), item_info[2]))
                exist[0].discount = round(float(item_info[2]) / float(exist[0].last_price), 2)  # 0.01
                logging.warning('Item id %s changed price: %s to %s', item_info[0], exist[0].last_price, item_info[2])
        else:
            new_item = SmartPhone_9987653655(item_id=item_info[0], item_name=item_info[1], item_price=item_info[2],
                                             subtitle=item_info[3], status=1, add_time=time_now, update_time=time_now)
            self.session.add(new_item)
        self.session.commit()

    def write_user(self, user_name, email_address, category):
        new_user = User(user_name=user_name, email=email_address, category=category)
        self.session.add(new_user)
        self.session.commit()

    def update_item_name(self, column_id, item_name):
        if not item_name:
            return False

        update_item = self.session.query(Monitor).get(column_id)
        update_item.item_name = item_name
        self.session.commit()

    def update_item_price(self, column_id, item_prices):
        if len(item_prices) == 0:
            return False

        p = min(item_prices.items(), key=lambda x: float(x[1]))[0]
        item_price = float(item_prices[p])
        time_now = datetime.datetime.now()
        update_item = self.session.query(Monitor).get(column_id)
        if update_item.item_price and update_item.item_price != item_price:  # if new price
            update_item.last_price = update_item.item_price
            if float(update_item.last_price) > 0:
                update_item.discount = round(float(item_price) / float(update_item.last_price), 2)  # round(,2) set to 0.01
            else:
                update_item.discount = 0.01

        update_item.item_price = item_price
        update_item.update_time = time_now
        update_item.ext = self.field_ext_init(update_item)
        update_item.ext['prices'] = item_prices
        self.session.commit()
        return item_price, update_item.discount

    def update_item_subtitle(self, column_id, subtitle):
        if not subtitle:
            return False

        update_item = self.session.query(Monitor).get(column_id)
        update_item.subtitle = subtitle
        self.session.commit()

    def update_item_plus_price(self, column_id, plus_price):
        if not plus_price:
            return False

        update_item = self.session.query(Monitor).get(column_id)
        update_item.plus_price = plus_price
        self.session.commit()

    def update_item_max_price(self, column_id, highest_price):
        if not highest_price:
            return False

        update_item = self.session.query(Monitor).get(column_id)
        update_item.highest_price = highest_price
        self.session.commit()

    def update_item_min_price(self, column_id, lowest_price):
        if not lowest_price:
            return False

        update_item = self.session.query(Monitor).get(column_id)
        update_item.lowest_price = lowest_price
        self.session.commit()

    def bulk_update_item_ext(self, column_id, data = {}):
        for name in data:
            self.update_item_ext(column_id, name, data[name])

    def update_item_ext(self, column_id, name, value):
        if not value:
            return False

        update_item = self.session.query(Monitor).get(column_id)
        update_item.ext = self.field_ext_init(update_item)
        update_item.ext[name] = value
        update_item.update_time = datetime.datetime.now()
        self.session.commit()

    def update_status(self, column_id, status = 0):
        if isinstance(column_id, list):
            for update_item in self.session.query(Monitor).filter(Monitor.column_id.in_(tuple(column_id))):
                update_item.status = status

        else:
            update_item = self.session.query(Monitor).get(column_id)
            update_item.status = status

        self.session.commit()

    def field_ext_init(self, update_item):
        update_item.ext = update_item.ext if update_item.ext is not None else {}
        return update_item.ext

if __name__ == '__main__':
    logging.basicConfig(level=logging.DEBUG)
    sql = Sql()

    # add user named 'test'
    # sql.write_user('test', '404013419@qq.com', 'SmartPhone_9987653655')
    # sql.write_user('douya', '7999994@qq.com', 'SmartPhone_9987653655')

    # add test item
    # sql.write_cate_item(['5544068', '【新年货】华为 HUAWEI Mate 10 4GB+64GB 亮黑色 移动联通电信4G手机 双卡双待',
    #                      '3899.00', '【白条6期免息】AI智能拍照！给你年货新选择！猛戳进入主会场>>'])

    # read all items needed update
    # print(sql.read_all_not_updated_item(600))

    # read all user emails for category user
    # print(sql.check_cate_user_mail('SmartPhone_9987653655'))

    # update all items needed update
    # sql.update_item_name(1, '123456')

    # check all items needed to send email
    # print(sql.check_cate_item_need_to_remind())
