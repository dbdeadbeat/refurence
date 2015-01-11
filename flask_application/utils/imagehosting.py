import requests, os
from bs4 import BeautifulSoup, SoupStrainer

class HostedImageDriver(object):
    def __init__(self, url):
        self.url = url

    def _filter_out_images(self, urls):
        valid_exts = {
                '.jpg':'',
                '.png':'',
                '.gif':'',
                '.jpeg':'',
                '.tif':'',
                '.tiff':''}
        out = []
        for url in urls:
            root,ext = os.path.splitext(url['href'])
            if not ext in valid_exts:
                continue
            out.append(url)
        return out
    
    def get_image_urls(self):
        return []

class GDriveDriver(HostedImageDriver):
    def get_image_urls(self):
        session = requests.session()
        doc = session.get(self.url)
        if not doc:
            return []

        out = []
        for link in self._filter_out_images(BeautifulSoup(doc.content, parse_only=SoupStrainer('a', href=True))):
            if 'host' in link['href']:
                out.append(self.url + os.path.basename(link['href']))
        return out

class DropbBoxDriver(HostedImageDriver):
    def get_image_urls(self):
        session = requests.session()
        doc = session.get(self.url)
        if not doc:
            return []
        imgs = {}
        for link in BeautifulSoup(doc.content, parse_only=SoupStrainer('a', href=True)):
            if link['href'].endswith('dl=0'):
                imgs[link['href']] = True
        out = []
        for k in imgs.keys():
            out.append(k.replace('dl=0', 'raw=1'))
        return out

def _get_driver(url):
    if 'googledrive' in url:
        return GDriveDriver(url)
    elif 'dropbox' in url:
        return DropbBoxDriver(url)
    else:
        return HostedImageDriver(url)

def get_hosted_image_urls(dir_url):
    # dir_url = 'https://www.dropbox.com/sh/qld85pm3a798vh4/AACEdqHHZ9yq04SeHcsitNJpa?dl=0'
    driver = _get_driver(dir_url)
    return driver.get_image_urls()
