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

        # List of servers in the neighbourhood
        self.neighbourhood_servers = [self.uri]

    # Run server
    async def run():
        pass


# Run server
if __name__ == "__main__":
    server = Server("localhost",8765)
    print("server uri: ", server.uri)