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

For the server, the websockets library for Python can be installed using pip.

```
pip install websockets
```

## Setup Instructions
As the server is a Python file, no compilation is necessary, and it can be started directly.

```
cd server
python3 server.py
```

To build and run the client, run the following commands:

```
cd client
make
./client
```

(this section is very incomplete)
