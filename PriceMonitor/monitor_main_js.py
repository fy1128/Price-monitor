#!/usr/bin/env python3
# coding=utf-8
from gevent import monkey  # IMPORT: must import gevent at first
monkey.patch_all()
from gevent.pool import Pool
from proxy import Proxy
from crawler_js import Crawler
from conn_sql import Sql
from mail import Mail
from CONFIG import ITEM_CRAWL_TIME, UPDATE_TIME, Email_TIME, PROXY_CRAWL, THREAD_NUM
import logging
import logging.config
import time
from os import path  # Supervisor cannot find logger.conf
import sys, random

CRAWLER_POOL = Pool(THREAD_NUM)


class Entrance(object):

    proxy_info_zhima = ()
    proxy_info_zhima = ()

    def _item_info_update(self, item):
        #curr_item = item.__dict__
        # do a copy to avoid old item being changed. some ways
        # new_list = old_list[:]; new_list = list(ld_list); import copy, new_list = copy.deepcopy(old_list)
        curr_item = dict(item)
    

        column_id = item['column_id']
        item_id = str(item['item_id'])
        item_area = str(item['area'])
        sq = Sql()
        cr = Crawler(item_id, item_area)        
        
        #check whether field was updated.
        curr_item['updated'] = 1

        name = cr.get_name_jd()
        updated = sq.update_item_name(column_id, name)
        curr_item['item_name'] = name

        prices = cr.get_price_jd()
        # tunple current price, discount
        updated = price = sq.update_item_price(column_id, prices)
        if not price:
            curr_item['item_price'] = curr_item['discount'] = False
        else:
            curr_item['item_price'] = price[0]
            curr_item['discount'] = price[1]

        subtitle = cr.get_subtitle_jd()
        updated = sq.update_item_subtitle(column_id, subtitle)
        curr_item['subtitle'] = subtitle
        
        ext = {}
        ext['stock'] = cr.get_stock_jd()
        ext['coupon'] = cr.get_coupon_jd()
        ext['promo'] = cr.get_promo_jd()
        sq.bulk_update_item_ext(column_id, ext)
        curr_item['ext'] = ext

        huihui_info = cr.get_info_huihui()
        if huihui_info:  # skip this if not crawled
            sq.update_item_max_price(column_id, huihui_info[0])
            sq.update_item_min_price(column_id, huihui_info[1])
            updated = curr_item['highest_price'] = huihui_info[0]
            updated = curr_item['lowest_price'] = huihui_info[1]

        if not updated:
            curr_item['updated'] = 0

        return curr_item

    @staticmethod
    def _check_item():
        sq = Sql()
        updated_time = UPDATE_TIME
        items = sq.read_all_not_updated_item(updated_time)
        logging.warning('This loop: %s', [item['item_id'] for item in items])
        return items

    @staticmethod
    def _send_email(prev_items = None, curr_items = None):
        # Send email in a loop, avoid sending simultaneously.
        sq = Sql()
        items = sq.check_item_need_to_remind(prev_items, curr_items)

        items_stdout =[]
        mail_map = {}
        for item in items[0]:  # email, item_name, item_price, user_price, item_id, column_id
            if item[0] not in mail_map:
                mail_map[item[0]] = {'mon': {'ids': [], 'msg': []}}

            # skip duplicate item in items_need_mail
            if item[7] in mail_map[item[0]]['mon']['ids']:
                continue

            mail_map[item[0]]['mon']['ids'].append(item[7])
                
            item_url = 'https://item.jd.com/' + str(item[6]) + '.html'
            email_text = ', '.join(item[10]) + '！\n' + \
                         '物品：' + item[1] + '，\n' + \
                         '现在价格为：' + str(item[4]) + '，\n' + \
                         '上次监控价格为：' + str(item[3]) + '，\n' + \
                         '您设定的价格为：' + str(item[5]) + '，赶紧购买吧！\n' + \
                         '子标题：' + item[2] + '，\n' + \
                         '历史最高价参考：' + str(item[8]) + '，\n' + \
                         '历史最低价参考：' + str(item[9]) + '，\n' + \
                         item_url

            items_stdout.append({item[6]: item[1]})
            mail_map[item[0]]['mon']['msg'].append(email_text)

        email_subject = '您监控类别中的物品大幅度降价了！'
        for item in items[1]:  # email, item_name, item_price, discount, item_id, column_id, last_price
            if item[0] not in mail_map:
                mail_map[item[0]] = {'alert': {'ids': [], 'msg': []}}

            if 'alert' not in mail_map[item[0]]:
                mail_map[item[0]]['alert'] = {'ids': [], 'msg': []}

            mail_map[item[0]]['alert']['ids'].append(item[7])
            item_url = 'https://item.jd.com/' + str(item[6]) + '.html'
            email_text = '物品：' + item[1] + '，\n' + \
                         '现在价格为：' + str(item[4]) + '，\n' + \
                         '上次监控价格为：' + str(item[3]) + '，\n' + \
                         '降价幅度为：' + str(100 * float(item[3])) + '折，赶紧购买吧！\n' + \
                         '子标题：' + item[2] + '，\n' + \
                         '历史最高价参考：' + str(item[8]) + '，\n' + \
                         '历史最低价参考：' + str(item[9]) + '，\n' + \
                         item_url

            items_stdout.append({item[6]: item[1]})
            mail_map[item[0]]['alert']['msg'].append(email_text)

            
        logging.warning('This loop sent email: %s', items_stdout)

        items_processed = {'s': [], 'f': []}
        for user, msg in mail_map.items():
            for type, msg_text in msg.items():
                if type == 'mon':
                    email_subject = '您监控的物品有变更！'

                elif type == 'alert':
                    email_subject = '您监控类别中的物品大幅度降价了！'

                try:
                    send_email = Mail('\n\n\n'.join(msg_text['msg']), 'admin', 'user', email_subject, user)
                    send_email.send()
                    items_processed['s'] = items_processed['s'] + msg_text['ids']
                    time.sleep(Email_TIME)
                except Exception as e:
                    logging.critical('Sent email failure with error: %s, skip in this loop: %s', e, user)
                    items_processed['f'] = items_processed['f'] + msg_text['ids']
                    continue

            logging.warning('Finish sending email to user: %s', user)
        
        sq.update_status(items_processed['f'], 1)
        sq.update_status(items_processed['s'], 0)

    def run(self):
        while True:
            start = time.time()
            items = self._check_item()  # dict of create_db.Monitor object
            items_info = CRAWLER_POOL.map(self._item_info_update, items)  # return two values as a tuple
            logging.warning('This loop updated information: %s', [{item['item_id']: item['item_name']} for item in items_info])
            self._send_email(items, items_info)
            time_cost = (time.time() - start)

            RAND_INT = random.randint(-5,5)
            SLEEP_INTERVAL_RANDOM = int(ITEM_CRAWL_TIME - time_cost + RAND_INT)
            if SLEEP_INTERVAL_RANDOM < 1:
                SLEEP_INTERVAL_RANDOM = 1

            sys.stdout.write("\n")
            for i in range(SLEEP_INTERVAL_RANDOM,0,-1):
                sys.stdout.write("\r等待 " + str(i)+"秒 更新..."+"\r")
                time.sleep(1)
                sys.stdout.flush()

if __name__ == '__main__':

    log_file_path = path.join(path.dirname(path.abspath(__file__)), 'logger.conf')
    logging.config.fileConfig(log_file_path)
    logger = logging.getLogger("console_file_2")
    ent = Entrance()
    ent.run()



