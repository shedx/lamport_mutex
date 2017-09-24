import time
import fcntl

from rpc.constants import STDIN, REMOTE


class Lamport:
    def __init__(self, rpc, mutex_file):
        self._rpc = rpc
        self.queue = []
        self.unreceived_ack = set()
        self.clock = 0
        self.stress_mode = False
        self.mutex_file = mutex_file

    def request(self, req):
        self.queue.append(
            (req['clocks'], self._rpc.addrs.index(req['host']))
        )
        self.queue.sort()
        self.clock = max(self.clock, req['clocks']) + 1
        self._rpc.send_to_fd(
            self._rpc.fd_by_host[req['host']], 'ACKNOW'
        )

    def acknowledgement(self, req):
        self.unreceived_ack.remove(req['host'])

    def release(self, req):
        self.queue = [
            (clock, host_id) for clock, host_id in self.queue
            if host_id != self._rpc.addrs.index(req['host'])
            ]

    def acquire(self):
        self.clock += 1
        self.queue.append((self.clock, self._rpc.id))
        self.queue.sort()
        self._rpc.broadcast('REQUEST', clocks=self.clock)
        for i, addr in enumerate(self._rpc.addrs):
            if i == self._rpc.id:
                continue
            self.unreceived_ack.add(addr)

    def start_stress_mode(self):
        self.acquire()
        self.stress_mode = True

    def get_mutex(self):
        mutex = open(self.mutex_file, 'a')
        fcntl.flock(mutex, fcntl.LOCK_EX | fcntl.LOCK_NB)
        mutex.write('pid: {} clock: {} real_time: {}\n' \
                    .format(self._rpc.id, self.clock, time.time()))
        fcntl.flock(mutex, fcntl.F_UNLCK)
        mutex.close()

    def check(self):
        if self.queue and self.queue[0][1] == self._rpc.id \
                and not self.unreceived_ack:
            print('{} locked mutex'.format(self._rpc.id))
            self.get_mutex()
            self.clock += 1
            print('{} unlocked mutex'.format(self._rpc.id))

            self.queue = [
                (clock, host_id) for clock, host_id in self.queue
                if host_id != self._rpc.id
                ]

            self._rpc.broadcast('RELEASE', clocks=self.clock)

            if self.stress_mode:
                self.acquire()

    def run(self):
        for req_type, data in self._rpc.run():
            if req_type == STDIN:
                if data['callback'] == 'ACQUIRE':
                    self.acquire()
                elif data['callback'] == 'STRESSMODE_START':
                    self.start_stress_mode()
                else:
                    print('local request', data)

            elif req_type == REMOTE:
                # cause after json serialisation tuple converts to list
                #  and list is unhashable so we can't use it as a key
                data['host'] = tuple(data['host'])
                if data['callback'] == 'REQUEST':
                    self.request(data)
                elif data['callback'] == 'ACKNOW':
                    self.acknowledgement(data)
                    self.check()
                elif data['callback'] == 'RELEASE':
                    self.release(data)
                    self.check()
