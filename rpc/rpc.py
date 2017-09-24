import selectors
import sys
import time

from .constants import STDIN, REMOTE, INTRODUCTION
from .client import Client
from .server import Server
from .transport import Transport


class RPC:
    def __init__(self, host, addrs):
        self.id = sorted(addrs).index(host)
        self.server = Server(host)
        self.hosts = {}
        self.addrs = sorted(addrs)
        self.fd_by_host = {}

        for ip, port in addrs:
            host = Client((ip, port))
            client_fd = host.connect()
            self.hosts[client_fd] = host
            self.fd_by_host[(ip, port)] = client_fd

    def send_to_fd(self, host_fd, callback, clocks=None):
        self.hosts[host_fd].send(
            {
                'callback': callback,
                'host': self.addrs[self.id],
                'clocks': clocks
            }
        )

    def broadcast(self, callback, clocks=None):
        for host_fd in self.hosts.keys():
            if host_fd != self.fd_by_host[self.addrs[self.id]]:
                self.send_to_fd(host_fd, callback, clocks)

    def run(self):

        sel = selectors.DefaultSelector()
        for client_fd in self.server.accept_n(len(self.addrs)):
            sel.register(client_fd, selectors.EVENT_READ)

        time.sleep(3)  # wait until all servers are running
        for fd in self.hosts.keys():
            self.send_to_fd(fd, INTRODUCTION)

        delivered_clients = set()
        while len(delivered_clients) != len(self.addrs):
            events = sel.select()

            for key, mask in events:
                data = Transport.read(key.fd)
                if data['callback'] == INTRODUCTION:
                    delivered_clients.add(key.fd)
                else:
                    raise Exception('INTRODUCTION ERROR')

        sel.register(sys.stdin.fileno(), selectors.EVENT_READ)

        while KeyboardInterrupt:
            events = sel.select()
            for key, mask in events:
                data = Transport.read(key.fd)

                if key.fd == sys.stdin.fileno():
                    yield STDIN, data
                else:
                    yield REMOTE, data

        self.stop()

    def stop(self):
        self.server.close()
        [client.close() for client_fd, client in self.hosts]
