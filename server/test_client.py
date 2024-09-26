# Debug client for testing the server
# Real client will have additional features included

import asyncio
import json
from websockets.sync.client import connect

signed_data_msg = {
    "type": "signed_data",
    "data": {
        "type": "hello",
        "public_key": "<Exported RSA public key>"
    },
    "counter": 1,
    "signature": "<Base64 signature of data + counter>"
}

def hello():
    with connect("ws://localhost:8765") as websocket:
        # text = input("enter a message: ")
        websocket.send(json.dumps(signed_data_msg))
        message = websocket.recv()
        print(f"Received: {message}")
hello()


# msg = 