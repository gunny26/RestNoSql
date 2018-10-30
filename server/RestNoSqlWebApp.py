#!/usr/bin/python
"""
Blockstorage Web Application
Backend to store chunks of Blocks to disk, and retrieve thru RestFUL API
"""
import web
import os
import sys
import time
from sqlitedict import SqliteDict
import json
import logging
FORMAT = '%(module)s.%(funcName)s:%(lineno)s %(levelname)s : %(message)s'
logging.basicConfig(level=logging.INFO, format=FORMAT)
logging.getLogger("sqlitedict").setLevel(logging.ERROR)

urls = (
    "/manager/(.*)", "RestNoSqlManager", # to create or drop database
    "/database/(.*)", "RestNoSql", # to use pre-created databases
)

# in PROD this will be put in config file
CONFIG = json.load(open(os.path.expanduser("~/RestNoSqlWebApp.json")))


def authenticator(config):
    def real_authenticator(func):
        """
        decorator for authentication
        """
        log = logging.getLogger(func.__name__)
        def inner(*args, **kwds):
            call_str = "%s(%s, %s)" % (func.__name__, args[1:], kwds)
            log.debug("args: %s", args[1:])
            log.debug("kwds: %s", kwds)
            log.debug("function to call: %s", call_str)
            # log.info(web.ctx.env)
            try:
                if web.ctx.env.get("HTTP_X_IDKEY") is None:
                    log.error("X-IDKEY Header missing")
                    web.ctx.status = "401 Unauthorized"
                    return
                idkey = web.ctx.env.get("HTTP_X_IDKEY")
                log.debug("idkey : %s", idkey)
                if idkey not in config:
                    log.error("X-IDKEY %s is unknown", idkey)
                    web.ctx.status = "401 Unauthorized"
                    return
                if web.ctx.env.get("HTTP_X_APIKEY") is None:
                    log.error("X-APIKEY Header missing")
                    web.ctx.status = "401 Unauthorized"
                    return
                apikey = web.ctx.env.get("HTTP_X_APIKEY")
                log.debug("apikey : %s", apikey)
                if apikey not in config[idkey]:
                    log.error("X-APIKEY %s not found", apikey)
                    web.ctx.status = "401 Unauthorized"
                    return
                method = web.ctx.env.get("REQUEST_METHOD")
                log.debug("method : %s", method)
                if method not in config[idkey][apikey]["methods"]:
                    log.error("X-APIKEY %s not allowed for method %s", apikey, method)
                    web.ctx.status = "401 Unauthorized"
                    return
                log.debug("successfully authorized with APIKEY %s for method %s", apikey, method)
                # injecting _x_apikey and _x_idkey
                kwds["_x_idkey"] = web.ctx.env.get("HTTP_X_IDKEY")
                kwds["_x_apikey"] = web.ctx.env.get("HTTP_X_APIKEY")
                ret_val = func(*args, **kwds)
                return ret_val
            except Exception as exc:
                log.exception(exc)
                log.error("call to %s caused Exception", call_str)
                web.internalerror()
        # set inner function __name__ and __doc__ to original ones
        inner.__name__ = func.__name__
        inner.__doc__ = func.__doc__
        return inner
    return real_authenticator

def encode_json(func):
    """
    to encode returned value to json string
    and set Content-Type
    """
    log = logging.getLogger(func.__name__)
    def inner(*args, **kwds):
        call_str = "%s(%s, %s)" % (func.__name__, args[1:], kwds)
        log.debug("args: %s", args[1:])
        log.debug("kwds: %s", kwds)
        log.debug("function to call: %s", call_str)
        try:
            ret_val = func(*args, **kwds)
            web.header('Content-Type', 'application/json')
            return json.dumps(ret_val)
        except Exception as exc:
            log.exception(exc)
            log.error("call to %s caused Exception", call_str)
            web.internalerror()
    # set inner function __name__ and __doc__ to original ones
    inner.__name__ = func.__name__
    inner.__doc__ = func.__doc__
    return inner

