import asyncio
import aiohttp
from lxml import html as lh
from urllib.parse import urljoin
import motor.motor_asyncio
from aiosocks.connector import ProxyConnector, ProxyClientRequest
import itertools, datetime


class BaseCrawler:

    def __init__(self, proxy, mongo_url, mongo_db, mongo_collection, exclusions=None, **kwargs):

        self._urls_to_crawl = asyncio.Queue()
        self._data_to_parse = asyncio.Queue()
        self._data_to_save = asyncio.Queue()
        self._for_saving = asyncio.Queue()

        self.proxy = proxy

        self.crawled = []
        self.exclusions = exclusions if exclusions else []

        self.mongo_client = motor.motor_asyncio.AsyncIOMotorClient(mongo_url)
        self.database = self.mongo_client[mongo_db]
        self.collection = self.database[mongo_collection]

        conn = ProxyConnector(remote_resolve=True)
        self.session = aiohttp.ClientSession(connector=conn, request_class=ProxyClientRequest)

    async def wrapper_request(self):
        if not self._urls_to_crawl.empty():
            url = await self._urls_to_crawl.get()
            if url not in self.crawled:
                self.crawled.append(url)
                try:
                    print ("TRY %s" %(str(url)))
                    async with self.session.get(url, proxy=self.proxy, timeout=30) as response:
                        print ("-> %s [%s]" % (response.url, response.status))
                        html = await response.read()
                        if response.url != url and response.url not in self.crawled:
                            self.crawled.append(response.url)
                        self._data_to_parse.put_nowait({'url': response.url, 'html': html, 'status': response.status})
                        return None
                except Exception as e:
                    print("-> %s [%s]" % (url, 503))
                    # self.logger.warning(e)
                    print (e)
                    print ("ERROR")
                    await self.collection.insert_one({"url": url, "status": 503, "seen_time": datetime.datetime.utcnow()})


    async def link_parser(self, base_url):
        if not self._data_to_parse.empty():
            data = await self._data_to_parse.get()
            html = data.get('html', '')
            dom = lh.fromstring(html)
            self._data_to_save.put_nowait(data)
            for href in dom.xpath('//a/@href'):
                if any(e in href for e in self.exclusions):
                    continue
                url = urljoin(base_url, href)
                if url not in self.crawled and url.startswith(base_url):
                    self._urls_to_crawl.put_nowait(url)
            return None
        else:
            return None

    async def send_to_saver(self, data):
        raise NotImplementedError

    async def data_parser(self):
        if not self._data_to_save.empty():
            data = await self._data_to_save.get()
            result = await self.send_to_saver(data)
            if result:
                self._for_saving.put_nowait(result)


    async def saving(self):
        if not self._for_saving.empty():
            data = await self._for_saving.get()
            if isinstance(data, dict):
                result = await self.collection.insert_one(data)
            elif isinstance(data, list):
                result = await self.collection.insert_many(data)

    async def outer(self, url):

        self._urls_to_crawl.put_nowait(url)
        while not self._urls_to_crawl.empty() or not self._for_saving.empty():
                try:
                    await self.wrapper_request()
                    await self.link_parser(url)
                    await self.data_parser()
                    await self.saving()
                except Exception as e:
                    print(e)


    def grouper(self, n, iterable):
        it = iter(iterable)
        while True:
            chunk = tuple(itertools.islice(it, n))
            if not chunk:
                return
            yield chunk

    # def single_run(self, url):
    #     event_loop = asyncio.get_event_loop()
    #     tasks = [event_loop.create_task(self.outer(url))]
    #     event_loop.run_until_complete(asyncio.wait(tasks))
    #     self.session.close()
    #     event_loop.close()
    #
    # def run(self,urls, group_len):
    #     event_loop = asyncio.get_event_loop()
    #     grouped = self.grouper(group_len, urls)
    #     # print (list(grouped))
    #     for group in grouped:
    #         urls = list(group)
    #         tasks = [event_loop.create_task(self.outer(i)) for i in urls]
    #         event_loop.run_until_complete(asyncio.wait(tasks))
    #         self.session.close()
    #     event_loop.close()

    def run(self, urls, group_len=None):
        event_loop = asyncio.get_event_loop()
        # print (list(grouped))
        if type(urls)  == list:
            if group_len and len(urls) > group_len:
                grouped = self.grouper(group_len, urls)
                for group in grouped:
                    urls = list(group)
                    tasks = [event_loop.create_task(self.outer(i)) for i in urls]
            else:
                tasks = [event_loop.create_task(self.outer(i)) for i in urls]
        else:
            event_loop = asyncio.get_event_loop()
            tasks = [event_loop.create_task(self.outer(urls))]
        event_loop.run_until_complete(asyncio.wait(tasks))
        self.session.close()

        event_loop.close()
