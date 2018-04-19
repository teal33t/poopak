from bs4 import BeautifulSoup
from urllib.parse import urlparse, urlunparse



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

            if parsed_href.netloc != "":
                href = urlunparse((parsed_href.scheme, parsed_href.netloc, parsed_href.path, '', parsed_href.query, ''))
            if parsed_href.netloc != "":
                if parsed_href.netloc == parsed_url.netloc:
                    href = urlunparse((parsed_url.scheme, parsed_url.netloc, parsed_href.path, '', parsed_href.query, ''))
            if href.startswith('/') or href.startswith('?'):
                href = urlunparse((parsed_url.scheme, parsed_url.netloc, parsed_href.path, '', parsed_href.query, ''))
            # else:
            #     href = urlunparse((parsed_url.scheme, parsed_url.netloc, parsed_href.path, '', parsed_href.query, ''))
            is_onion =  True if '.onion' in parsed_href.netloc else False
            in_scope = True if parsed_href.netloc == parsed_url.netloc else False
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
            pass

