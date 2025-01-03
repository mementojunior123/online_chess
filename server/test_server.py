import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), os.path.pardir)))

from typing import Any
import socket
from time import sleep
import _thread
import game.chess_module as chess_module
import online.network_client as network_client
import pygame
pygame.init()

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

network_client.init()
from online.network_client import NetworkClient

def manage_client(conn1 : socket.socket, adress1 : Any):
    client1 : NetworkClient = NetworkClient(connection_socket=conn1, connection_ip='')
    sleep(0.2)
    client1.send_message(b'ConnectionEstablished')
    #conn2, address2 = s.accept()
    #client2 : NetworkClient = NetworkClient(connection_socket=conn2, connection_ip='')
    client1.send_message(b'GameStarting')
    #client2.send_message(b'GameStarting')
    sleep(2)
    client1.send_message(b'GameOver')
    #client2.send_message(b'GameOver')
    sleep(3)
    client1.close()
    #client2.close()
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
        sleep(0.5)
    else:
        pass