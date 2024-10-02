import asyncio
import websockets
import json
import hashlib
import base64
from Crypto.PublicKey import RSA

clients = {}  # A dictionary to store connected clients and their WebSocket connections

# Helper function to generate the client fingerprint from the public key
def generate_fingerprint(public_key):
    sha256_hash = hashlib.sha256(public_key.encode('utf-8')).digest()
    return base64.b64encode(sha256_hash).decode('utf-8')

# Notify all clients about the current client list
async def notify_clients():
    client_list = list(clients.keys())
    message = {"type": "client_list", "clients": client_list}
    await asyncio.gather(*[asyncio.create_task(client.send(json.dumps(message))) for client in clients.values()])

# Handle incoming messages from clients
async def handle_client(websocket, path):
    client_id = None
    try:
        # Receive and handle the "hello" message containing the public key
        hello_message = await websocket.recv()
        data = json.loads(hello_message)
        
        if data["data"]["type"] == "hello":
            public_key = data["data"]["public_key"]
            client_id = generate_fingerprint(public_key)
            print(f"Received 'hello' from client: {client_id}")

            # Store the client in the dictionary
            clients[client_id] = websocket

            # Acknowledge the hello message
            await websocket.send(json.dumps({"status": "hello received", "client_id": client_id}))

            # Notify all clients about the updated client list
            await notify_clients()

        # Listen for further messages from the client
        async for message in websocket:
            data = json.loads(message)
            
            # Handle signed_data messages
            if data["type"] == "signed_data":
                message_type = data["data"]["type"]

                # Handle public chat messages
                if message_type == "public_chat":
                    sender = data["data"]["sender"]
                    chat_message = data["data"]["message"]
                    print(f"Public message from {sender}: {chat_message}")
                    
                    # Forward public chat to all clients
                    forward_message = {
                        "type": "signed_data",
                        "data": {
                            "type": "public_chat",
                            "sender": sender,
                            "message": chat_message
                        }
                    }
                    await asyncio.gather(*[asyncio.create_task(client.send(json.dumps(forward_message))) for client in clients.values()])

                # Handle private chat messages
                elif message_type == "chat":
                    recipient_id = data["data"]["destination_client"]
                    chat_message = data["data"]["message"]
                    sender = data["data"]["sender"]
                    print(f"Private message from {sender} to {recipient_id}: {chat_message}")

                    # Forward private chat to the recipient client
                    if recipient_id in clients:
                        forward_message = {
                            "type": "signed_data",
                            "data": {
                                "type": "chat",
                                "sender": sender,
                                "message": chat_message
                            }
                        }
                        await clients[recipient_id].send(json.dumps(forward_message))
                    else:
                        print(f"Client {recipient_id} is not connected.")
            
    except websockets.exceptions.ConnectionClosed:
        print(f"Client {client_id} disconnected")
        if client_id in clients:
            del clients[client_id]  # Remove the client from the dictionary
        await notify_clients()  # Notify other clients about the updated client list

# Start the server
async def start_server():
    async with websockets.serve(handle_client, "localhost", 8001):
        print("Server running on ws://localhost:8001")
        await asyncio.Future()  # Run the server forever

if __name__ == "__main__":
    asyncio.run(start_server())