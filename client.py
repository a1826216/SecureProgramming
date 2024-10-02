import asyncio
import websockets
import json
import hashlib
import base64
from aioconsole import ainput
from Crypto.Signature import pss
from Crypto.PublicKey import RSA
from Crypto.Hash import SHA256
from Crypto.Cipher import AES, PKCS1_OAEP
import secrets

class Client:
    def __init__(self, uri):
        self.uri = uri
        self.counter = 0
        self.websocket = None
        self.client_id = None
        self.username = None
        self.messages = []
        self.clients = []  # List of usernames

        # Generate RSA key pair (2048 bits)
        self.key_pair = RSA.generate(2048)
        self.public_key = self.key_pair.publickey().export_key().decode('utf-8')
        self.client_id = self.generate_fingerprint(self.public_key)

    def generate_fingerprint(self, public_key):
        hash = SHA256.new(base64.b64encode(bytes(public_key, 'utf-8')))
        return hash.hexdigest()

    def generate_signed_data(self, data: dict):
        data_c = bytes(json.dumps(data) + str(self.counter), 'utf-8')
        hash_value = SHA256.new(data_c)

        signature = pss.new(self.key_pair).sign(hash_value)
        signature_b64 = base64.b64encode(signature).decode('utf-8')

        signed_data = {
            "type": "signed_data",
            "data": data,
            "counter": self.counter,
            "signature": signature_b64
        }

        self.counter += 1
        return json.dumps(signed_data)

    # Helper function to send hello message (initial connection)
    async def send_hello(self):
        data = {
            "type": "hello",
            "client_id": self.client_id,
            "username": self.username
        }
        hello_msg = self.generate_signed_data(data)
        await self.websocket.send(hello_msg)

    # Helper function to send public chat message to all clients
    async def send_public_chat(self, message):
        data = {
            "type": "public_chat",
            "sender": self.client_id,
            "message": message
        }
        public_chat_msg = self.generate_signed_data(data)
        await self.websocket.send(public_chat_msg)
        print("Public chat message sent.")

    # Helper function to send private chat message to a specific client
    async def send_chat(self, recipient_username, message):
        data = {
            "type": "chat",
            "sender": self.client_id,
            "recipient_username": recipient_username,
            "message": message
        }
        chat_msg = self.generate_signed_data(data)
        await self.websocket.send(chat_msg)
        print(f"Sent message to {recipient_username}.")

    # Request the list of connected clients
    async def request_client_list(self):
        await self.websocket.send(json.dumps({"type": "client_list_request"}))

    async def handle_chat(self, message):
        sender = message["data"]["sender"]
        chat_message = message["data"]["message"]
        self.messages.append({"sender": sender, "message": chat_message})
        print(f"Received message from {sender}: {chat_message}")

    async def handle_public_chat(self, message):
        await self.handle_chat(message)

    async def handle_client_list(self, message):
        self.clients = message["clients"]
        print("\nClient list updated:")
        for client in self.clients:
            print(f"Username: {client}")
        print()

    async def handle_messages(self, message):
        message_type = message.get("type")
        if message_type == "chat":
            await self.handle_chat(message)
        elif message_type == "public_chat":
            await self.handle_public_chat(message)
        elif message_type == "client_list":
            await self.handle_client_list(message)
        else:
            print(f"Invalid message type received: {message}")

    async def listen(self):
        async for message in self.websocket:
            data = json.loads(message)
            await self.handle_messages(data)

    async def read_messages(self):
        if self.messages:
            for msg in self.messages:
                print(f"Message from {msg['sender']}: {msg['message']}")
            self.messages.clear()
        else:
            print("No new messages.")

    async def run(self):
        self.websocket = await websockets.connect(self.uri)
        print("Starting OLAF Neighbourhood client...")

        self.username = await ainput("Enter a username: ")
        await self.send_hello()

        asyncio.ensure_future(self.listen())

        while True:
            print("\nOptions:")
            print("list: List all clients")
            print("public: Send a public chat message")
            print("chat: Send an encrypted chat message")
            print("close: Close the connection")
            option = await ainput("> ")

            if option == 'list':
                await self.request_client_list()
            elif option == 'public':
                public_message = await ainput("Enter a message: ")
                await self.send_public_chat(public_message)
            elif option == 'chat':
                recipient_username = await ainput("Enter recipient's username: ")
                chat_message = await ainput("Enter a message: ")
                await self.send_chat(recipient_username, chat_message)
            elif option == 'close':
                print("Closing connection to server...")
                if self.websocket:
                    await self.websocket.close()
                break
            else:
                print("Invalid option. Please use 'list', 'public', 'chat', or 'close'.")

if __name__ == "__main__":
    client = Client("ws://localhost:8001")
    asyncio.run(client.run())