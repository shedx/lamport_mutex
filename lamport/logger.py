import os
import time


class LamportLogger:
    def __init__(self, pid, logdir='logs/'):
        self.pid = pid
        self.logdir = logdir
        self.path = os.path.join(self.logdir, '{}_pid_log'.format(self.pid))
        if os.path.exists(self.path):
            os.remove(self.path)

    def log(self, log_clock, event):
        if not os.path.exists(self.logdir):
            os.mkdir(self.logdir)
            time.sleep(0.5)

        with open(self.path, 'a') as file:
            file.write(
                '{} {} {} {}\n'.format(self.pid, time.time(), log_clock, event)
            )
