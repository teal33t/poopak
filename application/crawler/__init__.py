# from .config_crawler import *
# from pymongo import MongoClient
# from .curl import query
# from  .extractors import proccess_html
# from web import q
from .spider import Spider

def run(url):
    spider = Spider(base_url=url, depth=1)
    spider.proccess()

    # print (url)
    # client = MongoClient(mongodb_uri)
    #
    # exist = 0
    # try:
    #     exist = client.crawler.documents.find({'url': url}).count()
    # except:
    #     pass
    #
    # result = query(url)
    #
    # if result['status']:
    #     resp = proccess_html(result['html'], url)
    #
    #     if exist > 0:
    #         # print ("NOT EXIST -> UPDATE")
    #         client.crawler.documents.update_one({'url': url}, {"$set": resp}, upsert=False)
    #     else:
    #         client.crawler.documents.insert_one(resp)
    # else:
    #     client.crawler.documents.insert_one(result)
