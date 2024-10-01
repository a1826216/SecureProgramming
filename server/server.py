import asyncio
import websockets
import json
import base64
import hashlib
import secrets

from Crypto.Signature import pss
from Crypto.PublicKey import RSA
from Crypto.Hash import SHA256

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
    def check_json_headers(self, message:dict):
        # List of valid keys for messages sent by client
        valid_keys = ["type","data","counter","signature"]

        # List of valid data types for messages sent by client
        valid_data_types = ["hello", "chat", "public_chat"]

        # Check if message has the required keys (and nothing else)
        for key in message.keys():
            if key not in valid_keys:
                print("Message has invalid key \"", key, "\"")
                return False
            
        # Check validity of data type (content is not checked at the moment)
        data_type = message["data"]["type"]
        if data_type not in valid_data_types:
            print("Message has invalid data type \"", data_type, "\"")
            return False
            
        return True
    
    # Function to validate signed data signatures
    def validate_signature(self, message, public_key):
        data = json.dumps(message["data"])
        counter = str(message["counter"])
        signature = message["signature"]

        public_key = RSA.import_key(public_key)
        
        data_c = bytes(data + counter, 'utf-8')

        hash = SHA256.new(data_c)

        signature = base64.b64decode(signature)

        verifier = pss.new(public_key)

        try:
            verifier.verify(hash, signature)
            print("Signature is authentic")
            return True
        except ValueError:
            print("Signature is not authentic.")
            return False
        
    
    # Helper function to return a client ID
    def get_client_id(self, public_key):
        return SHA256.new(base64.b64encode(bytes(public_key, 'utf-8'))).hexdigest()
    
    # Check if a user has an active websocket connection
    def check_connection(self, websocket):
        # Check if websocket belongs to server
        for client in self.clients:
            if self.clients[client]["websocket"] == websocket:
                # print (f"Client {client} is connected!")
                return self.clients[client]
            
        # Check neighbourhood websockets (when server-server is added)
            
        # print("Client is not connected!")
        return None
    
    # Send hello message to other servers
    async def send_server_hello(self, websocket):
        server_ip = f"{self.host}:{self.port}"
    
    # Handler for all types of signed data messages
    async def handle_signed_data(self, websocket, message):
        # Check message has the valid headers first
        if self.check_json_headers(message) == False:
            await websocket.send(json.dumps({"status": "error", "message": "Invalid signed data message"}))
            return
        
        data_type = message["data"]["type"]

        # Get current client (this will allow counter and signature validation)
        current_client = self.check_connection(websocket)

        # Check active websocket status
        if current_client == None:
            if data_type == "hello":
                await self.handle_hello(websocket, message)
            else:
                await websocket.send(json.dumps({"status": "error", "message": "Hello message not sent yet"}))
        else:
            # Get public key from client
            public_key = current_client["public_key"]

            # Get counter from client
            counter = current_client["counter"]
            
            # Validate signature before proceeding
            if self.validate_signature(message, public_key) == False:
                await websocket.send(json.dumps({"status": "error", "message": "Message has invalid signature"}))
            else:
                # Validate counter
                if message["counter"] <= counter:
                    await websocket.send(json.dumps({"status": "error", "message": "Counter value is too low"}))
                else:
                    match data_type:
                        case "public_chat":
                            await self.handle_public_chat(websocket, message)
                        case "chat":
                            print("Data type is chat!")
                        case _:
                            await websocket.send(json.dumps({"status": "error", "message": "Invalid message type for connected client"}))

    
    # Handle new client hello message
    async def handle_hello(self, websocket, message):
        # Get public key from message
        public_key = message["data"]["public_key"]

        # Validate signature using new public key
        self.validate_signature(message, public_key)
        
        # Generate unique client ID (SHA256 of base64 encoded RSA public key)
        client_id = self.get_client_id(public_key)

        # Check if client ID is a duplicate
        if client_id in self.clients:
            await websocket.send(json.dumps({"status": "error", "message": "Client ID already exists"}))
            return

        # Get counter value from message
        counter = message["counter"]

        # Add the client to the connected_clients dictionary
        self.clients[client_id] = {
            'fingerprint': client_id,  # Client ID is also the fingerprint (stored for easier access)
            'public_key': public_key,  # Store the client's public key
            'websocket': websocket,    # Store the WebSocket object for communication
            'counter': counter         # Store most recent counter value (used to prevent replay attacks)
        }

        # Append raw public key to client list
        self.client_list["clients"].append(public_key)

        # Respond to the client to confirm receipt of the 'hello'
        await websocket.send(json.dumps({"status": "success", "message": "Hello successfully received", "client_id": str(client_id)}))

    # Handle public chat (broadcast to clients in all neighbourhoods)
    async def handle_public_chat(self, websocket, message):
        # Get fingerprint of sender
        sender_fingerprint = message["data"]["sender"]

        # Relay to all clients connected to server
        for client in self.clients:
            if client != sender_fingerprint:
                await self.clients[client]["websocket"].send(json.dumps(message))

        # Relay to all neighbourhood clients

    # Handle private chat (route to individual recipients)
    async def handle_chat(self, websocket, message):
        pass

    # Handle client list request
    async def handle_client_list_request(self, websocket):
        # Basic request body
        client_list_req = {
            "type": "client_list",
            "servers": []
        }

        # Append our server client list to the request
        client_list_req["servers"].append(self.client_list)

        # Get lists from other servers (needs server-server communication first)

        # Send request back to client
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

                # Get type of message
                message_type = data["type"]

                # Handle signed data message
                if message_type == "signed_data":
                    await self.handle_signed_data(websocket, data)

                # Handle client list request
                elif message_type == "client_list_request":
                    await self.handle_client_list_request(websocket)

                # Handle server hello
                elif message_type == "server_hello":
                    print("message is server_hello")

                # Handle server client update request
                elif message_type == "client_update_request":
                    print("message is client update request")

                # Handle server client update
                elif message_type == "client_update":
                    print("message is client update")

                # Handle error
                else:
                    print(f"Unknown message type received: {data}")

        except websockets.ConnectionClosed:
            print(f"Connection closed from: {websocket.remote_address}")
            # Remove client from list upon disconnection
            if self.check_connection(websocket):
                await self.handle_disconnection(websocket)

        finally:
            print(f"Cleaning up connection for {websocket.remote_address}")
            # Remove client from list upon disconnection
            if self.check_connection(websocket):
                await self.handle_disconnection(websocket)

    # Run server
    async def run(self):
        async with websockets.serve(self.handle_connection, self.host, self.port, ping_interval=20, ping_timeout=100):
            print("Server running on", self.uri)
            await asyncio.get_running_loop().create_future()


if __name__ == "__main__":
    # Run server with specified hostname and port
    server = Server("localhost",8765)
    asyncio.run(server.run())


    