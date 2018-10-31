#!/usr/bin/python3
# pylint: disable=line-too-long
# disable=locally-disabled, multiple-statements, fixme, line-too-long
"""
command line program to search for files in stores webstorage archives
"""
import os
import time
import datetime
import sys
import socket
import json
import threading
import queue
import argparse
import logging
logging.basicConfig(stream=sys.stdout, level=logging.INFO, format='%(message)s')
logging.getLogger("requests").setLevel(logging.WARNING)
logging.getLogger("urllib3").setLevel(logging.WARNING)
# own modules
from webstorage import WebStorageArchiveClient as WebStorageArchiveClient
from RestNoSqlClient import RestNoSqlClient as RestNoSqlClient

def search_checksum(directory, checksum):
    """
    update or create local webstorage index database
    """
    filename_db = os.path.join(directory, "checksum_backupsets.sqlite")
    with rnsc.open("absfilename_checksums") as db:
        print("searching checksum ", checksum)
        try:
            value = db[checksum]
            return value
        except KeyError:
            print("\t not found")

def search_absfile(directory, absfile):
    """
    update or create local webstorage index database
    """
    with rnsc.open("checksum_backupset") as db:
        print("searching absfile ", absfile)
        try:
            value = db[absfile]
            print(value)
            return value
        except KeyError:
            print("\t not found")

def create_nosql():
    """
    update or create local webstorage index database
    """
    num_worker_thread = 4
    #rnsc.delete("absfilename_checksums")
    #rnsc.delete("checksum_backupset")
    #rnsc.delete("backupset_log")
    # prepare queue and threads
    q = queue.Queue()
    threads = []
    for i in range(num_worker_thread):
        t = threading.Thread(target=checksum_thread, args=[q, ])
        t.start()
        threads.append(t)
    myhostname = socket.gethostname()
    wsa = WebStorageArchiveClient()
    backupsets = wsa.get_backupsets(myhostname)
    for backupset in backupsets:
        print("working on backupset ", backupset["basename"])
        if backupset["basename"] in db_backupsets.keys():
            print("this backupset was already done on ", db_backupsets[backupset["basename"]])
            continue
        hostname, tag, isoformat_ext = backupset["basename"].split("_")
        print(hostname, tag, backupset["date"], backupset["time"])
        data = wsa.get(backupset["basename"])
        for absfile in sorted(data["filedata"].keys()):
            checksum = data["filedata"][absfile]["checksum"]
            q.put([backupset, absfile, checksum]) # put in queue
        logging.info("main thread is waiting")
        q.join() # wait until queue is empty
        logging.info("backupset finished")
        if backupset["basename"] not in db_backupsets.keys():
            db_backupsets[backupset["basename"]] = datetime.datetime.now().isoformat()
    for i in range(num_worker_thread):
        q.put(None)
    for t in threads:
        t.join()

def checksum_thread(myqueue):
    # one session per thread
    # until que is empty
    while True:
        item = myqueue.get()
        if item is None:
            break
        backupset, absfilename, checksum = item
        try:
            # build absfilename to checksum KV
            if absfilename in db_absfilename:
                db_absfilename[absfilename].append(checksum)
            else:
                print("%s first appeared with checksum %s" % (absfilename, checksum))
                db_absfilename[absfilename] = [checksum, ]
            # build checksum to backupset KV
            if backupset["datetime"] in db_checksum and backupset["datetime"] > db_checksum[checksum]["datetime"]:
                db_checksum[checksum] = backupset
            else:
                print("%s first appeared in %s" % (checksum, backupset["basename"]))
                db_checksum[checksum] = backupset
        except Exception as exc:
            logging.error(exc)
        myqueue.task_done()


def main1():
    """
    parse commandline and to something useful
    """
    parser = argparse.ArgumentParser(description='search for files and checksum in local index database')
    parser.add_argument("--update", action="store_true", default=False, help="create or update local index database", required=False)
    parser.add_argument("-c", "--checksum", help="search for checksum", required=False)
    parser.add_argument("-n", '--name', help="search for name", required=False)
    parser.add_argument("-m", '--mime-type', help="search by mime-type", required=False)
    parser.add_argument("-b", '--backupset', help="search for backupset", required=False)
    parser.add_argument("-x", '--exact', action="store_true", default=False, help="dont use wildcard search, use the provided argument exactly", required=False)
    parser.add_argument('-d', '--database', default="~/.webstorage/searchindex.db", help="sqlite3 database to use", required=False)
    parser.add_argument('-q', "--quiet", action="store_true", help="switch to loglevel ERROR", required=False)
    parser.add_argument('-v', "--verbose", action="store_true", help="switch to loglevel DEBUG", required=False)
    args = parser.parse_args()
    database = os.path.expanduser(args.database) # expand user directory in path
    if os.path.isfile(database):
        logging.info("using database %s", database)
    else:
        logging.info("first use, creating database %s, you should run --update first", database)
    if args.update is True:
        update(database)
    if args.name is not None:
        search_name(database, args.name, args.exact)
    elif args.checksum is not None:
        search_checksum(database, args.checksum)
    elif args.mime_type is not None:
        search_mime_type(database, args.mime_type)


if __name__ == "__main__":
    config = json.load(open(os.path.expanduser("~/.restnosql/config.json")))
    rnsc = RestNoSqlClient(url=config["url"], apikey=config["apikey"], idkey=config["idkey"], proxies=config["proxies"])
    with rnsc.open("backupsets_log") as db_backupsets:
        with rnsc.open("absfilename_checksums") as db_absfilename:
            with rnsc.open("checksum_backupset") as db_checksum:
                create_nosql()
                file_to_search = "/home/mesznera/Dokumente/Patidok_performance/videobenchmark/auswertung.ods"
                checksums = search_absfile(tmpdir, file_to_search)
                if checksums:
                    print("found file %s in %d backupsets" % (file_to_search, len(checksums)))
                    for checksum in checksums:
                        search_checksum(checksum)
                else:
                    print("file %s not found" % file_to_search)
