#!/usr/bin/python3
# pylint: disable=line-too-long
"""
RestFUL Webclient to use BlockStorage WebApps
"""
import logging
import json
import requests

class RestNoSqlClient(object):
    """stores chunks of data into BlockStorage"""

    def __init__(self, url=None, apikey=None, idkey=None, cache=True, proxies=None):
        """__init__"""
        self._logger = logging.getLogger(self.__class__.__name__)
        self._version = "0.1"
        self._url = url
        self._apikey = apikey
        self._idkey = idkey
        self._proxies = proxies
        self._headers = {
            "user-agent": "%s-%s" % (self.__class__.__name__, self._version),
            "x-apikey" : self._apikey,
            "x-idkey" : self._idkey
        }
        #self._proxies = {
        #    "http" : "ubuntu.tilak.cc:3128",
        #    "https" : "ubuntu.tilak.cc:3128"
        #    }
        self._session = requests.session()

    def _request(self, method, path="", data=None):
        """
        single point of request
        """
        url = "/".join((self._url, "manager", path))
        res = self._session.request(method, url, data=data, headers=self._headers, proxies=self._proxies)
        if 199 < res.status_code < 300:
            return res
        elif 399 < res.status_code < 500:
            raise KeyError("HTTP_STATUS %s received" % res.status_code)
        elif 499 < res.status_code < 600:
            raise IOError("HTTP_STATUS %s received" % res.status_code)

    def create(self, database):
        self._request("POST", database)

    def open(self, database, mode="c"):
        if mode == "c": # create if not exists
            if database not in self.list():
                self.create(database)
        return RestNoSqlDatabase(self._url + "/database/" + database, self._session, self._apikey, self._headers, self._proxies)

    def delete(self, database):
        self._request("DELETE", database)

    def exists(self, database):
        return database in self.list()

    def list(self):
        res = self._request("OPTIONS")
        return res.json()

class RestNoSqlDatabase(object):


    def __init__(self, url, session, apikey, headers, proxies):
        """__init__"""
        self._logger = logging.getLogger(self.__class__.__name__)
        self._version = "0.1"
        self._url = url
        self._apikey = apikey
        self._headers = headers
        self._proxies = proxies
        self._session = session
        self._keys = None
        self._data = {}

    def _request(self, method, path="", data=None):
        """
        single point of request
        """
        url = "/".join((self._url, path))
        res = self._session.request(method, url, data=json.dumps(data), headers=self._headers, proxies=self._proxies)
        if 199 < res.status_code < 300:
            return res
        elif 399 < res.status_code < 500:
            raise KeyError("HTTP_STATUS %s received" % res.status_code)
        elif 499 < res.status_code < 600:
            raise IOError("HTTP_STATUS %s received" % res.status_code)

    def __enter__(self):
        return self

    def __exit__(self, *args):
        pass

    def __contains__(self, item):
        """ mimic x in y behaviour """
        # print("contains %s" % item)
        return item in self.keys()

    def keys(self):
        if self._keys is None:
            self._keys = self._request("OPTIONS").json()
        return self._keys

    def __getitem__(self, key):
        res = self._request("GET", data=key)
        return res.json()

    def __setitem__(self, key, value):
        res = self._request("POST", data=[key, value])
        self._keys.append(key)

    def __delitem__(self, key):
        res = self._request("DELETE", data=key)
        self._keys.remove(key)

    def items(self):
        for key in self.keys():
            yield (key, self[key])

    def values(self):
        for key in self.keys():
            yield self[key]

    #def __getattribute__(self, attr):
    #    print("requesting %s" % attr)
    #    return object.__getattribute__(self, attr)
