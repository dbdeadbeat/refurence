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
        #  for link in BeautifulSoup(doc.content, parse_only=SoupStrainer('a', href=True)):
        soup = BeautifulSoup(doc.content)
        for link in soup.findAll('a', {'class' : 'thumb-link'}):
            if link['href'].endswith('dl=0') and not self._is_link_a_dir(link):
                imgs[link['href']] = True
        out = []
        for k in imgs.keys():
            out.append(k.replace('dl=0', 'raw=1'))
        return out

    def get_directory_urls(self):
        session = requests.session()
        doc = session.get(self.url)
        if not doc:
            return []

        dirs = []
        soup = BeautifulSoup(doc.content)
        for link in soup.findAll('a', {'class' : 'thumb-link'}):
            if self._is_link_a_dir(link):
                dirs.append(link)

        out = []
        for l in dirs:
            dirname = l['href'].split('/')[-1].split('?')[0]
            dirname = dirname.replace('%20', ' ')
            out.append({'name' : dirname, 'url': l['href']})
        return out

    def _is_link_a_dir(self, link):
        for child in link.findChildren():
            for cls in child['class']:
                if 'folder' in cls:
                    return True
        return False

def _get_driver(url):
    if 'googledrive' in url:
        return GDriveDriver(url)
    elif 'dropbox' in url:
        return DropbBoxDriver(url)
    else:
        return HostedImageDriver(url)

def get_hosted_image_urls(dir_url):
    driver = _get_driver(dir_url)
    return driver.get_image_urls()

def get_hosted_dir_urls(dir_url):
    driver = _get_driver(dir_url)
    return driver.get_directory_urls()
