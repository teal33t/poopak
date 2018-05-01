from homura import download
from urllib.parse import urlparse, urlunparse
from web.queues import detector_q
from web import client
from crawler.html_extractors import Extractor
from bson import ObjectId
from web import config




import uuid
import exifread
import pycurl

from os.path import splitext

def set_exif_data(id, tags):
    try:
        client.crawler.documents.update_one({'_id': ObjectId(id)}, {"$set": tags}, upsert=False)
    except:
        return None

def download_and_detect(id, url, filename):
    # try:
        opt = {pycurl.PROXY: config.tor_pool_url,
               pycurl.PROXYPORT: config.tor_pool_port,
               pycurl.PROXYTYPE: pycurl.PROXYTYPE_SOCKS5_HOSTNAME}
        download(url,path=filename, pass_through_opts=opt)
        f = open (filename, 'rb')
        tags = exifread.process_file(f)
        set_exif_data(id, {'exif': tags.keys()})
        f.close()
    # except:
    #     return None

def detect_exif_metadata(id):

    data = client.crawler.documents.find_one({"_id": ObjectId(id)})
    exta = Extractor(base_url=data['url'], html=data['html'])
    srcs = exta.get_img_links()
    for src in srcs:
        n, ext = splitext(urlparse(src).path)
        obj_uuid = uuid.uuid4().hex
        path = config.get_exif_save_path(obj_uuid, ext)
        detector_q.enqueue_call(download_and_detect, args=(id, src, path), ttl=86400, result_ttl=1)

    return True
