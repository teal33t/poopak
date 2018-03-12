# from spider import Crawler
# from .application.cfg import mongodb_uri
# from application.cfg import mongodb_uri
# # mongodb_uri = "mongodb://Samans-Air:27019/crawler"
import datetime
mongodb_uri =  "mongodb://%s:%s@mongodb:27017/crawler" % ("admin", "54nn4n")
# # from web import huey
# from .ucurl import query
from pymongo import MongoClient
from lxml import html as lh
#
#
# @huey.task()
# def run_crawler(url):
#     # proxy = "torpool:5566"
#     mongo_url=mongodb_uri
#     mongo_collection='documents'
#     mongo_db='crawler'
#     mongo_client = motor.motor_asyncio.AsyncIOMotorClient(mongo_url)
#     database = mongo_client[mongo_db]
#     collection = database[mongo_collection]
#     if type(url) == list:
#         for item in url:
#             response = query(url, "torpool", 5566)
#             collection.insert_one(response)
#     else:
#         print ("SINGLE THREAD")
#         response = query(url, "torpool", 5566)
#         collection.insert_one(response)

from .tor_scraper import start_tor, query
def run(url):
    print (url)
    client = MongoClient(mongodb_uri)
    # client = motor.motor_asyncio.AsyncIOMotorClient(mongodb_uri)

    # web_crawler = Crawler(proxy="torpool:5566",
    #                       mongo_url=mongodb_uri,
    #                       mongo_collection='documents',
    #                       mongo_db='crawler')
    # web_crawler.run(urls=url,group_len=100)

    # url = list(url)
    result = query(url)
    client.crawler.documents.insert_one(result)
    # return True
#
#
# # def hard_run(url):
# #     if url is list:
#
#
#
# # def single_run(url):
# #     web_crawler = Crawler(proxy="socks5://localhost:5566",
# #                           mongo_url='mongodb://localhost:27017',
# #                           mongo_collection='documents',
# #                           mongo_db='crawler')
# #     web_crawler.single_run(url=url)
# #     return {"status": "run"}
# #
# # def multiple_run(urls):
# #     web_crawler = Crawler(proxy="socks5://localhost:5566",
# #                               mongo_url='mongodb://localhost:27017',
# #                               mongo_collection='documents',
# #                               mongo_db='crawler')
# #     web_crawler.run(urls=urls, group_len=100)
# #     return {"status": "run"}
