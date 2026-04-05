import socket
import json
import os
import threading
from cryptography.fernet import Fernet
import base64

class Pusher:
    def __init__(self, host='0.0.0.0', port=5050):
        self.host = host
        self.port = port
        self.target_ip = None
        # Derived key to ensure encryption works out-of-the-box
        shared_secret = b"PusherUniversalKey_2026_Secure!"
        self.cipher = Fernet(base64.urlsafe_b64encode(shared_secret.ljust(32)[:32]))

    def ipaddr(self, ip):
        self.target_ip = ip
        return self

    def request(self, filename):
        if not self.target_ip:
            print("Set IP address first.")
            return
        try:
            client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            client.connect((self.target_ip, self.port))
            client.send(json.dumps({"file": filename}).encode())
            
            status = client.recv(1024).decode()
            if status == "ACCEPTED":
                with open(f"pushed_{filename}", "wb") as f:
                    encrypted_buffer = b""
                    while True:
                        chunk = client.recv(8192)
                        if not chunk: break
                        encrypted_buffer += chunk
                    f.write(self.cipher.decrypt(encrypted_buffer))
                print(f"Transfer of {filename} complete.")
            else:
                print("Request denied.")
            client.close()
        except Exception as e:
            print(f"Error: {e}")

    def _handler(self, conn, addr):
        try:
            data = conn.recv(1024).decode()
            if not data: return
            fname = json.loads(data).get("file")
            print(f"\n[REQUEST] {addr[0]} -> {fname}")
            
            if input("Accept? (y/n): ").lower() == 'y' and os.path.exists(fname):
                conn.send("ACCEPTED".encode())
                with open(fname, "rb") as f:
                    raw_data = f.read()
                conn.sendall(self.cipher.encrypt(raw_data))
            else:
                conn.send("DECLINED".encode())
        finally:
            conn.close()

    def listen(self):
        server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        server.bind((self.host, self.port))
        server.listen(5)
        print(f"Pusher Server Active | Port {self.port}")
        while True:
            conn, addr = server.accept()
            threading.Thread(target=self._handler, args=(conn, addr), daemon=True).start()