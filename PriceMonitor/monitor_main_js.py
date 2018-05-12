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

CRAWLER_POOL = Pool(THREAD_NUM)


class Entrance(object):

    proxy_info_zhima = ()
    proxy_info_zhima = ()

    def _item_info_update(self, item):
        column_id = item.column_id
        item_id = str(item.item_id)
        item_area = str(item.area)
        sq = Sql()
        pr = Proxy()
        cr = Crawler(item_id, item_area)
        if PROXY_CRAWL == 1:
            # Using free proxy pool
            while True:
                proxy_info = pr.get_proxy(0)  # tuple: header, proxy
                name = cr.get_name_jd(item_id, proxy_info[0], proxy_info[1])
                if name:
                    sq.update_item_name(column_id, name)
                    while True:
                        proxy = pr.get_proxy(1)  # tuple: header, proxy
                        price = cr.get_price_jd(item_id, item_area, proxy[0], proxy[1])
                        if price:
                            sq.update_item_price(column_id, price)

                            stock = cr.get_stock_jd(item_id, item_area, pr.get_ua(), proxy[0], proxy[1])
                            if stock:
                                sq.update_item_stock(column_id, stock)

                            huihui_info = cr.get_info_huihui(item_id, pr.get_ua(), proxy[0], proxy[1])
                            if huihui_info:  # skip this if not crawled
                                sq.update_item_max_price(column_id, huihui_info[0])
                                sq.update_item_min_price(column_id, huihui_info[1])

                            break
                    break
        elif PROXY_CRAWL == 2:
            # Using zhima proxy
            while True:
                if not self.proxy_info_zhima:
                    self.proxy_info_zhima = pr.get_proxy_zhima()
                print('Name proxy:', self.proxy_info_zhima, item)
                name = cr.get_name_jd(item_id, self.proxy_info_zhima[0], self.proxy_info_zhima[1])
                if not name:
                    self.proxy_info_zhima = ()
                    time.sleep(20)
                    continue
                else:
                    time.sleep(5)  # Avoid get proxy too fast
                    sq.update_item_name(column_id, name)
                    while True:
                        if not self.proxy_info_zhima:
                            self.proxy_info_zhima = pr.get_proxy_zhima()
                        print('Price proxy:', self.proxy_info_zhima, items)
                        price = cr.get_price_jd(item_id, item_area, self.proxy_info_zhima[0], self.proxy_info_zhima[1])
                        if not price:
                            self.proxy_info_zhima = ()
                            time.sleep(20)
                            continue
                        else:
                            sq.update_item_price(column_id, price)
                            stock = cr.get_stock_jd(item_id, item_area, pr.get_ua(), self.proxy_info_zhima[0], self.proxy_info_zhima[1])
                            if stock:
                                sq.update_item_stock(column_id, stock)

                            huihui_info = cr.get_info_huihui(item_id, pr.get_ua(), self.proxy_info_zhima[0], self.proxy_info_zhima[1])
                            if huihui_info:  # skip this if not crawled
                                sq.update_item_max_price(column_id, huihui_info[0])
                                sq.update_item_min_price(column_id, huihui_info[1])

                            break
                    break
        else:
            # Using local ip
            name = cr.get_name_jd()
            sq.update_item_name(column_id, name)
            prices = cr.get_price_jd()
            price = sq.update_item_price(column_id, prices)
            
            ext = {}
            ext['stock'] = cr.get_stock_jd()
            ext['coupon'] = cr.get_coupon_jd()
            ext['promo'] = cr.get_promo_jd()
            sq.bulk_update_item_ext(column_id, ext)

            huihui_info = cr.get_info_huihui()
            if huihui_info:  # skip this if not crawled
                sq.update_item_max_price(column_id, huihui_info[0])
                sq.update_item_min_price(column_id, huihui_info[1])

            return name, price, ext

    @staticmethod
    def _check_item():
        sq = Sql()
        updated_time = UPDATE_TIME
        items = sq.read_all_not_updated_item(updated_time)
        logging.warning('This loop: %s', [item.item_id for item in items])
        return items

    @staticmethod
    def _send_email(prev_items):
        # Send email in a loop, avoid sending simultaneously.
        sq = Sql()
        items = sq.check_item_need_to_remind()
        logging.warning('This loop sent email: %s', items)

        for item in items[0]:  # email, item_name, item_price, user_price, item_id, column_id
            item_url = 'https://item.jd.com/' + str(item[4]) + '.html'
            email_text = '您监控的物品：' + item[1] + '，现在价格为：' + item[2] + \
                         '，您设定的价格为：' + item[3] + '，赶紧购买吧！' + item_url
            email_subject = '您监控的物品降价了！'
            try:
                send_email = Mail(email_text, 'admin', 'user', email_subject, item[0])
                send_email.send()
                time.sleep(Email_TIME)
            except:
                logging.critical('Sent email failure, skip in this loop: %s', item[0])
                continue
            sq.update_status(item[5])
            logging.warning('Sent email SUCCESS: %s', item[0])

    def run(self):
        while True:
            items = self._check_item()  # create_db.Monitor object
            items_info = CRAWLER_POOL.map(self._item_info_update, items)  # return two values as a tuple
            logging.warning('This loop updated information: %s', items_info)
            self._send_email(items)
            time.sleep(ITEM_CRAWL_TIME)


if __name__ == '__main__':

    log_file_path = path.join(path.dirname(path.abspath(__file__)), 'logger.conf')
    logging.config.fileConfig(log_file_path)
    logger = logging.getLogger("console_file_2")
    ent = Entrance()
    ent.run()



