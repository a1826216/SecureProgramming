import asyncio
import json
import ssl

from websockets.asyncio.server import serve

# Server class
class Server:
    def __init__(self, host, port):
        # IP and port number
        self.host = host
        self.port = port
        self.uri = f'ws://{self.host}:{self.port}'

        # Store connected clients
        self.clients = {}

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
                return False
            
        # Check validity of data type (content is not checked at the moment)
        data_type = message["data"]["type"]
        if data_type not in valid_data_types:
            return False
            
        return True
    
    # Echo message back to client (for testing)
    async def echo(self, websocket):
        async for message in websocket:
            print(message)
            # print(json.loads(message).keys())
            print(self.check_msg_is_valid(json.loads(message)))
            await websocket.send(message)

    # Run server
    async def run(self):
        async with serve(self.echo, self.host, self.port):
            print("echo server started on: ", self.uri)
            await asyncio.get_running_loop().create_future()


if __name__ == "__main__":
    # Run server with specified hostname and port
    server = Server("localhost",8765)
    asyncio.run(server.run())


    