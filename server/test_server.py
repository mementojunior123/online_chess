import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), os.path.pardir)))

from typing import Any
import socket
from time import sleep
import _thread
import game.chess_module as chess_module
from random import shuffle
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
    conn2, address2 = s.accept()
    client2 : NetworkClient = NetworkClient(connection_socket=conn2, connection_ip='')
    order = [b'W', b'B']
    shuffle(order)
    client1.send_message(b'GameStarting' + order[0])
    client2.send_message(b'GameStarting' + order[1])
    game : chess_module.ChessGame = chess_module.ChessGame()
    client1_team = chess_module.TeamType.WHITE if order[0] == 'W' else chess_module.TeamType.BLACK
    client2_team = client1_team.opposite()
    outcome1 : bytes = b'None'
    outcome2 : bytes = b'None'
    break_loop : bool = False

    other_message : bytes|None = None


    while True:
        other_message = None
        current_client = client1 if client1_team != game.current_turn else client2
        other_client = client2 if current_client == client1 else client1

        message : bytes = current_client.wait_for_message()
        print(message)
        if message == b'Disconnecting':
            current_client.close()
            outcome1 = b'Your opponent disconnected. You win!'
            outcome2 = b'Your opponent disconnected. You win!'
            break
        elif message.startswith(b'TryMove'):
            print('Move attempted')
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
        sleep(0.5)
    else:
        pass