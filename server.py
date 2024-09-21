import asyncio
import websockets
import json
import base64
from Crypto.PublicKey import RSA
from Crypto.Signature import pss
from Crypto.Hash import SHA256
from Crypto.Cipher import AES
from Crypto.Random import get_random_bytes

# To store connected clients
connected_clients = {}

neighbourhood_servers = ["ws://localhost:8001"]

# Broadcast message to all clients
async def broadcast(message):
    for client in connected_clients.values():
        await client['websocket'].send(message)

# Handle client hello messages
async def handle_hello(websocket, message):
    public_key = message['data']['public_key']
    client_id = base64.b64encode(public_key.encode()).decode()  # Mock client ID based on the public key
    
    print(f"Received 'hello' from client: {client_id}")
    
    connected_clients[client_id] = {
        'public_key': public_key,
        'websocket': websocket
    }

    # Respond to the client
    await websocket.send(json.dumps({"status": "hello received"}))

# Handle client list request
async def handle_client_list_request(websocket):
    print("Received 'client_list_request' from client")
    
    client_list = []
    for addr, clients in connected_clients.items():
        client_info = {
            'address': addr,
            'clients': [{'client-id': client_id, 'public-key': client['public_key']} for client_id, client in clients.items()]
        }
        client_list.append(client_info)

    response = {
        "type": "client_list",
        "servers": client_list
    }

    await websocket.send(json.dumps(response))

# Handle WebSocket connection
async def handle_connection(websocket, path):
    print(f"New connection from: {websocket.remote_address}")

    try:
        async for message in websocket:
            print(f"Received message: {message}")
            data = json.loads(message)
            
            if data['data']['type'] == 'hello':
                await handle_hello(websocket, data)
            elif data['type'] == 'client_list_request':
                await handle_client_list_request(websocket)
            else:
                print(f"Unknown message type received: {data['type']}")

    except websockets.ConnectionClosed:
        print(f"Connection closed from: {websocket.remote_address}")

    finally:
        print(f"Cleaning up connection for {websocket.remote_address}")

# Main server entry point
async def main():
    print("Server starting...")
    async with websockets.serve(handle_connection, "localhost", 8001):
        print("Server running on ws://localhost:8001")
        await asyncio.Future()  # Run forever

if __name__ == "__main__":
    asyncio.run(main())
