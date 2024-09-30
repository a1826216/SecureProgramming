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

        # Websocket connection object
        self.websocket = None

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

    
    async def send_hello(self):
        # Generate hello message
        data = {
            "type": "hello", 
            "public_key": self.public_key.decode('utf-8')
        }

        hello_msg = self.generate_signed_data(data)

        # Send hello message
        await self.websocket.send(hello_msg)

        response = await self.websocket.recv()
        print(f"Received: ", response)

    async def send_public_chat(self, message):
        # Get fingerprint of sender
        fingerprint = SHA256.new(base64.b64encode(bytes(self.public_key.decode('utf-8'), 'utf-8'))).hexdigest()

        data = {
            "type": "public_chat",
            "sender": fingerprint,
            "message": message
        }

        public_chat_msg = self.generate_signed_data(data)

        await self.websocket.send(public_chat_msg)

    async def send_chat(self, message):
        pass


    # Send client list request
    async def client_list_request(self):
        # Send message
        message = {"type": "client_list_request"}
        await self.websocket.send(json.dumps(message))

        # Wait for response
        response = await self.websocket.recv()
        print(f"Received: ", response)

    # Listen for messages
    async def listen(self):
        pass

    # Handle incoming messages
    async def handle_messages(self):
        pass

    # Run the client
    async def run(self):
        async with websockets.connect(self.uri) as self.websocket:
            print("Starting OLAF Neighbourhood client...")

            # Send hello message
            print(f"Connecting to server at {self.uri}...")
            await self.send_hello()

            # Main loop
            while (1):
                prompt = input("> ")

                match prompt:
                    case "public":
                        message = input("Enter a message: ")
                        await self.send_public_chat(message)
                    case "chat":
                        print("not implemented yet!")
                    case "list":
                        await self.client_list_request()
                    case "close":
                        print("Closing connection to server...")
                        await self.websocket.close()
                        return

    # # Basic tests for client functionality
    # async def tests(self):
    #     async with websockets.connect(self.uri) as websocket:
    #         # Try to send a public chat before hello is sent
    #         await self.send_public_chat(websocket, "public chat!")
            
    #         # Send hello and get client list
    #         await self.send_hello(websocket)
    #         await self.client_list_request(websocket)

    #         # Send a duplicate hello
    #         await self.send_hello(websocket)

    #         # Send a public chat
    #         await self.send_public_chat(websocket, "public chat!")

    #         # await websocket.close()
    #         return

if __name__ == "__main__":
    client = Client("ws://localhost:8765")

    # Testing signed data
    asyncio.run(client.run())