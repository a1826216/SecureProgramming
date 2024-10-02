import asyncio
import websockets
import json
import random
import string

# Function to generate a random unique client ID (or public key)
def generate_unique_id(length=8):
    return ''.join(random.choices(string.ascii_letters + string.digits, k=length))

async def main():
    # Generate or ask the user for a unique public key (client ID)
    unique_id = generate_unique_id()

    async with websockets.connect("ws://localhost:8001", ping_interval=60, ping_timeout=120) as websocket:
        # Send the hello message with the unique public key
        hello_message = {
            "data": {
                "type": "hello",
                "public_key": unique_id  # Unique identifier for each client
            }
        }
        await websocket.send(json.dumps(hello_message))
        response = await websocket.recv()
        print(f"Received: {response}")

        while True:
            print("\nOptions:\n1. Read a message\n2. Send a message to another client")
            option = input("Select an option (1 or 2): ")

            if option == "1":
                # Send request to read a message
                read_message_request = {"data": {"type": "read_message"}}
                await websocket.send(json.dumps(read_message_request))
                response = await websocket.recv()
                print(f"Received message: {response}")

            elif option == "2":
                # Send a message to another client
                recipient_id = input("Enter the recipient's client ID: ")
                message = input("Enter the message to send: ")
                message_data = {
                    "data": {
                        "type": "message",
                        "recipient_id": recipient_id,
                        "message": message
                    }
                }
                await websocket.send(json.dumps(message_data))
                print(f"Sent message to {recipient_id}: {message}")

asyncio.run(main())