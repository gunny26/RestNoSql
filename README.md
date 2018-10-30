# RestNoSql

NoSQL Database with REST Interface, client and backend software.

## Backend

Backend WSGI Application is working with sqlite and sqlitedict to store some key value data locally on disk.
Basic Permission concept, one Tenant, multiple roles for this Tenant.

Tenant 1
  Key1 for Read Only
  Key2 for Read Write
  Key3 for Admin Tasks, like creating new database or droppinn

### Installation

On ubuntu 18.04 to use WSGI application on apache2

sudo apt install apache2
sudo apt install libapache2-mod-wsgi-py3
sudo apt install python3-webpy

also configure your VirtualHosts like this

    # allow apache2 to access webapps directory
    <Directory /opt/RestNoSql/server>
        AllowOverride None
        Require all granted
    </Directory>
    # RestNoSqlWebApp
    WSGIScriptAlias /restnosql /opt/RestNoSql/server/RestNoSqlWebApp.py
    WSGIDaemonProcess restnosql processes=1 threads=10
    WSGIProcessGroup restnosql 
  
## Client

Clients makes heavy use of requests and json. Client will act as dict replacement.

### Installation

To work with RestNoSqlClient you need python3 and requests.
To configure RestNoSqlClient you have to provide some data

{
    "url" : "https://someurl.google.com/restnosql",
    "apikey" : "a42c79ce-9682-477d-1234-7e2db335a9f5",
    "idkey" : "f52fd982-d971-4430-1234-db13f8e4fc9a",
    "proxies" : {
        "http" : "someproxy.home:3128",
        "https" : "someproxy.hom:3128"
    }
}

to initialize use something like


rnsc = RestNoSqlClient(url=config["url"], apikey=config["apikey"], idkey=config["idkey"], proxies=config["proxies"])

to create some new database

with rnsc.open("name_of_database") as db:
    db["somekey"] = "somevalue

every key and value has to be json serializable.

