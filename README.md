# RestNoSql

NoSQL Database with REST Interface, client and backend software.

## Backend

Backend WSGI Application is working with sqlite and sqlitedict to store some key value data locally on disk.
Basic Permission concept, one Tenant, multiple roles for this Tenant.

Tenant 1
  Key1 for Read Only
  Key2 for Read Write
  Key3 for Admin Tasks, like creating new database or droppinn
  
## Client

Clients makes heavy use of requests and json. Client will act as dict replacement.
