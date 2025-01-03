import socket
import _thread
from time import perf_counter

class EventModuleShadow:
    @staticmethod
    def custom_type():
        return 0
    
    @staticmethod
    def post(event = None):
        return True

class FakeEvent:
    def __init__(self, type_arg = 'Fake', event_dict = None):
        self.type = type_arg


def init(use_pygame_events : bool = True):
    global NetworkClient, NETWORK_MESSAGE_RECIVED, NETWORK_SERVER_DISCONNECTED, NETWORK_MESSAGE_SENT, NETWORK_MESSAGE_FAILED
    global pygame, event, Event, USE_PYGAME_EVENTS
    USE_PYGAME_EVENTS = use_pygame_events
    if use_pygame_events:
        import pygame
        from pygame import event, Event
        NETWORK_MESSAGE_RECIVED = event.custom_type()
        NETWORK_SERVER_DISCONNECTED = event.custom_type()
        NETWORK_MESSAGE_SENT = event.custom_type()
        NETWORK_MESSAGE_FAILED = event.custom_type()
    else:
        NETWORK_MESSAGE_RECIVED = 1
        NETWORK_SERVER_DISCONNECTED = 2
        NETWORK_MESSAGE_SENT = 3
        NETWORK_MESSAGE_FAILED = 4
        event = EventModuleShadow
        Event = FakeEvent

    class NetworkClient:
        NETWORK_MESSAGE_RECIVED = NETWORK_MESSAGE_RECIVED
        NETWORK_SERVER_DISCONNECTED = NETWORK_SERVER_DISCONNECTED
        NETWORK_MESSAGE_SENT = NETWORK_MESSAGE_SENT
        NETWORK_MESSAGE_FAILED = NETWORK_MESSAGE_FAILED

        PREFIX_LENTGH = 2
        BUFF_SIZE = 4096

        def __init__(self, port : int = 40674, connection_ip : str = '127.0.0.1', connection_socket : socket.socket|None = None):
            self.socket : socket.socket = connection_socket or socket.socket()
            self.socket.settimeout(1)
            self.port : int = port
            self.connection_ip : str = connection_ip
            self._closed : bool = False
            self.listening : int = 0
            self.connected : bool = False
            self.use_pygame_events : bool = USE_PYGAME_EVENTS
            self.untreated_data : bytes = bytes(0)
            
        def close(self):
            self._closed = True
        
        def cleanup(self):
            self.socket.shutdown(socket.SHUT_RDWR)
            self.socket.close()
        
        
        def connect_to_server(self):
            self.socket.connect((self.connection_ip, self.port))
            self.connected = True
        

        def receive_messages(self, message_count : int = -1) -> bool:
            if self._closed: return False
            _thread.start_new_thread(self._receive_messages, (message_count,))
            return True
        
        def wait_for_message(self) -> bytes:
            if self._closed: return
            while True:
                if self._closed: return
                prefix : bytes = self.receive_prefix()
                if prefix is None: return
                msg_len : int = from_base_256(prefix)
                data = self._receive_message(msg_len)
                if data is None: return None
                if data:
                    if self.use_pygame_events: event.post(Event(NETWORK_MESSAGE_RECIVED, {'data' : data, 'network' : self}))
                    break
            return data

        def _receive_messages(self, message_count : int = -1):
            if self._closed: return
            self.listening += 1
            messages_received : int = 0
            while messages_received < message_count or (message_count < 0):
                if self._closed: return
                prefix : bytes = self.receive_prefix()
                if prefix is None: return
                msg_len : int = from_base_256(prefix)
                data = self._receive_message(msg_len)
                if data:
                    messages_received += 1
                    if self.use_pygame_events: event.post(Event(NETWORK_MESSAGE_RECIVED, {'data' : data, 'network' : self}))
            self.listening -= 1
        
        def receive_prefix(self) -> bytes|None:
            prefix_received : int = 0
            prefix : bytes = bytes(0)
            while prefix_received < NetworkClient.PREFIX_LENTGH:
                try:
                    if self._closed: return
                    data = self.untreated_data or self.socket.recv(NetworkClient.BUFF_SIZE)
                    self.untreated_data = bytes(0)
                except socket.timeout:
                    continue
                if data == b'':
                    if self.use_pygame_events: event.post(Event(NETWORK_SERVER_DISCONNECTED, {'network' : self}))
                    return None
                prefix_received += len(data)
                prefix += data

            self.untreated_data += prefix[NetworkClient.PREFIX_LENTGH:]
            return prefix[:NetworkClient.PREFIX_LENTGH]
        
        def _receive_message(self, lentgh : int) -> bytes|None:
            data_received : int = 0
            total_data : bytes = bytes(0)
            while data_received < lentgh:
                if self._closed: return
                try:
                    data = self.untreated_data or self.socket.recv(NetworkClient.BUFF_SIZE)
                    self.untreated_data = bytes(0)
                except socket.timeout:
                    continue
                if data == b'':
                    if self.use_pygame_events: event.post(Event(NETWORK_SERVER_DISCONNECTED, {'network' : self}))
                    return None
                data_received += len(data)
                total_data += data
            self.untreated_data += total_data[lentgh:]
            return total_data[:lentgh]

        def send_message(self, data : bytes) -> bool:
            if self._closed: return False
            _thread.start_new_thread(self._send_message, (data,))
            return True
        
        @staticmethod
        def make_prefix(message_lentgh : int) -> bytes:
            if message_lentgh > 2 ** (8 * NetworkClient.PREFIX_LENTGH):
                return None
            return bytes(convert_to_base_256(message_lentgh, min_chars=NetworkClient.PREFIX_LENTGH))
        
        @staticmethod
        def read_prefix(prefix : bytes) -> int:
            return from_base_256(prefix)

        def _send_message(self, data : bytes):
            byte_count : int = len(data)
            bytes_sent : int = 0
            prefix = self.make_prefix(byte_count)

            final_data : bytes = b''.join([prefix, data])
            final_byte_count : int = len(final_data)

            while bytes_sent < final_byte_count:
                try:
                    successful_sent : int = self.socket.send(final_data[bytes_sent:])
                except socket.timeout:
                    continue
                if successful_sent == 0:
                    if self.use_pygame_events: event.post(Event(NETWORK_SERVER_DISCONNECTED, {'network' : self}))
                    if self.use_pygame_events: event.post(Event(NETWORK_MESSAGE_FAILED, {'data_sent' : data, 'progress' : bytes_sent - (final_byte_count - byte_count), 'network' : self}))
                    return
                bytes_sent += successful_sent
            
            if self.use_pygame_events: event.post(Event(NETWORK_MESSAGE_SENT, {'data' : data, 'network' : self}))

    global _is_init
    _is_init = True

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


_is_init : bool = False