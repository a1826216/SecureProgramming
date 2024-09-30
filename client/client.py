import asyncio
import websockets
import json
import base64
import hashlib
from aioconsole import ainput

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

        # Client's own client ID
        self.client_id = SHA256.new(base64.b64encode(bytes(self.public_key.decode('utf-8'), 'utf-8'))).hexdigest()

        # List of clients on home server (excluding this one)
        self.clients = {}

        # List of clients on other servers
        self.neighbourhood_clients = {}

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
    
    # Helper function to return client ID (for adding clients to server client list)
    def get_client_id(self, public_key):
        return SHA256.new(base64.b64encode(bytes(public_key, 'utf-8'))).hexdigest()

    # Helper function to generate and send a hello message
    async def send_hello(self):
        # Generate hello message
        data = {
            "type": "hello", 
            "public_key": self.public_key.decode('utf-8')
        }

        hello_msg = self.generate_signed_data(data)

        # Send hello message
        await self.websocket.send(hello_msg)

    # Helper function to generate and send a public chat message
    async def send_public_chat(self, message):
        # Generate public chat message
        data = {
            "type": "public_chat",
            "sender": self.client_id,
            "message": message
        }

        public_chat_msg = self.generate_signed_data(data)

        # Send public chat message
        await self.websocket.send(public_chat_msg)

    async def send_chat(self, message, recipients):
        pass

    # Send client list request
    async def client_list_request(self):
        # Send message
        message = {"type": "client_list_request"}
        await self.websocket.send(json.dumps(message))

    # Handle client list
    async def handle_client_list(self, message):
        # Create list of client IDs
        temp_list = {}
        
        # Handle clients on all servers
        for server in message["servers"]:
            for public_key in server['clients']:
                client_id = self.get_client_id(public_key)
                    
                # Add client if client ID is not this client
                if client_id != self.client_id:
                    temp_list[client_id] = {
                        "home_server": server["address"], 
                        "fingerprint": client_id,
                        "public_key": public_key,
                    }

        # Replace client list
        self.clients = temp_list

    # Print client list
    def print_client_list(self):
        # List clients on all servers
        print("List of clients:")
        for client in self.clients:
            home_server = self.clients[client]["home_server"]
            print(f"{client} ({home_server})")

    # Handle signed data messages
    async def handle_signed_data(self, message):
        message_type = message["data"]["type"]

        match message_type:
            case "public_chat":
                sender = message["data"]["sender"]
                chat = message["data"]["message"]
                print(f"From {sender} (public): {chat}")
            case "chat":
                print("regular chat")
            case _:
                print("Invalid message type sent to client")

    # Handle chat sent by another client
    async def handle_chat(self):
        pass

    # Listen for messages
    async def listen(self):
        # Receive message
        async for message in self.websocket:
            data = json.loads(message)
            if "type" not in data.keys():
                print(f"Received from server: {message}")
            else:
                await self.handle_messages(data)

    # Handle incoming messages
    async def handle_messages(self, message):
        message_type = message["type"]

        match message_type:
            case "signed_data":
                await self.handle_signed_data(message)
            case "client_list":
                await self.handle_client_list(message)
            case _:
                print("Invalid message type received")

    async def run(self):
        self.websocket = await websockets.connect(self.uri)
        print("Starting OLAF Neighbourhood client...")

        # Send hello message
        print(f"Connecting to server at {self.uri}...")
        await self.send_hello()

        # Listen for incoming messages
        asyncio.ensure_future(self.listen())

        # Get client list
        await self.client_list_request()

        # Main loop
        while True:
            prompt = await ainput("> ")

            match prompt:
                case "public":
                    message = await ainput("Enter a message: ")
                    await self.send_public_chat(message)
                case "chat":
                    print("not implemented yet!")
                case "list":
                    await self.client_list_request()
                    self.print_client_list()
                case "close":
                    print("Closing connection to server...")
                    if self.websocket:
                        await self.websocket.close()
                    return
                case _:
                    print("Valid commands are ('public', 'chat', 'list', 'close')")

if __name__ == "__main__":
    client = Client("ws://localhost:8765")

    # Run client
    asyncio.run(client.run())



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