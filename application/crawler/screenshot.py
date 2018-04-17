from homura import download
from .config_crawler import get_splash_uri, get_save_path

def get_screenshot(url, filename):
    download(url=get_splash_uri(url),path=get_save_path(filename))