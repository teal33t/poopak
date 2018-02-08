import datetime

from lxml import html as lh

# import crawler
from .core import BaseCrawler


class Crawler(BaseCrawler):

    async def send_to_saver(self, data):

        result = {}
        result['url'] = str(data.get('url'))
        result['status'] = data.get('status')
        result['seen_time'] = datetime.datetime.utcnow()

        if data.get('status') != 200:
            print("-> %s [%s] | %s" % (result['url'], result['status'], result['seen_time']))
            return result

        html = data.get('html', '')

        dom = lh.fromstring(html)
        title = dom.cssselect('title')

        if title:
            title = title[0].text_content()
            result['title'] = title

        result['body'] = dom.body.text_content()
        result['raw'] = html

        print ("-> %s [%s] | %s" % (result['url'], result['status'], result['seen_time']))
        return result



# def single_run(url):
#     web_crawler = Crawler(proxy="socks5://localhost:5566",
#                           mongo_url='mongodb://localhost:27017',
#                           mongo_collection='documents',
#                           mongo_db='crawler')
#     web_crawler.single_run(url=url)
#     return {"status": "run"}
#
# def multiple_run(urls):
#     web_crawler = Crawler(proxy="socks5://localhost:5566",
#                           mongo_url='mongodb://localhost:27017',
#                           mongo_collection='documents',
#                           mongo_db='crawler')
#     web_crawler.run(urls=urls, group_len=100)
#     return {"status": "run"}

#             #
# if __name__ == '__main__':
#
#     # urls = ["http://krushux2j2feimt6.onion"]
#
#     _file = open('urls.txt', 'r')
#     urls = []
#     for url in _file.readlines():
#         urls.append(url.strip())
#     _file.close()
#
#     web_crawler = Crawler(proxy="socks5://localhost:5566",
#                           mongo_url='mongodb://localhost:27017',
#                           mongo_collection='documents',
#                           mongo_db='crawler')
#     web_crawler.run(urls=urls, group_len=100)