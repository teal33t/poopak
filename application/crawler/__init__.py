import io
import pycurl
import os
import sys
import random
from stem.control import Controller
from stem.util import system

import stem.process
from stem.util import term
import datetime

# import mongodb_client


SOCKS_PORT = 7000
CONTROL_PORT = 6969

# sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'common'))

# USER_AGENTS_FILE = '../common/user_agents.txt'
USER_AGENTS = []

from lxml import html as lh


"""Uses pycurl to fetch a site using the proxy on the SOCKS_PORT"""
def query(url):

    output = io.BytesIO()
    seen_time = datetime.datetime.utcnow()

    try_count = 0
    resp = None
    while try_count < 4 :
        try:
            query = pycurl.Curl()
            query.setopt(pycurl.URL, url)
            query.setopt(pycurl.CONNECTTIMEOUT, 15)
            query.setopt(pycurl.TIMEOUT, 25)
            query.setopt(pycurl.FOLLOWLOCATION, 1)
            query.setopt(pycurl.HTTPHEADER, getHeaders())
            query.setopt(pycurl.PROXY, 'torpool')
            query.setopt(pycurl.PROXYPORT, 5566)
            # query.setopt(pycurl.PROXYTYPE, pycurl.PROXYTYPE_HTTP)

            query.setopt(pycurl.PROXYTYPE, pycurl.PROXYTYPE_SOCKS5_HOSTNAME)
            query.setopt(pycurl.WRITEFUNCTION, output.write)
            query.perform()
            # http_code = query.getinfo(pycurl.HTTP_CODE)
            # print (200)
            http_code = query.getinfo(pycurl.HTTP_CODE)
            response = output.getvalue()
            html = response.decode('iso-8859-1')
            # header_len = query.getinfo(pycurl.HEADER_SIZE)
            # header = resp[0: header_len]
            # html = resp[header_len:]
            if http_code == 200:
                # through = True
                try:
                    dom = lh.fromstring(html)
                    title = dom.cssselect('title')

                    if title:
                        title = title[0].text_content()
                        # result['title'] = title

                    body = dom.body.text_content()
                    resp = {"url": url, "html": html, 'body': body,
                            "title": title,"status": http_code,
                            "seen_time": seen_time}

                except:
                    resp = {"url": url, "html": html, "status": http_code, "seen_time": seen_time}

                break
            else:
                print ('error httpcode:' +str(http_code))
                resp = {"url": url, "status": http_code, "seen_time": seen_time}
                try_count = try_count + 1


                # except pycurl.error as exc:
        except pycurl.error as e:
            print (e)
            try_count = try_count + 1
            resp = {"url": url, "status": 503, "seen_time": seen_time}

    return resp



        # return output.getvalue()


"""print tor bootstrap info"""
def print_bootstrap_lines(line):
  if "Bootstrapped " in line:
    print(term.format(line, term.Color.BLUE))


"""get user-agent and httpheader string list"""
def getHeaders():
  # ua = random.choice(USER_AGENTS)  # select a random user agent
  ua = "Mozilla/5.0 (Windows NT 6.1; rv:45.0) Gecko/20100101 Firefox/45.0"
  headers = [
    "Connection: close",
    "User-Agent: %s"%ua
  ]
  # print headers
  return headers


"""start tor process"""
def start_tor():
  tor_process = system.pid_by_port(SOCKS_PORT)
  if  tor_process is None:
    tor_process = system.pid_by_name('tor')
  if  tor_process is None:
    tor_process = stem.process.launch_tor_with_config(
      config={
        'SocksPort': str(SOCKS_PORT),
        'ControlPort': str(CONTROL_PORT),
        'ExitNodes': '{ru}',
      },
      init_msg_handler=print_bootstrap_lines,
    )
  else:
    print ("tor already running, no need to start")


"""renew tor circuit"""
def renew_tor():
   """
   Create a new tor circuit
   """
   try:
      stem.socket.ControlPort(port = CONTROL_PORT)
   except stem.SocketError as exc:
      print ("Tor", "[!] Unable to connect to port %s (%s)" %(CONTROL_PORT , exc))
   with Controller.from_port(port = CONTROL_PORT) as controller:
      controller.authenticate()
      controller.signal(stem.Signal.NEWNYM)
      print ("TorTP", "[+] New Tor circuit created")
      # print ('renewed:' + query("http://icanhazip.com")


"""stop tor process"""
def stop_process_on_name():
  process =  system.pid_by_name('tor')
  if  process is not None:
    os.kill(process, 2)

# """read user-agent"""
# with open(USER_AGENTS_FILE, 'rb') as uaf:
#     for ua in uaf.readlines():
#         if ua:
#             USER_AGENTS.append(ua.strip())
# random.shuffle(USER_AGENTS)


# """start tor instance when called this module"""
# start_tor()
#
# query("www.zillow.com")
#
# db = None
# db = mongodb_client.getDB()
# if  db is None:
#   print "fail"
# else:
#   print "succeed"
#



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

# from crawler.tor_scraper import query

# from application.crawler.tor_scraper import

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
    # print (type(url))
    # if type(url) == list:
    #     for item in url:
    #         result = query(item)
    #         client.crawler.documents.insert_one(result)
    # else:
    result = query(url)
    client.crawler.documents.insert_one(result)

def hard_run(seed_path):
    # python hard_run seed_path
    pass
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
