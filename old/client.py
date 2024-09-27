import asyncio
import websockets
import json
import base64
from Crypto.PublicKey import RSA

async def request_client_list():
    uri = "ws://localhost:8001"  # Server WebSocket URI

    async with websockets.connect(uri) as websocket:
        # Send a request for the client list
        request_message = {
            "type": "client_list_request",
            "data": {}
        }
        await websocket.send(json.dumps(request_message))

        # Wait for the server to respond
        response = await websocket.recv()
        print(f"Available Clients: {response}")

async def hello():
    uri = "ws://localhost:8001"
    async with websockets.connect(uri) as websocket:
        # Generate RSA keypair
        key = RSA.generate(2048)
        public_key = key.publickey().export_key()
        username = input("Enter your username: ")

        # Send a "hello" message to the server
        message = {
            "data": {
                "type": "hello",
                "public_key": base64.b64encode(public_key).decode('utf-8'),
                "username": username
            }
        }
        await websocket.send(json.dumps(message))

        # Wait for a response from the server
        response = await websocket.recv()
        # Request client list after receiving 'hello' response
        print(f"Who would you like to message?")
        await request_client_list()

# Run the client
asyncio.get_event_loop().run_until_complete(hello())