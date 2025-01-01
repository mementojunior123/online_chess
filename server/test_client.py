import socket
from time import sleep

# Create a socket object
s = socket.socket()

# Define the port on which you want to connect
port = 40674

# connect to the server on local computer
s.connect(('127.0.0.1', port))

while True:
    message = s.recv(1024)
    if message == b'ConnectionEstablished':
        print('Connection established; Waiting for second player...')
    elif message == b'GameStarting':
        print('Starting game!')
    elif message == b'GameOver':
        print("Game Over!")
        break
s.close()