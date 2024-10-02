import asyncio
import websockets
import json

clients = {}  # Maps client_id to websocket
usernames = {}  # Maps client_id to username


async def notify_clients():
    if clients:  # Only send to clients if there are any connected
        message = {"type": "client_list", "clients": list(usernames.values())}
        await asyncio.gather(
            *[asyncio.create_task(client.send(json.dumps(message))) for client in clients.values()]
        )


async def handle_client(websocket, path):
    client_id = None
    try:
        async for message in websocket:
            data = json.loads(message)

            # If it's a hello message, store the client_id and username
            if data["data"]["type"] == "hello":
                client_id = data["data"]["client_id"]
                username = data["data"]["username"]

                clients[client_id] = websocket
                usernames[client_id] = username
                print(f"Received 'hello' from client: {client_id} (username: {username})")

                # Notify all clients about updated client list
                await notify_clients()

            # If it's a chat message, send the message to the intended recipient
            elif data["data"]["type"] == "chat":
                sender_id = data["data"]["sender"]
                recipient_username = data["data"]["recipient_username"]
                chat_message = data["data"]["message"]

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
                            "sender": usernames[sender_id],  # Send the username instead of client ID
                            "message": chat_message
                        }
                    }
                    await clients[recipient_id].send(json.dumps(message_to_send))
                    print(f"Message forwarded to recipient: {recipient_username} (ID: {recipient_id})")

    except websockets.exceptions.ConnectionClosed:
        print(f"Client {client_id} disconnected")
    finally:
        if client_id:
            clients.pop(client_id, None)
            usernames.pop(client_id, None)
            await notify_clients()


start_server = websockets.serve(handle_client, "localhost", 8001)

print("Server running on ws://localhost:8001")
asyncio.get_event_loop().run_until_complete(start_server)
asyncio.get_event_loop().run_forever()