def stats(func):
    """
    to encode returned value to json string
    and set Content-Type
    """
    log = logging.getLogger(func.__name__)
    def inner(*args, **kwds):
        call_str = "%s(%s, %s)" % (func.__name__, args[1:], kwds)
        log.debug("args: %s", args[1:])
        log.debug("kwds: %s", kwds)
        starttime = time.time()
        try:
            ret_val = func(*args, **kwds)
            log.debug("function %s duration %s", call_str, (time.time() - starttime))
            return ret_val
        except Exception as exc:
            log.exception(exc)
            log.error("call to %s caused Exception", call_str)
            web.internalerror()
    # set inner function __name__ and __doc__ to original ones
    inner.__name__ = func.__name__
    inner.__doc__ = func.__doc__
    return inner



#logging.info("scanning existing databases")
STORAGE_DIR = "/var/www/data"
if not os.path.isdir(STORAGE_DIR):
    os.mkdir(STORAGE_DIR)
for idkey in CONFIG.keys():
    id_dir = os.path.join(STORAGE_DIR, idkey)
    if not os.path.isdir(id_dir):
        logging.info("creating subdirectory for id %s", idkey)
        os.mkdir(id_dir)
#logging.info("found %s", os.listdir(STORAGE_DIR))


class RestNoSqlManager(object):
    """
    Stores Chunks of Data into Blockstorage Directory with sha1 as filename and identifier

    Interface

    every call must have X-ACCESS-KEY SET
    ever X-ACCESS-KEY could have 3 roles
        R - read only, using only HEAD/GET Method
        RW - read, add and modify, usind HEAD/GET/POST/PUT Method
        RWD - read, add and modify and delete, using HEAD/GET/POST/PUT/DELETE Method

    key must be string with maximum length of 100

    HEAD   /<database>  exists databases
    GET    /            return all databases
    PUT    /<database>  create database
    DELETE /<database>  delete database
    """

    @authenticator(CONFIG)
    @encode_json
    def GET(self, *args, **kwds):
        """
        LIST available Databases
        """
        id_dir = os.path.join(STORAGE_DIR, kwds["_x_idkey"])
        return os.listdir(id_dir)

    @authenticator(CONFIG)
    def POST(self, *args, **kwds):
        """
        CREATE empty DB
        """
        database = args[0].split("/")[0]
        id_dir = os.path.join(STORAGE_DIR, kwds["_x_idkey"])
        if not os.path.isdir(id_dir):
            os.mkdir(id_dir)
        db_dir = os.path.join(id_dir, database)
        if not os.path.isdir(db_dir):
            os.mkdir(db_dir)
        filename = os.path.join(db_dir, "data.sqlite")
        # if file already exists, nothing special happens !
        with SqliteDict(filename) as db:
            logging.info("POST database %s in file %s created", database, filename)
        return database

    @authenticator(CONFIG)
    def PUT(self, *args, **kwds):
        """
        TODO: IMPORT from provided Data
        """
        return
        #database = args[0].split("/")[0]
        #os.mkdir(os.path.join(STORAGE_DIR, database))
        #with dbm.open(os.path.join(STORAGE_DIR, database, "data.dbm"), "c") as db:
        #    for key, value in json.loads(web.data.decode("utf-8")):
        #        db[key] = json.dumps(value)
        #logging.info("PUT database %s imported", database)

    @authenticator(CONFIG)
    def HEAD(self, *args, **kwds):
        """
        does database exist
        """
        database = args[0].split("/")[0]
        id_dir = os.path.join(STORAGE_DIR, kwds["_x_idkey"])
        if database not in os.listdir(id_dir):
            web.notfound()

    @authenticator(CONFIG)
    def DELETE(self, *args, **kwds):
        """
        delete database
        """
        database = args[0].split("/")[0]
        id_dir = os.path.join(STORAGE_DIR, kwds["_x_idkey"])
        if database not in os.listdir(id_dir):
            web.notfound()
        else:
            db_filename = os.path.join(id_dir, database, "data.sqlite")
            if os.path.isfile(db_filename):
                os.unlink(db_filename)
            os.rmdir(os.path.join(id_dir, database))
            logging.info("database %s deleted", database)

    @authenticator(CONFIG)
    @encode_json
    def OPTIONS(self, *args, **kwds):
        id_dir = os.path.join(STORAGE_DIR, kwds["_x_idkey"])
        return os.listdir(id_dir)


