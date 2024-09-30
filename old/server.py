import asyncio
import websockets
import json
import base64
from Crypto.PublicKey import RSA

# To store connected clients
connected_clients = {}

neighbourhood_servers = ["ws://localhost:8001"]

# Broadcast message to all clients
async def broadcast(message):
    for client in connected_clients.values():
        await client['websocket'].send(message)

# Handle client hello messages
async def handle_hello(websocket, message):
    username = message['data']['username']
    if username in connected_clients:
        print(f"username taken")
        await websocket.send(json.dumps({"status": "error", "message": "Username already taken"}))
        return
    public_key = message['data']['public_key']  # Extract the public key from the message
    client_id = base64.b64encode(public_key.encode()).decode()  # Generate a unique client ID based on the public key

    print(f"Received 'hello' from client: {username}")

    # Add the client to the connected_clients dictionary
    connected_clients[client_id] = {
        'username': username,
        'public_key': public_key,  # Store the client's public key
        'websocket': websocket      # Store the WebSocket object for communication
    }

    # Respond to the client to confirm receipt of the 'hello'
    await websocket.send(json.dumps({"status": "hello received"}))

# Handle client list request
async def handle_client_list_request(websocket):
    print("Received 'client_list_request' from client")
    
    client_list = []
    for client_id, client in connected_clients.items():
        client_info = {
            'username': client['username'],

        }
        client_list.append(client_info)

    response = {
        "clients": client_list
    }

    await websocket.send(json.dumps(response))

# Handle WebSocket connection
async def handle_connection(websocket, path):
    print(f"New connection from: {websocket.remote_address}")

    try:
        async for message in websocket:
            print(f"Received message: {message}")
            data = json.loads(message)

            # Check if "type" is directly in the message (e.g., for "client_list_request")
            if "type" in data and data['type'] == 'client_list_request':
                await handle_client_list_request(websocket)
            elif "data" in data and data['data']['type'] == 'hello':
                await handle_hello(websocket, data)
            else:
                print(f"Unknown message type received: {data}")

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