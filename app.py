from flask import Flask, request, jsonify, send_from_directory
import socket

app = Flask(__name__, static_folder='static')

HOST = '192.168.78.52'
PORT = 5001

client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
client.connect((HOST, PORT))

@app.route('/')
def index():
    return send_from_directory('.', 'client_gui.html')

@app.route('/auth', methods=['POST'])
def auth():
    data = request.json
    msg = f"{data['username']}::{data['password']}"
    client.send(msg.encode())
    response = client.recv(1024).decode()
    return response

@app.route('/command', methods=['POST'])
def command():
    data = request.json
    client.send(data['command'].encode())
    response = client.recv(4096).decode()
    return response

if __name__ == '__main__':
    app.run(debug=True)