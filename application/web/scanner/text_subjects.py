import json
import requests
from web.config import spacy_server_url
# from web.config import mongodb_uri

# from web import client
from bson import ObjectId

from pymongo import MongoClient

mongodb_uri = "mongodb://%s:%s@mongodb:27017/crawler" % ("admin", "123qwe")


def _text_subject(id):
    s = SpacyDetector(id)
    return s.get_subjects_and_update()

class SpacyDetector:

    def __init__(self, id):
        self.client = MongoClient(mongodb_uri)
        self.id = id
        # child_data = str
        result = self.client.crawler.documents.find_one({"_id": ObjectId(id)})
        self.whole_text = result['body']
        # netloc = result['netloc']
        # all_childs = self.client.crawler.documents.find({'netloc': netloc})
        # if all_childs.count() > 0:
        #     for child in all_childs:
        #         child_data = "%s\n%s\n" % (child_data, child['body'])

            # self.whole_text = child_data

    def _get_spacy_subj(self):
        headers = {'content-type': 'application/json'}
        d = {'text': self.whole_text, 'model': 'en'}
        print (d)
        response = requests.post(spacy_server_url, data=json.dumps(d), headers=headers)
        r = response.json()
        # print (vars(r))
        return r

    def get_subjects(self):
        resp = self._get_spacy_subj()
        subjs = []
        for item in resp['words']:
            if item['tag'] == "NNP" or item['tag'] == "NNPS":
                subjs.append(item['text'])
        return {'subjects': subjs}

    def get_subjects_and_update(self):
        subjs = self.get_subjects()
        self.client.crawler.documents.update_one({'_id': ObjectId(self.id)}, {"$set": subjs}, upsert=False)
        return True
