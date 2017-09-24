import unittest
import os
import subprocess
import time
import sys

from spawn_local import LocalTransport
from rpc.constants import INTRODUCTION


class LocalTest(unittest.TestCase):
    def setUp(self):
        self.pipes = []
        for _ in range(2):
            self.pipes.append(os.pipe())

        self.process = subprocess.Popen(
            [
                'python3',
                'spawn_local.py',
                '-i', str(1)
            ],
            stdin=self.pipes[0][0],
            stderr=sys.stderr,
            stdout=self.pipes[1][1],
        )

        self.write = self.pipes[0][1]
        self.read = self.pipes[1][0]
        time.sleep(6)
        LocalTransport.send(
            self.write,
            {
                'callback': INTRODUCTION,
                'id': 0
            }
        )

    def tearDown(self):
        self.process.kill()

    def test_acquire(self):
        LocalTransport.send(
            self.write,
            {
                'callback': 'ACQUIRE',
                'id': 0
            }
        )

        data = LocalTransport.read(self.read)
        self.assertEqual(data, {'callback': 'REQUEST', 'clock': 0, 'id': 1})
        data = LocalTransport.read(self.read)
        self.assertEqual(data, {'callback': 'RELEASE', 'clock': 1, 'id': 1})

    def test_stressmode(self):
        LocalTransport.send(
            self.write,
            {
                'callback': 'STRESSMODE_START',
                'id': 0
            }
        )

        data = LocalTransport.read(self.read)
        self.assertEqual(data, {'callback': 'REQUEST', 'clock': 2, 'id': 1})
        data = LocalTransport.read(self.read)
        self.assertEqual(data, {'callback': 'RELEASE', 'clock': 3, 'id': 1})


if __name__ == '__main__':
    unittest.main()
