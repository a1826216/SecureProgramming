import asyncio
import json
import ssl

from websockets.asyncio.server import serve

# Server class
class Server:
    def __init__(self):
        self.host = "localhost"
        self.port = 8765
        self.uri = "ws://localhost:8765"

    # Run server
    async def main():
        pass


# Run server
if __name__ == "__main__":
    server = Server()
    print("main function!")