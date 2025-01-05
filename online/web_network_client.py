import sys
import pygame
from pygame import event, Event
import socket
from select import select
from enum import Enum
import asyncio
from time import perf_counter
WEBPLATFORM = 'emscripten'

NETWORK_MESSAGE_RECIVED = event.custom_type()
NETWORK_SERVER_DISCONNECTED = event.custom_type()
NETWORK_MESSAGE_SENT = event.custom_type()
NETWORK_MESSAGE_FAILED = event.custom_type()


if sys.platform != WEBPLATFORM:
    pass
    #raise ImportError('Imported the web client while offline!')

class MessageBuildingPhase(Enum):
    PREFIX = 1
    MESSAGE = 2

class MessageBuilder:
    def __init__(self):
        self.phase : MessageBuildingPhase = MessageBuildingPhase.PREFIX
        self.held_data : list[bytes|None] = [None]
    
    def process(self, data : bytes) -> tuple[int, bytes|None]:
        total_data_processed : int = 0
        if self.phase == MessageBuildingPhase.PREFIX:
            if len(data) < WebNetworkClient.PREFIX_LENTGH: return total_data_processed, None
            prefix : bytes = data[:WebNetworkClient.PREFIX_LENTGH]
            data = data[WebNetworkClient.PREFIX_LENTGH:]
            total_data_processed += WebNetworkClient.PREFIX_LENTGH
            self.held_data[0] = prefix
            self.phase = MessageBuildingPhase.MESSAGE
            
        if self.phase == MessageBuildingPhase.MESSAGE:
            prefix : bytes = self.held_data[0]
            if prefix is None: 
                self.phase = MessageBuildingPhase.PREFIX
                return (total_data_processed, None)
            msg_len : int = from_base_256(prefix)
            if len(data) < msg_len: return (total_data_processed, None)
            message : bytes = data[:msg_len]
            total_data_processed += msg_len
            data = data[msg_len:]
            self.phase = MessageBuildingPhase.PREFIX
            self.held_data[0] = None
            return (total_data_processed, message)
        
