import os
import time

from .serialize import serialize, deserialize


class Transport:
    @staticmethod
    def send(data, sock):
        data = serialize(**data)
        sent = 0
        while sent < len(data):
            curr = sock.send(data[sent:])
            if not curr:
                raise Exception('CLIENT COULD NOT SEND DATA')
            sent += curr

    @staticmethod
    def read(fd):
        data = b''
        read = os.read(fd, 1)
        while len(read):
            data += read
            if b'\n' in read:
                break
            read = os.read(fd, 1)
        return deserialize(data)
