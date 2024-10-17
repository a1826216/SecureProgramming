import asyncio
import websockets
import json
import base64
import hashlib
import secrets
from aioconsole import ainput

from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.hazmat.primitives import serialization

class Client:
    def __init__(self, uri):
        # Address of server to connect to
        self.uri = uri

        # Counter value (to be sent with signed data)
        self.counter = 0

        # Websocket connection object
        self.websocket = None

        # 2048-bit RSA key pair
        self.private_key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
        
        self.private_key_pem = self.private_key.private_bytes(
            encoding=serialization.Encoding.PEM, 
            format=serialization.PrivateFormat.PKCS8,
            encryption_algorithm=serialization.NoEncryption()
            )

        self.public_key_pem = self.private_keyprivate_key.public_key().public_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PublicFormat.SubjectPublicKeyInfo
            )
        
        print(self.public_key_pem)

        # Client's own client ID (SHA256 of base64 encoded public key)
        self.client_id = hashlib.sha256(base64.b64encode(self.public_key.encode('utf-8'))).hexdigest()

        # List of clients on home server (excluding this one)
        self.clients = {}

    # Function to generate signed data messages
    def generate_signed_data(self, data):
        # Concatenate data and counter (this will form the signature)
        data_c = bytes(json.dumps(data) + str(self.counter), 'utf-8')

        # Get SHA256 sum of data and counter
        hash_value = SHA256.new(data_c)

        # Sign the hash using the RSA private key
        signature = pss.new(self.key_pair).sign(hash_value)

        # Base64 encode the signature
        signature_b64 = base64.b64encode(signature).decode('utf-8')

        # Create the signed data structure
        signed_data = {
            "type": "signed_data",
            "data": data,
            "counter": self.counter,
            "signature": signature_b64
        }

        # Increment counter value (for future signed data messages)
        self.counter += 1

        return json.dumps(signed_data)

    # Helper function to generate and send a hello message
    async def send_hello(self):
        # Create hello message with the client's public key
        data = {"type": "hello", "public_key": self.public_key}

        # Generate signed data for the hello message
        hello_msg = self.generate_signed_data(data)

        # Send the hello message
        await self.websocket.send(hello_msg)

    # Function to encrypt a message using AES-GCM
    def aes_encrypt_message(self, aes_key, message):
        aes_cipher = AES.new(aes_key, AES.MODE_GCM)
        ciphertext, tag = aes_cipher.encrypt_and_digest(message.encode('utf-8'))

        # Return the encrypted message components in base64 format for safe transmission
        return {
            "ciphertext": base64.b64encode(ciphertext).decode('utf-8'),
            "nonce": base64.b64encode(aes_cipher.nonce).decode('utf-8'),
            "tag": base64.b64encode(tag).decode('utf-8')
        }

    # Function to decrypt a message using AES-GCM
    def aes_decrypt_message(self, aes_key, encrypted_message):
        ciphertext = base64.b64decode(encrypted_message["ciphertext"])
        nonce = base64.b64decode(encrypted_message["nonce"])
        tag = base64.b64decode(encrypted_message["tag"])

        aes_cipher = AES.new(aes_key, AES.MODE_GCM, nonce=nonce)
        try:
            # Decrypt the message and verify its integrity
            message = aes_cipher.decrypt_and_verify(ciphertext, tag)
            return message.decode('utf-8')
        except ValueError:
            print("Decryption failed. Invalid AES key or message tampered.")
            return None

    # Function to encrypt the AES key using the recipient's RSA public key
    def encrypt_aes_key(self, recipient_public_key):
        # Generate a 256-bit AES key
        aes_key = secrets.token_bytes(32)

        # Import the recipient's RSA public key and encrypt the AES key
        recipient_key = RSA.import_key(recipient_public_key.encode('utf-8'))
        cipher_rsa = PKCS1_OAEP.new(recipient_key)
        encrypted_aes_key = cipher_rsa.encrypt(aes_key)

        return aes_key, base64.b64encode(encrypted_aes_key).decode('utf-8')

    # Function to decrypt the AES key using the client's own RSA private key
    def decrypt_aes_key(self, encrypted_aes_key):
        encrypted_aes_key_bytes = base64.b64decode(encrypted_aes_key)

        # Decrypt the AES key using the client's private RSA key
        cipher_rsa = PKCS1_OAEP.new(self.key_pair)
        aes_key = cipher_rsa.decrypt(encrypted_aes_key_bytes)

        return aes_key

    # Function to send a public chat message to all connected clients
    async def send_public_chat(self, message):
        # Create the public chat message structure
        data = {
            "type": "public_chat",
            "sender": self.client_id,
            "message": message
        }

        # Generate signed data for the public chat message
        public_chat_msg = self.generate_signed_data(data)

        # Send the public chat message to the server
        await self.websocket.send(public_chat_msg)
        print("Public chat message sent.")

    # Function to send an encrypted private chat message
    async def send_chat(self, message, recipient_id):
        if recipient_id not in self.clients:
            print(f"Client {recipient_id} not found in client list.")
            return

        # Get the recipient's public key
        recipient_public_key = self.clients[recipient_id]['public_key']

        # Encrypt the AES key with the recipient's RSA public key
        aes_key, encrypted_aes_key = self.encrypt_aes_key(recipient_public_key)

        # Encrypt the message using AES
        encrypted_message = self.aes_encrypt_message(aes_key, message)

        # Create the chat message structure
        data = {
            "type": "chat",
            "sender": self.client_id,
            "recipient": recipient_id,
            "aes_key": encrypted_aes_key,
            "message": encrypted_message
        }

        # Generate signed data and send it
        chat_msg = self.generate_signed_data(data)
        await self.websocket.send(chat_msg)
        print("Encrypted chat message sent.")

    # Function to send a client list request
    async def client_list_request(self):
        # Create a client list request message
        message = {"type": "client_list_request"}
        await self.websocket.send(json.dumps(message))

    # Handle the received client list from the server
    async def handle_client_list(self, message):
        # Create a temporary list to store the received clients
        temp_list = {}

        for server in message["servers"]:
            for public_key in server['clients']:
                client_id = hashlib.sha256(base64.b64encode(public_key.encode('utf-8'))).hexdigest()
                if client_id != self.client_id:
                    temp_list[client_id] = {
                        "home_server": server["address"],
                        "fingerprint": client_id,
                        "public_key": public_key,
                    }

        # Replace the client's stored client list with the received list
        self.clients = temp_list

    # Print the list of clients
    def print_client_list(self):
        print("List of clients:")
        for client in self.clients:
            home_server = self.clients[client]["home_server"]
            print(f"{client} ({home_server})")

    # Handle signed data messages
    async def handle_signed_data(self, message):
        message_type = message["data"]["type"]

        match message_type:
            case "public_chat":
                sender = message["data"]["sender"]
                chat = message["data"]["message"]
                print(f"From {sender} (public): {chat}")
            case "chat":
                sender = message["data"]["sender"]
                encrypted_message = message["data"]["message"]
                encrypted_aes_key = message["data"]["aes_key"]

                # Decrypt the AES key using the client's private key
                aes_key = self.decrypt_aes_key(encrypted_aes_key)

                # Decrypt the message using the AES key
                decrypted_message = self.aes_decrypt_message(aes_key, encrypted_message)

                if decrypted_message:
                    print(f"From {sender} (private): {decrypted_message}")
            case _:
                print("Invalid message type received")

    # Listen for messages from the server
    async def listen(self):
        async for message in self.websocket:
            data = json.loads(message)
            if "type" not in data.keys():
                print(f"Received from server: {message}")
            else:
                await self.handle_messages(data)

    # Handle the received message based on its type
    async def handle_messages(self, message):
        message_type = message["type"]

        match message_type:
            case "signed_data":
                await self.handle_signed_data(message)
            case "client_list":
                await self.handle_client_list(message)
            case _:
                print("Invalid message type received")

    # Run the client
    async def run(self):
        print(f"Connecting to server at {self.uri}...")
        self.websocket = await websockets.connect(self.uri)

        # Send hello message
        await self.send_hello()

        # Start listening for incoming messages
        asyncio.ensure_future(self.listen())

        # Request the client list
        await self.client_list_request()

        # Main loop to handle user inputs
        while True:
            prompt = await ainput("> ")

            match prompt:
                case "public":
                    public_message = await ainput("Enter a message: ")
                    await self.send_public_chat(public_message)
                case "chat":
                    await self.client_list_request()
                    self.print_client_list()
                    recipient_id = await ainput("Enter recipient Client ID: ")
                    chat_message = await ainput("Enter a message: ")
                    await self.send_chat(chat_message, recipient_id)
                case "list":
                    await self.client_list_request()
                    self.print_client_list()
                case "close":
                    print("Closing connection to server...")
                    if self.websocket:
                        await self.websocket.close()
                    return
                case _:
                    print("Valid commands are ('public', 'chat', 'list', 'close')")

if __name__ == "__main__":
    # Get host and port from user input
    hostname = input("Enter address (host:port) of server to connect to: ")
    uri = "ws://" + hostname
    
    # Connect to server
    client = Client(uri)
    asyncio.run(client.run())
