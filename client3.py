import asyncio
import websockets
import json
import base64
from Crypto.PublicKey import RSA
from collections import deque

# Queue to store incoming messages
message_queue = deque()

# Function to handle receiving messages in a loop
async def receive_messages(websocket):
    try:
        while True:
            response = await websocket.recv()
            response_data = json.loads(response)
            message_type = response_data.get("type", "")
            
            if message_type == "message":
                message_queue.append(response_data)  # Add received messages to the queue
                print("\nNew message received!")
            else:
                print("\nReceived: ", response)
    except websockets.ConnectionClosedOK:
        print("Connection closed gracefully")
    except websockets.ConnectionClosedError as e:
        print(f"Connection closed with error: {e}")

# Function to display the message and prompt the user
def display_message():
    if message_queue:
        message = message_queue.popleft()  # Get the oldest message in the queue
        print(f"\nMessage from {message['from']}: {message['message']}")
    else:
        print("No messages to read.")

# Send a "hello" message to the server and continuously listen for incoming messages
async def hello():
    uri = "ws://localhost:8001"
    try:
        async with websockets.connect(uri) as websocket:
            # Generate RSA keypair
            key = RSA.generate(2048)
            public_key = key.publickey().export_key()

            # Send a "hello" message to the server
            hello_message = {
                "data": {
                    "type": "hello",
                    "public_key": base64.b64encode(public_key).decode('utf-8')
                }
            }
            await websocket.send(json.dumps(hello_message))
            print(f"Sent 'hello' message: {json.dumps(hello_message)}")

            # Wait for a response from the server
            response = await websocket.recv()
            print(f"Received: {response}")
            response_data = json.loads(response)
            client_id = response_data['client_id']

            # Start receiving messages in the background
            asyncio.create_task(receive_messages(websocket))

            # Now allow the user to send messages or read received messages
            while True:
                print("\nOptions:")
                print("1. Read a message")
                print("2. Send a message to another client")
                choice = input("Select an option (1 or 2): ").strip()

                if choice == "1":
                    display_message()
                elif choice == "2":
                    recipient_id = input("Enter the recipient's client ID: ")  # Recipient's client ID
                    message_to_send = input("Enter the message to send: ")

                    # Send a message to another client
                    message = {
                        "data": {
                            "type": "message",
                            "recipient_id": recipient_id,
                            "message": message_to_send
                        }
                    }
                    await websocket.send(json.dumps(message))
                    print(f"Sent message to {recipient_id}: {message_to_send}")
                else:
                    print("Invalid choice. Please enter 1 or 2.")

    except Exception as e:
        print(f"An error occurred: {e}")

# Run the client
if __name__ == "__main__":
    asyncio.run(hello())