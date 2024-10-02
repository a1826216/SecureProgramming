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
        self.counter = 0
        self.websocket = None

        # Generate 2048-bit RSA key pair
        self.key_pair = RSA.generate(2048)
        self.public_key = self.key_pair.public_key().export_key()
        self.private_key = self.key_pair.export_key()

        # Client ID based on the public key fingerprint
        self.client_id = self.generate_client_id()

        # Store messages
        self.messages = []

        # Connected clients
        self.clients = []

    def generate_client_id(self):
        sha256_hash = hashlib.sha256(base64.b64encode(bytes(self.public_key.decode('utf-8'), 'utf-8'))).digest()
        return base64.b64encode(sha256_hash).decode('utf-8')

    def generate_signed_data(self, data: dict):
        data_c = bytes(json.dumps(data) + str(self.counter), 'utf-8')
        hash = SHA256.new(data_c)
        signature = pss.new(self.key_pair, salt_bytes=32).sign(hash)
        signature = base64.b64encode(signature)
        signed_data = {
            "type": "signed_data",
            "data": data,
            "counter": self.counter,
            "signature": bytes.decode(signature)
        }
        self.counter += 1
        return json.dumps(signed_data)

    async def send_hello(self):
        data = {
            "type": "hello",
            "public_key": self.public_key.decode('utf-8')
        }
        hello_msg = self.generate_signed_data(data)
        await self.websocket.send(hello_msg)

    async def send_chat(self, recipient_id, message):
        data = {
            "type": "chat",
            "destination_client": recipient_id,
            "sender": self.client_id,
            "message": message
        }
        chat_msg = self.generate_signed_data(data)
        await self.websocket.send(chat_msg)

    async def read_messages(self):
        if self.messages:
            for msg in self.messages:
                print(f"Message from {msg['sender']}: {msg['message']}")
            self.messages.clear()  # Clear messages after reading
        else:
            print("No new messages.")

    async def request_client_list(self):
        message = {"type": "client_list_request"}
        await self.websocket.send(json.dumps(message))

    async def handle_signed_data(self, message):
        try:
            message_type = message["data"]["type"]
            if message_type == "chat":
                sender = message["data"]["sender"]
                chat_message = message["data"]["message"]
                self.messages.append({"sender": sender, "message": chat_message})
            elif message_type == "public_chat":
                sender = message["data"]["sender"]
                chat_message = message["data"]["message"]
                print(f"Public message from {sender}: {chat_message}")
        except KeyError as e:
            print(f"KeyError in handle_signed_data: {e}")

    async def handle_messages(self, message):
        try:
            # Safely check if the message has a type
            if "type" in message:
                message_type = message["type"]
                if message_type == "signed_data":
                    await self.handle_signed_data(message)
                elif message_type == "client_list":
                    await self.handle_client_list(message)
                else:
                    print("Invalid message type received")
            else:
                print(f"Unexpected message format: {message}")
        except KeyError as e:
            print(f"KeyError in handle_messages: {e}")

    async def handle_client_list(self, message):
        self.clients = message["clients"]
        print("Client list updated:")
        for client in self.clients:
            print(f"Client ID: {client}")

    async def listen(self):
        async for message in self.websocket:
            try:
                data = json.loads(message)
                await self.handle_messages(data)
            except json.JSONDecodeError as e:
                print(f"JSONDecodeError: {e}")
            except Exception as e:
                print(f"Unexpected error while listening: {e}")

    async def run(self):
        self.websocket = await websockets.connect(self.uri)
        print("Starting OLAF Neighbourhood client...")
        await self.send_hello()

        asyncio.ensure_future(self.listen())

        while True:
            print("\nOptions:")
            print("1. Send a message to another client")
            print("2. Read messages from other clients")
            print("3. Request client list")
            print("4. Exit")
            option = await ainput("Select an option (1-4): ")

            if option == '1':
                recipient_id = await ainput("Enter the recipient's client ID: ")
                message = await ainput("Enter the message: ")
                await self.send_chat(recipient_id, message)
            elif option == '2':
                await self.read_messages()
            elif option == '3':
                await self.request_client_list()
            elif option == '4':
                print("Closing connection to server...")
                if self.websocket:
                    await self.websocket.close()
                break
            else:
                print("Invalid option. Please select a valid option.")


if __name__ == "__main__":
    client = Client("ws://localhost:8001")
    asyncio.run(client.run())