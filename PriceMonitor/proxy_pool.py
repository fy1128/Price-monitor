#!/usr/bin/env python
# -*- coding: utf-8 -*-
import random
import requests
import logging
import time
from CONFIG import PROXY_POOL

USER_AGENT_LIST = [
    "Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.1 (KHTML, like Gecko) Chrome/22.0.1207.1 Safari/537.1",
    "Mozilla/5.0 (X11; CrOS i686 2268.111.0) AppleWebKit/536.11 (KHTML, like Gecko) Chrome/20.0.1132.57 Safari/536.11",
    "Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/536.6 (KHTML, like Gecko) Chrome/20.0.1092.0 Safari/536.6",
    "Mozilla/5.0 (Windows NT 6.2) AppleWebKit/536.6 (KHTML, like Gecko) Chrome/20.0.1090.0 Safari/536.6",
    "Mozilla/5.0 (Windows NT 6.2; WOW64) AppleWebKit/537.1 (KHTML, like Gecko) Chrome/19.77.34.5 Safari/537.1",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/536.5 (KHTML, like Gecko) Chrome/19.0.1084.9 Safari/536.5",
    "Mozilla/5.0 (Windows NT 6.0) AppleWebKit/536.5 (KHTML, like Gecko) Chrome/19.0.1084.36 Safari/536.5",
    "Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/536.3 (KHTML, like Gecko) Chrome/19.0.1063.0 Safari/536.3",
    "Mozilla/5.0 (Windows NT 5.1) AppleWebKit/536.3 (KHTML, like Gecko) Chrome/19.0.1063.0 Safari/536.3",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_8_0) AppleWebKit/536.3 (KHTML, like Gecko) Chrome/19.0.1063.0 Safari/536.3",
    "Mozilla/5.0 (Windows NT 6.2) AppleWebKit/536.3 (KHTML, like Gecko) Chrome/19.0.1062.0 Safari/536.3",
    "Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/536.3 (KHTML, like Gecko) Chrome/19.0.1062.0 Safari/536.3",
    "Mozilla/5.0 (Windows NT 6.2) AppleWebKit/536.3 (KHTML, like Gecko) Chrome/19.0.1061.1 Safari/536.3",
    "Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/536.3 (KHTML, like Gecko) Chrome/19.0.1061.1 Safari/536.3",
    "Mozilla/5.0 (Windows NT 6.1) AppleWebKit/536.3 (KHTML, like Gecko) Chrome/19.0.1061.1 Safari/536.3",
    "Mozilla/5.0 (Windows NT 6.2) AppleWebKit/536.3 (KHTML, like Gecko) Chrome/19.0.1061.0 Safari/536.3",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/535.24 (KHTML, like Gecko) Chrome/19.0.1055.1 Safari/535.24",
    "Mozilla/5.0 (Windows NT 6.2; WOW64) AppleWebKit/535.24 (KHTML, like Gecko) Chrome/19.0.1055.1 Safari/535.24",
    "Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/43.0.2357.132 Safari/537.36",
    "Mozilla/5.0 (Windows NT 6.1; WOW64; rv:41.0) Gecko/20100101 Firefox/41.0",
    'Mozilla/5.0 (compatible; Googlebot/2.1; +http://www.google.com/bot.html)',  # search engine header
    'Mozilla/5.0 (compatible; Bingbot/2.0; +http://www.bing.com/bingbot.htm)',
    'Mozilla/5.0 (compatible; Yahoo! Slurp; http://help.yahoo.com/help/us/ysearch/slurp)',
    'DuckDuckBot/1.0; (+http://duckduckgo.com/duckduckbot.html)',
    'Mozilla/5.0 (compatible; Baiduspider/2.0; +http://www.baidu.com/search/spider.html)',
    'Mozilla/5.0 (compatible; YandexBot/3.0; +http://yandex.com/bots)',
    'ia_archiver (+http://www.alexa.com/site/help/webmasters; crawler@alexa.com)'
]

class Proxy(object):

    @staticmethod
    def check_jd(proxy):
        logging.info('Validating name proxy: %s', proxy)
        header = Proxy.get_ua()
        retry_count = 2
        while retry_count > 0:
            try:
                http_proxy = "http://{}".format(proxy)
                #r = requests.get('https://item.m.jd.com/coupon/coupon.json?wareId=5089253', headers = header, proxies={"http": http_proxy, "https": http_proxy}, timeout=5) # Iphone X
                r = requests.get('https://pm.3.cn/prices/mgets?origin=2&area=19_1684_19467_0&pdtk=&pduid=&pdpin=&pdbp=0&skuIds=5089253', headers = header, proxies={"http": http_proxy, "https": http_proxy}, timeout=5) # Iphone X
                # 使用代理访问
                #if 'coupon' not in r.json():
                if 'op' not in r.json()[0]:
                    return False
                    
                return True
            except Exception:
                retry_count -= 1

        # 出错5次, 删除代理池中代理
        logging.info('Proxy %s is invalid, deleting...', proxy)
        Proxy.delete_proxy(proxy)
        return False

    def get_proxy(self):
        while True:
            res = requests.get(PROXY_POOL + "/get/")
            try:
                data = res.json()
                proxy = data['proxy']
                if not self.check_jd(proxy):
                    logging.warning('Validate proxy failure, retrying')
                    continue
                logging.info('Validate SUCCESS，using proxy: %s', proxy)
                return proxy
            except Exception:
                logging.critical('No proxy now from remote server, retrying')
                time.sleep(5)

    def delete_proxy(proxy):
        requests.get(PROXY_POOL + "/?proxy={}".format(proxy))

    @staticmethod
    def get_ua():
        ua = random.choice(USER_AGENT_LIST)
        ua = {'user-agent': ua}  # dict
        logging.debug('Generating header: %s', ua)
        return ua
        
if __name__ == '__main__':
    logging.basicConfig(level=logging.DEBUG)
    p = Proxy()