class WebNetworkClient:
    UUID = 0
    PREFIX_LENTGH = 2
    PORT = 40674
    USE_PREFIXES = True
    BUFF_SIZE = 4096

    NETWORK_MESSAGE_RECIVED = NETWORK_MESSAGE_RECIVED
    NETWORK_SERVER_DISCONNECTED = NETWORK_SERVER_DISCONNECTED
    NETWORK_MESSAGE_SENT = NETWORK_MESSAGE_SENT
    NETWORK_MESSAGE_FAILED = NETWORK_MESSAGE_FAILED

    def __init__(self, port : int|None = None, connection_ip : str = f'http://localhost:{PORT}/', connection_socket : socket.socket|None = None):
        self.socket = connection_socket or socket.socket()
        self.socket.setblocking(False)

        self.connection_ip : str = connection_ip
        self.port : int = port or WebNetworkClient.PORT
        self._closed : bool = False
        self.identifier = WebNetworkClient.UUID
        WebNetworkClient.UUID += 1
        self.connected : bool = False
        self.listening : int = 1

        self.unread_data : bytes = bytes(0)
        self.unsent_data : bytes = bytes(0)
        self.messsage_builder : MessageBuilder = MessageBuilder()
    
    def update(self):
        if self._closed: return
        self.poll_data()
        self.process_send_queue()
        self.process_reception_queue()
        
    def poll_data(self) -> bool:
        ready_read : list[socket.socket] = (select([self.socket], [], [], 0.0))[0]
        if self.socket not in ready_read: return False
        if not self.connected: return False
        data : bytes = self.socket.recv(WebNetworkClient.BUFF_SIZE)
        if data == b'':
            self.send_dc_event()
            return False
        self.unread_data += data
        return True

    def process_send_queue(self) -> bool:
        if not self.unsent_data: return False
        ready_write : list[socket.socket] = (select([self.socket], [self.socket], [self.socket], 0.0))[1]
        if self.socket not in ready_write: return False
        if not self.connected: return False
        result : int = self.socket.send(self.unsent_data)
        if result == 0: 
            self.send_dc_event()
            return False
        self.unsent_data = self.unsent_data[result:]
        return True
    
    def process_reception_queue(self) -> bool:
        if not self.unread_data: return False
        if not self.USE_PREFIXES:
            self.send_message_received_event(self.unread_data)
            self.unread_data = bytes(0)
            return True
        total_processed, message = self.messsage_builder.process(self.unread_data)
        self.unread_data = self.unread_data[total_processed:]
        if message:
            self.send_message_received_event(message)
        return True
    
    @staticmethod
    def is_socket_alive(sock : socket.socket) -> bool:
        data_sent : int = 0
        try:
            result : int = sock.send((bytes(convert_to_base_256(1, min_chars=WebNetworkClient.PREFIX_LENTGH)) + bytes([90]))[data_sent:])
        except:
            return False
        if result == 0: return False
        if result >= 3: return True
        data_sent += result
        while data_sent < 3:
            try:
                result = sock.send((bytes(convert_to_base_256(1, min_chars=WebNetworkClient.PREFIX_LENTGH)) + bytes([90]))[data_sent:])
            except:
                return False
            if result == 0: return False
            data_sent += result
        
        return True     
    
    async def connect_to_server(self):
        start_time = perf_counter()
        while perf_counter() < start_time + 60:
            try:
                self.socket.connect((self.connection_ip, self.port))
            except BlockingIOError:
                await asyncio.sleep(0)
                if self.is_socket_alive(self.socket):
                    #print('socket alive')
                    self.connected = True
                    return
            except OSError as e:
                if e.errno in {30, 106} or e.winerror in {10056}:
                    self.connected = True
                    return
                print(e)
            else:
                self.connected = '???'
                return
    def receive_messages(self, message_count : int = -1) -> bool:
        if self._closed: return False
        return True
    
    @staticmethod
    def make_prefix(message_lentgh : int) -> bytes:
        if message_lentgh > 2 ** (8 * WebNetworkClient.PREFIX_LENTGH):
            return None
        return bytes(convert_to_base_256(message_lentgh, min_chars=WebNetworkClient.PREFIX_LENTGH))
    
    @staticmethod
    def read_prefix(prefix : bytes) -> int:
        return from_base_256(prefix)
    
    def send_message(self, data : bytes) -> bool:
        print(f'attempted_send : {data}', self._closed, self.connected)
        if self._closed: return False
        if self.connected == False: return False
        final_data : bytes
        if WebNetworkClient.USE_PREFIXES:
            prefix : bytes = self.make_prefix(len(data))
            final_data = prefix + data
        else:
            final_data = data

        self.unsent_data += final_data
        print('hello')
        pygame.event.post(Event(NETWORK_MESSAGE_SENT, {'data' : data, 'network' : self}))
        self.update()
        return True
    
    def send_message_received_event(self, data : bytes):
        pygame.event.post(Event(NETWORK_MESSAGE_RECIVED, {'data' : data, 'network' : self}))
    
    def send_message_sent_event(self, data : bytes):
        pygame.event.post(Event(NETWORK_MESSAGE_SENT, {'data' : data, 'network' : self}))
    
    def send_dc_event(self):
        pygame.event.post(Event(NETWORK_SERVER_DISCONNECTED, {'network' : self}))
        self.connected = False
    
    def close(self):
        self._closed = True
    
    def cleanup(self):
        self.socket.close()


def convert_to_base_256(n : int, min_chars : int) -> list[int]:
    base = 256
    if n == 0: return [0]
    result = []
    char_count : int = 0
    while n or char_count < min_chars:
        n, remainder = divmod(n, base)
        result.append(remainder)
        char_count += 1
    return result

def from_base_256(val : bytes|list[int]):
    return sum([x * (256 ** n) for n, x in enumerate(val)])