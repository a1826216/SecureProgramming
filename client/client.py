import asyncio
import websockets
import json
import base64
import hashlib

from Crypto.PublicKey import RSA

class Client:
    def __init__(self, uri):
        # Address of server to connect to
        self.uri = uri
        
        # Counter value (to be sent with signed data)
        self.counter = 0

        # Generate 2048-bit RSA key pair
        self.key_pair = RSA.generate(2048)

        # Exported PEM of public key
        self.public_key = self.key_pair.public_key().export_key()

        # List of all clients on all servers
        self.client_list = {}

    # Helper function to generate signed data messages
    def generate_signed_data(self, data:dict):
        # Base64 signature of data + counter
        signature = bytes(json.dumps(data)+str(self.counter), 'utf-8')
        
        # Get SHA256 sum of signature
        signature = hashlib.sha256(signature).hexdigest()

        # Base64 encode SHA256 sum of signature
        signature = base64.b64encode(bytes(signature,'utf-8'))
        
        signed_data = {
            "type": "signed_data",
            "data": data,
            "counter": self.counter,
            "signature": str(signature)
        }

        return json.dumps(signed_data)
    


    # Run the client
    def run(self):
        pass


if __name__ == "__main__":
    client = Client("ws://localhost:8765")

    test_data = {"type": "test_data"}

    # Testing signed data
    signed_data = client.generate_signed_data(test_data)
    print(signed_data)