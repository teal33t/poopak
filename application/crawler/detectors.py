from urllib.request import urlopen
from .config_crawler import get_polyglot_uri
import json


def detect_lang_locale(phrase):
    data = get_polyglot_uri(phrase=phrase).encode('utf-8')
    polyglot_api = urlopen(data)
    data = polyglot_api.read()
    # encoding = data.info().get_content_charset('utf-8')
    _json = json.loads(data)
    return _json['locale']