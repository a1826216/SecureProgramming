import asyncio
import websockets
import json
import hashlib
import base64
from Crypto.PublicKey import RSA
from Crypto.Hash import SHA256
from Crypto.Signature import pss

clients = {}  # Maps client_id to websocket
usernames = {}  # Maps client_id to username

# Helper function to broadcast messages to all connected clients
async def notify_clients():
    if clients:  # Only send to clients if there are any connected
        message = {"type": "client_list", "clients": list(usernames.values())}
        await asyncio.gather(
            *[client.send(json.dumps(message)) for client in clients.values()]
        )

# Handle messages from each client
async def handle_client(websocket, path):
    client_id = None
    try:
        async for message in websocket:
            data = json.loads(message)

            # Determine the message type
            message_type = data.get("type")
            if message_type == "signed_data":
                # Handle messages that contain signed data
                inner_data = data.get("data", {})
                inner_type = inner_data.get("type")

                if inner_type == "hello":
                    client_id = inner_data["client_id"]
                    username = inner_data["username"]

                    clients[client_id] = websocket
                    usernames[client_id] = username
                    print(f"Received 'hello' from client: {client_id} (username: {username})")

                    # Notify all clients about updated client list
                    await notify_clients()

                elif inner_type == "public_chat":
                    sender_id = inner_data["sender"]
                    chat_message = inner_data["message"]

                    print(f"Public message from {sender_id}: {chat_message}")

                    # Relay the public chat message to all clients except the sender
                    for cid, ws in clients.items():
                        if cid != sender_id:
                            message_to_send = {
                                "type": "public_chat",
                                "data": {
                                    "sender": usernames[sender_id],
                                    "message": chat_message
                                }
                            }
                            await ws.send(json.dumps(message_to_send))

                elif inner_type == "chat":
                    sender_id = inner_data["sender"]
                    recipient_username = inner_data["recipient_username"]
                    chat_message = inner_data["message"]

                    print(f"Private message from {sender_id} to {recipient_username}: {chat_message}")

                    # Find the recipient's client ID from the username
                    recipient_id = None
                    for cid, uname in usernames.items():
                        if uname == recipient_username:
                            recipient_id = cid
                            break

                    if recipient_id and recipient_id in clients:
                        message_to_send = {
                            "type": "chat",
                            "data": {
                                "sender": usernames[sender_id],
                                "message": chat_message
                            }
                        }
                        await clients[recipient_id].send(json.dumps(message_to_send))
                        print(f"Message forwarded to recipient: {recipient_username} (ID: {recipient_id})")
                    else:
                        print(f"Recipient {recipient_username} not found or not connected.")

            elif message_type == "client_list_request":
                # Handle client list request
                message_to_send = {
                    "type": "client_list",
                    "clients": list(usernames.values())
                }
                await websocket.send(json.dumps(message_to_send))
                print("Client list sent to requester")

            else:
                print(f"Invalid or unrecognized message received: {data}")

    except websockets.exceptions.ConnectionClosed:
        print(f"Client {client_id} disconnected")
    finally:
        if client_id:
            clients.pop(client_id, None)
            usernames.pop(client_id, None)
            await notify_clients()

# Start the server
start_server = websockets.serve(handle_client, "localhost", 8001)

print("Server running on ws://localhost:8001")
asyncio.get_event_loop().run_until_complete(start_server)
asyncio.get_event_loop().run_forever()