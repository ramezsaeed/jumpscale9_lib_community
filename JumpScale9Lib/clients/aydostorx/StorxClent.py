from js9 import j
import requests
from urllib.parse import urljoin, urlparse


class StorxFactory:

    def __init__(self,):
        super(StorxFactory, self).__init__()
        self.__jslocation__ = "j.clients.storx"
        self.__imports__ = "requests"

    def get(self, base_url):
        """
        base_url: str, url of the store e.g: https://aydostorx.com
        """
        return StorxClient(base_url)


class StorxClient:
    """Client for the AYDO Stor X"""

    def __init__(self, base_url):
        super(StorxClient, self).__init__()
        self.session = requests.Session()

        o = urlparse(base_url)
        self.base_url = o.geturl()
        self.path = o.path

    def _postURLStore(self, path):
        return urljoin(self.base_url, j.sal.fs.joinPaths(self.path, "store", path)).rstrip('/')

    def _getURLStore(self, namespace, hash):
        return urljoin(self.base_url, j.sal.fs.joinPaths(self.path, "store", namespace, hash)).rstrip('/')

    def _URLFixed(self, name):
        return urljoin(self.base_url, j.sal.fs.joinPaths(self.path, "static", name)).rstrip('/')

    def authenticate(self, login, password):
        if login and password:
            base = login + ":" + password
            auth_header = "Basic " + j.data.serializer.base64.dumps(base)
            self.session.headers = {"Authorization": auth_header}

    def putFile(self, namespace, file_path):
        """
        Upload a file to the store

        @namespace: str, namespace
        @file_path: str, path of the file to upload
        return: str, md5 hash of the file
        """
        url = self._postURLStore(namespace)
        resp = None
        with open(file_path, 'rb') as f:
            # streaming upload, avoid reading all file in memory
            resp = self.session.post(url, data=f, headers={
                                     'Content-Type': 'application/octet-stream'})
            resp.raise_for_status()

        return resp.json()["Hash"]

    def getFile(self, namespace, hash, destination):
        """
        Retreive a file from the store and save it to a file

        @namespace: str, namespace
        @hash: str, hash of the file to retreive
        """
        url = self._getURLStore(namespace, hash)
        resp = self.session.get(url, stream=True)

        resp.raise_for_status()

        with open(destination, 'wb') as fd:
            for chunk in resp.iter_content(65536):
                fd.write(chunk)

        return True

    def deleteFile(self, namespace, hash):
        """
        Delete a file from the Store

        @namespace: str, namespace
        @hash: str, hash of the file to delete
        """
        url = self._getURLStore(namespace, hash)
        resp = self.session.delete(url)

        resp.raise_for_status()

        return True

    def existsFile(self, namespace, hash):
        """
        Test if a file exists
        @namespace: str, namespace
        @hash: str, hash of the file to test
        return: bool
        """
        url = self._getURLStore(namespace, hash)
        resp = self.session.head(url)

        if resp.status_code == requests.codes.ok:
            return True
        elif resp.status_code == requests.codes.not_found:
            return False
        else:
            resp.raise_for_status()

    def existsFiles(self, namespace, hashes):
        """
        Test if a list of file exists

        @namespace: str, namespace
        @hashes: list, list of hashes to test
        return: dict, directory with keys as hashes and value boolean indicating of hash exists or not
        example :
            {'7f820c17fa6f8beae0828ebe87ef238a': True,
            'a84da677c7999e6bed29a8b2d9ebf0e3': True}

        """
        url = self._getURLStore(namespace, "exists")
        data = {'Hashes': hashes}
        resp = self.session.post(url, json=data)

        resp.raise_for_status()

        return resp.json()

    def listNameSpace(self, namespace, compress=False, quality=6):
        """
        Retreive list of all file from a namespace

        @namespace: str, namespace
        @compress: bool, enable compression of the files
        @quality: int, if compress is enable, defined the quality of compression.
            low number is fast but less efficent, hight number is slow but best compression
        """
        url_params = {
            'compress': compress,
            'quality': quality,
        }
        url = self._getURLStore(namespace, "")
        resp = self.session.get(url, params=url_params)

        resp.raise_for_status()

        return resp.json()

    def putStaticFile(self, name, file_path):
        """
        Upload a file to the store and give bind a name to it

        @name: str, name to give to the file
        @file_path: str, path of the file to upload
        """
        url = self._URLFixed(name)
        resp = None
        with open(file_path, 'rb') as f:
            # streaming upload, avoid reading all file in memory
            resp = self.session.post(url, data=f, headers={
                                     'Content-Type': 'application/octet-stream'})
            resp.raise_for_status()

        return True

    def getStaticFile(self, name, destination):
        """
        Retreive a named file from the store and save it to a file

        @name: str, name of the file to rertieve
        """
        url = self._URLFixed(name)
        resp = self.session.get(url, stream=True)

        resp.raise_for_status()

        with open(destination, 'wb') as fd:
            for chunk in resp.iter_content(65536):
                fd.write(chunk)

        return True
