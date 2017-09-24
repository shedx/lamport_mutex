import random
import os
import subprocess

import time

import sys

rand = random.randint(0, 1000)
addrs = [('0.0.0.0', 12000 + rand + i) for i in range(10)]

pipes = []
for _ in range(10):
    pipes.append(os.pipe())

processes = []
for i in range(10):
    processes.append(subprocess.Popen(
        [
            'python3',
            'spawn.py',
            '-i', addrs[i][0],
            '-p', str(addrs[i][1]),
            '-a', *list(map(lambda a: '{}:{}'.format(a[0], a[1]), addrs)),
         ],
        stdin=pipes[i][0],
        stderr=sys.stderr,
        stdout=sys.stdout
    ))

time.sleep(5)

for _, write_fd in pipes:
    os.write(write_fd, b'{"callback": "STRESSMODE_START"}\n')

time.sleep(10)
for pr in processes:
    pr.kill()
