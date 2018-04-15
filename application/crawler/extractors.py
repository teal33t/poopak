from bs4 import BeautifulSoup
from urllib.parse import urlparse


def get_links(soup, base_url):
    parsed_url = urlparse(base_url)
    _urls  = []
    for link in soup.find_all('a'):
        href = link.get('href')
        parsed_href = urlparse(href)
        if not parsed_href.netloc and parsed_href.path:
            href = ("%s://%s%s") % (parsed_url.scheme,parsed_url.netloc,parsed_href.path)
            print (href)
        parsed_href = urlparse(href)
        is_onion =  True if '.onion' in parsed_href.netloc else False
        in_scope = True if parsed_href.netloc == parsed_url.netloc else False
        _urls.append({'url': href, 'is_onion': is_onion, 'in_scope': in_scope})
    return _urls

def proccess_html(html, base_url):
    soup = BeautifulSoup(html, "lxml")
    body = soup.body.get_text(" ",strip=True)
    title = soup.title.get_text()
    links = get_links(soup, base_url)
    return {'body': body, 'title': title, 'links': links}