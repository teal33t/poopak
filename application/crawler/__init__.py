import io
import pycurl
import os

from stem.control import Controller
from stem.util import system

import stem.process
from stem.util import term
import datetime

from lxml import html as lh
import datetime
from .config_crawler import *
# from web.helper import extract_onions

from pymongo import MongoClient
import re
from bs4 import BeautifulSoup


# Crawler query for tor proxy request


def query(url):

    output = io.BytesIO()
    seen_time = datetime.datetime.utcnow()

    try_count = 0
    resp = None
    while try_count < max_try_count :
        try:
            query = pycurl.Curl()
            query.setopt(pycurl.URL, url)
            query.setopt(pycurl.CONNECTTIMEOUT, 15)
            query.setopt(pycurl.TIMEOUT, 25)
            query.setopt(pycurl.FOLLOWLOCATION, 1)
            query.setopt(pycurl.HTTPHEADER, get_headers())
            query.setopt(pycurl.PROXY, tor_pool_url)
            query.setopt(pycurl.PROXYPORT, tor_pool_port)
            query.setopt(pycurl.PROXYTYPE, pycurl.PROXYTYPE_SOCKS5_HOSTNAME)
            query.setopt(pycurl.WRITEFUNCTION, output.write)
            query.perform()

            http_code = query.getinfo(pycurl.HTTP_CODE)
            response = output.getvalue()
            html = response.decode('utf8')

            if http_code == 200:
                # try:
                # onions = extract_onions(html)
                resp = {"url": url,
                        "html": html,
                        'body': get_body(html),
                        "title": get_title(html),
                        "status": http_code,
                        "emails": get_emails(html),
                        # "onions": list(set(onions)),
                        "found_ips": get_ips(html),
                        "btc_addresses": get_btc_addresses(html),
                        "seen_time": seen_time}
                # except:
                #     resp = {"url": url, "html": html, "status": http_code, "seen_time": seen_time}

                try_count = 99
            else:
                print ('error httpcode:' +str(http_code))
                resp = {"url": url, "status": http_code, "seen_time": seen_time}
                try_count = try_count + 1

        except pycurl.error as e:
            print (e)
            try_count = try_count + 1
            resp = {"url": url, "status": 503, "seen_time": seen_time}

    return resp


def get_body(s):
    dom = lh.fromstring(str(s))
    body = dom.body.text_content()
    return body


def get_title(s):
    regex = re.findall(r'<title.*?>(.+?)</title>', str(s))
    return regex[0]

def get_headers():
  ua = "Mozilla/5.0 (Windows NT 6.1; rv:45.0) Gecko/20100101 Firefox/45.0"
  headers = [
    "Connection: close",
    "User-Agent: %s"%ua
  ]
  return headers


def get_emails(s):
    regex = re.findall(r'[\w\.-]+@[\w\.-]+', str(s))
    return regex

def get_ips(s):
    ips = re.findall(r'[0-9]+(?:\.[0-9]+){3}', str(s))
    return ips

def get_btc_addresses(s):
    btc_addresses = re.findall(r'^[13][a-km-zA-HJ-NP-Z1-9]{25,34}$', str(s))
    return btc_addresses



def run(url):
    print (url)
    client = MongoClient(mongodb_uri)

    exist = 0
    try:
        exist = client.crawler.documents.find({'url': url}).count()
    except:
        pass

    result = query(url)
    print (exist)
    if exist > 0:
        # print ("NOT EXIST -> UPDATE")
        client.crawler.documents.update_one({'url': url}, {"$set": result}, upsert=False)
    else:
        client.crawler.documents.insert_one(result)

