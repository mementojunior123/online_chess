import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), os.path.pardir)))

from typing import Any
import socket
from time import sleep
import _thread
import game.chess_module as chess_module

s = socket.socket()
print("Socket successfully created")

# reserve a port
port = 40674

# Next bind to the port
# we have not typed any ip in the ip field --> LAN
s.bind(('', port))
print("socket binded to %s" %(port))

s.listen(5)    
print("socket is listening")


def make_new_thread(connection1 : socket.socket, adress1 : Any):
    _thread.start_new_thread(manage_client, (connection1, adress1))


def manage_client(client1 : socket.socket, adress1 : Any):
    client1.send(b'ConnectionEstablished')
    client2, address2 = s.accept()
    client1.send(b'GameStarting')
    client2.send(b'GameStarting')
    sleep(5)
    client1.send(b'GameOver')
    client2.send(b'GameOver')
    client1.close()
    client2.close()
    global current_thread_count
    current_thread_count -= 1
    print("Removing a trhead")
    print(f'Current Trhead Count: {current_thread_count}')
    return

MAX_THREAD_COUNT = 3
current_thread_count : int = 0

while True:
    if current_thread_count <= MAX_THREAD_COUNT:
        c, addr = s.accept()
        make_new_thread(c, addr)
        current_thread_count += 1
        print('Making new thread')
        print(f'Current Trhead Count: {current_thread_count}')
        sleep(0.1)
    else:
        pass