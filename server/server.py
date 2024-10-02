import asyncio
import websockets
import json
import base64
from Crypto.PublicKey import RSA

class SecureServer:
    def __init__(self):
        self.clients = {}  # Store client public keys and websocket connections
        self.port = 8001

    async def handler(self, websocket, path):
        """Handle incoming messages from clients."""
        print(f"Client connected: {websocket.remote_address}")
        try:
            async for message in websocket:
                print(f"Received message from client: {message}")
                data = json.loads(message)
                if 'data' in data and 'type' in data['data']:
                    if data['data']['type'] == 'hello':
                        await self.process_hello(websocket, data)
                    elif data['data']['type'] == 'chat':
                        await self.process_chat(websocket, data)
        except websockets.exceptions.ConnectionClosed as e:
            print(f"Client disconnected: {websocket.remote_address} - {e}")
            if websocket in self.clients:
                del self.clients[websocket]

    async def process_hello(self, websocket, data):
        """Process hello message and store client's public key."""
        print(f"Processing 'hello' from client: {websocket.remote_address}")
        public_key = base64.b64decode(data['data']['public_key'])
        rsa_public_key = RSA.import_key(public_key)
        self.clients[websocket] = rsa_public_key
        print(f"Registered client with public key: {public_key}")

    async def process_chat(self, websocket, data):
        """Process chat message and relay it to other clients."""
        print(f"Processing 'chat' message: {data}")
        # Broadcast the message to all connected clients except the sender
        for client in self.clients:
            if client != websocket:  # Don't send the message back to the sender
                try:
                    await client.send(json.dumps(data))
                    print(f"Relayed message to client: {client.remote_address}")
                except Exception as e:
                    print(f"Error relaying message: {e}")

    async def start_server(self):
        """Start the WebSocket server."""
        print(f"Starting server on port {self.port}")
        server = await websockets.serve(self.handler, "localhost", self.port)
        await server.wait_closed()

# Run the server
secure_server = SecureServer()
asyncio.run(secure_server.start_server())