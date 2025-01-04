import sys
import platform
import pygame
from pygame import event, Event
WEBPLATFORM = 'emscripten'

NETWORK_MESSAGE_RECIVED = event.custom_type()
NETWORK_SERVER_DISCONNECTED = event.custom_type()
NETWORK_MESSAGE_SENT = event.custom_type()
NETWORK_MESSAGE_FAILED = event.custom_type()
class WebEvent:
    

    def __init__(self):
        pass

class MessageEventInterface(WebEvent):
    def __init__(self):
        self.data : str
        self.origin : str
        lastEventId : str


class CloseEventInterface(WebEvent):
    def __init__(self):
        self.code : int
        self.reason : str
        self.wasClean : bool

class WebSocketInterface:
    def __init__(self, url : str, protocols : list[str] = None):
        if protocols is None: protocols = []
        self.url : str = url
        self.protocol : str = ''
        self.binaryType : str = 'blob'
        self.bufferedAmount : int = 0
        self.extensions : str = ''
        self.readyState : int = 0
    
    def close(self, code : int = 1005, reason : str = 'Unknown'):
        self.readyState = 3
    
    def send(self, data : str):
        pass

    @staticmethod
    def onclose(event : WebEvent):
        pass
    
    @staticmethod
    def onmessage(event : MessageEventInterface):
        pass

if sys.platform == WEBPLATFORM:
    WebSocket = WebSocketInterface
    exec('WebSocket = platform.WebSocket')
else:
    raise ImportError('Imported the web client while offline!')

class WebNetworkClient:
    UUID = 0
    PREFIX_LENTGH = 2

    def __init__(self, url : str = 'http://localhost:7999/'):
        self.socket = WebSocket(url)
        self.socket.onmessage = self.handle_message_received_event
        self.socket.onclose = self.handle_close_event
        self._closed : bool = False
        self.identifier = WebNetworkClient.UUID
        WebNetworkClient.UUID += 1
        self.connected : bool = True
        self.listening : int = 1
    
    def connect_to_server(self):
        self.connected = True

    def receive_messages(self, message_count : int = -1) -> bool:
        if self._closed: return False
        return True
    
    def send_message(self, data : bytes) -> bool:
        if self._closed: return False
        if self.socket.readyState == 0: return False
        self.socket.send(data.decode())
        pygame.event.post(Event(NETWORK_MESSAGE_SENT, {'data' : data, 'network' : self}))
        return True
    
    def handle_message_received_event(self, event : MessageEventInterface):
        data_received : bytes = bytes(event.data)
        pygame.event.post(Event(NETWORK_MESSAGE_RECIVED, {'data' : data_received, 'network' : self}))
    
    def handle_close_event(self, event : CloseEventInterface):
        pygame.event.post(Event(NETWORK_SERVER_DISCONNECTED, {'network' : self}))
    
    def close(self):
        self._closed = True
    
    def cleanup(self):
        self.socket.close()