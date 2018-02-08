from .spider import Crawler

uri =  "mongodb://%s:%s@mongodb:27017/crawler" % ("admin", "54nn4n")

def run(url):
    web_crawler = Crawler(proxy="socks5://torpool:5566",
                          mongo_url=uri,
                          mongo_collection='documents',
                          mongo_db='crawler')
    web_crawler.run(urls=url,group_len=100)
    return True


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
#                               mongo_url='mongodb://localhost:27017',
#                               mongo_collection='documents',
#                               mongo_db='crawler')
#     web_crawler.run(urls=urls, group_len=100)
#     return {"status": "run"}
