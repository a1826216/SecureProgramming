import asyncio
from websockets.sync.client import connect

def hello():
    with connect("ws://localhost:8765") as websocket:
        while(1):
            text = input("enter a message: ")
            websocket.send(text)
            message = websocket.recv()
            print(f"Received: {message}")

hello()