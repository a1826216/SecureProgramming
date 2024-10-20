import asyncio
import websockets
import json
import base64
import hashlib
import sys

import cryptography.exceptions

from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.asymmetric import padding

# Server class
class Server:
    def __init__(self, host, port):
        # IP and port number
        self.host = host
        self.port = port
        self.uri = f'ws://{self.host}:{self.port}'

        # Store connected clients (to this server)
        self.clients = {}

        # Client list (For client list request)
        self.client_list = {"address": self.uri, "clients": []}

        # List of servers in the neighbourhood (hard coded for now, can probably be passed in as a text file)
        self.neighbourhood_servers = [self.uri]

        # List of clients in the neighbourhood (outside this server)
        self.neighbourhood_clients = {}

    # Check if a message is a valid OLAF Neighbourhood protocol message
    def check_json_headers(self, message: dict):
        # List of valid keys for messages sent by client
        valid_keys = ["type", "data", "counter", "signature"]

        # List of valid data types for messages sent by client
        valid_data_types = ["hello", "chat", "public_chat"]

        # Check if message has the required keys (and nothing else)
        for key in message.keys():
            if key not in valid_keys:
                print(f"Message has invalid key: {key}")
                return False

        # Check validity of data type (content is not checked at the moment)
        data_type = message["data"]["type"]
        if data_type not in valid_data_types:
            print(f"Message has invalid data type: {data_type}")
            return False

        return True

    # Function to validate signed data signatures
    def validate_signature(self, message, public_key:bytes):
        data = json.dumps(message["data"])
        counter = str(message["counter"])
        signature = message["signature"]

        public_key = serialization.load_pem_public_key(public_key)
        data_c = bytes(data + counter, 'utf-8')

        signature = base64.b64decode(signature)

        try:
            public_key.verify(
                signature,
                data_c,
                padding.PSS(
                    mgf=padding.MGF1(hashes.SHA256()),
                    salt_length=padding.PSS.MAX_LENGTH
                ), 
                hashes.SHA256()
                )
            print("Signature is authentic.")
            return True

        except cryptography.exceptions.InvalidSignature:
            print("Signature is not authentic.")
            return False


    # Helper function to return a client ID
    def get_client_id(self, public_key:bytes):
        return hashlib.sha256(base64.b64encode(public_key)).hexdigest()

    # Check if a user has an active websocket connection
    def check_connection(self, websocket):
        for client in self.clients:
            if self.clients[client]["websocket"] == websocket:
                return self.clients[client]
        return None

    # Handler for all types of signed data messages
    async def handle_signed_data(self, websocket, message):
        # Check message has the valid headers first
        if not self.check_json_headers(message):
            await websocket.send(json.dumps({"status": "error", "message": "Invalid signed data message"}))
            return

        data_type = message["data"]["type"]
        current_client = self.check_connection(websocket)

        if current_client is None:
            if data_type == "hello":
                await self.handle_hello(websocket, message)
            else:
                await websocket.send(json.dumps({"status": "error", "message": "Hello message not sent yet"}))
        else:
            public_key = current_client["public_key"]
            counter = current_client["counter"]

            if not self.validate_signature(message, public_key):
                await websocket.send(json.dumps({"status": "error", "message": "Message has invalid signature"}))
            else:
                if message["counter"] <= counter:
                    await websocket.send(json.dumps({"status": "error", "message": "Counter value is too low"}))
                else:
                    # Update the counter
                    self.clients[current_client["fingerprint"]]["counter"] = message["counter"]

                    # Handle valid message types
                    if data_type == "public_chat":
                        await self.handle_public_chat(websocket, message)
                    elif data_type == "chat":
                        await self.handle_chat(websocket, message)
                    else:
                        await websocket.send(json.dumps({"status": "error", "message": "Invalid message type for connected client"}))

    # Handle new client hello message
    async def handle_hello(self, websocket, message):
        public_key = message["data"]["public_key"]

        # Convert public key to bytes format
        public_key = bytes(public_key, 'utf-8')

        # Validate signature using new public key
        if not self.validate_signature(message, public_key):
            await websocket.send(json.dumps({"status": "error", "message": "Invalid signature for hello message"}))
            return

        # Generate unique client ID (SHA256 of base64 encoded RSA public key)
        client_id = self.get_client_id(public_key)

        # Check if client ID is a duplicate
        if client_id in self.clients:
            await websocket.send(json.dumps({"status": "error", "message": "Client ID already exists"}))
            return

        # Get counter value from message
        counter = message["counter"]

        # Add the client to the connected clients dictionary
        self.clients[client_id] = {
            'fingerprint': client_id,  # Client ID is also the fingerprint (stored for easier access)
            'public_key': public_key,  # Store the client's public key
            'websocket': websocket,    # Store the WebSocket object for communication
            'counter': counter         # Store most recent counter value (used to prevent replay attacks)
        }

        # Append string version of public key to client list
        self.client_list["clients"].append(public_key.decode('utf-8'))

        # Respond to the client to confirm receipt of the 'hello'
        await websocket.send(json.dumps({"status": "success", "message": "Hello successfully received", "client_id": str(client_id)}))

    # Handle public chat (broadcast to clients in all neighbourhoods)
    async def handle_public_chat(self, websocket, message):
        sender_fingerprint = message["data"]["sender"]

        # Relay to all clients connected to the server
        for client in self.clients:
            if client != sender_fingerprint:
                await self.clients[client]["websocket"].send(json.dumps(message))

    # Handle private chat (route to individual recipients)
    async def handle_chat(self, websocket, message):
        recipient_id = message["data"]["recipient"]

        # Check if the recipient is connected to the current server
        if recipient_id not in self.clients:
            await websocket.send(json.dumps({"status": "error", "message": "Recipient not found"}))
            return

        # Retrieve recipient websocket and forward the message
        recipient_ws = self.clients[recipient_id]["websocket"]
        await recipient_ws.send(json.dumps(message))
        print(f"Forwarded encrypted message from {message['data']['sender']} to {recipient_id}.")

    # Handle client list request
    async def handle_client_list_request(self, websocket):
        client_list_req = {
            "type": "client_list",
            "servers": [self.client_list]
        }
        await websocket.send(json.dumps(client_list_req))

    # Handle when a client disconnects
    async def handle_disconnection(self, websocket):
        public_key = ""

        # Remove from local client list
        for client in self.clients:
            if self.clients[client]["websocket"] == websocket:
                public_key = self.clients[client]["public_key"]
                del self.clients[client]
                break

        if public_key in self.client_list["clients"]:
            self.client_list["clients"].remove(public_key)

    # Handle WebSocket connection
    async def handle_connection(self, websocket, path):
        print(f"New connection from: {websocket.remote_address}")

        try:
            async for message in websocket:
                print(f"Received message: {message}")
                data = json.loads(message)
                message_type = data.get("type", "")

                if message_type == "signed_data":
                    await self.handle_signed_data(websocket, data)
                elif message_type == "client_list_request":
                    await self.handle_client_list_request(websocket)
                else:
                    print(f"Unknown message type received: {data}")

        except websockets.ConnectionClosed:
            print(f"Connection closed from: {websocket.remote_address}")
            if self.check_connection(websocket):
                await self.handle_disconnection(websocket)

        finally:
            print(f"Cleaning up connection for {websocket.remote_address}")
            if self.check_connection(websocket):
                await self.handle_disconnection(websocket)

    # Run server
    async def run(self):
        async with websockets.serve(self.handle_connection, self.host, self.port, ping_interval=20, ping_timeout=100):
            print("Server running on", self.uri)
            await asyncio.get_running_loop().create_future()


if __name__ == "__main__":
    # Default port (if no port is specified)
    port = 8765

    # Get port from command line
    if len(sys.argv) > 1:
        port = sys.argv[1]

    server = Server("localhost", port)
    asyncio.run(server.run())