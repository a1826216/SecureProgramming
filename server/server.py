import asyncio
import json
import base64
import ssl

import websockets

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
    def check_msg_is_valid(self, message:dict):
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
    
    # Handle new client hello message
    async def handle_hello(self, websocket, message):
        # Handle situation where client already exists

        
        
        # Username code (commented out for now)
        # username = message['data']['username']
        # if username in connected_clients:
        #     print(f"username taken")
        #     await websocket.send(json.dumps({"status": "error", "message": "Username already taken"}))
        #     return
        
        # Get public key from message
        public_key = message["data"]["public_key"]
        client_id = base64.b64encode(public_key.encode()).decode()  # Generate a unique client ID based on the public key

        # Get counter value from message
        counter = message["counter"]

        # Add the client to the connected_clients dictionary
        self.clients[client_id] = {
            # 'username': username,
            'public_key': public_key,  # Store the client's public key
            'websocket': websocket,    # Store the WebSocket object for communication
            'counter': counter         # Store most recent counter value (used to prevent replay attacks)
        }

        # Append public key to client list
        self.client_list["clients"].append(public_key)
        print(self.client_list)

        # Respond to the client to confirm receipt of the 'hello'
        await websocket.send(json.dumps({"status": "hello received"}))

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
    
    # Echo message back to client (for testing)
    async def echo(self, websocket):
        async for message in websocket:
            print(message)
            # print(json.loads(message).keys())
            print(self.check_msg_is_valid(json.loads(message)))
            await websocket.send(message)


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
                    # Check validity of signed message
                    if self.check_msg_is_valid(data) == False:
                        await websocket.send(json.dumps({"status": "error", "message": "Invalid message"}))
                    else:
                        # Check type of signed message and handle accordingly
                        data_type = data["data"]["type"]
                        if data_type == "hello":
                            await self.handle_hello(websocket, data)
                        elif data_type == "public_chat":
                            print("Data type is public chat!")
                        elif data_type == "chat":
                            print("Data type is chat!")

                # Handle client list request
                elif message_type == "client_list_request":
                    await self.handle_client_list_request(websocket)

                # Handle error
                else:
                    print(f"Unknown message type received: {data}")

        except websockets.ConnectionClosed:
            print(f"Connection closed from: {websocket.remote_address}")

        finally:
            # Remove client from list here?
            print(f"Cleaning up connection for {websocket.remote_address}")

    # Run server
    async def run(self):
        async with websockets.serve(self.handle_connection, self.host, self.port):
            print("Server running on", self.uri)
            await asyncio.get_running_loop().create_future()


if __name__ == "__main__":
    # Run server with specified hostname and port
    server = Server("localhost",8765)
    asyncio.run(server.run())


    