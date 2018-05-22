import socket
import socketserver

from typing import Union, ByteString, TypeVar, Generic, Callable, NamedTuple

from prompy.container import BasePromiseContainer
from prompy.promise import Promise

TMessage = TypeVar('TMessage', str, bytes)


class MessagioConfig(NamedTuple):
    address: str
    port: str
    content_type: str = 'text'
    encoding: str = 'UTF-8'
    protocol: str = 'tcp'


class MessagioClient:
    def __init__(self, config: MessagioConfig,
                 promise_container: BasePromiseContainer=None,
                 prom_type=Promise,
                 message_handler=None):
        self.config = config
        self.message_handler = message_handler
        self._promise_container = promise_container
        self._socket: socket.SocketType = None
        self._prom_type = prom_type

    def start(self, **kwargs) -> Promise:
        def starter(resolve, reject):
            try:
                s = socket.socket()
            except Exception as e:
                pass

        return self._prom_type(starter, **kwargs)

    def send_message(self, message):
        pass



class MessagioServer:
    def __init__(self, config: MessagioConfig, ):
        pass

    def send(self, client_id, ):
        pass



