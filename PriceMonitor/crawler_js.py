#!/usr/bin/env python3
# coding=utf-8
import requests
import json
from lxml import etree
from CONFIG import PROXY_CRAWL
from proxy import Proxy
import logging
import time
import random
import operator
import re

class Crawler(object):
    # TODO: Move get_url to independent function
    # TODO: Add them to sql

    def __init__(self, item_id, area):
        self.item_id = item_id
        self.area = area
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
            self.skuInfo = self.get_skuinfo_jd()

    def get_info_huihui(self):
        url = 'https://zhushou.huihui.cn/productSense?phu=https://item.jd.com/' + self.item_id + '.html'
        logging.debug('Ready to crawl huihui price URL：%s', url)
        r = self.load_html(url, 'huihui')

        try:
            max_price = r.json()['max']
            min_price = r.json()['min']
            logging.info('max and min price: %s, %s', max_price, min_price)
            return max_price, min_price

        except AttributeError as e:
            logging.warning(e, 'Catch huihui failed with remote error')
            return False

    def get_subtitle_jd(self):
        subtitle = None
        if self.skuInfo:
            try:
                subtitle = re.sub(r'<[^>]*?>', '', self.skuInfo['AdvertCount']['ad'])
            except KeyError as e:
                logging.warning('Get subtitle from sku info failed with error: %s', e)
                pass

        if subtitle is None:
            subtitle = self._get_promo_jd('subtitle')
            if not subtitle:
                logging.warning('Captcha subtitle failed!')
                return False

        logging.info('subtitle: %s', subtitle)
        return subtitle

    def get_price_jd(self):
        price = None
        prices = self.get_prices_jd()

        if self.skuInfo:
            try:
                logging.debug('Ready to get price from sku info!')
                price = self.skuInfo['price']['p']
            except KeyError as e:
                logging.warning('Get price from sku info failed with error: %s', e)
                pass

        if price is None:
            url = 'https://p.3.cn/prices/mgets?callback=&skuIds=J_' + self.item_id
            logging.debug('Ready to crawl JD price URL：%s', url)
            r = self.load_html(url, 'price')    

            try:
                price = r.text
            except AttributeError as e:
                logging.warning(e, 'Catch price failed with remote error')
                return prices

                # can not use status code because wrong id also get 200
            if price == 'skuids input error\n':  # Avoid invalid item id
                return prices
            try:
                price = price[2:-4]
                price_js = json.loads(str(price))
                price = price_js['p']
            except json.decoder.JSONDecodeError as e:
                logging.warning('Captcha price error: %s', e)
                return prices
            
        prices['p'] = price
        logging.info('Item: %s ,price JS with all platforms: %s', self.item_id, prices)
        return prices

    def get_prices_jd(self):
        data={}
        platform = {'m': 'mobile', 'w': 'wechat', 'q': 'qq'}
        price_urls = {'m':'https://pm.3.cn/prices/mgets?origin=2&area=' + self.area + '&pdtk=&pduid=&pdpin=&pdbp=0&skuIds=' + self.item_id, 'w':'https://pe.3.cn/prices/mgets?origin=5&area=' + self.area + '&pdtk=&pduid=&pdpin=&pdbp=0&skuids=' + self.item_id, 'q':'https://pe.3.cn/prices/mgets?origin=4&area=' + self.area + '&pdtk=&pduid=&pdpin=&pdbp=0&skuids=' + self.item_id}
        if self.skuInfo:
            try:
                data['m'] = self.skuInfo['price']['p']
                del price_urls['m']
                logging.info('Got mobile price from sku info successfully, skipped.')
            except KeyError as e:
                logging.info("Got mobile price from sku info failed, going to crawl in the original way.")
                pass

        for k, v in price_urls.items():
            time.sleep(1)
            try:
                r = self.load_html(price_urls[k], 'prices of ' + platform[k])
                data[k] = r.json()[0]['p']
            except AttributeError as e:
                logging.warning("Get price from「" + platform[k] + "」failed...")
                continue
                pass

        if len(data) > 0:
            logging.info('Prices %s', {platform[k]: v for k,v in data.items()})
        else:
            logging.warning('Got prices failed')
        
        return data

        
    def get_stock_jd(self):
        stock = None
        if self.skuInfo:
            try:
                logging.debug('Ready to get stock from sku info!')
                stock = self.skuInfo['stock']['StockState']
            except KeyError as e:
                logging.warning('Get stock from sku info failed with error: %s', e)
                pass

        if stock is None:
            url = 'https://c0.3.cn/stocks?type=batchstocks&skuIds=' + self.item_id + '&area=' + self.area
            logging.debug('Ready to crawl JD stock URL：%s', url)
            r = self.load_html(url, 'stock')

            try:
                # can not use status code because wrong id also get 200
                if r.status_code != 200:  # Avoid invalid item id
                    return False

            except AttributeError as e:
                logging.warning(e, 'Catch stock failed with remote error')
                return False

            try:
                stock_js = json.loads(str(r.text))
                stock = stock_js[self.item_id]['StockState']
            except json.decoder.JSONDecodeError as e:
                logging.warning('Captcha stock error: %s', e)
                return False

        logging.info('Item: %s, stock JS: %s', self.item_id, stock)
        return stock

    def get_coupon_jd(self):
        coupons = []
        """Use post method to query whether there is a coupon."""
        #Communication procedure seen on httptrace extension in Chrome.
        #headers = {"Connection": "keep-alive", "Content-Type": "application/x-www-form-urlencoded"}
        #req = urllib.request.Request(url = 'https://item.m.jd.com/coupon/coupon.json', data = bytes("wareId=%s"%self.id_i, "ascii"), headers = headers, method = "POST")
        url = 'https://item.m.jd.com/coupon/coupon.json?wareId=' + self.item_id
        data = bytes("wareId=%s" % self.item_id, "ascii")
        r = self.load_html(url, 'coupon', {}, data)

        try:
            #Escape the " for eval use.
            #content = json.dumps(json.loads(r.text)["coupon"]).replace("true", "\"true\"").replace("false", "\"false\"")
            content = r.json()['coupon']
        except (AttributeError, KeyError) as e:
            logging.warning(e, 'Catch coupon failed with remote error')
            return False

        content = sorted(content, key=operator.itemgetter('encryptedKey'))
        for coupon in content:
            coupons.append(str(coupon["discount"])+"满"+str(coupon["quota"])+coupon["name"])

        logging.info('Item: %s, coupon JS: %s', self.item_id, coupons)
        return coupons
   
    def get_promo_jd(self):
        promo = []
        if self.skuInfo:
            try:
                logging.debug('Ready to get promo from sku info!')
                for item in self.skuInfo['promov2']:
                    if 'pis' not in item:
                        continue

                    pis = sorted(item['pis'], key=operator.itemgetter('pid'))
                    for pi in pis:
                        if '15' not in pi:
                            continue
                            
                        promo.append(re.sub(r'<[^>]*?>', '', pi['15']))

            except KeyError as e:
                logging.warning('Get promo from sku info failed with error: %s', e)

                promo = self._get_promo_jd('promo')
                if not promo:
                    logging.warning('Captcha promo error')
                    return False

        logging.info('Item: %s ,promo JS: %s', self.item_id, promo)
        return promo


    def _get_promo_jd(self, name):
        result = False
        url = 'https://cd.jd.com/promotion/v2?callback=jQuery6525446&skuId=' + self.item_id + \
              '5181380&area=' + self.area + '&shopId=1000000904&venderId=1000000904&cat=9987%2C653%2C655'
        r = self.load_html(url, 'promotion')

        try:
            promotion = r.text.strip()
        except AttributeError as e:
            logging.warning(e, 'Catch promotion failed with remote error')
            return False

        try:
            promotion = promotion[14:-1]
            promotion_js = json.loads(str(promotion))
        except json.decoder.JSONDecodeError as e:
            logging.warning('Captcha promotion error: %s', e)
            return False

        if name == 'subtitle':
            try:
                result = re.sub(r'<[^>]*?>', '', promotion_js['ads'][0]['ad'])
            except KeyError as e:
                logging.info(name + ': maybe empty: %s', e)
                return False
        
        if name == 'promo':
            result = []
            try:
                tags = promotion_js['prom']['pickOneTag']
                for item in tags:
                    if 'code' in tags and tags['code'] == '15':
                        result.append(re.sub(r'<[^>]*?>', '', tags['content']))

            except KeyError as e:
                logging.info(name + ': maybe empty: %s', e)
                return False
            
        logging.info(name + ': %s', result)
        return result

    def get_name_jd(self):
        name = None
        if self.skuInfo:
            try:
                logging.debug('Ready to get name from sku info!')
                name = self.skuInfo['skuName'].strip()
            except KeyError as e:
                logging.warning('Get name from sku info failed with error: %s', e)
                pass
                
        if name is None:
            url = 'https://item.jd.com/' + self.item_id + '.html'
            logging.debug('Ready to crawl JD name URL：%s', url)

            r = self.load_html(url, 'name')

            try:  # normal
                selector = etree.HTML(r.text)
                name = selector.xpath("//*[@class='sku-name']/text()")  # list
                name = ' '.join(name).strip()
                if not len(name):  # jd chaoshi
                    logging.warning('Change method to catch name: jd chaoshi')
                    name = name[1].strip()
            except AttributeError as e:
                logging.warning(e, 'Catch name failed with remote error')
                return False
            except IndexError as e:
                logging.warning(e, name)
                logging.warning('Change method to catch name: jd jingxuan')
                try:  # jd jingxuan
                    name = selector.xpath("//*[@id='name']/h1/text()")
                    name = ' '.join(name).strip()
                except IndexError as e:
                    logging.warning(e, name)
                    logging.warning('Catch name error')
                    return False

        logging.info('Item: %s, name: %s', self.item_id, name)
        return name

    def load_html(self, url, desc='', cookies = {}, data=None):
        s = requests.session()
        try:
            if data is not None: # get
                if self.proxy:  # Using proxy
                    logging.info('Using proxy %s to crawl %s', self.proxy, desc)
                    res = s.get(url, cookies = cookies, headers = self.header, proxies = self.proxy, timeout=6)
                else:  # Not using proxy
                    logging.info('Not using proxy to crawl %s', desc)
                    res = s.get(url, cookies = cookies, headers = self.header, timeout=6)

                return res

            else: # post
                if self.proxy:  # Using proxy
                    logging.info('Using proxy %s to crawl %s', self.proxy, desc)
                    res = s.post(url, cookies = cookies, data = data, headers = self.header, proxies = self.proxy, timeout=6)
                else:  # Not using proxy
                    logging.info('Not using proxy to crawl %s', desc)
                    res = s.post(url, cookies = cookies, data = data, headers = self.header, timeout=6)

                return res

        except requests.exceptions.ProxyError as e:
            logging.warning('Proxy error: %s', e)
            return ''  # as False
        except requests.exceptions.ConnectionError as e:
            logging.warning('Https error: %s', e)
            return ''  # as False
        except requests.exceptions.ReadTimeout as e:
            logging.warning('Timeout error: %s', e)
            return ''  # as False
        except requests.exceptions.ChunkedEncodingError as e:
            logging.warning('ChunkedEncodingError error: %s', e)
            return ''  # as False

    def get_skuinfo_jd(self):
        url = 'https://item.m.jd.com/item/mview2?datatype=1&callback=skuInfoCBA&cgi_source=mitem&sku=%s&t=%s' % (self.item_id, random.random())
        cookies = {'jdAddrId': self.area}
        r = self.load_html(url, 'skuInfo', cookies)
        try:
            info = json.loads(r.text.strip()[11:-1])
        except (json.decoder.JSONDecodeError, AttributeError) as e:
            logging.warning(e, 'Catch skuInfo failed with remote error')
            return False

        return info
            
        
            
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
