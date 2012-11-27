# Real-Time-Web-App-Stack-with-Python-Tornado
A collection of examples, tests and documentation for building a real-time web app with python tornado.


## Technology Overview

### MongoDB
- Document-orientated database
- Uses BSON (Binary JSON), faster especially when storing binary data
- You can use a simple query-syntax or map/reduce for retreiving data
- Dynamic queries, meaning queries can be run without planing for it (CouchDB does not support this)
- Geospatial Indexes
- Updating in-place: very fast lazy writing but less safe
- Easily scalable with master-slave setup or sharding


## Implementations / Examples

### Tornado, MongoDB, PyMongo, Longpolling
- Example: Not yet deployed.
- <a href="https://github.com/nellessen/Real-Time-Web-App-Stack-with-Python-Tornado/tree/master/chat-pymongo-longpolling">Source Code</a>

### Tornado, MongoDB, Asyncmongo, Longpolling
- Example: Not yet deployed.
- <a href="https://github.com/nellessen/Real-Time-Web-App-Stack-with-Python-Tornado/tree/master/chat-asyncmongo-longpolling">Source Code</a>

### Tornado, Redis, brukva, Longpolling
- Example: Not yet deployed.
- <a href="https://github.com/nellessen/Real-Time-Web-App-Stack-with-Python-Tornado/tree/master/chat-brukva-longpolling">Source Code</a>

### Tornado, Redis, brukva, Websockets
- Example: Not yet deployed.
- <a href="https://github.com/nellessen/Real-Time-Web-App-Stack-with-Python-Tornado/tree/master/chat-brukva-websockets">Source Code</a>