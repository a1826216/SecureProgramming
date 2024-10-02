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
        self.uri = uri
        self.websocket = None

        # Counter value (to be sent with signed data)
        self.counter = 0

        # Generate 2048-bit RSA key pair
        self.key_pair = RSA.generate(2048)

        # Exported PEM of public key
        self.public_key = self.key_pair.public_key().export_key()

        # Exported PEM of private key
        self.private_key = self.key_pair.export_key()

        # Client's own client ID
        self.client_id = self.generate_fingerprint(self.public_key)

        # Username to identify the user
        self.username = None

        # List of clients and usernames
        self.usernames = {}

    # Generate fingerprint from public key
    def generate_fingerprint(self, public_key):
        hash = SHA256.new(base64.b64encode(bytes(public_key.decode('utf-8'), 'utf-8')))
        return hash.hexdigest()

    # Helper function to generate signed data messages
    def generate_signed_data(self, data: dict):
        # Concatenate data and counter (this will form the signature)
        data_c = bytes(json.dumps(data) + str(self.counter), 'utf-8')

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

    # Helper function to generate and send a hello message
    async def send_hello(self):
        # Generate hello message
        data = {
            "type": "hello",
            "client_id": self.client_id,
            "username": self.username
        }

        hello_msg = self.generate_signed_data(data)

        # Send hello message
        await self.websocket.send(hello_msg)

    # Helper function to generate and send a public chat message
    async def send_chat(self, recipient_username, message):
        # Generate chat message
        data = {
            "type": "chat",
            "sender": self.client_id,
            "recipient_username": recipient_username,
            "message": message
        }

        chat_msg = self.generate_signed_data(data)

        # Send chat message
        await self.websocket.send(chat_msg)

    # Send client list request
    async def client_list_request(self):
        # Send message
        message = {"type": "client_list_request"}
        await self.websocket.send(json.dumps(message))

    # Handle client list
    async def handle_client_list(self, message):
        self.usernames = {client: username for client, username in zip(message["clients"], message["clients"])}
        print("\nClient list updated:")
        for username in self.usernames.values():
            print(f"Username: {username}")
        print()

    # Handle signed data messages
    async def handle_signed_data(self, message):
        message_type = message["data"]["type"]

        if message_type == "chat":
            sender = message["data"]["sender"]
            chat_message = message["data"]["message"]
            print(f"Message from {sender}: {chat_message}")

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

        if message_type == "signed_data":
            await self.handle_signed_data(message)
        elif message_type == "client_list":
            await self.handle_client_list(message)

    async def run(self):
        self.websocket = await websockets.connect(self.uri)
        print("Starting OLAF Neighbourhood client...")

        # Set username
        self.username = await ainput("Enter a username: ")

        # Send hello message
        print(f"Connecting to server at {self.uri}...")
        await self.send_hello()

        # Listen for incoming messages
        asyncio.ensure_future(self.listen())

        # Main loop
        while True:
            print("\nOptions:")
            print("1. Send a message to another client")
            print("2. Read messages from other clients")
            print("3. Request client list")
            print("4. Exit")
            option = await ainput("Select an option (1-4): ")

            if option == "1":
                recipient_username = await ainput("Enter the recipient's username: ")
                message = await ainput("Enter the message: ")
                await self.send_chat(recipient_username, message)
            elif option == "2":
                print("Reading messages...")
            elif option == "3":
                await self.client_list_request()
            elif option == "4":
                print("Closing connection to server...")
                if self.websocket:
                    await self.websocket.close()
                return
            else:
                print("Invalid option. Please select a valid option.")

if __name__ == "__main__":
    client = Client("ws://localhost:8001")

    # Run client
    asyncio.run(client.run())