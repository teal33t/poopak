from pymongo import MongoClient
from .config_crawler import *


class DataStorage:
    def __init__(self):
        self.client = MongoClient(mongodb_uri)

    def is_url_exist(self, url):
        try:
            return True if self.client.crawler.documents.find({'url': url}).count() > 0 else False
        except:
            return False

    def add_crawled_url(self, data):
        obj = self.client.crawler.documents.insert_one(data)
        return obj.inserted_id

    def update_crawled_url(self, url, data):
        self.client.crawler.documents.update_one({'url': url}, {"$set": data}, upsert=False)
        return True
