from bs4 import BeautifulSoup
from urllib.parse import urlparse, urlunparse

import re


class Extractor:

    def __init__(self, base_url, html):
        self.html = html
        self.soup = BeautifulSoup(html, "lxml")
        self.base_url = base_url

    def get_links(self):
        parsed_url = urlparse(self.base_url)
        _urls  = []
        for link in self.soup.find_all('a'):
            href = link.get('href')
            parsed_href = urlparse(href)
            in_scope = False
            is_onion =  True if '.onion' in parsed_href.netloc else False

            if parsed_href.netloc != "":
                href = urlunparse((parsed_href.scheme, parsed_href.netloc, parsed_href.path, '', parsed_href.query, ''))
            if parsed_href.netloc != "":
                if parsed_href.netloc == parsed_url.netloc:
                    in_scope = True
                    href = urlunparse((parsed_url.scheme, parsed_url.netloc, parsed_href.path, '', parsed_href.query, ''))
            if href.startswith('/') or href.startswith('?'):
                in_scope = True
                href = urlunparse((parsed_url.scheme, parsed_url.netloc, parsed_href.path, '', parsed_href.query, ''))
            if href.startswith("#"):
                in_scope = True
                href = urlunparse((parsed_url.scheme, parsed_url.netloc, parsed_href.path, '', parsed_href.query, ''))
            _urls.append({'url': href, 'is_onion': is_onion, 'in_scope': in_scope})
        return _urls

    def get_body(self):
        try:
            return self.soup.body.get_text(" ",strip=True)
        except:
            pass

    def get_title(self):
        try:
            return self.soup.title.get_text()
        except:
            return None

    def get_img_links(self):
        parsed_url = urlparse(self.base_url)
        _imgs  = []
        for link in self.soup.find_all('img'):
            src = link.get('src')
            parsed_src = urlparse(src)

            if parsed_src.netloc != "":
                src = urlunparse((parsed_src.scheme, parsed_src.netloc, parsed_src.path, '', parsed_src.query, ''))
            if parsed_src.netloc != "":
                if parsed_src.netloc == parsed_url.netloc:
                    src = urlunparse((parsed_url.scheme, parsed_url.netloc, parsed_src.path, '', parsed_src.query, ''))
            if src.startswith('/') or src.startswith('?'):
                src = urlunparse((parsed_url.scheme, parsed_url.netloc, parsed_src.path, '', parsed_src.query, ''))
            if src.startswith('data'):
                src = urlunparse((parsed_url.scheme, parsed_url.netloc, parsed_src.path, '', parsed_src.query, ''))
            _imgs.append(src)
        return _imgs

    # match email addresses from body
    def get_emails(self):
        try:
            match = re.findall(r'[\w\.-]+@[\w\.-]+', self.html)
            return match
        except:
            return None


    # match bitcoin addresses from body
    def get_bitcoin_addrs(self):
        try:
            _find = re.findall('[13][a-km-zA-HJ-NP-Z1-9]{25,34}', self.get_body())
            return _find
        except:
            return None

    # match eth addresses from body
    def get_eth_addrs(self):
        try:
            _find = re.findall('0x[a-fA-F0-9]{40}', self.get_body())
            return _find
        except:
            return None

    # match monero addresses from body
    def get_monero_addrs(self):
        try:
            _find = re.findall('4[0-9AB][1-9A-HJ-NP-Za-km-z]{93}', self.get_body())
            return _find
        except:
            return None


