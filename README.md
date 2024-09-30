# Secure Programming S2 2024 - Group 15

An implementation of the OLAF Neighbourhood protocol as defined here:

https://github.com/xvk-64/2024-secure-programming-protocol

## Group Members
Alanna Anna Shibu

Samuel Hunter

Phapada Thanachotiwit

Henry Winter

## Setup Instructions

Python libraries can be installed using pip:

```
pip install websockets
pip install aioconsole
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

## Using the Client
When the client starts for the first time, it will immediately send a hello message to the server, and refresh the client list. 

### Examples:
List all currently online clients:
```
> list
List of clients:
9f7694c0f2b297bddedd6734b6df45509e6853bdd69eb8193e31685ab1146d1d (ws://localhost:8765)
bcb0c86e8959879aff164a6a3f5b5a304cc7957bbab4cbd8926474ee8791e715 (ws://localhost:8765)
```

Send a public chat message:
```
> public
Enter a message: <message>
```

When a public chat message is received it will appear directly in the terminal:
```
From 3bbea2cfb33c676350fe935a0dbca6c0e565cb49cf6d39772c3b1a54230818f1 (public): <message>
```

Send an encrypted chat message:
```
> chat
Not implemented yet!
```

Close connection to the server (this will exit the client):
```
> close
Closing connection to server...
$
```
