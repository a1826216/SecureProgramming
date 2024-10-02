import asyncio
import websockets
import json
import base64
from Crypto.PublicKey import RSA
from Crypto.Cipher import AES, PKCS1_OAEP
from Crypto.Signature import pkcs1_15
from Crypto.Hash import SHA256
import os

class SecureClient:
    def __init__(self):
        self.key = RSA.generate(2048)
        self.public_key = self.key.publickey().export_key()
        self.counter = 0  # To prevent replay attacks

    async def connect(self):
        uri = "ws://localhost:8001"
        print(f"Connecting to {uri}")
        async with websockets.connect(uri) as websocket:
            await self.send_hello(websocket)

            while True:
                # Prompt for user message input
                message = input("Enter a message: ")
                await self.send_chat(websocket, message)

                # Receive and process message
                response = await websocket.recv()
                print(f"Received message: {response}")
                await self.process_incoming_message(response)

    async def send_hello(self, websocket):
        """Send 'hello' message to server."""
        print("Sending 'hello' message to server")
        message = {
            "data": {
                "type": "hello",
                "public_key": base64.b64encode(self.public_key).decode('utf-8')
            }
        }
        await websocket.send(json.dumps(message))
        print(f"Sent 'hello' message: {json.dumps(message)}")

    def encrypt_message(self, message, recipient_public_key):
        """Encrypt message using AES and recipient's public key."""
        aes_key = os.urandom(32)  # 256-bit AES key
        iv = os.urandom(16)  # 16-byte IV
        cipher = AES.new(aes_key, AES.MODE_GCM, iv)
        ciphertext = cipher.encrypt(message.encode('utf-8'))

        # Encrypt the AES key using the recipient's public RSA key
        rsa_cipher = PKCS1_OAEP.new(recipient_public_key)
        encrypted_aes_key = rsa_cipher.encrypt(aes_key)

        return base64.b64encode(iv).decode('utf-8'), base64.b64encode(ciphertext).decode('utf-8'), base64.b64encode(encrypted_aes_key).decode('utf-8')

    def decrypt_message(self, encrypted_message):
        """Decrypt incoming message using AES and the client's private key."""
        print(f"Decrypting message: {encrypted_message}")
        encrypted_aes_key = base64.b64decode(encrypted_message['symm_keys'][0])
        iv = base64.b64decode(encrypted_message['iv'])
        ciphertext = base64.b64decode(encrypted_message['chat'])

        # Decrypt the AES key using the client's private RSA key
        rsa_cipher = PKCS1_OAEP.new(self.key)
        aes_key = rsa_cipher.decrypt(encrypted_aes_key)

        # Decrypt the message using AES
        cipher = AES.new(aes_key, AES.MODE_GCM, iv)
        decrypted_message = cipher.decrypt(ciphertext)
        return decrypted_message.decode('utf-8')

    async def process_incoming_message(self, message):
        """Process incoming chat message by decrypting it."""
        data = json.loads(message)
        if data['type'] == 'chat':
            decrypted_message = self.decrypt_message(data['data'])
            print(f"Decrypted message: {decrypted_message}")

    def sign_message(self, message):
        """Sign message using the client's private RSA key."""
        message_hash = SHA256.new(message.encode('utf-8'))
        signature = pkcs1_15.new(self.key).sign(message_hash)
        return base64.b64encode(signature).decode('utf-8')

    async def send_chat(self, websocket, message):
        """Send an encrypted and signed chat message."""
        self.counter += 1  # Increment counter to prevent replay attacks

        # For simplicity, encrypt with our own public key (this should be the recipient's key)
        recipient_public_key = self.key.publickey()

        # Encrypt the message
        iv, ciphertext, encrypted_aes_key = self.encrypt_message(message, recipient_public_key)

        # Structure the chat message
        chat_message = {
            "type": "chat",
            "data": {
                "destination_servers": ["localhost:8001"],  # Destination server for message forwarding
                "iv": iv,
                "symm_keys": [encrypted_aes_key],  # Symmetric AES key encrypted for recipient
                "chat": ciphertext
            },
            "counter": self.counter,
            "signature": self.sign_message(message)
        }

        await websocket.send(json.dumps(chat_message))
        print(f"Sent encrypted message: {json.dumps(chat_message)}")


# Run the client
secure_client = SecureClient()
asyncio.run(secure_client.connect())