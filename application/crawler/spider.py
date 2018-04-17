#!/usr/bin/env python
# -*- coding:utf-8 -*-

from .curl import query
from  .html_extractors import Extractor
from .data_storage import DataStorage

import uuid

from rq import Queue
from worker import conn

from .screenshot import get_screenshot

def go_depth(target, parent, depth=0, is_onion=True,
             in_scope=False, use_proxy=True, re_crawl=True):
    spider = Spider(base_url=target,
           depth=depth,
           is_onion=is_onion,
           in_scope=in_scope,
           use_proxy=use_proxy,
           re_crawl=re_crawl,
           parent=parent)
    spider.proccess()

class Spider:

    def __init__(self, base_url, depth=0, is_onion=True,
                 in_scope=False, use_proxy=True, re_crawl=True, parent=None):
        self.base_url = base_url
        self.is_onion = is_onion
        self.in_scope = in_scope
        self.depth = depth
        self.proxy = use_proxy
        self.re_crawl = re_crawl
        self.response = query(base_url)
        self.ds = DataStorage()
        self.parent = parent
        self.q = Queue(name="high", connection=conn)


    def _save_or_update(self, data):
        if self.ds.is_url_exist(self.base_url):
            if self.re_crawl:
                self.ds.update_crawled_url(self.base_url, data)
        else:
            self.ds.add_crawled_url(data)

    def proccess(self):

        json_data = {'url': self.base_url,
                     'status': self.response['status'],
                     'seen_time': self.response['seen_time'],
                     'parent': self.parent}

        if self.response['status']:
            if 'html' in self.response:
                data = Extractor(base_url=self.base_url, html=self.response['html'])


                json_data = {'url': self.base_url,
                        'status': self.response['status'],
                        'html': self.response['html'],
                        'body': data.get_body(),
                        'title': data.get_title(),
                        'links': data.get_links(),
                        'seen_time': self.response['seen_time'],
                        'parent': self.parent}


                if int(self.response['status']) == 200: #OK
                    filename = uuid.uuid4().hex
                    get_screenshot(self.base_url, filename)
                    json_data['capture_name'] = filename


            self._save_or_update(json_data)

            if self.depth: # depth > 0
                depth_step = 0
                while depth_step < self.depth: # while step not reached the thr
                    for link in json_data['links']:
                        self.q.enqueue_call(func=go_depth,
                                       args=(link['url'], self.base_url,
                                             depth_step, link['is_onion'],
                                             link['in_scope'],),
                                       ttl=86400, result_ttl=1)
                    depth_step = depth_step + 1



                        # def add_to_queue(self, link):





