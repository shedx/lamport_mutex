import argparse
import os
import selectors
import sys
import time

from lamport.lamport import Lamport
from rpc.constants import STDIN, REMOTE, INTRODUCTION
from rpc.serialize import serialize
from rpc.transport import Transport


class LocalTransport(Transport):
    @staticmethod
    def send(fd, data):
        data = serialize(**data)
        sent = 0
        while sent < len(data):
            curr = os.write(fd, data[sent:])
            if not curr:
                raise Exception('CLIENT COULD NOT SEND DATA')
            sent += curr


class LocalRPC:
    def __init__(self, id):
        self.id = id
        self.write_descriptors = [sys.stdin.fileno()]
        self.read_descriptors = [sys.stdout.fileno()]

    def send_to_fd(self, host_fd, callback, clocks=None):
        LocalTransport.send(
            host_fd,
            {
                'callback': callback,
                'id': self.id,
                'clocks': clocks
            }
        )

    def broadcast(self, callback, clocks=None):
        for host_fd in self.write_descriptors:
            self.send_to_fd(host_fd, callback, clocks)

    def run(self):

        sel = selectors.DefaultSelector()
        print('sh')
        for client_fd in self.read_descriptors:
            sel.register(client_fd, selectors.EVENT_READ)
            print('sh')

        time.sleep(3)  # wait until all servers are running
        for fd in self.write_descriptors:
            self.send_to_fd(fd, INTRODUCTION)

        delivered_clients = set()
        while len(delivered_clients) != len(self.write_descriptors):
            print('aaa')
            events = sel.select()

            for key, mask in events:
                data = LocalTransport.read(key.fd)
                if data['callback'] == INTRODUCTION:
                    delivered_clients.add(key.fd)
                else:
                    raise Exception('INTRODUCTION ERROR')

        while KeyboardInterrupt:
            events = sel.select()
            for key, mask in events:
                data = LocalTransport.read(key.fd)

                if key.fd == sys.stdin.fileno():
                    yield STDIN, data
                else:
                    yield REMOTE, data

        self.stop()

    def stop(self):
        [os.close(client_fd) for client_fd in self.write_descriptors]


class LocalLamport(Lamport):
    def request_handler(self, req):
        self.queue.append(
            (req['clocks'], req['id'])
        )
        self.queue.sort()
        self.clock = max(self.clock, req['clocks']) + 1
        self._rpc.send_to_fd(
            self._rpc.write_descriptors[req['id']], 'ACKNOW'
        )

    def acknowledgement_handler(self, req):
        self.unreceived_ack.remove(req['id'])

    def release_handler(self, req):
        self.clock = max(self.clock, req['clocks']) + 1
        self.queue = [
            (clock, host_id) for clock, host_id in self.queue
            if host_id != req['id']
            ]

    def request(self):
        self.queue.append((self.clock, self._rpc.id))
        self.queue.sort()
        self.logger.log(self.clock, 'REQUEST')
        self._rpc.broadcast('REQUEST', clocks=self.clock)

        self.unreceived_ack.update(
            [i for i in range(len(self._rpc.write_descriptors)) if i != self._rpc.id]
        )


if __name__ =='__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--id', '-i', type=int)
    parser.add_argument('--mutex-file', '-m', type=str, help='path to mutex file', default='mutex.txt')
    # parser.add_argument('--write-descriptors', nargs='+', help='specify all write descriptors in format fd1, fd2 ...')
    # parser.add_argument('--read-descriptors', nargs='+', help='specify all read descriptors in format fd1, fd2 ...')
    args = parser.parse_args()

    # write_descriptors = list(map(int, args.write_descriptors))
    # read_descriptors = list(map(int, args.read_descriptors))
    rpc = LocalRPC(args.id)
    lamport = LocalLamport(rpc, args.mutex_file)
    lamport.run()

