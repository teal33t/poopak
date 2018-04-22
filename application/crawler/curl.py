import io
import pycurl
import datetime
from .config_crawler import *

def get_headers():
  ua = "Mozilla/5.0 (Windows NT 6.1; rv:45.0) Gecko/20100101 Firefox/45.0"
  headers = [
    "Connection: close",
    "User-Agent: %s"%ua
  ]
  return headers

def query(url):

    output = io.BytesIO()
    seen_time = datetime.datetime.utcnow()

    try_count = 0
    resp = None
    while try_count < max_try_count :
        try:
            query = pycurl.Curl()
            query.setopt(pycurl.URL, url)
            query.setopt(pycurl.CONNECTTIMEOUT, CONNECTION_TIMEOUT)
            query.setopt(pycurl.TIMEOUT, REQUEST_TIMEOUT)
            query.setopt(pycurl.FOLLOWLOCATION, FOLLOWLOCATION)
            query.setopt(pycurl.HTTPHEADER, get_headers())
            query.setopt(pycurl.PROXY, tor_pool_url)
            query.setopt(pycurl.PROXYPORT, tor_pool_port)
            query.setopt(pycurl.PROXYTYPE, pycurl.PROXYTYPE_SOCKS5_HOSTNAME)
            query.setopt(pycurl.WRITEFUNCTION, output.write)
            query.perform()

            http_code = query.getinfo(pycurl.HTTP_CODE)
            response = output.getvalue()
            html = response.decode('utf8')

            if http_code in http_codes:
                if http_code == 200:
                    resp = {"url": url,
                            "html": html,
                            "status": http_code,
                            "seen_time": seen_time}
                    try_count = 9999
                else:
                    resp = {"url": url,
                            "status": http_code,
                            "seen_time": seen_time}
                    try_count = 9999

        except pycurl.error:
            try_count = try_count + 1
            resp = {"url": url,
                    "status": 503, # Not server exist
                    "seen_time": seen_time}

    return resp