class RestNoSql(object):
    """
    Stores Chunks of Data into Blockstorage Directory with sha1 as filename and identifier

    Interface

    every call must have X-ACCESS-KEY SET
    ever X-ACCESS-KEY could have 3 roles
        R - read only, using only HEAD/GET Method
        RW - read, add and modify, usind HEAD/GET/POST/PUT Method
        RWD - read, add and modify and delete, using HEAD/GET/POST/PUT/DELETE Method

    key must be string with maximum length of 100 character TODO

    OPTIONS     /<database>/     return list of keys
    GET         /<database>/key  return value of key or 404
    PUT         /<database>/     replace existing data with provided data, json formatteddata must be dict
    POST        /<database>/key  existing value will be replaced
    DELETE      /<database>/key  delete key/value pair
    """

    def _db(self, database, x_idkey):
        db_filename = os.path.join(STORAGE_DIR, x_idkey, database, "data.sqlite")
        return db_filename

    @authenticator(CONFIG)
    @encode_json
    @stats
    def GET(self, *args, **kwds):
        """
        key data
        data should be string or None
        """
        database = args[0].split("/")[0]
        key = json.loads(web.data().decode("utf-8"))
        try:
            with SqliteDict(self._db(database, kwds["_x_idkey"])) as db:
                return db[key]
        except KeyError:
            web.notfound()

    @authenticator(CONFIG)
    @stats
    def PUT(self, *args, **kwds):
        """
        append data to existing data of key, value will be unique
        
        value has to be of type list

        if key in data:
            data[key] = list(set(data[key] + value))
        else:
            data[key] = value
        """
        database = args[0].split("/")[0]
        key, value = json.loads(web.data().decode("utf-8"))
        with SqliteDict(self._db(database, kwds["_x_idkey"]), autocommit=True) as db:
            if key in db:
                if db[key] != value:
                    db[key] = value
            else:
                db[key] = value

    @authenticator(CONFIG)
    @stats
    def POST(self, *args, **kwds):
        """
        set key to value, if key already exists, the old value will be destroyed
        if value ha to be of type list

        assert isinstance(value, list)
        data[key] = value
        """
        database = args[0].split("/")[0]
        key, value = json.loads(web.data().decode("utf-8"))
        with SqliteDict(self._db(database, kwds["_x_idkey"]), autocommit=True) as db:
            db[key] = value

    @authenticator(CONFIG)
    @encode_json
    @stats
    def OPTIONS(self, *args, **kwds):
        """
        return list of keys in database
        """
        database = args[0].split("/")[0]
        keys = []
        with SqliteDict(self._db(database, kwds["_x_idkey"])) as db:
            return list(db.keys())

    @authenticator(CONFIG)
    @stats
    def DELETE(self, *args, **kwds):
        """
        delete key in database or 404 if key not found
        """
        database = args[0].split("/")[0]
        key = json.loads(web.data().decode("utf-8"))
        try:
            with SqliteDict(self._db(database, kwds["_x_idkey"]), autocommit=True) as db:
                del db[key]
        except KeyError:
            web.notfound()

    @authenticator(CONFIG)
    @stats
    def PATCH(self, *args, **kwds):
        """
        delete one key if key given or delete all keys if no key is given

        TODO: theres a slight chance, the database is not ready,
            so i will try 2 times, and wait for 1 s in between
        """
        return
        #database = args[0].split("/")[0]
        #with dbm.open(self._db(database), "w") as db:
        #    db.reorganize()


if __name__ == "__main__":
    app = web.application(urls, globals())
    # app.run()
    app.request("/info")
else:
    application = web.application(urls, globals()).wsgifunc()
