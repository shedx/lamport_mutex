import os
import selectors
import socket
import sys
import time

from .constants import LOCAL, REMOTE, INTRODUCTION, STOP
from .serialize import serialize, deserialize
from contextlib import suppress
from json.decoder import JSONDecodeError


class RPC:
    def __init__(self, host, addrs):
        self.id = sorted(addrs).index(host)
        self.server = Server(host)
        self.hosts = {}
        self.addrs = addrs
        self.fd_by_host = {}

        for ip, port in addrs:
            host = Client((ip, port))
            client_fd = host.connect()
            self.hosts[client_fd] = host
            self.fd_by_host[(ip, port)] = client_fd

    def send_to_fd(self, host_fd, callback, args=None):
        self.hosts[host_fd].send(
            {'callback': callback, 'args': args, 'host': self.addrs[self.id]}
        )

    def run(self, stressmode=False):

        sel = selectors.DefaultSelector()
        for client_fd in self.server.accept_n(len(self.addrs)):
            sel.register(client_fd, selectors.EVENT_READ)
        time.sleep(3)
        for fd in self.hosts.keys():
            self.send_to_fd(fd, INTRODUCTION)


        delivered_clients = set()
        while len(delivered_clients) != len(self.addrs):
            events = sel.select()

            for key, mask in events:
                print('sh')

                data = self.read_from_socket(key.fd)
                if data['callback'] == INTRODUCTION:
                    delivered_clients.add(key.fd)
                else:
                    raise Exception('INTRODUCTION ERROR')
        print('ooops')
        if not stressmode:
            sel.register(sys.stdin.fileno(), selectors.EVENT_READ)

        running = True
        while running:
            events = sel.select()
            for key, mask in events:
                data = self.read_from_socket(key.fd)

                if key.fd == sys.stdin.fileno():
                    if data['callback'] == STOP:
                        running = False
                        break
                    yield LOCAL, key.fd, data
                else:
                    yield REMOTE, key.fd, data

        self.stop()


    def read_from_socket(self, fd):
        data = b''
        read = os.read(fd, 1024)
        while len(read):
            data += read
            with suppress(JSONDecodeError):
                if isinstance(deserialize(data), dict):
                    break
            read = os.read(fd, 1024)
        return deserialize(data)

    def stop(self):
        self.server.close()
        [client.close() for client_fd, client in self.hosts]


class Client:
    def __init__(self, host):
        self._host = host
        self._socket = None

    def connect(self):
        while True:
            try:
                self._socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                self._socket.connect(self._host)
            except Exception as e:
                print(str(e))
                time.sleep(1)
                continue
            else:
                return self._socket.fileno()

    def send(self, data: dict):
        data = serialize(**data)
        sent = 0
        while sent < len(data):
            curr = self._socket.send(data[sent:])
            if not curr:
                raise Exception('CLIENT {} COULD NOT SEND DATA'\
                                .format(self._host))
            sent += curr

    def close(self):
        self._socket.close()


class Server:
    def __init__(self, host):
        self._connections = []
        self._socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self._socket.bind(host)
        self._socket.listen(0)

    def accept(self):
        conn, addr = self._socket.accept()
        self._connections.append(conn)
        return conn

    def accept_n(self, n):
        for _ in range(n):
            self.accept()
        return [conn.fileno() for conn in self._connections[-n:]]

    def close(self):
        self._socket.close()
