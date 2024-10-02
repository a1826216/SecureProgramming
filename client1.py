import asyncio
import websockets
import json
from aioconsole import ainput

class Client:
    def __init__(self, uri):
        self.uri = uri
        self.counter = 0
        self.websocket = None
        self.client_id = None
        self.username = None
        self.messages = []
        self.clients = []  # List of usernames

    async def send_hello(self):
        data = {
            "type": "hello",
            "client_id": self.client_id,
            "username": self.username
        }
        await self.websocket.send(json.dumps({"data": data}))

    async def send_chat(self, recipient_username, message):
        data = {
            "type": "chat",
            "sender": self.client_id,
            "recipient_username": recipient_username,
            "message": message
        }
        await self.websocket.send(json.dumps({"data": data}))

    async def request_client_list(self):
        await self.websocket.send(json.dumps({"type": "client_list_request"}))

    async def handle_chat(self, message):
        sender = message["data"]["sender"]
        chat_message = message["data"]["message"]
        self.messages.append({"sender": sender, "message": chat_message})

    async def handle_client_list(self, message):
        self.clients = message["clients"]
        print("Client list updated:")
        for client in self.clients:
            print(f"Username: {client}")

    async def handle_messages(self, message):
        message_type = message.get("type")
        if message_type == "chat":
            await self.handle_chat(message)
        elif message_type == "client_list":
            await self.handle_client_list(message)
        else:
            print(f"Invalid message type received: {message}")

    async def listen(self):
        async for message in self.websocket:
            data = json.loads(message)
            await self.handle_messages(data)

    async def read_messages(self):
        if self.messages:
            for msg in self.messages:
                print(f"Message from {msg['sender']}: {msg['message']}")
            self.messages.clear()
        else:
            print("No new messages.")

    async def run(self):
        self.websocket = await websockets.connect(self.uri)
        print("Starting OLAF Neighbourhood client...")

        self.username = await ainput("Enter a username: ")
        self.client_id = f"{self.username}_client_id"  # Use username to generate a dummy client ID for simplicity
        await self.send_hello()

        asyncio.ensure_future(self.listen())

        while True:
            print("\nOptions:")
            print("1. Send a message to another client")
            print("2. Read messages from other clients")
            print("3. Exit")
            option = await ainput("Select an option (1-3): ")

            if option == '1':
                recipient_username = await ainput("Enter the recipient's username: ")
                message = await ainput("Enter the message: ")
                await self.send_chat(recipient_username, message)
            elif option == '2':
                await self.read_messages()
            elif option == '3':
                print("Closing connection to server...")
                if self.websocket:
                    await self.websocket.close()
                break
            else:
                print("Invalid option. Please select a valid option.")


if __name__ == "__main__":
    client = Client("ws://localhost:8001")
    asyncio.run(client.run())