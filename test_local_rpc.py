import random
import unittest
import os
import subprocess
import time
import sys

from lamport.lamport import Lamport

from rpc.constants import STDIN, REMOTE


class MockedRPC:
    def __init__(self):
        self.id = 1
        self.addrs = [('0.0.0.0', 12922 + i) for i in range(5)]
        self.fd_by_host = {key: i for key, i in zip(self.addrs, range(5))}

    def send_to_fd(self, *args, **kwargs):
        pass

    def broadcast(self, *args, **kwargs):
        pass

    def run(self):

        return [(STDIN, {'callback': 'ACQUIRE'})]

class LocalTest(unittest.TestCase):
    def setUp(self):
        self.rpc = MockedRPC()
        self.lamport = Lamport(self.rpc, 'mutex.txt')

    def test_acquire(self):
        self.lamport.run()
        self.assertEqual(
            self.lamport.unreceived_ack,
            set([addr for addr in self.rpc.addrs if addr != self.rpc.addrs[1]])
        )
        self.assertTrue(len(self.lamport.queue) >= 1)

    def test_stressmode(self):
        def run():
            return [(STDIN, {'callback': 'STRESSMODE_START'})]
        self.rpc.run = run
        self.lamport.run()
        self.assertEqual(self.lamport.stress_mode, True)

    def test_request_handler(self):
        def run():
            return [(REMOTE, {'callback': 'REQUEST', 'clocks': 10000, 'host': self.rpc.addrs[2]})]
        self.rpc.run = run
        queue_len = len(self.lamport.queue)
        self.lamport.run()
        self.assertEqual(self.lamport.clock, 10001)
        self.assertTrue(len(self.lamport.queue) > queue_len)

    def test_check(self):
        def run():
            return [(REMOTE, {'callback': 'RELEASE', 'clocks': 100, 'host': self.rpc.addrs[2]})]
        self.rpc.run = run
        self.lamport.unreceived_ack.clear()
        self.lamport.queue = [(random.randint(1, 100), self.rpc.id)]
        self.lamport.run()
        self.assertEqual(self.lamport.queue, [])

        with open('mutex.txt', 'r') as file:
            lines = file.readlines()
        self.assertEqual(lines[-1].split()[1], str(self.rpc.id))
        self.assertEqual(lines[-1].split()[-1], 'unlocked')


if __name__ == '__main__':
    unittest.main()
