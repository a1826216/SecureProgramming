import asyncio
import websockets
import json
import base64
from Crypto.PublicKey import RSA

async def hello():
    uri = "ws://localhost:8001"
    async with websockets.connect(uri) as websocket:
        # Generate RSA keypair
        key = RSA.generate(2048)
        public_key = key.publickey().export_key()

        # Send a "hello" message to the server
        message = {
            "data": {
                "type": "hello",
                "public_key": base64.b64encode(public_key).decode('utf-8')
            }
        }
        await websocket.send(json.dumps(message))
        print(f"Sent 'hello' message: {json.dumps(message)}")

        # Wait for a response from the server
        response = await websocket.recv()
        print(f"Received: {response}")

# Run the client
asyncio.get_event_loop().run_until_complete(hello())
