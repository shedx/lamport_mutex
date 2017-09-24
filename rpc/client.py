import socket
import time

from .transport import Transport


class Client:
    def __init__(self, host):
        self._host = host
        self._socket = None

    def connect(self):
        while True:
            try:
                self._socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                self._socket.connect(self._host)
            except:
                time.sleep(0.2)
                continue
            else:
                return self._socket.fileno()

    def send(self, data: dict):
        Transport.send(data, self._socket)

    def close(self):
        self._socket.close()
