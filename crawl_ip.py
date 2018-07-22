# coding:utf-8

# from bs4 import BeautifulSoup
# import lxml
# import random
# import json
import time
# Process多进程  Queue: 任务队列
from multiprocessing import Process, Queue
from lxml import etree
import requests


class Proxies(object):
    """docstring for Proxies"""

    def __init__(self, start_page=1, end_pages=2):
        print("初始化")
        self.proxies = []
        self.verify_pro = []
        self.start_page = start_page
        self.end_pages = end_pages
        # self.agency_ip = {'http': '//101.96.9.160:8080'}
        self.headers = {
            'Accept': '*/*',
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.34 (KHTML, like Gecko) Chrome/45.0.2454.101 Safari/537.36',
            'Accept-Encoding': 'gzip, deflate, sdch',
            'Accept-Language': 'zh-CN,zh;q=0.8'
        }
        self.get_proxies()

    def get_proxies(self):
        print('发送请求')
        start_page = self.start_page
        end_pages = start_page + self.end_pages

        while start_page < end_pages:

            url = 'http://www.xicidaili.com/nn/%d' % start_page
            try:
                str_html = requests.get(url, headers=self.headers)
                if str_html.status_code != 200:
                    break
                str_html = str_html.content.decode()

            except Exception as e:
                break

            html = etree.HTML(str_html)
            ip_list = html.xpath('//table[@id="ip_list"]/tr')[1:]
            for odd in ip_list:
                ip = odd.xpath('./td[2]/text()')[0]
                port = odd.xpath('./td[3]/text()')[0]
                protocol = odd.xpath('./td[6]/text()')[0].lower()
                protocol_ip_port = "{}://{}:{}".format(protocol, ip, port)
                self.proxies.append(protocol_ip_port)

            print('第%s页,获取完' % start_page)
            start_page += 1

    def verify_proxies(self):
        # 没验证的代理
        old_queue = Queue()
        # 验证后的代理
        new_queue = Queue()

        # 进程池列表
        works = []
        for _ in range(15):
            # 循环 Process生成15个子进程, 加入进程池
            works.append(Process(target=self.verify_one_proxy, args=(old_queue, new_queue)))
        for work in works:
            # 循环开启子进程
            work.start()

        for proxy in self.proxies:
            # 将需要处理的(ip)任务加入old_queue队列
            old_queue.put(proxy)

        for work in works:
            old_queue.put(0)

        for work in works:
            # 等待子进程执行完后关闭
            work.join()

        # 将有效ip从new_queue队列中循环取出
        self.proxies = []
        while True:
            try:
                self.proxies.append(new_queue.get(timeout=1))
            except:
                break

    # 验证ip的时效
    def verify_one_proxy(self, old_queue, new_queue):
        while True:

            # 子进程等待任务加入old_queue队列中, 以便获取
            proxy = old_queue.get()
            if proxy == 0: break
            protocol = 'https' if 'https' in proxy else 'http'
            ip_prot = {protocol: proxy}
            try:
                # 发送请求,判断ip, 将有效ip加入new_queue队列

                co = requests.get('https://www.lagou.com/', proxies=ip_prot, timeout=2)
                print('状态码: ', co.status_code)

                if co.status_code == 200:
                    print(ip_prot)
                    new_queue.put(proxy)
            except Exception as e:
                print('无效ip')
                pass


if __name__ == '__main__':
    import random

    # random.randint(0, 10) 为随机页码, 2 为需爬取多少页
    a = Proxies(random.randint(0, 10), 2)
    print('调用')
    a.verify_proxies()
    proxie = a.proxies
    with open('proxies.txt', 'w') as f:
        for proxy in proxie:
            f.write(proxy + '\n')
