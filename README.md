# Secure Programming S2 2024 - Group 15

An implementation of the OLAF Neighbourhood protocol as defined here:

https://github.com/xvk-64/2024-secure-programming-protocol

## Group Members
Alanna Anna Shibu

Samuel Hunter

Phapada Thanachotiwit

Henry Winter

## Third-Party Libraries
WebSocket++ (https://github.com/zaphoyd/websocketpp/tree/master)

JSON (https://github.com/nlohmann/json)

OpenSSL (https://github.com/openssl/openssl)

## Setup Instructions
Install C++ libraries (for Ubuntu/WSL):

```
sudo apt update
sudo apt install nlohmann-json3-dev 
sudo apt install libwebsocketpp-dev
```

OpenSSL should already be installed on most systems.

Python libraries can be installed using pip:

```
pip install websockets
pip install pycryptodome
```

## Running the Client and Server
As the client is a Python file, no compilation is necessary, and it can be started directly.

```
cd client
python3 client.py
```

The server can be started using the same process.

```
cd server
python3 server.py
```

(this section is very incomplete)
