"""
Crawler package for web crawling operations.

This package provides modules for crawling web pages, extracting content,
and storing results in the database.
"""

from .spider import crawl_with_depth


def run(url):
    """
    Run a simple crawl for a single URL.

    Args:
        url: URL to crawl
    """
    crawl_with_depth(target=url, parent=None, depth=1)

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
