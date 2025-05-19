import socket
import threading
import os
import json
from threading import Lock

HOST = '192.168.78.52'
PORT = 5001

file_lock = Lock()

# Load users with roles from JSON (users.json should have format: { "username": {"password": "pass", "role": "admin/user"} })
with open('users.json', 'r') as f:
    USERS = json.load(f)

def handle_client(client_socket, address):
    print(f"[CONNECTED] Client {address} connected.")
    try:
        # Receive authentication
        data = client_socket.recv(1024).decode()
        print("Received:", data)
        parts = data.strip().split("::")

        if len(parts) != 2:
            client_socket.send("Invalid authentication format.".encode())
            client_socket.close()
            return

        username, password = parts

        # Authenticate and get role
        if username in USERS and USERS[username]["password"] == password:
            role = USERS[username]["role"]
            client_socket.send("Authentication successful".encode())
        else:
            client_socket.send("Authentication failed".encode())
            client_socket.close()
            return

        # Wait for commands
        while True:
            data = client_socket.recv(2048).decode()
            if not data:
                break

            print(f"[COMMAND FROM {address}] {data}")
            parts = data.split("::")
            command = parts[0]

            # Role-based access check
            if command in ["CREATE", "DELETE"] and role != "admin":
                client_socket.send("Permission denied: Admin only command.".encode())
                continue

            if command == "LIST":
                files = os.listdir('.')
                client_socket.send(', '.join(files).encode())

            elif command == "CREATE":
                if len(parts) >= 3:
                    filename = parts[1]
                    content = "::".join(parts[2:])
                    with file_lock:
                        with open(filename, 'w') as f:
                            f.write(content)
                    client_socket.send(f"File '{filename}' created.".encode())
                else:
                    client_socket.send("Invalid CREATE command.".encode())

            elif command == "READ":
                if len(parts) == 2:
                    filename = parts[1]
                    if os.path.exists(filename):
                        with open(filename, 'r') as f:
                            content = f.read()
                        client_socket.send(content.encode())
                    else:
                        client_socket.send("File not found.".encode())
                else:
                    client_socket.send("Invalid READ command.".encode())

            elif command == "DELETE":
                if len(parts) == 2:
                    filename = parts[1]
                    with file_lock:
                        if os.path.exists(filename):
                            os.remove(filename)
                            client_socket.send(f"File '{filename}' deleted.".encode())
                        else:
                            client_socket.send("File not found.".encode())
                else:
                    client_socket.send("Invalid DELETE command.".encode())

            else:
                client_socket.send("Unknown command.".encode())

    except Exception as e:
        print(f"[ERROR] {e}")
    finally:
        print(f"[DISCONNECTED] Client {address} disconnected.")
        client_socket.close()

def start_server():
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.bind((HOST, PORT))
    server.listen(5)
    print(f"[SERVER STARTED] Listening on {HOST}:{PORT}")

    while True:
        client_socket, address = server.accept()
        thread = threading.Thread(target=handle_client, args=(client_socket, address))
        thread.start()

if __name__ == "__main__":
    start_server()
