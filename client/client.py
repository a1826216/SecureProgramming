import asyncio
import websockets
import json
import base64
import hashlib

from Crypto.Signature import pss
from Crypto.PublicKey import RSA
from Crypto.Hash import SHA256

class Client:
    def __init__(self, uri):
        # Address of server to connect to
        self.uri = uri
        
        # Counter value (to be sent with signed data)
        self.counter = 0

        # Generate 2048-bit RSA key pair
        self.key_pair = RSA.generate(2048)

        # Exported PEM of public key
        self.public_key = self.key_pair.public_key().export_key()

        # Exported PEM of private key
        self.private_key = self.key_pair.export_key()

        # List of all clients on all servers
        self.client_list = {}

    # Helper function to generate signed data messages
    def generate_signed_data(self, data:dict):
        # Concatenate data and counter (this will form the signature)
        data_c = bytes(json.dumps(data)+str(self.counter), 'utf-8')
        
        # Get SHA256 sum of data and counter
        hash = SHA256.new(data_c)

        # Sign signature with RSA private key
        signature = pss.new(self.key_pair, salt_bytes=32).sign(hash)

        # Base64 encode the signature
        signature = base64.b64encode(signature)
        
        signed_data = {
            "type": "signed_data",
            "data": data,
            "counter": self.counter,
            "signature": bytes.decode(signature)
        }

        # Increment counter value (for future signed data messages)
        self.counter += 1

        return json.dumps(signed_data)
    
    async def send_hello(self, websocket):
        # Generate hello message
        data = {
            "type": "hello", 
            "public_key": str(self.public_key)
        }

        hello_msg = self.generate_signed_data(data)

        # Send hello message
        await websocket.send(hello_msg)

        response = await websocket.recv()
        print(f"Received: ", response)

    async def send_public_chat(self, websocket, message):
        # Get fingerprint of sender
        fingerprint = ""

        data = {
            "type": "public_chat",
            "sender": fingerprint,
            "message": message
        }

        public_chat_msg = self.generate_signed_data(data)

        await websocket.send(public_chat_msg)

    async def send_chat(self, websocket, message):
        pass


    # Send client list request
    async def client_list_request(self, websocket):
        message = {"type": "client_list_request"}

        await websocket.send(json.dumps(message))

        response = await websocket.recv()
        print(f"Received: ", response)

    # Run the client
    async def run(self):
        async with websockets.connect(self.uri) as websocket:
            await self.send_hello(websocket)
            await self.client_list_request(websocket)


if __name__ == "__main__":
    client = Client("ws://localhost:8765")

    # Testing signed data
    asyncio.run(client.run())