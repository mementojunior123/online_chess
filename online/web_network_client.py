import sys
import platform
import pygame
from pygame import event, Event
import socket
WEBPLATFORM = 'emscripten'

NETWORK_MESSAGE_RECIVED = event.custom_type()
NETWORK_SERVER_DISCONNECTED = event.custom_type()
NETWORK_MESSAGE_SENT = event.custom_type()
NETWORK_MESSAGE_FAILED = event.custom_type()


if sys.platform != WEBPLATFORM:
    raise ImportError('Imported the web client while offline!')

class WebNetworkClient:
    UUID = 0
    PREFIX_LENTGH = 2
    PORT = 7999

    def __init__(self, url : str = f'http://localhost:{PORT}/', port_used : int|None = None):
        self.socket = socket.socket()
        self.socket.setblocking(False)

        self.connection_ip : str = url
        self.port : int = port_used or WebNetworkClient.PORT
        self._closed : bool = False
        self.identifier = WebNetworkClient.UUID
        WebNetworkClient.UUID += 1
        self.connected : bool = False
        self.listening : int = 1

        self.unread_data : bytes = bytes(0)
        self.unsent_data : bytes = bytes(0)
    
    def connect_to_server(self):
        self.socket.connect((self.connection_ip, self.port))
        self.connected = True

    def receive_messages(self, message_count : int = -1) -> bool:
        if self._closed: return False
        return True
    
    def send_message(self, data : bytes) -> bool:
        if self._closed: return False
        if self.connected == False: return False
        self.unsent_data += data
        pygame.event.post(Event(NETWORK_MESSAGE_SENT, {'data' : data, 'network' : self}))
        return True
    
    def send_message_received_event(self, data : bytes):
        pygame.event.post(Event(NETWORK_MESSAGE_RECIVED, {'data' : data, 'network' : self}))
    
    def send_message_sent_event(self, data : bytes):
        pygame.event.post(Event(NETWORK_MESSAGE_SENT, {'data' : data, 'network' : self}))
    
    def send_dc_event(self):
        pygame.event.post(Event(NETWORK_SERVER_DISCONNECTED, {'network' : self}))
    
    def close(self):
        self._closed = True
    
    def cleanup(self):
        self.socket.close()