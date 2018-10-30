#!/usr/bin/python3
# pylint: disable=line-too-long
"""
RestFUL Webclient to use BlockStorage WebApps
"""
import json
import unittest
import logging
from client import RestNoSqlClient, RestNoSqlDatabase


class Test(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.config = json.load(open("Test_RestNoSqlClient.json"))

    def test_list(self):
        print("connect and list existing databases, there should be any")
        rnsc = RestNoSqlClient(url=self.config["url"], apikey=self.config["apikey"], idkey=self.config["idkey"], proxies=self.config["proxies"])
        self.assertTrue(isinstance(rnsc.list(), list))

    def test_create_db(self):
        print("creating database and deleting it afterwards")
        rnsc = RestNoSqlClient(url=self.config["url"], apikey=self.config["apikey"], idkey=self.config["idkey"], proxies=self.config["proxies"])
        rnsc.create("testdatabase")
        self.assertTrue("testdatabase" in rnsc.list())
        rnsc.create("testdatabase") # doing multiple times does not affect anything
        self.assertTrue("testdatabase" in rnsc.list())
        rnsc.delete("testdatabase")

    def test_create_db(self):
        print("creating db, insert data, manipulate and delete database afterwards")
        rnsc = RestNoSqlClient(url=self.config["url"], apikey=self.config["apikey"], idkey=self.config["idkey"], proxies=self.config["proxies"])
        rnsc.create("testdatabase")
        self.assertTrue("testdatabase" in rnsc.list())
        with rnsc.open("testdatabase") as db:
            print(db.keys())
            self.assertTrue(len(db.keys()) == 0)
            db["testkey1"] = "testvalue1"
            self.assertTrue(len(db.keys()) == 1)
            db["testkey2"] = ["testvalue1", "testvalue2"]
            self.assertTrue(isinstance(db["testkey2"], list))
            print("testing items()")
            for key, value in db.items():
                print(key, value)
            print("testing keys()")
            for key in db.keys():
                print(key)
            print("testing values()")
            for value in db.values():
                print(value)
            del db["testkey2"]
            self.assertTrue(len(db.keys()) == 1)
            del db["testkey1"]
            self.assertTrue(len(db.keys()) == 0)
            print("accessing non existing key")
            try:
                db["notexistingkey"]
                raise Exception("this should result in KeyError")
            except KeyError:
                pass
        rnsc.delete("testdatabase")
