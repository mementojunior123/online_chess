import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), os.path.pardir)))

from typing import Any
import socket
from time import sleep
import _thread
import game.chess_module as chess_module
from random import shuffle, randint
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
    global current_thread_count
    SOCKET_TIMEOUT = 2
    client1 : NetworkClient = NetworkClient(connection_socket=conn1, connection_ip='')
    sleep(0.2)
    client1.socket.settimeout(SOCKET_TIMEOUT)
    client1.send_message(b'ConnectionEstablished')
    conn2, address2 = s.accept()
    client2 : NetworkClient = NetworkClient(connection_socket=conn2, connection_ip='')
    client2.socket.settimeout(SOCKET_TIMEOUT)
    order = [b'W', b'B'] if randint(0, 1) else [b'B', b'W']
    id1, id2 = client1.identifier, client2.identifier
    print(id1, id2)
    game : chess_module.ChessGame = chess_module.ChessGame()
    first_client : NetworkClient
    print(f'{order[0]}-->', end='')
    if order[0] == b'W':
        client1_team = chess_module.TeamType.WHITE
    else:
        client1_team = chess_module.TeamType.BLACK
    print(first_client.identifier)
    client2_team = client1_team.opposite()
    outcome1 : bytes = b'None'
    outcome2 : bytes = b'None'
    break_loop : bool = False

    other_message : bytes|None = None
    message : bytes|None = None

    client1.send_message(b'GameStarting' + order[0])
    client2.send_message(b'GameStarting' + order[1])

    current_client : NetworkClient
    other_client : NetworkClient
    while True:
        current_client = client1 if client1_team == game.current_turn else client2
        other_client = client2 if current_client == client1 else client1
        message = None
        other_message = None
        while message is None and other_message is None:
            if current_client.peek():
                try:
                    message : bytes|None = current_client.wait_for_message(use_buffer=True)
                    if message is None: message = b'Disconnecting'
                except OSError:
                    current_thread_count -= 1
                    print("Removing a trhead")
                    print(f'Current Trhead Count: {current_thread_count}')
                    other_client.send_message(b'GameOverYour opponent disconnected. You win!')
                    sleep(1.5)
                    
                    other_client.close()
                    other_client.cleanup()
                    current_client.close()
                    current_client.cleanup()
                    return
            elif other_client.peek():
                try:
                    other_message : bytes|None = other_client.wait_for_message(use_buffer=True)
                    if other_message is None: other_message = b'Disconnecting'
                except OSError:
                    current_thread_count -= 1
                    print("Removing a trhead")
                    print(f'Current Trhead Count: {current_thread_count}')
                    current_client.send_message(b'GameOverYour opponent disconnected. You win!')
                    sleep(1.5)          
                    other_client.close()
                    other_client.cleanup()
                    current_client.close()
                    current_client.cleanup()
                    return
        
        print(f'Received {message or other_message}')
        
        if other_message == b'Disconnecting':
            break_loop = True
            outcome1 = b'Your opponent disconnected. You win!'
            outcome2 = b'Your opponent disconnected. You win!'
            other_client.close() 

        elif message == b'Disconnecting':
            current_client.close()
            outcome1 = b'Your opponent disconnected. You win!'
            outcome2 = b'Your opponent disconnected. You win!'
            break
        elif message.startswith(b'TryMove'):
            move_data : bytes = message.removeprefix(b'TryMove')
            move_made : chess_module.ChessMove = chess_module.decode_move(move_data)
            if game.validate_move(move_made['start_pos'], move_made['end_pos'], move_made['extra_info']):
                ext = game.make_move(move_made['start_pos'], move_made['end_pos'], move_made['extra_info'])
                other_client.send_message(b'OpponentMove' + chess_module.encode_move(move_made))
                for inst in ext:
                    if inst['type'] == 'stalemate':
                        outcome1 = b'Stalemate!'
                        outcome2 = b'Stalemate!'
                        break_loop = True
                        break
                    elif inst['type'] == 'insufficent_material':
                        outcome1 = b'Draw by insufficent material!'
                        outcome2 = b'Draw by insufficent material!'
                        break_loop = True
                        break

                    elif inst['type'] == 'checkmate':
                        outcome1 = b'Checkmate!'
                        outcome2 = b'Checkmate!'
                        break_loop = True
                        break
            else:
                current_client.send_message(b'MadeInvalidMove')
                outcome1 = b'Your opponent disconnected. You win!'
                outcome2 = b'Your opponent disconnected. You win!'
                break
        if break_loop:
            break
        
    
    sleep(0.1)
    client1.send_message(b'GameOver' + outcome1)
    client2.send_message(b'GameOver' + outcome2)
    sleep(3)
    client1.close()
    client1.cleanup()
    client2.close()
    client2.cleanup()
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