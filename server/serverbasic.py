import asyncio
import websockets
import json

clients = {}
message_queues = {}

async def handle_client(websocket, path):
    # Get the public key (hello message)
    message = await websocket.recv()
    message_data = json.loads(message)
    
    if message_data["data"]["type"] == "hello":
        client_id = message_data["data"]["public_key"][:8]  # Simplified client ID
        clients[client_id] = websocket
        message_queues[client_id] = []

        # Send back a confirmation with the assigned client ID
        response = {"status": "hello received", "client_id": client_id}
        await websocket.send(json.dumps(response))
        print(f"Received 'hello' from client: {client_id}")

        try:
            # Keep listening for messages from the client
            while True:
                client_message = await websocket.recv()
                message_data = json.loads(client_message)

                if message_data["data"]["type"] == "message":
                    recipient_id = message_data["data"]["recipient_id"]
                    if recipient_id in clients:
                        message_queues[recipient_id].append(message_data["data"]["message"])
                        print(f"Forwarding message to recipient: {recipient_id}")
                    else:
                        print(f"Recipient {recipient_id} not found.")
                elif message_data["data"]["type"] == "read_message":
                    if message_queues[client_id]:
                        # Send the first message in the queue
                        message_to_send = message_queues[client_id].pop(0)
                        await websocket.send(json.dumps({"message": message_to_send}))
                    else:
                        await websocket.send(json.dumps({"message": "No messages to read."}))

        except websockets.ConnectionClosed:
            print(f"Client {client_id} disconnected")
        finally:
            # Clean up the client connection and message queue
            del clients[client_id]
            del message_queues[client_id]

# Function to keep the connection alive using ping/pong
async def ping_clients():
    while True:
        to_remove = []
        for client_id, websocket in clients.items():
            try:
                await websocket.ping()
            except websockets.ConnectionClosed:
                print(f"Client {client_id} has been disconnected due to timeout.")
                to_remove.append(client_id)
        
        # Clean up disconnected clients
        for client_id in to_remove:
            del clients[client_id]
            del message_queues[client_id]
        
        await asyncio.sleep(60)  # Send a ping every 60 seconds

async def main():
    async with websockets.serve(handle_client, "localhost", 8001, ping_timeout=120):
        print("Server running on ws://localhost:8001")
        await ping_clients()

asyncio.run(main())