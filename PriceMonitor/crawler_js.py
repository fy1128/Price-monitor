#!/usr/bin/env python3
# coding=utf-8
import requests
import json
from lxml import etree
from CONFIG import PROXY_CRAWL
from proxy import Proxy
import logging


class Crawler(object):
    # TODO: Move get_url to independent function
    # TODO: Add them to sql

    def __init__(self):
        if PROXY_CRAWL == 1:
            # Using free proxy pool
            proxy_info = pr.get_proxy(0)  # tuple: header, proxy
        elif PROXY_CRAWL == 2:
            # Using zhima proxy
            if not self.proxy_info_zhima:
                self.proxy_info_zhima = pr.get_proxy_zhima()
            print('Name proxy:', self.proxy_info_zhima, items)

        else:
            self.header = Proxy.get_ua()
            self.proxy = None

    def get_info_huihui(self, item_id):
        url = 'https://zhushou.huihui.cn/productSense?phu=https://item.jd.com/' + item_id + '.html'
        logging.debug('Ready to crawl huihui price URL：%s', url)
        r = self.load_html(url, 'huihui')

        try:
            max_price = r.json()['max']
            min_price = r.json()['min']
            logging.info('max and min price: %s, %s', max_price, min_price)
            return max_price, min_price

        except AttributeError as e:
            logging.info(e, 'Catch huihui failed with remote error')
            return False

    def get_subtitle_jd(self, item_id):
        url = 'https://cd.jd.com/promotion/v2?callback=jQuery6525446&skuId=' + item_id + \
              '5181380&area=1_72_2799_0&shopId=1000000904&venderId=1000000904&cat=9987%2C653%2C655'
        logging.debug('Ready to crawl jd subtitle URL：%s', url)
        r = self.load_html(url, 'subtitle')

        try:
            subtitle = r.text
        except AttributeError as e:
            logging.info(e, 'Catch subtitle failed with remote error')
            return False

        try:
            subtitle = subtitle[14:-1]
            print(subtitle)
            subtitle_js = json.loads(str(subtitle))
        except json.decoder.JSONDecodeError as e:
            logging.info('Captcha error: %s', e)
            return False
        logging.info('subtitle: %s, %s', subtitle)
        return subtitle_js['ads'][0]['ad']

    def get_price_jd(self, item_id):
        url = 'https://p.3.cn/prices/mgets?callback=&skuIds=J_' + item_id
        logging.debug('Ready to crawl JD price URL：%s', url)
        r = self.load_html(url, 'stock')

        try:
            price = r.text
        except AttributeError as e:
            logging.info(e, 'Catch price failed with remote error')
            return '-1'

            # can not use status code because wrong id also get 200
        if price == 'skuids input error\n':  # Avoid invalid item id
            js_fake = '-1'
            return js_fake
        try:
            price = price[2:-4]
            price_js = json.loads(str(price))
        except json.decoder.JSONDecodeError as e:
            logging.info('Captcha error: %s', e)
            return False
        logging.info('Item: %s ,price JS: %s', item_id, price_js)
        return price_js['p']

    def get_stock_jd(self, item_id, area):
        url = 'https://c0.3.cn/stocks?type=batchstocks&skuIds=' + item_id + '&area=' + area
        logging.debug('Ready to crawl JD stock URL：%s', url)
        r = self.load_html(url, 'stock')

        try:
            # can not use status code because wrong id also get 200
            if r.status_code != 200:  # Avoid invalid item id
                js_fake = -1
                return js_fake
        except AttributeError as e:
            logging.info(e, 'Catch stock failed with remote error')
            return '-1'

        try:
            stock_js = json.loads(str(r.text))
        except json.decoder.JSONDecodeError as e:
            logging.info('Captcha error: %s', e)
            return False
        logging.info('Item: %s ,stock JS: %s', item_id, stock_js)
        return stock_js[item_id]['StockState']

    def get_name_jd(self, item_id):
        url = 'https://item.jd.com/' + item_id + '.html'
        logging.debug('Ready to crawl JD name URL：%s', url)

        r = self.load_html(url, 'name')

        try:  # normal
            selector = etree.HTML(r.text)
            name = selector.xpath("//*[@class='sku-name']/text()")  # list
            name_true = ' '.join(name).strip()
            if not len(name_true):  # jd chaoshi
                logging.info('Change method to catch name: jd chaoshi')
                name_true = name[1].strip()
        except AttributeError as e:
            logging.info(e, 'Catch name failed with remote error')
            name_true = '本轮抓取该商品名称失败，请等待重试'
        except IndexError as e:
            logging.info(e, name)
            logging.info('Change method to catch name: jd jingxuan')
            try:  # jd jingxuan
                name = selector.xpath("//*[@id='name']/h1/text()")
                name_true = ' '.join(name).strip()
            except IndexError as e:
                logging.warning(e, name)
                logging.warning('Catch name error')
                name_true = '本轮抓取该商品名称失败，请等待重试'

        logging.info('Item: %s', name_true)
        return name_true

    def load_html(self, url, desc):
        try:
            if self.proxy:  # Using proxy
                logging.info('Using proxy %s to crawl %s', self.proxy, desc)
                res = requests.get(url, headers=self.header, proxies=self.proxy, timeout=6)
            else:  # Not using proxy
                logging.info('Not using proxy to crawl %s', desc)
                res = requests.get(url, headers=self.header, timeout=6)

            return res

        except requests.exceptions.ProxyError as e:
            logging.info('Proxy error: %s', e)
            return ''  # as False
        except requests.exceptions.ConnectionError as e:
            logging.info('Https error: %s', e)
            return ''  # as False
        except requests.exceptions.ReadTimeout as e:
            logging.info('Timeout error: %s', e)
            return ''  # as False
        except requests.exceptions.ChunkedEncodingError as e:
            logging.info('ChunkedEncodingError error: %s', e)
            return ''  # as False


if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO)
    c = Crawler()
    # logging.debug(c.get_price_jd('2777811', {'user-agent': 'Mozilla/5.0 (Windows NT 6.1; WOW64) '
    #                                                    'AppleWebKit/536.6 (KHTML, like Gecko) '
    #                                                    'Chrome/20.0.1092.0 Safari/536.6'}))
    # logging.debug(c.get_name_jd('2777811', {'user-agent': 'Mozilla/5.0 (Windows NT 6.1; WOW64) '
    #                                                       'AppleWebKit/536.6 (KHTML, like Gecko) '
    #                                                       'Chrome/20.0.1092.0 Safari/536.6'}))
    logging.debug(c.get_subtitle_jd('5181380', {'user-agent': 'Mozilla/5.0 (Windows NT 6.1; WOW64) '
                                                          'AppleWebKit/536.6 (KHTML, like Gecko) '
                                                          'Chrome/20.0.1092.0 Safari/536.6'}))
    # logging.debug(c.get_info_huihui('2777811', {'user-agent': 'Mozilla/5.0 (Windows NT 6.1; WOW64) '
    #                                                           'AppleWebKit/536.6 (KHTML, like Gecko) '
    #                                                           'Chrome/20.0.1092.0 Safari/536.6'}))
